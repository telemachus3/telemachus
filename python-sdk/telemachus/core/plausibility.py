"""Unit plausibility — refusing a file whose numbers cannot be what they claim.

A wrong unit is the failure mode this format is least able to survive and most
likely to meet. Every schema check passes: the column is named ``speed_mps``,
its type is float32, its values are positive and finite. Only the magnitudes
are wrong, by a factor 3.6, and nothing downstream will say so — the harsh
braking threshold simply never fires, or fires everywhere.

Two families of test are used here, and the difference between them decides
whether a finding is an error or a warning.

**Cross-checks** compare a column against another measurement of the same
thing. ``speed_mps`` against the speed implied by consecutive positions is the
strongest one available: it is independent, it is present in every conformant
file, and the ratio it returns names the wrong unit outright. A ratio of 3.6
is not a suspicion.

The strength is conditional on the independence, and the independence is not
guaranteed. An adapter that fills ``speed_mps`` by differentiating the very
positions it will later be compared against turns the test into a tautology:
the ratio is exactly 1, the report is empty, and the silence reads as a pass.
The check therefore measures the *scatter* of the ratio as well as its median,
and says when it is looking at a mirror.

**Magnitude checks** compare a column against what physics allows. They are
weaker, because a plausible magnitude can still be wrong and an implausible one
can be genuine, so they warn rather than fail — except where the value is
outside anything a ground carrier can do, which SPEC-03 §4.4 already treats as
a physics check.

Accelerometer magnitude is read against the declared AccPeriod frame
(SPEC-01 §3 rule 3): ``|a| ≈ 9.81`` for ``raw``, ``≈ 0`` for ``compensated``.
Without that declaration the same number means both "correct raw" and "wrong
by 9.8 in compensated", so the check reports what it sees and does not judge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .units import EPOCH_UNIT_BY_SUFFIX, G0, epoch_unit_of, from_epoch

__all__ = ["Finding", "check_epoch_columns", "check_heading_convention",
           "check_timestamps", "check_units"]

# Ratios worth naming when a cross-check finds one. Half a percent of tolerance
# either side: a real unit error lands on the ratio almost exactly, while a
# genuine disagreement between two sensors wanders.
_SPEED_RATIOS = [
    (3.6, "km/h", 0.08),
    (1.94384, "knots", 0.08),
    (2.23694, "mph", 0.08),
    (100.0, "cm/s", 0.10),
]

# Above this, a ground carrier is no longer plausible. SPEC-03 §4.4 states the
# same bound as a physics check.
MAX_GROUND_SPEED_MPS = 100.0

#: No GNSS receiver can date a fix before GPS time began. A timestamp under this
#: floor was not read from the constellation, which is the only clock a
#: telematics device has that survives a power cut.
GPS_EPOCH = pd.Timestamp("1980-01-06T00:00:00Z")

#: Tolerance on "the future". Generous on purpose: a device clock drifts, a
#: gateway stamps on receipt, and neither is worth an error. Days ahead is not
#: drift.
FUTURE_TOLERANCE = pd.Timedelta(days=2)

#: A single Telemachus file spanning longer than this is not one collection.
MAX_PLAUSIBLE_SPAN = pd.Timedelta(days=3653)   # ten years

#: Nanoseconds in one tick of each epoch resolution, used to name the factor
#: between the resolution a column promises and the one its values carry.
_NS_PER_TICK = {"s": 1_000_000_000, "ms": 1_000_000, "us": 1_000, "ns": 1}

#: Written out, because "the column carries microseconds" is a diagnosis and
#: "the column carries us" is a typo.
_RESOLUTION_NAMES = {"s": "seconds", "ms": "milliseconds",
                     "us": "microseconds", "ns": "nanoseconds"}


def _ticks_of(instant: pd.Timestamp, unit: str) -> int:
    """Ticks since the Unix epoch, for stating how long a correct value is."""
    return int((instant - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(1, unit))


@dataclass(frozen=True)
class Finding:
    """One plausibility result.

    ``severity`` is ``"error"`` when the values cannot be what the column name
    says, and ``"warning"`` when they merely look unlikely.
    """

    column: str
    severity: str
    message: str

    def __str__(self) -> str:
        return self.message


def _finite(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()


def _norm(df: pd.DataFrame, cols: tuple[str, str, str]) -> pd.Series | None:
    if not set(cols) <= set(df.columns):
        return None
    block = df[list(cols)].apply(pd.to_numeric, errors="coerce").dropna()
    if block.empty:
        return None
    return pd.Series(np.linalg.norm(block.to_numpy(dtype=float), axis=1))


def _name_ratio(ratio: float, table) -> str | None:
    for value, name, tol in table:
        if abs(ratio - value) <= value * tol:
            return name
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_speed_against_positions(df: pd.DataFrame,
                                   declared_origin: str | None = None,
                                   ) -> list[Finding]:
    """Compare the declared speed with the speed the positions imply.

    Only pairs of consecutive fixes closer than 10 s and actually moving are
    used: at a standstill the ratio is 0/0, and across a long gap the straight
    line between two fixes understates the distance travelled, which would
    manufacture a ratio of its own.
    """
    need = {"ts", "lat", "lon", "speed_mps"}
    if not need <= set(df.columns):
        return []

    from ..metrics.basic import haversine_m

    # Grouped by entity, and that is not a detail. This function differences
    # two consecutive rows, so on a frame carrying several devices sorted by
    # time the rows interleave and every step jumps between vehicles. Measured
    # on two devices forty kilometres apart: the implied speed explodes, the
    # median ratio collapses to 0.00, and a checker built to catch wrong units
    # raises a false alarm on data that is perfectly sound.
    #
    # The invariant, which applies to every function in the library that
    # differences consecutive rows: either group by the entity, or say in the
    # signature that you do not.
    keep = ["ts", "lat", "lon", "speed_mps"]
    by = "device_id" if "device_id" in df.columns else None
    if by:
        keep.append(by)

    fixes = df.loc[df["lat"].notna() & df["lon"].notna() & df["speed_mps"].notna(),
                   keep].copy()
    if len(fixes) < 30:
        return []
    fixes["ts"] = pd.to_datetime(fixes["ts"], utc=True, errors="coerce")
    fixes = fixes.dropna(subset=["ts"])
    fixes = fixes.sort_values([by, "ts"] if by else ["ts"])
    if len(fixes) < 30:
        return []

    if by:
        grp = fixes.groupby(by, sort=False)
        dt = grp["ts"].diff().dt.total_seconds().to_numpy()
        prev_lat, prev_lon = grp["lat"].shift(), grp["lon"].shift()
    else:
        dt = fixes["ts"].diff().dt.total_seconds().to_numpy()
        prev_lat, prev_lon = fixes["lat"].shift(), fixes["lon"].shift()
    dist = np.asarray(haversine_m(prev_lat, prev_lon,
                                  fixes["lat"], fixes["lon"]), dtype=float)
    declared = fixes["speed_mps"].to_numpy(dtype=float)

    usable = (dt > 0) & (dt <= 10.0) & np.isfinite(dist) & (declared > 0)
    if usable.sum() < 30:
        return []

    implied = dist[usable] / dt[usable]
    moving = implied > 2.0          # below walking pace the ratio is noise
    if moving.sum() < 30:
        return []

    ratios = declared[usable][moving] / implied[moving]
    ratio = float(np.median(ratios))
    if not np.isfinite(ratio) or ratio <= 0:
        return []

    # A wrong unit is a wrong unit whatever the provenance: a column derived
    # from positions and then scaled by 3.6 still carries km/h, and the ratio
    # still names it. So the unit test comes first, before any question of
    # independence.
    unit = _name_ratio(ratio, _SPEED_RATIOS)
    if unit:
        return [Finding(
            "speed_mps", "error",
            f"speed_mps is {ratio:.2f}x the speed its own positions imply, which is "
            f"the ratio of {unit} to m/s: the column appears to carry {unit}",
        )]

    # No unit named, ratio near 1 — but is that agreement worth anything? A
    # Doppler speed disagrees with its positions sample by sample (curvature,
    # receiver noise, timing), so the ratio scatters. A column *derived* from
    # those same positions cannot: it tracks them exactly, and the cross-check
    # would be comparing the data to itself, then reporting a clean bill of
    # health it has no grounds to give. Real independent speeds show an
    # interquartile spread of several percent; a derived one shows none.
    spread = float(np.subtract(*np.percentile(ratios, [75, 25])))
    tracks_its_own_positions = spread < 0.01

    # What that dispersion MEANS depends on what the manifest claims, and this
    # is where a declaration earns its keep. Alone, the measurement can only
    # hedge: "tracks its positions exactly" has an innocent reading, since a
    # constant speed on a straight road is indistinguishable from a derivation.
    # Beside a declaration, the same number stops being a guess about the data
    # and becomes a check ON the declaration.
    if declared_origin == "measured" and tracks_its_own_positions:
        return [Finding(
            "speed_mps", "error",
            f"speed_mps is declared `measured` but tracks the speed its own "
            f"positions imply exactly (ratio spread {spread:.4f}; an independent "
            f"measurement scatters by several percent). Two sensors do not agree "
            f"to that precision. Either the column was computed from the "
            f"positions and the declaration is false, or it was measured and "
            f"something upstream overwrote it — either way the dataset is not "
            f"what it says it is (SPEC-02 §3.15)")]

    if declared_origin in ("derived", "absent"):
        # Declared derived: the agreement is expected, the cross-check cannot
        # run, and repeating that on every file would be noise. Silence is what
        # declaring buys.
        return []

    if tracks_its_own_positions:
        return [Finding(
            "speed_mps", "warning",
            f"speed_mps tracks the speed its own positions imply too closely "
            f"(ratio spread {spread:.4f}) to be an independent measurement: it "
            f"appears to be derived from them. This check therefore cannot "
            f"validate it — a derived column always agrees with its source. "
            f"Nothing here says the values are wrong, only that they are "
            f"unverified. Declaring `column_provenance.speed_mps` settles it "
            f"(SPEC-02 §3.15)",
        )]

    if ratio > 1.5 or ratio < 0.67:
        return [Finding(
            "speed_mps", "warning",
            f"speed_mps is {ratio:.2f}x the speed its own positions imply "
            f"(expected ~1.0); no known unit matches that ratio",
        )]
    return []


def _check_speed_magnitude(df: pd.DataFrame) -> list[Finding]:
    out: list[Finding] = []
    for col in ("speed_mps", "speed_obd_mps"):
        if col not in df.columns:
            continue
        s = _finite(df[col])
        if s.empty:
            continue
        p999 = float(s.quantile(0.999))
        if p999 > MAX_GROUND_SPEED_MPS:
            out.append(Finding(
                col, "error",
                f"{col} reaches {p999:.0f} m/s ({p999 * 3.6:.0f} km/h) at the 99.9th "
                f"percentile, above the {MAX_GROUND_SPEED_MPS:.0f} m/s physics bound "
                f"of SPEC-03 §4.4: the column is most likely in km/h",
            ))
    return out


def _check_accel(df: pd.DataFrame, acc_frame: str | None) -> list[Finding]:
    norm = _norm(df, ("ax_mps2", "ay_mps2", "az_mps2"))
    if norm is None or len(norm) < 30:
        return []
    median = float(norm.median())

    # A median |a| near 1 is the signature of a file left in g. Near 9.81 it is
    # a raw frame. Near 0 it is a compensated one. The three are far enough
    # apart to be told apart; what they mean depends on the declared frame.
    looks_like_g = 0.7 <= median <= 1.4
    looks_raw = G0 - 1.5 <= median <= G0 + 1.5
    looks_compensated = median < 0.5

    if acc_frame == "raw":
        if looks_like_g:
            return [Finding(
                "ax_mps2", "error",
                f"|a| has median {median:.2f} m/s² in an AccPeriod declared `raw`, "
                f"where SPEC-01 §3 expects ~{G0:.2f}: the accelerometer columns "
                f"appear to still be in g",
            )]
        if not looks_raw:
            return [Finding(
                "ax_mps2", "warning",
                f"|a| has median {median:.2f} m/s² in an AccPeriod declared `raw`, "
                f"where SPEC-01 §3 expects {G0:.2f} ± 1.0",
            )]
        return []

    if acc_frame == "compensated":
        if looks_raw:
            return [Finding(
                "ax_mps2", "error",
                f"|a| has median {median:.2f} m/s² in an AccPeriod declared "
                f"`compensated`, where SPEC-01 §3 expects ~0: gravity is still "
                f"present, so either the frame is `raw` or the compensation did "
                f"not run",
            )]
        if not looks_compensated:
            return [Finding(
                "ax_mps2", "warning",
                f"|a| has median {median:.2f} m/s² in an AccPeriod declared "
                f"`compensated`, where SPEC-01 §3 expects 0 ± 1.0",
            )]
        return []

    # No frame declared. `partial` covers the whole band between the two, so
    # only a magnitude that fits neither reading says anything.
    if looks_like_g:
        return [Finding(
            "ax_mps2", "warning",
            f"|a| has median {median:.2f} m/s², which is what a raw signal left "
            f"in g looks like. Declare the AccPeriod frame (SPEC-02 §3.7) so this "
            f"can be checked rather than guessed",
        )]
    if median > 3 * G0:
        return [Finding(
            "ax_mps2", "error",
            f"|a| has median {median:.2f} m/s², over three times gravity: no "
            f"carrier sustains that, so the columns are not in m/s²",
        )]
    return []


def _check_gyro(df: pd.DataFrame) -> list[Finding]:
    norm = _norm(df, ("gx_rad_s", "gy_rad_s", "gz_rad_s"))
    if norm is None or len(norm) < 30:
        return []
    p99 = float(norm.quantile(0.99))
    # A vehicle turning hard runs at 0.5–1 rad/s; a handheld phone can reach a
    # few. 17 rad/s is 1000 deg/s, which is the full scale of most MEMS parts:
    # reaching it at the 99th percentile means the numbers are degrees.
    if p99 > 17.0:
        return [Finding(
            "gx_rad_s", "error",
            f"|ω| reaches {p99:.0f} rad/s ({np.degrees(p99):.0f} deg/s) at the 99th "
            f"percentile, beyond the full scale of common MEMS gyroscopes: the "
            f"columns appear to carry deg/s",
        )]
    if p99 > 8.0:
        return [Finding(
            "gx_rad_s", "warning",
            f"|ω| reaches {p99:.1f} rad/s at the 99th percentile, high for a "
            f"vehicle-mounted sensor",
        )]
    return []


def _check_magneto(df: pd.DataFrame) -> list[Finding]:
    norm = _norm(df, ("mx_uT", "my_uT", "mz_uT"))
    if norm is None or len(norm) < 30:
        return []
    median = float(norm.median())
    # The Earth's field runs 25–65 µT everywhere on the surface. A vehicle's own
    # steel distorts it, so the band is widened rather than tightened.
    if median <= 0:
        return []
    if 10.0 <= median <= 150.0:
        return []
    for factor, unit in ((1e-3, "nT"), (1e3, "mT"), (100.0, "gauss"), (0.1, "milligauss")):
        if 10.0 <= median * factor <= 150.0:
            return [Finding(
                "mx_uT", "error",
                f"|m| has median {median:.3g} µT, outside the 25–65 µT of the "
                f"Earth's field but consistent with {unit}: the columns appear to "
                f"carry {unit}",
            )]
    return [Finding(
        "mx_uT", "warning",
        f"|m| has median {median:.3g} µT, outside the 25–65 µT of the Earth's field",
    )]


def _check_altitude(df: pd.DataFrame) -> list[Finding]:
    if "altitude_gps_m" not in df.columns:
        return []
    a = _finite(df["altitude_gps_m"])
    if a.empty:
        return []
    peak = float(a.abs().quantile(0.99))
    if peak > 9000.0:
        return [Finding(
            "altitude_gps_m", "error",
            f"altitude_gps_m reaches {peak:.0f} m at the 99th percentile, above any "
            f"road on Earth: the column is most likely in feet",
        )]
    return []


def check_heading_convention(values) -> Finding | None:
    """Classify a `heading_deg` column that falls outside [0, 360).

    SPEC-01 §2.5 fixes the canonical range, and a validator that reports only
    "out of range" sends the producer looking for corrupt data when the usual
    cause is neither corruption nor a bug: Movebank and many receivers express
    course over ground on [-180, 180]. It is the same measurement in a
    different convention, and `% 360` converts it exactly.

    **Why this needs no declaration, where a unit does.** The two cases are not
    symmetric. A speed of 50 does not say whether it is m/s or km/h, so only the
    producer can tell you. A heading *does* say — but only when it varies, which
    is why the order of the checks below is part of the answer rather than an
    implementation detail.

    The checks run from what is knowable to what is inferable:

    1. **A column that never varies carries no convention to identify.** It is
       the one case where the function must say what it knows and stop. An
       earlier version went straight to the convention question and answered
       it, which on a column entirely at -1 produced a confident instruction to
       take it modulo 360 — turning a file whose heading is unknown everywhere
       into one that points due north everywhere. A wrong message costs more
       than an absent one.
    2. **Negatives that cannot be signed headings are sentinels**, whether they
       sit beside canonical values above 180 or are simply too far negative to
       be an angle. Both are the same defect and both are made worse by the
       same advice: -1 % 360 is 359, -999 % 360 is 81.
    3. **The closed interval [0, 360]** — a source writing 360 for north — is
       not a convention error and not corrupt data. It is the single value the
       half-open range excludes, and it is the commonest deviation there is.
    4. Only then, the signed convention.

    Returns
    -------
    Finding or None
        None when the column is canonical, or when it is empty.
    """
    h = _finite(pd.Series(values))
    if h.empty:
        return None

    lo, hi = float(h.min()), float(h.max())
    if lo >= 0 and hi < 360:
        return None

    # 1. Degenerate. Reached only for a column that is *also* out of range, so
    # a stationary vehicle reporting a constant valid heading never lands here.
    if lo == hi:
        return Finding(
            "heading_deg", "error",
            f"heading_deg is {lo:g} on every row, and {lo:g} is outside the "
            f"canonical range [0, 360). A heading that never varies identifies "
            f"no convention: this is indistinguishable from a sentinel meaning "
            f"'unknown'. If that is what it means, write NaN — a missing "
            f"heading and a heading of {lo % 360:g} are not the same claim "
            f"(SPEC-01 §2.5)")

    negatives = h[h < 0]
    n_neg = int(negatives.size)
    max_non_negative = float(h[h >= 0].max()) if (h >= 0).any() else float("nan")

    # 2. Sentinels. A signed heading lives in [-180, 180], so a negative is not
    # one when it falls below -180, or when the same column reaches past 180.
    # An out-of-scale positive side is the headline, not the negatives: a
    # column running to 32 515 is not a file with a few sentinels in it.
    plausible_positive_side = not (max_non_negative > 360)

    if n_neg and plausible_positive_side:
        worst = float(negatives.min())
        # Two different reasons, and they deserve two different sentences: one
        # is about the negative itself, the other about the company it keeps.
        if worst < -180:
            why = (f"{worst:g} is not an angle in any convention — the signed "
                   f"range stops at -180")
            remainder = h[h >= -180]
        elif max_non_negative >= 180:
            why = (f"this column reaches {max_non_negative:.1f}, past the 180 "
                   f"a signed column never exceeds")
            remainder = h[h >= 0]
        else:
            why = None

        if why is not None:
            # What is left once the sentinels are NaN may still be in the wrong
            # convention, and saying so here saves a second round: a producer
            # who fixes only what the message named re-runs and is told the
            # rest, which reads as the validator having held something back.
            rest = ""
            if not remainder.empty and (remainder < 0).any() \
                    and float(remainder.max()) < 180:
                rest = (" Once they are NaN the column that remains is the "
                        "signed convention on [-180, 180] and still needs "
                        "`% 360`; both defects are present, and only the "
                        "sentinels must survive it.")
            return Finding(
                "heading_deg", "error",
                f"heading_deg carries {n_neg} negative value(s), down to "
                f"{worst:g}, which are not a signed convention: {why}. They are "
                f"sentinels for a missing heading. Do NOT take them modulo 360 "
                f"— that turns {worst:g} into {worst % 360:g}, a heading as "
                f"plausible as any other and entirely invented. Write NaN "
                f"(SPEC-01 §2.5)." + rest)

    # 3. The closed interval: 360 written for north.
    if lo >= 0 and hi == 360:
        n_360 = int((h == 360).sum())
        return Finding(
            "heading_deg", "error",
            f"heading_deg uses the closed interval [0, 360]: {n_360} row(s) "
            f"carry exactly 360. SPEC-01 §2.5 requires the half-open [0, 360), "
            f"so that north has one spelling and a consumer never has to test "
            f"for two. 360 and 0 are the same bearing, so this is a change of "
            f"representation and not a correction: `heading_deg % 360` fixes it "
            f"exactly, and the source column needs no `_adj` (SPEC-01 §2.13.1)")

    if lo < -180 or hi >= 360:
        return Finding(
            "heading_deg", "error",
            f"heading_deg spans {lo:.1f} to {hi:.1f}, outside both the canonical "
            f"range [0, 360) and the signed convention [-180, 180]. These are not "
            f"a convention, they are values no course over ground can take")

    # 4. The signed convention, reached only once the alternatives are excluded.
    return Finding(
        "heading_deg", "error",
        f"heading_deg spans {lo:.1f} to {hi:.1f}: this is course over ground on "
        f"[-180, 180], the convention Movebank and many receivers use. It is the "
        f"same measurement as the canonical [0, 360) and converts exactly with "
        f"`heading_deg % 360` — no information is lost and it is a change of "
        f"representation, not a correction (SPEC-01 §2.5)")


def check_timestamps(df: pd.DataFrame, *, ts: str = "ts",
                     now: pd.Timestamp | None = None) -> list[Finding]:
    """Check that the instants in a frame can be instants at all.

    :func:`check_units` asks whether a number can be the quantity its column
    claims. This asks the same of time, and nothing did: a trace carrying four
    rows stamped ``1970-01-01`` passes every rule in SPEC-01 §3 without a word,
    and the descriptive summary downstream then reports a three-minute drive as
    spanning fifty-six years.

    The two bounds are not arbitrary thresholds, which is what makes them
    usable as errors rather than warnings:

    * **Below the GPS epoch.** GNSS *is* the clock. A receiver that has a
      position has the constellation's time, so a fix dated before 1980-01-06
      was stamped by something else — almost always a real-time clock that lost
      power and restarted at the Unix epoch.
    * **In the future.** Recorded data cannot postdate its own reading.

    Between them they also catch the epoch-unit confusion, and the message
    names it the way the speed check names km/h: seconds read as milliseconds
    land in January 1970, milliseconds read as seconds land some fifty thousand
    years out. Neither is a plausible date, and both are a one-character fix.

    The two are less distinct than they look, which is why the first message
    offers both readings rather than picking one. A far-future instant that
    passes back through ``pd.to_datetime`` on a plain list wraps silently into
    1970 — so by the time a frame reaches a validator, "milliseconds read as
    seconds" and "clock never set" can be the same four rows.

    Parameters
    ----------
    now : pd.Timestamp or None
        Upper reference, defaulting to the current instant. Explicit so the
        check is reproducible: a validator whose verdict depends on the day it
        runs cannot be regression-tested.

    Returns
    -------
    list[Finding]
        Empty when the instants are plausible. Errors first.
    """
    if ts not in df.columns or not len(df):
        return []

    t = pd.to_datetime(df[ts], utc=True, errors="coerce").dropna()
    if t.empty:
        return []

    now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")

    findings: list[Finding] = []

    stale = t[t < GPS_EPOCH]
    if len(stale):
        # January 1970 is the signature of an uninitialised clock *and* of
        # epoch seconds read as milliseconds. Both are real, both are fixed
        # where the timestamp is produced, so the message offers both readings
        # rather than picking one.
        near_epoch = int((stale < pd.Timestamp("1971-01-01T00:00:00Z")).sum())
        cause = ("a real-time clock that restarted at the Unix epoch, or epoch "
                 "seconds read as milliseconds"
                 if near_epoch == len(stale)
                 else "a clock that was never set from the constellation")
        findings.append(Finding(
            ts, "error",
            f"{len(stale)} row(s) are dated before GPS time began "
            f"({GPS_EPOCH.date()}), the earliest {t.min()}. A receiver that has "
            f"a position has the constellation's clock, so these were stamped by "
            f"something else: {cause}"))

    ahead = t[t > now + FUTURE_TOLERANCE]
    if len(ahead):
        latest = t.max()
        cause = (" — around fifty thousand years out is epoch milliseconds read "
                 "as seconds" if latest.year > 5000 else "")
        findings.append(Finding(
            ts, "error",
            f"{len(ahead)} row(s) are dated in the future, the latest {latest}. "
            f"Recorded data cannot postdate its own reading{cause}"))

    # Only worth saying when neither bound fired: otherwise it restates them.
    if not findings:
        span = t.max() - t.min()
        if span > MAX_PLAUSIBLE_SPAN:
            findings.append(Finding(
                ts, "warning",
                f"the file spans {span.days / 365.25:.0f} years "
                f"({t.min().date()} to {t.max().date()}). That is longer than "
                f"one collection campaign, so the file probably concatenates "
                f"unrelated periods or carries a few stray instants"))

    return findings


def check_epoch_columns(df: pd.DataFrame, *,
                        now: pd.Timestamp | None = None) -> list[Finding]:
    """Check that an integer instant is at the resolution its name promises.

    :func:`check_timestamps` reads ``ts``, which is a datetime and therefore
    carries its own resolution. A column like ``ts_received_ms`` carries an
    integer, and an integer means nothing until something says which tick it
    counts. The only thing that says so is the suffix, so the suffix is what
    this check holds the values to.

    Why it is worth its own check. A wrong factor here is invisible in every way
    the format can normally see: the column is named right, the type is right,
    the value is a positive integer of the right order of magnitude for *a*
    timestamp. It only shows up once the number is subtracted from something
    else — and then only if the result is absurd enough to notice. A factor of a
    million produced a latency of 1.78e12 seconds, which got caught; the same
    defect at a factor of a thousand yields a latency in hours, which is
    plausible and wrong, and nobody writes a bug report about it.

    That asymmetry is why the check is here and not only in the conversion. The
    conversion repairs what this library produces. This repairs nothing, and
    catches what arrived from somewhere else — the point of a pivot format being
    precisely that most of its files were written by someone else's code.

    The bounds are :func:`check_timestamps`', for the same reasons: a receipt
    instant before GPS time began or days in the future is not a threshold
    someone chose, it is an impossibility. Read at the promised resolution, a
    2026 millisecond timestamp is thirteen digits; sixteen is microseconds
    wearing the wrong name.

    Returns
    -------
    list[Finding]
        Empty when every epoch column decodes to a plausible instant. Errors:
        the values cannot be what the column name says.
    """
    now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    ceiling = now + FUTURE_TOLERANCE

    findings: list[Finding] = []
    for column in df.columns:
        promised = epoch_unit_of(column)
        if promised is None:
            continue
        # A datetime in an integer column is a type mismatch, which SPEC-01 §3
        # rule 9 owns and `coerce_schema_dtypes` fixes. This check is about
        # magnitude, and reporting the type here would say the same thing twice
        # in the language of the wrong rule.
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            continue
        values = _finite(df[column])
        if values.empty:
            continue

        read = from_epoch(values, promised)
        outside = (read < GPS_EPOCH) | (read > ceiling)
        n = int(outside.sum())
        if not n:
            continue

        # Which resolution *would* be plausible. Naming it is the difference
        # between "these values are odd" and "divide by a thousand": the
        # candidates are a factor of a thousand apart, so at most one of them
        # can put the same integers in a plausible window.
        candidates = []
        for other in EPOCH_UNIT_BY_SUFFIX:
            if other == promised:
                continue
            alt = from_epoch(values, other)
            if ((alt >= GPS_EPOCH) & (alt <= ceiling)).all():
                candidates.append((other, alt))

        if len(candidates) == 1:
            other, alt = candidates[0]
            factor = _NS_PER_TICK[promised] // _NS_PER_TICK[other]
            fix = (f"Read as {_RESOLUTION_NAMES[other]} the same integers date "
                   f"{alt.min()} to {alt.max()}, so the column carries "
                   f"{_RESOLUTION_NAMES[other]}: it is a factor {factor} out and "
                   f"`{column} // {factor}` is the whole of the fix")
        else:
            fix = ("No other epoch resolution puts these integers in a "
                   "plausible window either, so this is not a confusion between "
                   "two units but values that were never instants")

        digits = len(str(_ticks_of(now, promised)))
        findings.append(Finding(
            column, "error",
            f"{n} of {len(values)} value(s) in {column} are not "
            f"{_RESOLUTION_NAMES[promised]} since the Unix epoch: read as the "
            f"name promises, they date {read.min()} to {read.max()}. {fix}. The "
            f"suffix is the unit (SPEC-01 §1.1), and today a {promised} instant "
            f"is {digits} digits long"))

    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_units(df: pd.DataFrame, *, acc_frame: str | None = None,
                provenance: dict[str, str] | None = None) -> list[Finding]:
    """Check that the magnitudes in a frame match the units its columns claim.

    Parameters
    ----------
    df : pd.DataFrame
        Telemachus-conformant frame.
    acc_frame : str or None
        Declared AccPeriod frame — ``"raw"``, ``"compensated"`` or
        ``"partial"`` (SPEC-02 §3.7). When a dataset is validated through
        :func:`telemachus.validate_dataset` this comes from the manifest.
        Without it the accelerometer check cannot separate a correct
        compensated frame from a raw one left in g, and says so instead of
        picking one.
    provenance : dict or None
        `column_provenance` from the manifest (SPEC-02 §3.15), mapping a column
        to `measured`, `derived` or `absent`. Without it the speed cross-check
        can only hedge; with it the same measurement becomes a check on the
        declaration, and a column declared `measured` that tracks its own
        positions exactly is a contradiction rather than a suspicion.

    Returns
    -------
    list[Finding]
        Empty when nothing is suspect. Errors first.
    """
    provenance = provenance or {}
    findings: list[Finding] = []
    findings += _check_speed_against_positions(df, provenance.get("speed_mps"))
    # The magnitude bound and the cross-check have the same cause when both
    # fire. Reporting it once, from the test that names the unit, is more use
    # than reporting it twice.
    named = any(f.column == "speed_mps" and f.severity == "error" for f in findings)
    findings += [f for f in _check_speed_magnitude(df)
                 if not (named and f.column == "speed_mps")]
    findings += _check_accel(df, acc_frame)
    findings += _check_gyro(df)
    findings += _check_magneto(df)
    findings += _check_altitude(df)
    return sorted(findings, key=lambda f: f.severity != "error")
