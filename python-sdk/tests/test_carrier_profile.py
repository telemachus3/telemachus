"""Carrier profiles (SPEC-02 §3.8) — the indirection that opens the manifest
to carriers that are not vehicles, without changing what a vehicle means."""

import pytest

import telemachus as tele
from telemachus.core.carrier import (
    REGISTERED_PROFILES,
    CarrierProfileError,
    resolve_carrier_profile,
)

COLLAR = {
    "name": "collar",
    "states": {"foraging": "analysable", "resting": "analysable",
               "handled": "excluded", "unknown": "optional"},
}


# ---------------------------------------------------------------------------
# Zero breakage: the vehicle profile is what it always was
# ---------------------------------------------------------------------------

def test_absent_profile_means_vehicle():
    p = resolve_carrier_profile({})
    assert p.name == "vehicle" and p.registered


def test_vehicle_states_are_unchanged():
    p = resolve_carrier_profile(None)
    assert set(p.states) == {"mounted_driving", "mounted_idle", "unplugged",
                             "desk", "handheld", "unknown"}
    assert sorted(p.analysable_states) == ["mounted_driving", "mounted_idle"]


def test_is_vehicle_data_derives_exactly_as_before():
    p = resolve_carrier_profile({})
    assert p.is_vehicle_data("mounted_driving")
    assert p.is_vehicle_data("mounted_idle")
    for state in ("unplugged", "desk", "handheld", "unknown", None):
        assert not p.is_vehicle_data(state)


def test_optional_is_not_analysable_but_is_distinguishable():
    """`optional` means the consumer decides, which is not the same as no."""
    p = resolve_carrier_profile({})
    assert p.usability("unplugged") == "optional"
    assert not p.is_analysable("unplugged")
    assert p.usability("desk") == "excluded"


def test_a_published_manifest_still_validates():
    """The four datasets this project ships declare no profile."""
    for slug in ("aegis", "pvs", "stride", "rs3"):
        report = tele.validate_manifest(f"../datasets/{slug}/manifest.yaml")
        assert report.ok, (slug, report.errors)


# ---------------------------------------------------------------------------
# The indirection
# ---------------------------------------------------------------------------

def test_a_registered_name_needs_no_declaration():
    assert resolve_carrier_profile({"carrier_profile": "vehicle"}).registered


def test_an_inline_profile_carries_its_own_states():
    p = resolve_carrier_profile({"carrier_profile": COLLAR})
    assert p.name == "collar" and not p.registered
    assert p.is_analysable("foraging")
    assert not p.is_analysable("handled")
    assert p.usability("unknown") == "optional"


def test_only_vehicle_is_registered():
    """The mechanism ships in 1.0; a profile ships when a dataset carries it."""
    assert list(REGISTERED_PROFILES) == ["vehicle"]


def test_an_unregistered_name_says_how_to_declare_one():
    with pytest.raises(CarrierProfileError) as exc:
        resolve_carrier_profile({"carrier_profile": "animal"})
    assert "declares its own states inline" in str(exc.value)


def test_a_profile_must_declare_its_states():
    with pytest.raises(CarrierProfileError, match="declares no 'states'"):
        resolve_carrier_profile({"carrier_profile": {"name": "collar"}})


def test_a_profile_with_nothing_analysable_is_refused():
    with pytest.raises(CarrierProfileError, match="no analysable state"):
        resolve_carrier_profile({"carrier_profile": {
            "name": "collar", "states": {"resting": "excluded"}}})


def test_an_unknown_usability_value_is_refused():
    with pytest.raises(CarrierProfileError, match="usability must be one of"):
        resolve_carrier_profile({"carrier_profile": {
            "name": "collar", "states": {"resting": "maybe"}}})


def test_a_registered_name_cannot_be_redefined():
    with pytest.raises(CarrierProfileError, match="cannot\n?\\s*be redefined"):
        resolve_carrier_profile({"carrier_profile": {
            "name": "vehicle", "states": {"driving": "analysable"}}})


def test_an_unrecognised_state_degrades_rather_than_raising():
    p = resolve_carrier_profile({"carrier_profile": COLLAR})
    assert p.usability("swimming") == "excluded"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _manifest(tmp_path, body: str):
    path = tmp_path / "manifest.yaml"
    path.write_text("dataset_id: XX_test_2026\n"
                    "schema_version: telemachus-1.0\n"
                    "source: {type: synthetic}\n" + body)
    return path


def test_a_state_outside_the_profile_is_rejected(tmp_path):
    path = _manifest(tmp_path,
                     "trip_carrier_states:\n"
                     "  - {trip_id: T1, carrier_state: foraging}\n")
    report = tele.validate_manifest(path)
    assert not report.ok
    assert "not states of the 'vehicle' carrier profile" in report.errors[0]


def test_the_same_state_passes_under_a_profile_that_has_it(tmp_path):
    path = _manifest(tmp_path,
                     "carrier_profile:\n"
                     "  name: collar\n"
                     "  states: {foraging: analysable, handled: excluded}\n"
                     "trip_carrier_states:\n"
                     "  - {trip_id: T1, carrier_state: foraging}\n")
    report = tele.validate_manifest(path)
    assert report.ok, report.errors


def test_summary_keys_are_checked_too(tmp_path):
    path = _manifest(tmp_path, "carrier_state_summary: {swimming: 3}\n")
    assert not tele.validate_manifest(path).ok
