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
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
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
