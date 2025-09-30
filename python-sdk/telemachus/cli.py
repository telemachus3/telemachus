

import click
from .io_export import export_rs3_to_telemachus
from .validate import validate_manifest, summarize_dataset

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