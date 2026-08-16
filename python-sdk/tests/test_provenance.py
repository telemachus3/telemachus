"""Column provenance as validator input (SPEC-02 §3.15).

The dispersion heuristic could only ever guess. Beside a declaration it stops
guessing and starts checking the declaration, which is a different and much
stronger thing.
"""

import numpy as np
import pandas as pd
import yaml

import telemachus as tele
from telemachus.core.plausibility import check_units
from telemachus.core.provenance import (
    check_provenance_declaration,
    resolve_column_provenance,
)
from telemachus.metrics import haversine_m


def _drive(independent=True, n=400, seed=0):
    """A wandering track. `speed_mps` is either an independent reading — which
    scatters against its own positions — or derived from them, which cannot."""
    rng = np.random.default_rng(seed)
    lat = 49.33
    lon = 1.38 + np.cumsum(rng.normal(20.0, 3.0, n)) / (111_320 * np.cos(np.radians(lat)))
    la = lat + np.cumsum(rng.normal(0, 2.0, n)) / 111_320
    step = np.nan_to_num(haversine_m(np.r_[np.nan, la[:-1]], np.r_[np.nan, lon[:-1]],
                                     la, lon), nan=20.0)
    speed = step * rng.normal(1.0, 0.06, n) + rng.normal(0, 0.4, n) if independent else step
    return pd.DataFrame({
        "ts": pd.date_range("2026-03-01T08:00:00Z", periods=n, freq="1s"),
        "lat": la, "lon": lon, "speed_mps": np.clip(speed, 0, None), "device_id": "d1"})


def _sev(df, declared):
    f = check_units(df, provenance={"speed_mps": declared} if declared else None)
    return f[0].severity if f else None


# ---------------------------------------------------------------------------
# The truth table
# ---------------------------------------------------------------------------

def test_measured_and_independent_is_silent():
    assert _sev(_drive(independent=True), "measured") is None


def test_measured_but_tracking_its_own_positions_is_a_contradiction():
    """The case the declaration makes reachable. Without it, only a warning."""
    df = _drive(independent=False)
    findings = check_units(df, provenance={"speed_mps": "measured"})
    assert findings and findings[0].severity == "error"
    assert "declared `measured`" in findings[0].message
    assert "not what it says it is" in findings[0].message


def test_declaring_derived_buys_silence():
    """The incentive. A field nobody fills is a field that does not exist."""
    df = _drive(independent=False)
    assert _sev(df, None) == "warning"          # undeclared: the checker hedges
    assert _sev(df, "derived") is None          # declared: nothing left to say


def test_derived_but_independent_is_not_an_error():
    """Derived from another source — an odometer, a wheel — is legitimate."""
    assert _sev(_drive(independent=True), "derived") is None


def test_an_undeclared_derived_column_still_warns_and_asks():
    findings = check_units(_drive(independent=False))
    assert findings[0].severity == "warning"
    assert "column_provenance" in findings[0].message


def test_a_wrong_unit_outranks_the_declaration():
    """Declaring `derived` must not excuse km/h."""
    df = _drive(independent=False)
    df["speed_mps"] = df["speed_mps"] * 3.6
    findings = check_units(df, provenance={"speed_mps": "derived"})
    assert findings and findings[0].severity == "error"
    assert "km/h" in findings[0].message


# ---------------------------------------------------------------------------
# The declaration itself
# ---------------------------------------------------------------------------

def test_resolve_lowercases_and_drops_what_it_does_not_know():
    got = resolve_column_provenance({"column_provenance": {
        "speed_mps": "Measured", "heading_deg": "guessed", "ax_mps2": "absent"}})
    assert got == {"speed_mps": "measured", "ax_mps2": "absent"}


def test_an_unknown_value_is_reported_even_though_it_is_dropped():
    errors, _ = check_provenance_declaration(
        {"column_provenance": {"speed_mps": "guessed"}})
    assert errors and "guessed" in errors[0]


def test_declared_absent_but_carrying_values_is_refused():
    df = _drive()
    errors, _ = check_provenance_declaration(
        {"column_provenance": {"speed_mps": "absent"}}, df)
    assert errors and "declares 'speed_mps' absent" in errors[0]


def test_declared_absent_and_empty_is_consistent():
    df = _drive()
    df["speed_mps"] = np.nan
    assert check_provenance_declaration(
        {"column_provenance": {"speed_mps": "absent"}}, df) == ([], [])


def test_declaring_a_column_that_is_not_there_warns():
    _, warnings = check_provenance_declaration(
        {"column_provenance": {"rpm": "measured"}}, _drive())
    assert warnings and "not in the data" in warnings[0]


def test_the_spec_mandated_warning_on_a_core_profile():
    """SPEC-02 §3.15 asks for exactly this one."""
    _, warnings = check_provenance_declaration({}, _drive(), profile="core")
    assert any("speed_mps carries values and its provenance is not" in w
               for w in warnings)
    _, quiet = check_provenance_declaration(
        {"column_provenance": {"speed_mps": "measured"}}, _drive(), profile="core")
    assert not any("speed_mps" in w for w in quiet)


def test_a_malformed_block_is_reported_not_crashed():
    errors, _ = check_provenance_declaration({"column_provenance": ["speed_mps"]})
    assert errors and "must be a mapping" in errors[0]


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_validate_dataset_reads_the_declaration(tmp_path):
    df = _drive(independent=False)
    df.to_parquet(tmp_path / "data.parquet", index=False)
    manifest = {
        "dataset_id": "XX_prov_2026", "schema_version": "telemachus-1.0",
        "profile": "core", "source": {"type": "synthetic"},
        "data_files": [{"path": "data.parquet", "format": "parquet"}],
        "column_provenance": {"speed_mps": "measured"},
    }
    (tmp_path / "manifest.yaml").write_text(yaml.safe_dump(manifest))

    report = tele.validate_dataset(tmp_path, level="full")
    assert not report.ok
    assert any("declared `measured`" in e for e in report.errors)

    # the same data, honestly declared, passes
    manifest["column_provenance"] = {"speed_mps": "derived"}
    (tmp_path / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    assert tele.validate_dataset(tmp_path, level="full").ok
