"""Generic CSV adapter driven by a declarative mapping.

The three adapters that shipped before this one target three named research
datasets. They are useful to reproduce a published result and useless to
someone arriving with their own export, who has to write Python to convert a
file whose only difficulty is that its columns are called something else.

This adapter takes the mapping as data instead:

.. code-block:: yaml

    dataset_id: fr_myfleet_2026
    device_id: truck_07
    read:
      sep: ";"
      decimal: ","
    columns:
      ts:         {column: "Date UTC",  unit: iso8601}
      lat:        {column: "Latitude",  unit: deg}
      lon:        {column: "Longitude", unit: deg}
      speed_mps:  {column: "Vitesse",   unit: km/h}
      ax_mps2:    {column: "AccX",      unit: g}
      ay_mps2:    {column: "AccY",      unit: g}
      az_mps2:    {column: "AccZ",      unit: g}
      hdop:       {column: "HDOP"}

The unit is not optional on a column that carries one. That is the whole point:
the commonest defect in a telematics dataset is a correct column name over
values in the wrong unit, and every schema check in existence passes it. Asking
for the unit at the moment the column is named moves the question to the one
place where the answer is known — in front of the source's documentation —
instead of leaving it to be inferred later from magnitudes.

Mappings are files. They can be reviewed, diffed, sent to whoever produced the
export and corrected by them, and they are the same artefact whether the
conversion runs from Python or from ``tele convert csv``.
"""

from __future__ import annotations

import difflib
import warnings
from pathlib import Path

import pandas as pd
import yaml

from ..core.accounting import RowAccount, drop_duplicate_ts
from ..core.schemas import ALL_KNOWN_COLUMNS, coerce_schema_dtypes
from ..core.units import UnknownUnitError, convert_column, known_units, quantity_of

__all__ = ["MappingError", "load", "load_mapping", "manifest", "template"]

_READ_KEYS = {"sep", "delimiter", "decimal", "encoding", "skiprows", "header",
              "thousands", "na_values", "comment", "quotechar", "nrows",
              "skipfooter", "engine", "true_values", "false_values"}


class GuardWarning(UserWarning):
    """A declared guard found something, and no caller asked for the findings."""


class MappingError(ValueError):
    """The mapping is not usable against this file.

    Every message names what was wrong, what was expected, and — when the
    mistake is a misspelling — what was probably meant.
    """


# ---------------------------------------------------------------------------
# Reading and checking the mapping
# ---------------------------------------------------------------------------

def load_mapping(mapping) -> dict:
    """Accept a mapping as a path, a YAML string, or an already-parsed dict."""
    if isinstance(mapping, dict):
        return mapping
    if isinstance(mapping, str | Path):
        p = Path(mapping)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        if isinstance(mapping, str) and ("\n" in mapping or ":" in mapping):
            return yaml.safe_load(mapping) or {}
        raise MappingError(f"Mapping file not found: {mapping}")
    raise MappingError(f"Cannot read a mapping from {type(mapping).__name__}")


def _suggest(name, candidates) -> str:
    """A "did you mean" for a column name, when one can be offered.

    A headerless source addresses columns by index, so both the name and the
    candidates may be integers. ``difflib`` works on sequences and raises
    ``TypeError`` on an int, which replaced the clear "source has no such
    column" message with a traceback from inside the standard library — in
    precisely the case where the message matters most, a positional mapping
    whose file lost a field. There is no useful spelling suggestion for an
    index, so the honest answer is to offer none.
    """
    names = [c for c in candidates if isinstance(c, str)]
    if not isinstance(name, str) or not names:
        return ""
    close = difflib.get_close_matches(name, names, n=3, cutoff=0.6)
    return f" Did you mean {', '.join(repr(c) for c in close)}?" if close else ""


PROVENANCE_VALUES = ("measured", "derived", "absent")

# Columns whose provenance decides whether an analysis is valid, so their
# absence is stated rather than left to inference. A speed and a heading are
# the two an adapter commonly computes; an altitude is the one a source
# commonly omits.
_PROVENANCE_WATCHED = ("speed_mps", "heading_deg", "altitude_gps_m")


def _provenance_of(columns: dict[str, dict]) -> dict[str, str]:
    """Declare, per column, where the value came from (SPEC-01 §2.14).

    The adapter knows one thing for certain: whether it read a column from the
    file or made it up. It cannot know whether the *source* computed that
    column before writing it — a fleet API that differentiates two positions
    and calls the result a speed produces a file the adapter cannot tell from a
    Doppler one. So a column read from the file defaults to ``measured`` and
    the mapping may say otherwise, per column, next to its unit.

    Getting this wrong is not cosmetic. Selecting stationary samples by a
    Doppler speed and then measuring position scatter yields the receiver
    noise; doing it with a position-derived speed is circular and returns a
    plausible number that means nothing, with no error raised anywhere.
    """
    out: dict[str, str] = {}
    for target, rule in columns.items():
        declared = rule.get("provenance")
        if declared is not None:
            if declared not in PROVENANCE_VALUES:
                raise MappingError(
                    f"columns.{target}: provenance must be one of "
                    f"{list(PROVENANCE_VALUES)}, got {declared!r}")
            out[target] = declared
        elif "column" in rule:
            out[target] = "measured"
        else:
            # a constant is neither measured nor computed from the data
            out[target] = "derived"
    for target in _PROVENANCE_WATCHED:
        out.setdefault(target, "absent")
    return out


# ---------------------------------------------------------------------------
# Guards against a silent column shift
# ---------------------------------------------------------------------------

# Rows read to test the guards. A shift is structural: it is there on the first
# line or it is not there at all. Re-reading a whole export to check it would
# double the load time of a large source for nothing.
GUARD_SAMPLE_ROWS = 500


def _is_blank(series) -> bool:
    """True when a column carries no value at all in the rows examined."""
    if series.isna().all():
        return True
    return series.astype("string").str.strip().replace("", pd.NA).isna().all()


def _check_guards(raw: pd.DataFrame, out: pd.DataFrame, spec: dict) -> list[str]:
    """Test the invariants the mapping declares, and report what fails.

    Why this exists. The docstring of this module argues that a wrong unit is
    the most common silent failure a declarative mapping can carry. A wrong
    *position* is the same failure and it is worse. A wrong unit usually
    produces implausible values — a speed in the hundreds eventually gets
    noticed — whereas a shifted column produces plausible values in plausible
    columns. Observed on a real headerless export: one field removed mid-file,
    and `lat` reads 7.79, which is the longitude, while the speed reads
    133 km/h, which is the heading. Nothing raises, and no range check helps,
    because 7.79 is a perfectly valid latitude.

    Positional addressing is what this adapter introduces in its own right: it
    is what lets someone map a headerless CSV without writing Python. The
    exposure comes with the feature, so the guard belongs here.

    What actually catches it. Not the field count — in the observed case the
    count stayed correct and only the order moved. Not a range check either,
    for the reason above. What caught it was a *semantic* invariant: four
    columns empty across every extract received since April started carrying
    values. That does not prove a shift, but it is the only signal that arrives
    before the numbers are wrong.

    Reporting, not refusing. A column may legitimately start being filled one
    day. Blocking a conversion on that would cost more than it saves; passing
    it over in silence publishes shifted numbers. So the findings are returned
    and the caller decides.
    """
    guards = spec.get("guards") or {}
    if not guards:
        return []
    unknown = set(guards) - {"expected_fields", "always_empty", "range"}
    if unknown:
        raise MappingError(
            f"guards: unsupported key(s) {sorted(unknown)}. "
            f"Supported: ['always_empty', 'expected_fields', 'range']")

    head = raw.head(GUARD_SAMPLE_ROWS)
    found: list[str] = []

    expected = guards.get("expected_fields")
    if expected is not None:
        n = len(raw.columns)
        if n < int(expected):
            found.append(
                f"expected_fields: source has {n} fields, mapping expects at "
                f"least {expected}; a field was removed and every column after "
                f"it now reads its neighbour")
        elif n > int(expected):
            # A trailing separator adds an empty field without shifting
            # anything, and exports acquire one without warning. Crying wolf on
            # that is how a guard gets switched off.
            surplus = [c for c in raw.columns[int(expected):]
                       if not _is_blank(head[c])]
            if surplus:
                found.append(
                    f"expected_fields: source has {n} fields for an expected "
                    f"{expected}, and the surplus carries values ({surplus})")

    for idx in guards.get("always_empty") or []:
        if not isinstance(idx, int) or not 0 <= idx < len(raw.columns):
            found.append(
                f"always_empty: index {idx} is outside the source's "
                f"{len(raw.columns)} fields")
            continue
        col = raw.columns[idx]
        if not _is_blank(head[col]):
            # a headerless source names its columns by index, so repeating the
            # index as a name says nothing
            named = "" if str(col) == str(idx) else f" ({col})"
            found.append(
                f"always_empty: field {idx}{named} was empty in every known "
                f"extract and now carries values; the columns after it may be "
                f"shifted")

    for target, bounds in (guards.get("range") or {}).items():
        if target not in out.columns:
            found.append(f"range: {target} is not produced by this mapping")
            continue
        lo, hi = bounds
        v = pd.to_numeric(out[target].head(GUARD_SAMPLE_ROWS), errors="coerce")
        n_bad = int(((v < lo) | (v > hi)).sum())
        if n_bad:
            found.append(
                f"range: {target} leaves [{lo}, {hi}] on {n_bad} of the first "
                f"{min(len(out), GUARD_SAMPLE_ROWS)} rows")

    return found


def _normalise_columns(spec) -> dict[str, dict]:
    """Accept both ``{target: source}`` and ``{target: {column:, unit:}}``."""
    if not spec:
        raise MappingError("Mapping has no 'columns' block; nothing to convert")
    out: dict[str, dict] = {}
    for target, rule in spec.items():
        if isinstance(rule, str):
            rule = {"column": rule}
        if not isinstance(rule, dict):
            raise MappingError(
                f"columns.{target} must be a source column name or a mapping "
                f"with a 'column' key, got {type(rule).__name__}")
        if "column" not in rule and "value" not in rule:
            raise MappingError(
                f"columns.{target} declares neither 'column' (read from the file) "
                f"nor 'value' (a constant for every row)")
        out[str(target)] = dict(rule)
    return out


def _check_targets(columns: dict[str, dict]) -> None:
    for target, rule in columns.items():
        if target.startswith("x_"):
            if "unit" in rule:
                raise MappingError(
                    f"columns.{target}: vendor extras keep their source unit by "
                    f"definition (SPEC-01 §2.10); remove the 'unit' key")
            continue
        if target not in ALL_KNOWN_COLUMNS:
            raise MappingError(
                f"columns.{target}: not a Telemachus column."
                f"{_suggest(target, ALL_KNOWN_COLUMNS)} "
                f"A source field with no standard equivalent goes to "
                f"x_<source>_{target} (SPEC-01 §2.10)")

        quantity = quantity_of(target)
        if quantity and "unit" not in rule:
            raise MappingError(
                f"columns.{target}: 'unit' is required for this column. "
                f"Declare what the source carries, even when it is already "
                f"canonical: {known_units(quantity)}")
        if quantity is None and "unit" in rule:
            raise MappingError(
                f"columns.{target}: this column carries no unit; remove the "
                f"'unit' key")

    if "ts" not in columns:
        raise MappingError(
            "columns.ts is required: without a timestamp there is no record. "
            "Declare its unit too, e.g. {column: time, unit: iso8601} or "
            "{column: epoch, unit: epoch_ms}")


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def load(source_path, *, mapping, account: RowAccount | None = None,
         anomalies: list | None = None,
         extras: str = "drop") -> pd.DataFrame:
    """Read a CSV through a declarative mapping and return a conformant frame.

    Parameters
    ----------
    source_path : str or Path
        A CSV file, or a directory whose ``*.csv`` files are read in name order
        and concatenated. A per-file source column can be declared as
        ``{value: ...}`` only when it is the same for all files; otherwise
        convert the files one at a time.
    mapping : dict, str or Path
        The mapping, as a parsed dict, a path to a YAML file, or YAML text.
    account : RowAccount or None
        Filled in with the row accounting of SPEC-02 §3.5 when supplied. The
        adapter drops only what SPEC-01 §3 forbids it to keep — rows with an
        unreadable timestamp, and repeats of a timestamp already seen — and
        each of those is counted under its own reason.
    anomalies : list or None
        Filled in with what the ``guards`` block of the mapping found, one
        string per finding. A guard reports and does not refuse: a column may
        legitimately start being filled one day, and blocking a conversion on
        that would cost more than it saves.

        Left at ``None`` the guards still run, and anything they find is
        raised as a ``GuardWarning`` rather than dropped. It cannot reach the
        manifest, which is why :func:`manifest` then records ``findings: null``
        — an unknown that says so, rather than an empty list that would read as
        "checked, nothing found".
    extras : {"drop", "keep"}
        What to do with source columns the mapping does not name. ``keep``
        carries them through as ``x_csv_<name>``, which satisfies the coverage
        rule of SPEC-01 §2.13 at the cost of a wider file.

    Returns
    -------
    pd.DataFrame
        Telemachus columns in canonical units, sorted by ``ts``.
    """
    spec = load_mapping(mapping)
    columns = _normalise_columns(spec.get("columns"))
    _check_targets(columns)

    read_opts = {k: v for k, v in (spec.get("read") or {}).items() if k in _READ_KEYS}
    unknown_opts = set(spec.get("read") or {}) - _READ_KEYS
    if unknown_opts:
        raise MappingError(
            f"read: unsupported option(s) {sorted(unknown_opts)}. "
            f"Supported: {sorted(_READ_KEYS)}")

    raw = _read_source(Path(source_path), read_opts)

    missing = [rule["column"] for rule in columns.values()
               if "column" in rule and rule["column"] not in raw.columns]
    if missing:
        raise MappingError(
            f"Source has no column(s) {missing}."
            f"{_suggest(missing[0], raw.columns)} "
            f"Available: {list(raw.columns)}")

    if account is not None:
        account.raw_rows_in = len(raw)

    out = pd.DataFrame(index=raw.index)
    for target, rule in columns.items():
        if "value" in rule and "column" not in rule:
            out[target] = rule["value"]
            continue
        values = raw[rule["column"]]
        unit = rule.get("unit")
        if unit is None:
            out[target] = values
            continue
        try:
            # convert_column, not convert: the target name carries half the
            # unit. `ts_received_ms` asks for milliseconds and calling convert()
            # with the quantity alone silently returned a datetime, which the
            # integer cast then published at whatever resolution it found.
            out[target] = convert_column(values, target, unit, fmt=rule.get("format"))
        except UnknownUnitError as exc:
            raise MappingError(f"columns.{target}: {exc}") from exc

    if extras == "keep":
        named = {rule["column"] for rule in columns.values() if "column" in rule}
        for col in raw.columns:
            if col not in named:
                out[f"x_csv_{_slug(col)}"] = raw[col]
    elif extras != "drop":
        raise MappingError(f"extras must be 'drop' or 'keep', got {extras!r}")

    for key in ("device_id", "trip_id"):
        if key not in spec or key in out.columns:
            continue
        rule = spec[key]
        if isinstance(rule, dict):
            # A source that carries several entities in one file names the
            # entity in a column, not in the mapping. Movebank exports are the
            # common case: one file, thirty animals, one column telling them
            # apart. Accepting {column: ...} here and dropping it on the floor
            # was worse than refusing it, because drop_duplicate_ts then keys
            # on an all-null device_id, which is the same as keying on ts
            # alone, and one entity survives out of thirty.
            if set(rule) - {"column"}:
                raise MappingError(
                    f"{key}: only a scalar or {{column: ...}} is accepted, "
                    f"got {sorted(rule)}")
            if "column" not in rule:
                raise MappingError(f"{key}: {{column: ...}} is missing 'column'")
            src = rule["column"]
            if src not in raw.columns:
                raise MappingError(
                    f"{key}: source has no column {src!r}."
                    f"{_suggest(src, raw.columns)} "
                    f"Available: {list(raw.columns)}")
            out[key] = raw[src]
        else:
            out[key] = rule

    # The guards run whether or not the caller wants the findings: a mapping
    # that declares an invalid guard should say so at conversion time, not the
    # first time someone asks for the report.
    found = _check_guards(raw, out, spec)
    if anomalies is not None:
        anomalies.extend(found)
    elif found:
        # A caller who did not read the signature still gets told. Losing a
        # guard's report in silence is the failure this whole block exists to
        # prevent, and it would be a poor joke to reproduce it here.
        warnings.warn(
            "csv_mapping guards found "
            + ("; ".join(found))
            + ". Pass anomalies=[] to collect them and record them in the "
              "manifest.",
            GuardWarning, stacklevel=2)

    return _finish(out, account)


def _finish(out: pd.DataFrame, account: RowAccount | None) -> pd.DataFrame:
    """Apply the two drops SPEC-01 §3 forces, then conform the types."""
    before = len(out)
    out = out[out["ts"].notna()]
    if account is not None:
        account.drop("unparseable_ts", before - len(out))

    out = out.sort_values("ts", kind="stable")
    out, account = drop_duplicate_ts(out, account)

    out = coerce_schema_dtypes(out).reset_index(drop=True)
    return out


def _read_source(path: Path, read_opts: dict) -> pd.DataFrame:
    if path.is_dir():
        files = sorted(path.glob("*.csv"))
        if not files:
            raise MappingError(f"No .csv file in {path}")
        return pd.concat([pd.read_csv(f, **read_opts) for f in files],
                         ignore_index=True)
    if not path.exists():
        raise MappingError(f"Source not found: {path}")
    return pd.read_csv(path, **read_opts)


def _slug(name: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in str(name)]
    return "".join(keep).strip("_")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def manifest(mapping, *, account: RowAccount | None = None,
             rows_out: int | None = None,
             anomalies: list | None = None) -> dict:
    """Build the SPEC-02 manifest the mapping describes.

    Whatever the mapping declares under ``manifest`` is carried through as-is,
    so a user can put their license, provenance and sensor rates in the same
    file as the column mapping. The row accounting is filled in from the
    conversion that just ran, which is the only moment it is known.
    """
    spec = load_mapping(mapping)
    out = dict(spec.get("manifest") or {})
    out.setdefault("dataset_id", spec.get("dataset_id", "unnamed_dataset"))
    out.setdefault("schema_version", "telemachus-1.0")
    columns = _normalise_columns(spec.get("columns"))
    out.setdefault("profile", _profile_of(columns))
    out.setdefault("column_provenance", _provenance_of(columns))
    source = dict(out.get("source") or {})
    source.setdefault("type", "open_external")
    source.setdefault("adapter_status", "draft")
    if account is not None and rows_out is not None:
        source["metrics"] = account.finish(rows_out=rows_out)
    guards = spec.get("guards")
    if guards or anomalies:
        # What was checked, and what it found. `findings: null` when the
        # caller never collected them: an empty list here would read as
        # "checked, nothing found" when it means "checked, result not kept",
        # and a manifest that asserts a clean result it never saw is worse than
        # one that admits it does not know.
        source["guards"] = {
            "declared": dict(guards or {}),
            "findings": list(anomalies) if anomalies is not None else None,
        }
    out["source"] = source
    return out


def _profile_of(columns: dict) -> str:
    names = set(columns)
    if {"gx_rad_s", "gy_rad_s", "gz_rad_s"} <= names:
        return "full"
    if {"ax_mps2", "ay_mps2", "az_mps2"} <= names:
        return "imu"
    return "core"


# ---------------------------------------------------------------------------
# Getting started
# ---------------------------------------------------------------------------

def template(source_path=None) -> str:
    """A commented mapping to start from, pre-filled with the source's columns.

    Produced by ``tele mapping-template <file.csv>``. Guessing which source
    column is which Telemachus column would be a service to nobody: the guess
    would be right often enough to be trusted and wrong often enough to matter,
    and the unit — the part that actually causes the damage — cannot be guessed
    at all. So the template lists what the file contains and leaves the
    decisions blank.
    """
    lines = [
        "# Telemachus CSV mapping. Convert with:",
        "#   tele convert csv <source> --mapping this-file.yaml --outdir out/",
        "#",
        "# Every column that carries a unit must declare it. Accepted spellings:",
        f"#   speed         {known_units('speed')}",
        f"#   acceleration  {known_units('acceleration')}",
        f"#   angular rate  {known_units('angular_rate')}",
        f"#   lat / lon     {known_units('latlon')}",
        f"#   timestamp     {known_units('time')}",
        "",
        "dataset_id: xx_my_dataset_2026",
        "device_id: device_1",
        "",
        "read:",
        "  sep: ','",
        "",
        "columns:",
        "  ts: {column: CHANGE_ME, unit: iso8601}",
        "  lat: {column: CHANGE_ME, unit: deg}",
        "  lon: {column: CHANGE_ME, unit: deg}",
        "  speed_mps: {column: CHANGE_ME, unit: m/s}",
    ]
    if source_path is not None:
        head = pd.read_csv(source_path, nrows=5)
        lines += ["", "# Columns found in the source:"]
        lines += [f"#   {c}" for c in head.columns]
    return "\n".join(lines) + "\n"
