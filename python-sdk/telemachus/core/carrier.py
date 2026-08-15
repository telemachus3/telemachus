"""Carrier profiles — what the thing carrying the device is, and which of its
states an analysis may use.

The format is neutral about what carries the device. The manifest was not.
Position, timestamp, accelerometer, gyroscope, magnetometer, speed, GNSS
quality, AccPeriods and the multi-rate convention all pass unchanged onto an
animal collar, a bicycle or a rucksack — multi-rate is *more* relevant in
biologging than in fleet, where a GPS fix every quarter of an hour meets
accelerometer bursts at 20-50 Hz. What blocked was one enumeration:
``mounted_driving``, ``mounted_idle``, ``unplugged``, ``desk``, ``handheld``,
whose decision tree tests a vehicle battery voltage. None of those five means
anything on a collar.

The correction is one level of indirection, not a rewrite.

**The invariant is the declaration, not the vocabulary.** What every consumer
of a Telemachus dataset actually needs from this block is one bit per state:
may an analysis use the data recorded while the carrier was in it? A vehicle
parked with the engine running is usable — that is where ZUPT segments come
from. A device sitting on a desk is not. Which words a domain uses for those
situations is that domain's business; that it says which ones are analysable is
the format's.

A profile is therefore either **registered** — its states and their
analysability defined once in SPEC-02 §3.8.1, so a manifest names it and
declares nothing — or **inline**, in which case it declares its own states and
what each one is worth.

Only ``vehicle`` is registered, and it is the default, with exactly the states
and meanings the specification already had: an existing manifest is unchanged
and keeps validating. No animal, pedestrian or bicycle profile is registered
here. The mechanism ships in 1.0; a profile ships when a dataset carries it,
because an unkept promise in a specification costs more than an absence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

__all__ = [
    "REGISTERED_PROFILES",
    "USABILITY",
    "CarrierProfile",
    "CarrierProfileError",
    "resolve_carrier_profile",
]


class CarrierProfileError(ValueError):
    """The declared carrier profile cannot be resolved."""


#: What an analysis may do with the data recorded in a given state.
#:
#: ``analysable``  — use it.
#: ``optional``    — the carrier's situation is unknown; the consumer decides.
#: ``excluded``    — the data does not describe the phenomenon being studied.
USABILITY = ("analysable", "optional", "excluded")


#: Profiles defined by the specification. A manifest naming one of these
#: declares nothing further.
REGISTERED_PROFILES: dict[str, dict[str, str]] = {
    # Exactly the taxonomy of SPEC-02 §3.8 as it stood before profiles existed,
    # with the "Use for analytics" column of that table read as usability.
    # Nothing here changes meaning; it is only written down in a form another
    # profile can imitate.
    "vehicle": {
        "mounted_driving": "analysable",
        "mounted_idle": "analysable",
        "unplugged": "optional",
        "desk": "excluded",
        "handheld": "excluded",
        "unknown": "excluded",
    },
}

#: Profile assumed when a manifest declares none. SPEC-02 §3.8.
DEFAULT_PROFILE = "vehicle"


@dataclass(frozen=True)
class CarrierProfile:
    """A carrier profile, resolved and ready to answer questions about states."""

    name: str
    states: Mapping[str, str]
    registered: bool

    def usability(self, state: str | None) -> str:
        """What an analysis may do with data recorded in ``state``.

        An unknown state is ``excluded``, not an error: a consumer reading a
        dataset produced against a later profile revision should skip what it
        does not recognise rather than refuse the file. The validator, which
        does have the profile in front of it, is the one that rejects.
        """
        if state is None:
            return "excluded"
        return self.states.get(state, "excluded")

    def is_analysable(self, state: str | None) -> bool:
        """True for states this profile declares usable, ``optional`` excluded.

        The conservative reading is deliberate: ``optional`` means the carrier's
        situation is unknown, and a consumer that wants those rows asks for them
        with :meth:`usability`.
        """
        return self.usability(state) == "analysable"

    @property
    def analysable_states(self) -> tuple[str, ...]:
        return tuple(s for s, u in self.states.items() if u == "analysable")

    def is_vehicle_data(self, state: str | None) -> bool:
        """Backward-compatible alias, meaningful only under the vehicle profile.

        SPEC-01 §2.13 lists ``is_vehicle_data`` as derived from
        ``carrier_state``, and under ``vehicle`` it derives exactly as before:
        true for ``mounted_driving`` and ``mounted_idle``. Under any other
        profile the question is the wrong one — a collar is never "vehicle
        data" — and the answer is the general one.
        """
        return self.is_analysable(state)


def resolve_carrier_profile(manifest: dict | None) -> CarrierProfile:
    """Read ``carrier_profile`` from a manifest, defaulting to ``vehicle``.

    Accepts the two forms of SPEC-02 §3.8:

    - a name, ``carrier_profile: vehicle``, resolved from
      :data:`REGISTERED_PROFILES`;
    - an inline declaration, ``{name: ..., states: {<state>: <usability>}}``,
      for a carrier the specification does not cover.

    Raises
    ------
    CarrierProfileError
        For an unregistered name, a declaration with no states, or a usability
        value outside :data:`USABILITY`. Each message says what to write
        instead: a profile that cannot be resolved would silently make every
        trip unusable, which is worse than a refusal.
    """
    declared = (manifest or {}).get("carrier_profile")

    if declared is None:
        return CarrierProfile(DEFAULT_PROFILE,
                              dict(REGISTERED_PROFILES[DEFAULT_PROFILE]), True)

    if isinstance(declared, str):
        states = REGISTERED_PROFILES.get(declared)
        if states is None:
            raise CarrierProfileError(
                f"carrier_profile {declared!r} is not a registered profile "
                f"({sorted(REGISTERED_PROFILES)}). A carrier the specification "
                f"does not cover declares its own states inline: "
                f"{{name: {declared}, states: {{<state>: analysable|optional|excluded}}}}")
        return CarrierProfile(declared, dict(states), True)

    if not isinstance(declared, dict):
        raise CarrierProfileError(
            f"carrier_profile must be a registered name or a mapping with "
            f"'name' and 'states', got {type(declared).__name__}")

    name = declared.get("name")
    if not name:
        raise CarrierProfileError("carrier_profile declares no 'name'")

    states = declared.get("states")
    if not states:
        raise CarrierProfileError(
            f"carrier_profile {name!r} declares no 'states'. Every profile must "
            f"say which of its states an analysis may use — that declaration is "
            f"what the format requires, not any particular vocabulary")
    if not isinstance(states, dict):
        raise CarrierProfileError(
            f"carrier_profile.states must map each state to one of {list(USABILITY)}")

    bad = {s: u for s, u in states.items() if u not in USABILITY}
    if bad:
        raise CarrierProfileError(
            f"carrier_profile {name!r}: {bad} — usability must be one of "
            f"{list(USABILITY)}")
    if not any(u == "analysable" for u in states.values()):
        raise CarrierProfileError(
            f"carrier_profile {name!r} declares no analysable state, so no trip "
            f"in this dataset could ever be used. At least one state must be "
            f"'analysable'")

    # An inline profile that re-declares a registered name is refused rather
    # than silently shadowing it: two datasets naming the same profile must mean
    # the same thing, or the name is worthless.
    if name in REGISTERED_PROFILES and dict(states) != REGISTERED_PROFILES[name]:
        raise CarrierProfileError(
            f"carrier_profile {name!r} is registered by SPEC-02 §3.8.1 and cannot "
            f"be redefined. Name the variant something else, or use the "
            f"registered profile unchanged")

    return CarrierProfile(str(name), dict(states), False)
