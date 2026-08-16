"""No public docstring names something the public cannot see.

The leak that actually happens is not a stolen algorithm. It is a paragraph
recopied from a private module into a public one, carrying a reference to an
internal phase, an internal RFC paragraph or a private module name — each of
which tells a reader more about the private pipeline than the code itself does.

SPEC-04 §5.2 draws the line at *how to compute derived values*. This test draws
a narrower and mechanically checkable one: a public docstring may not name an
internal document. It is a release-checklist item in SPEC-04 §6.
"""

import ast
import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent.parent / "telemachus"

# Structural patterns: they describe the *shape* of a leak and name no project,
# so they are safe to publish. The proper nouns that must never appear are not
# written here — a guard that lists the private repositories it protects has
# published them itself. Those come from the environment (see PRIVATE_TERMS).
FORBIDDEN = [
    (re.compile(r"\bPhase [A-Z]\b"), "an internal project phase"),
    (re.compile(r"\bRFC\s*§"), "an internal RFC paragraph"),
    (re.compile(r"\b(?:cf\.?|voir|see)\s+RFC-\d+\s*§"), "an internal RFC paragraph"),
    (re.compile(r"\bupsampler\b", re.I), "a private module"),
    (re.compile(r"\bd1_[a-z_]+\b"), "a private pipeline module"),
    (re.compile(r"\bINV-\d+\b"), "an internal investigation"),
    (re.compile(r"\bBUG-\d+\b"), "an internal ticket"),
    # Identifiers that are client data whatever their source
    (re.compile(r"\b8\d{14}\b"), "what looks like an IMEI"),
    (re.compile(r"\b89\d{17,18}\b"), "what looks like a SIM ICCID"),
    (re.compile(r"\bmongodb(?:\+srv)?://"), "a database connection string"),
]

#: Proper nouns that must not appear anywhere public: private repositories,
#: client and partner names, device aliases, hostnames. Supplied as a
#: comma-separated list in TELEMACHUS_PRIVATE_TERMS rather than committed, for
#: the reason above. The release workflow feeds it from a repository secret.
PRIVATE_TERMS = [t.strip() for t in
                 os.environ.get("TELEMACHUS_PRIVATE_TERMS", "").split(",") if t.strip()]


def _public_docstrings(path: Path):
    """Every docstring of a public module, class or function, with its line."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    if (doc := ast.get_docstring(tree)):
        yield 1, doc
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        if node.name.startswith("_"):
            continue
        if (doc := ast.get_docstring(node)):
            yield node.lineno, doc


PUBLIC_MODULES = sorted(
    p for p in PACKAGE.rglob("*.py")
    if "__pycache__" not in p.parts and not p.name.startswith("_validate_legacy")
)


@pytest.mark.parametrize("path", PUBLIC_MODULES, ids=lambda p: p.name)
def test_no_internal_reference_in_a_public_docstring(path):
    offences = []
    for lineno, doc in _public_docstrings(path):
        for pattern, what in FORBIDDEN:
            if (m := pattern.search(doc)):
                offences.append(
                    f"{path.relative_to(PACKAGE.parent)}:{lineno} names {what}: "
                    f"{m.group(0)!r}")
    assert not offences, "\n".join(offences)


# ---------------------------------------------------------------------------
# The specification is published too, and it is the surface a reader studies.
# ---------------------------------------------------------------------------

# Narrower than FORBIDDEN above: a SPEC legitimately cites its own superseded
# RFCs by number, so the code-side patterns would fire on correct text. These
# are the names of private methods and private repositories, which have no
# reason to appear in a public specification at all.
FORBIDDEN_IN_SPEC = [
    (re.compile(r"\bupsampler\b", re.I), "a private module"),
    (re.compile(r"4\s*(?:θ|theta)", re.I), "a private method"),
    (re.compile(r"\bINV-\d+\b"), "an internal investigation"),
    (re.compile(r"\bBUG-\d+\b"), "an internal ticket"),
    (re.compile(r"\bPhase [A-Z]\b"), "an internal project phase"),
    (re.compile(r"\b8\d{14}\b"), "what looks like an IMEI"),
    (re.compile(r"\b89\d{17,18}\b"), "what looks like a SIM ICCID"),
]

SPEC_FILES = sorted((REPO / "spec").glob("SPEC-*.md"))


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda p: p.name)
def test_no_private_method_named_in_a_published_spec(path):
    """The contract is public. The methods behind it are not (SPEC-04 §5.2.1)."""
    text = path.read_text(encoding="utf-8")
    offences = [f"{path.name} names {what}: {m.group(0)!r}"
                for pattern, what in FORBIDDEN_IN_SPEC
                if (m := pattern.search(text))]
    assert not offences, "\n".join(offences)


def test_the_specs_were_actually_scanned():
    """A parametrised test over an empty list passes without testing anything."""
    assert len(SPEC_FILES) >= 4


# ---------------------------------------------------------------------------
# Client data. Everything above looks for leaked *internals*; this looks for
# leaked *third parties*, which is the one that cannot be walked back.
# ---------------------------------------------------------------------------

def _publishable_files():
    """Every file this repository would push, minus build output and vendored text."""
    skip_dirs = {".git", "site", "_site", "__pycache__", ".pytest_cache",
                 ".ruff_cache", "node_modules", "dist", "build"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg",
                                                         ".gif", ".pdf", ".parquet",
                                                         ".zip", ".ipynb_checkpoints"}:
            continue
        if set(path.relative_to(REPO).parts) & skip_dirs:
            continue
        # The licence texts legitimately contain words that look like anything.
        if path.name in {"LICENSE", "LICENSE.txt", "NOTICE"}:
            continue
        yield path


@pytest.mark.skipif(not PRIVATE_TERMS,
                    reason="TELEMACHUS_PRIVATE_TERMS not set (see the module docstring)")
def test_no_private_term_anywhere_in_the_repository():
    """No client, partner, private repository or device name in anything we push.

    Broader than the docstring and spec checks above on purpose: a client name
    is just as damaging in a comment, a fixture, a notebook or a YAML file as it
    is in a published paragraph.
    """
    # The offending term is deliberately NOT echoed. This runs in a public
    # repository, and a failing job writes its assertion message into a log
    # anyone can read — a guard that names the thing it protects, at the exact
    # moment it catches it, publishes it. The report gives the file, the line
    # and the index of the term in the list; the maintainer resolves it locally,
    # where saying the word costs nothing.
    patterns = [(re.compile(rf"\b{re.escape(t)}\b", re.I), i)
                for i, t in enumerate(PRIVATE_TERMS)]
    offences = []
    for path in _publishable_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue                      # this file holds the terms at runtime
        for pattern, index in patterns:
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                offences.append(
                    f"{path.relative_to(REPO)}:{line} matches private term #{index}")
    assert not offences, (
        "\n".join(offences[:40]) + "\n\nTerms are indexed, not printed: this log "
        "is public. Reproduce locally with TELEMACHUS_PRIVATE_TERMS set to see "
        "which word matched.")


def test_the_denylist_is_configured_in_ci():
    """Locally the check above may skip. In CI, skipping IS the failure.

    A guard that quietly does nothing is worse than no guard, because the green
    tick is read as "checked".
    """
    if os.environ.get("CI") == "true":
        assert PRIVATE_TERMS, (
            "TELEMACHUS_PRIVATE_TERMS is empty in CI. Set it from the repository "
            "secret, or the client-data check silently passes on everything.")


def test_the_guard_would_catch_the_thing_it_is_for():
    """A guard nobody has seen fire is a guard nobody trusts."""
    leaked = "Rows without a nearby fix stay NaN; the upsampler downstream "\
             "interpolates (cf. Phase C / RFC §4.2)."
    hits = [what for pattern, what in FORBIDDEN if pattern.search(leaked)]
    assert "an internal project phase" in hits
    assert "an internal RFC paragraph" in hits
    assert "a private module" in hits


# ---------------------------------------------------------------------------
# Personal data in the datasets themselves (SPEC-01 §2.4)
# ---------------------------------------------------------------------------

def test_pii_is_reported_in_an_internal_dataset():
    import pandas as pd

    from telemachus.core.privacy import check_pii

    df = pd.DataFrame({"ts": pd.date_range("2026-03-01T08:00:00Z", periods=5, freq="1s"),
                       "lat": 49.0, "lon": 1.0, "device_imei": "861327088147793"})
    errors, warnings = check_pii(df)
    assert errors == [], "internal use is legitimate, §2.4 defines the column"
    assert warnings and "MUST NOT be published" in warnings[0]


def test_pii_is_refused_once_the_manifest_declares_publication():
    import pandas as pd

    from telemachus.core.privacy import check_pii

    df = pd.DataFrame({"ts": pd.date_range("2026-03-01T08:00:00Z", periods=5, freq="1s"),
                       "lat": 49.0, "lon": 1.0, "sim_iccid": "8933150319000000000"})
    for manifest in ({"license": "CC-BY-4.0"},
                     {"source": {"type": "open_external"}},
                     {"source": {"doi": "10.5281/zenodo.1"}}):
        errors, _ = check_pii(df, manifest)
        assert errors, manifest


def test_an_empty_pii_column_is_not_a_leak():
    """An adapter that creates the column and never fills it did nothing wrong."""
    import numpy as np
    import pandas as pd

    from telemachus.core.privacy import check_pii

    df = pd.DataFrame({"ts": pd.date_range("2026-03-01T08:00:00Z", periods=5, freq="1s"),
                       "lat": 49.0, "lon": 1.0, "device_imei": np.nan})
    assert check_pii(df, {"license": "CC-BY-4.0"}) == ([], [])


def test_the_advice_is_to_drop_not_to_hash():
    import pandas as pd

    from telemachus.core.privacy import check_pii

    df = pd.DataFrame({"ts": pd.date_range("2026-03-01T08:00:00Z", periods=5, freq="1s"),
                       "lat": 49.0, "lon": 1.0, "device_imei": "861327088147793"})
    errors, _ = check_pii(df, {"license": "CC0-1.0"})
    assert "a hash is still a" in errors[0], "hashing an IMEI still joins"


def test_no_published_dataset_carries_pii():
    """The four datasets this project ships, checked rather than assumed."""
    import yaml

    from telemachus.core.privacy import PII_COLUMNS

    manifests = sorted((REPO / "datasets").glob("*/manifest.yaml"))
    assert manifests, "no dataset found to check"
    for path in manifests:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        for device in (data.get("hardware") or {}).get("devices") or []:
            imei = str(device.get("imei") or "")
            assert not imei.isdigit() or len(imei) != 15, \
                f"{path}: hardware.devices declares a real-looking IMEI"
        for column in PII_COLUMNS:
            assert f"{column}:" not in text or "EXAMPLE" in text, \
                f"{path}: manifest mentions {column}"


# ---------------------------------------------------------------------------
# The specification against the table the validator consults
# ---------------------------------------------------------------------------
#
# These belong in the hygiene file for the same reason as everything above it:
# they are release-checklist items (SPEC-04 §6) about the gap between what the
# project publishes and what it does. The other tests check that a docstring
# says nothing it should not. These check that the specification and the code
# say the same thing.
#
# 1.0.0a3 is why they exist. §2.3.1 was rewritten to make `speed_mps` optional
# for a receiver that does not measure it; the table in §2.3 still listed it
# under "All profiles"; and the validator followed the table. The release
# converted exactly the datasets the previous one converted and refused exactly
# the ones it refused. The relaxation existed only in a sentence, and every
# test was green — because nothing compared the two.

from telemachus.core.schemas import (  # noqa: E402
    CONDITIONAL_CORE,
    MANDATORY_BY_PROFILE,
)

#: The tables of SPEC-01 §2.3, keyed on the bold line that introduces each one,
#: and the profiles that line binds.
#:
#: Keying on the *heading* is the design, not an implementation detail. A
#: parser that looks for a word inside a description cell — "conditional",
#: "optional" — inherits exactly the ambiguity that produced a3, because a cell
#: can say one thing while the table it sits in says another. A heading cannot:
#: a row is under one heading or another, and §2.3.2 exists to keep it that way.
SPEC_TABLES = {
    "All profiles (core, imu, full):": ("core", "imu", "full"),
    "Conditional — required only when the receiver measures it (§2.3.1):": (),
    "Profile `imu` and `full` add:": ("imu", "full"),
    "Profile `full` adds:": ("full",),
}

CONDITIONAL_TABLE = "Conditional — required only when the receiver measures it (§2.3.1):"


def _tables_in_the_spec() -> dict[str, list[str]]:
    """Every bold-introduced table of §2.3, as ``{heading: [column, ...]}``."""
    text = (REPO / "spec" / "SPEC-01-record-format.md").read_text(encoding="utf-8")
    section = text[text.index("### 2.3 Mandatory Fields"):text.index("### 2.4 ")]
    parts = re.split(r"^\*\*(.+?)\*\*\s*$", section, flags=re.M)[1:]
    return {heading.strip(): re.findall(r"^\| `([a-z_0-9]+)` \|", body, re.M)
            for heading, body in zip(parts[::2], parts[1::2], strict=True)}


def test_every_table_in_the_section_is_accounted_for():
    """The canary — and deliberately not "did the parser find any rows".

    A parser that finds rows can still be blind. Add a fifth table tomorrow and
    one keyed on four known headings skips it without a word: the columns it
    makes mandatory are compared against nothing, and every assertion below
    stays green while measuring less than it claims. That is the failure mode
    that cost the a3, in a different disguise.

    So the assertion is about coverage of the *section*, not of the rows. A
    table nobody reads is a rule nobody enforces.
    """
    found = {heading for heading, columns in _tables_in_the_spec().items() if columns}
    unknown = found - set(SPEC_TABLES)
    missing = set(SPEC_TABLES) - found
    assert not unknown, (
        f"SPEC-01 §2.3 carries table(s) this test does not know: {sorted(unknown)}. "
        f"Whatever they make mandatory is currently compared against nothing — "
        f"add them to SPEC_TABLES with the profiles they bind.")
    assert not missing, (
        f"SPEC-01 §2.3 no longer carries table(s) this test expects: "
        f"{sorted(missing)}. Either they were renamed or the section was "
        f"restructured; either way this file measures less than it claims.")


@pytest.mark.parametrize("profile", ["core", "imu", "full"])
def test_the_code_requires_exactly_what_the_specification_requires(profile):
    """SPEC-01 §2.3 and ``MANDATORY_BY_PROFILE``, held to each other."""
    tables = _tables_in_the_spec()
    declared = {column
                for heading, profiles in SPEC_TABLES.items()
                for column in tables.get(heading, [])
                if profile in profiles}
    assert MANDATORY_BY_PROFILE[profile] == declared, (
        f"profile {profile!r}: SPEC-01 §2.3 requires {sorted(declared)}, the "
        f"validator requires {sorted(MANDATORY_BY_PROFILE[profile])}. "
        f"Only in the spec: {sorted(declared - MANDATORY_BY_PROFILE[profile])}; "
        f"only in the code: {sorted(MANDATORY_BY_PROFILE[profile] - declared)}")


def test_the_conditional_columns_agree_too():
    """The half a mandatory-only comparison cannot see.

    Drop a column from ``CONDITIONAL_CORE`` without moving it out of the
    conditional table and no mandatory set changes, so the check above stays
    green while the validator has quietly stopped treating it as conditional
    at all.
    """
    in_the_spec = set(_tables_in_the_spec().get(CONDITIONAL_TABLE, []))
    assert in_the_spec == set(CONDITIONAL_CORE), (
        f"SPEC-01 §2.3 marks {sorted(in_the_spec)} conditional, the validator "
        f"marks {sorted(CONDITIONAL_CORE)}")


def test_no_column_is_both_mandatory_and_conditional():
    """The contradiction §2.3.2 was written to make unrepresentable.

    Not reachable from the two comparisons above: a column listed in both the
    conditional table and a profile table satisfies each of them separately.
    """
    tables = _tables_in_the_spec()
    conditional = set(tables.get(CONDITIONAL_TABLE, []))
    for heading, profiles in SPEC_TABLES.items():
        if not profiles:
            continue
        clash = conditional & set(tables.get(heading, []))
        assert not clash, (
            f"{sorted(clash)} sits in the conditional table and under "
            f"{heading!r}. A column's obligation is carried by the heading "
            f"above it, so it may sit under exactly one (SPEC-01 §2.3.2)")
