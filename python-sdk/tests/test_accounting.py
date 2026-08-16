"""Row accounting (SPEC-02 §3.5) — the block a validator cannot reconstruct."""

import pandas as pd
import pytest

import telemachus as tele
from telemachus.core.accounting import (
    RowAccount,
    RowAccountError,
    check_row_accounting,
    drop_duplicate_ts,
)


def test_the_block_matches_spec02_section_3_5():
    account = RowAccount(raw_rows_in=2_693_414)
    account.drop("duplicate_ts", 12_000)
    account.drop("no_position_and_no_imu", 364)
    assert account.finish(rows_out=2_681_050) == {
        "raw_rows_in": 2_693_414,
        "rows_out": 2_681_050,
        "raw_rows_dropped": 12_364,
        "drop_reasons": {"duplicate_ts": 12_000, "no_position_and_no_imu": 364},
    }


def test_books_that_do_not_balance_fail_the_conversion():
    account = RowAccount(raw_rows_in=100)
    account.drop("duplicate_ts", 5)
    with pytest.raises(RowAccountError, match="does not balance"):
        account.finish(rows_out=90)          # 90 + 5 != 100


def test_zero_drops_leave_no_trace():
    account = RowAccount(raw_rows_in=10)
    account.drop("duplicate_ts", 0)
    assert "drop_reasons" not in account.finish(rows_out=10)


def test_dropping_on_gnss_valid_is_refused_by_name():
    """SPEC-01 §2.5: the flag is advisory, and dropping on it loses good fixes."""
    with pytest.raises(RowAccountError, match="not permitted"):
        RowAccount(raw_rows_in=10).drop("gnss_valid_false", 3)


def test_unexplained_drops_are_reported():
    problems = check_row_accounting(
        {"raw_rows_in": 100, "rows_out": 90, "raw_rows_dropped": 10})
    assert any("requires a non-zero drop to be explained" in p for p in problems)


def test_reasons_must_sum_to_the_declared_total():
    problems = check_row_accounting({
        "raw_rows_in": 100, "rows_out": 90, "raw_rows_dropped": 10,
        "drop_reasons": {"duplicate_ts": 3}})
    assert any("sum to 3" in p for p in problems)


def test_a_complete_block_passes():
    assert check_row_accounting({
        "raw_rows_in": 100, "rows_out": 90, "raw_rows_dropped": 10,
        "drop_reasons": {"duplicate_ts": 10}}) == []


def test_validate_manifest_reports_an_unbalanced_block(tmp_path):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "dataset_id: XX_test_2026\n"
        "schema_version: telemachus-1.0\n"
        "source:\n"
        "  type: live\n"
        "  metrics:\n"
        "    raw_rows_in: 100\n"
        "    rows_out: 80\n"
        "    raw_rows_dropped: 5\n"
        "    drop_reasons: {duplicate_ts: 5}\n")
    report = tele.validate_manifest(manifest)
    assert not report.ok
    assert any("does not balance" in e for e in report.errors)


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _frame(times, device="d1"):
    return pd.DataFrame({"ts": pd.to_datetime(times, utc=True),
                         "device_id": device, "lat": 49.0, "lon": 1.0})


def test_duplicate_timestamps_are_counted_under_their_own_reason():
    df = _frame(["2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z",
                 "2026-01-01T00:00:01Z", "2026-01-01T00:00:02Z"])
    account = RowAccount(raw_rows_in=len(df))
    out, account = drop_duplicate_ts(df, account)
    assert len(out) == 3
    assert account.drop_reasons == {"duplicate_ts": 1}


def test_two_devices_may_report_at_the_same_instant():
    df = pd.concat([_frame(["2026-01-01T00:00:00Z"], "d1"),
                    _frame(["2026-01-01T00:00:00Z"], "d2")], ignore_index=True)
    out, _ = drop_duplicate_ts(df, RowAccount(raw_rows_in=2))
    assert len(out) == 2, "a global drop_duplicates would delete one device's row"

def test_the_default_is_safe_because_finish_refuses_to_balance():
    """`raw_rows_in` defaults to zero so an adapter that counts as it reads need
    not write a value only to overwrite it. That is safe rather than merely
    convenient: a zero left in place by mistake cannot pass unnoticed."""
    account = RowAccount()
    assert account.raw_rows_in == 0

    account.drop("duplicate_ts", 2)
    with pytest.raises(RowAccountError, match="does not balance"):
        account.finish(rows_out=10)          # 10 + 2 != 0

    account.raw_rows_in = 12                 # what an adapter actually does
    assert account.finish(rows_out=10)["raw_rows_in"] == 12
