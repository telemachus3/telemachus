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

from .units import G0

__all__ = ["Finding", "check_units"]

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

def _check_speed_against_positions(df: pd.DataFrame) -> list[Finding]:
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

    fixes = df.loc[df["lat"].notna() & df["lon"].notna() & df["speed_mps"].notna(),
                   ["ts", "lat", "lon", "speed_mps"]].copy()
    if len(fixes) < 30:
        return []
    fixes["ts"] = pd.to_datetime(fixes["ts"], utc=True, errors="coerce")
    fixes = fixes.dropna(subset=["ts"]).sort_values("ts")
    if len(fixes) < 30:
        return []

    dt = fixes["ts"].diff().dt.total_seconds().to_numpy()
    dist = np.asarray(haversine_m(fixes["lat"].shift(), fixes["lon"].shift(),
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
    if spread < 0.01:
        return [Finding(
            "speed_mps", "warning",
            f"speed_mps tracks the speed its own positions imply too closely "
            f"(ratio spread {spread:.4f}) to be an independent measurement: it "
            f"appears to be derived from them. This check therefore cannot "
            f"validate it — a derived column always agrees with its source. "
            f"Nothing here says the values are wrong, only that they are "
            f"unverified",
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_units(df: pd.DataFrame, *, acc_frame: str | None = None) -> list[Finding]:
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

    Returns
    -------
    list[Finding]
        Empty when nothing is suspect. Errors first.
    """
    findings: list[Finding] = []
    findings += _check_speed_against_positions(df)
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
