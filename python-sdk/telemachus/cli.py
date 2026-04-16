

import click
from .io_export import export_rs3_to_telemachus
from ._validate_legacy import validate_manifest, summarize_dataset
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


@tele.command("convert")
@click.argument("adapter_name")
@click.argument("source_path")
@click.option("--outdir", "-o", required=True, help="Output directory for Telemachus parquet + manifest")
@click.option("--placement", default="dashboard", help="PVS: sensor placement (dashboard/above_suspension/below_suspension)")
@click.option("--side", default="left", help="PVS: MPU sensor side (left/right)")
@click.option("--category", default="driving", help="STRIDE: category (driving/anomalies/all)")
@click.option("--top-n-trips", type=int, default=None, help="AEGIS: load N longest trips")
def convert_cmd(adapter_name, source_path, outdir, placement, side, category, top_n_trips):
    """Convert an Open dataset to Telemachus format.

    ADAPTER_NAME: aegis, pvs, or stride
    SOURCE_PATH: path to the raw dataset directory
    """
    import os
    from telemachus.adapters import load as adapter_load

    kwargs = {}
    if adapter_name == "pvs":
        kwargs = {"placement": placement, "side": side}
    elif adapter_name == "stride":
        kwargs = {"category": category}
    elif adapter_name == "aegis":
        if top_n_trips:
            kwargs = {"top_n_trips": top_n_trips}

    click.echo(f"Converting {adapter_name} from {source_path}...")
    df = adapter_load(adapter_name, source_path, **kwargs)

    os.makedirs(outdir, exist_ok=True)
    pq_path = os.path.join(outdir, f"{adapter_name}.parquet")
    df.to_parquet(pq_path, index=False, compression="zstd")

    click.echo(f"  {len(df)} rows → {pq_path}")
    click.echo(f"  Columns: {list(df.columns)}")

    # Validate
    import telemachus as tele
    report = tele.validate(df)
    click.echo(f"  Validation: {report}")
    click.echo(f"Done.")


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