"""Row accounting — what an adapter read, what it wrote, what it threw away.

SPEC-02 §3.5 requires an adapter to report ``raw_rows_in``, ``rows_out``,
``raw_rows_dropped`` and a ``drop_reasons`` breakdown, and states that a
non-zero ``raw_rows_dropped`` MUST be explained by ``drop_reasons``. Until now
the specification asked for that block and nothing in this library produced it,
so every adapter that dropped a row dropped it silently.

The asymmetry is the reason the block exists: a validator only ever sees the
output file. It can tell that 2 681 050 rows are well-formed; it cannot tell
that 12 364 rows were discarded on the way in, still less whether they deserved
it. The accounting is the only channel through which that fact reaches a
consumer, which is why it is a count *per reason* and not a total.

Typical use inside an adapter::

    account = RowAccount(raw_rows_in=len(raw))
    df, account = drop_duplicate_ts(df, account)
    df = df.dropna(subset=["lat", "lon"])
    account.drop("no_position", n_before - len(df))
    manifest["source"]["metrics"] = account.finish(rows_out=len(df))
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

__all__ = [
    "FORBIDDEN_DROP_REASONS",
    "RowAccount",
    "RowAccountError",
    "check_row_accounting",
    "drop_duplicate_ts",
]


class RowAccountError(ValueError):
    """The accounting does not balance, or a forbidden reason was declared."""


# SPEC-01 §2.5 / SPEC-02 §3.5: `gnss_valid` is advisory. A fix flagged invalid
# is still a positioned fix, and the receivers that set the flag are the ones
# whose flag is least trustworthy. Discarding on it is the single most common
# way a pipeline loses good data, so the reason is refused by name rather than
# left to a reviewer to notice in a YAML file.
FORBIDDEN_DROP_REASONS = {
    "gnss_valid_false": (
        "SPEC-01 §2.5 forbids dropping rows on the advisory `gnss_valid` flag; "
        "keep the rows and let the consumer filter"
    ),
    "gnss_invalid": (
        "SPEC-01 §2.5 forbids dropping rows on the advisory `gnss_valid` flag; "
        "keep the rows and let the consumer filter"
    ),
}


@dataclass
class RowAccount:
    """Running tally of rows read, dropped by reason, and written.

    Parameters
    ----------
    raw_rows_in : int
        Frames read from the source, counted before any filtering. For a
        multi-file source this is the sum over files; for a multi-rate source
        it is the total across streams, so that the identity below still holds.
    """

    raw_rows_in: int
    drop_reasons: dict[str, int] = field(default_factory=dict)

    def drop(self, reason: str, n: int) -> RowAccount:
        """Record ``n`` rows discarded for ``reason``. Returns self, to chain.

        A zero count is accepted and not recorded: an adapter should be able to
        call ``drop`` unconditionally without littering the manifest with
        reasons that never fired.
        """
        if n < 0:
            raise RowAccountError(f"Negative drop count for {reason!r}: {n}")
        if reason in FORBIDDEN_DROP_REASONS and n > 0:
            raise RowAccountError(f"Drop reason {reason!r} is not permitted. "
                                  f"{FORBIDDEN_DROP_REASONS[reason]}")
        if n:
            self.drop_reasons[reason] = self.drop_reasons.get(reason, 0) + int(n)
        return self

    @property
    def raw_rows_dropped(self) -> int:
        return sum(self.drop_reasons.values())

    def finish(self, rows_out: int) -> dict:
        """Close the account and return the SPEC-02 §3.5 ``metrics`` block.

        Raises
        ------
        RowAccountError
            If ``raw_rows_in`` does not equal ``rows_out + raw_rows_dropped``.
            An adapter that cannot balance its own books has lost track of rows
            somewhere, and that is worth failing the conversion over rather
            than publishing a number that does not add up.
        """
        metrics = {
            "raw_rows_in": int(self.raw_rows_in),
            "rows_out": int(rows_out),
            "raw_rows_dropped": int(self.raw_rows_dropped),
        }
        if self.drop_reasons:
            metrics["drop_reasons"] = dict(sorted(self.drop_reasons.items()))
        problems = check_row_accounting(metrics)
        if problems:
            raise RowAccountError("; ".join(problems))
        return metrics


def check_row_accounting(metrics: dict) -> list[str]:
    """Verify a ``source.metrics`` block against SPEC-02 §3.5.

    Returns the list of problems found and never raises, so a validator can
    report all of them at once. :meth:`RowAccount.finish` is the caller that
    turns a non-empty result into an error.
    """
    problems: list[str] = []
    if not isinstance(metrics, dict):
        return ["source.metrics must be a mapping"]

    reasons = metrics.get("drop_reasons") or {}
    if not isinstance(reasons, dict):
        return ["source.metrics.drop_reasons must be a mapping reason -> count"]

    for reason, note in FORBIDDEN_DROP_REASONS.items():
        if reasons.get(reason):
            problems.append(f"source.metrics.drop_reasons.{reason}: {note}")

    have = {k: metrics.get(k) for k in ("raw_rows_in", "rows_out", "raw_rows_dropped")}
    missing = [k for k, v in have.items() if v is None]
    if missing:
        problems.append(
            f"source.metrics is incomplete: missing {sorted(missing)}. "
            "SPEC-02 §3.5 expects raw_rows_in, rows_out and raw_rows_dropped together"
        )
        return problems

    n_in, n_out, n_drop = (int(have["raw_rows_in"]), int(have["rows_out"]),
                           int(have["raw_rows_dropped"]))

    if n_drop and not reasons:
        problems.append(
            f"source.metrics.raw_rows_dropped is {n_drop} but drop_reasons is empty; "
            "SPEC-02 §3.5 requires a non-zero drop to be explained"
        )
    declared = sum(int(v) for v in reasons.values())
    if reasons and declared != n_drop:
        problems.append(
            f"source.metrics.drop_reasons sum to {declared}, "
            f"raw_rows_dropped says {n_drop}"
        )
    if n_out + n_drop != n_in:
        problems.append(
            f"source.metrics does not balance: rows_out ({n_out}) + "
            f"raw_rows_dropped ({n_drop}) = {n_out + n_drop}, "
            f"raw_rows_in says {n_in}"
        )
    return problems


def drop_duplicate_ts(df: pd.DataFrame, account: RowAccount | None = None, *,
                      ts: str = "ts", by: str | None = "device_id",
                      keep: str = "first") -> tuple[pd.DataFrame, RowAccount | None]:
    """Remove rows repeating a timestamp already seen for the same entity.

    SPEC-01 §3 rule 2 requires ``ts`` to be strictly increasing, so a duplicate
    timestamp is not a stylistic matter: a file carrying one is not a valid
    Telemachus file. Duplicates arrive constantly all the same — a gateway
    redelivering a frame, two overlapping exports concatenated, a device whose
    clock stalls across a burst.

    Deduplication is per entity when ``by`` names a column that exists: two
    devices legitimately report at the same instant, and a global
    ``drop_duplicates`` on ``ts`` would delete one of them.

    Returns the frame and the account, so the call can be written as a single
    assignment at the point where both are updated.
    """
    if ts not in df.columns:
        return df, account

    keys = [ts]
    if by and by in df.columns:
        keys = [by, ts]

    before = len(df)
    out = df.drop_duplicates(subset=keys, keep=keep)
    removed = before - len(out)
    if removed and account is not None:
        account.drop("duplicate_ts", removed)
    return out.reset_index(drop=True), account
