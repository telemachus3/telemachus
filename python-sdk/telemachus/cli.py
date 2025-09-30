

import click
from .io_export import export_rs3_to_telemachus
from .validate import validate_manifest, summarize_dataset
from .io_import import load_dataset
from .core.validate_tables import validate_all_tables

@click.group()
def tele():
    """Telemachus CLI (export/validate/info)."""

@tele.command("export")
@click.option("--traj", required=True, help="RS3 trajectory CSV (timestamp,lat,lon,alt?,speed)")
@click.option("--imu", required=True, help="RS3 IMU CSV (timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)")
@click.option("--events", default="", help="Events CSV (timestamp,event_type,severity?,meta?)")
@click.option("--outdir", required=True, help="Output dataset directory")
@click.option("--freq-hz", type=int, default=10, help="Nominal frequency (Hz)")
@click.option("--vehicle-id", default="VEH-01")
@click.option("--vehicle-type", default="passenger_car")
def export_cmd(traj, imu, events, outdir, freq_hz, vehicle_id, vehicle_type):
    """Export RS3 CSV files to a Telemachus dataset."""
    export_rs3_to_telemachus(traj, imu, events, outdir, freq_hz, vehicle_id, vehicle_type)
    click.echo(f"✅ Export OK → {outdir}")

@tele.command("validate")
@click.argument("manifest_path")
def validate_cmd(manifest_path):
    """Validate a Telemachus dataset manifest and check referenced tables."""
    ok, report = validate_manifest(manifest_path)
    click.echo(report)
    raise SystemExit(0 if ok else 1)

@tele.command("info")
@click.argument("manifest_path")
def info_cmd(manifest_path):
    """Summarize dataset rows, columns, and tables."""
    click.echo(summarize_dataset(manifest_path))


@tele.command("check-tables")
@click.argument("manifest_path")
@click.option("--no-align", is_flag=True, default=False, help="Disable trajectory↔IMU temporal alignment check")
@click.option("--tolerance-ns", type=int, default=5_000_000, show_default=True, help="Alignment tolerance in nanoseconds (default 5 ms)")
def check_tables_cmd(manifest_path, no_align, tolerance_ns):
    """Run tabular checks on dataset tables (types, ranges, monotonicity, optional alignment)."""
    ds = load_dataset(manifest_path)
    units = ds["manifest"].get("units")
    tables = ds["tables"]

    ok, report, _ = validate_all_tables(
        tables=tables,
        units=units,
        check_timing_alignment=not no_align,
        tolerance_ns=int(tolerance_ns),
    )
    click.echo(report)
    raise SystemExit(0 if ok else 1)