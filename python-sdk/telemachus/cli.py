"""Command line for Telemachus: convert, validate, describe.

``tele convert`` is the command that matters to someone arriving with their own
data. It writes the parquet file *and* the manifest, filling in the row
accounting of SPEC-02 §3.5 from the conversion that just ran, then validates
what it wrote. A conversion whose output does not validate reports the failure
and exits non-zero rather than leaving a broken dataset on disk with a cheerful
message above it.
"""

from pathlib import Path

import click
import yaml

from ._validate_legacy import summarize_dataset
from ._validate_legacy import validate_manifest as validate_manifest_legacy
from .core.validate_tables import validate_all_tables
from .io_export import export_rs3_to_telemachus
from .io_import import load_dataset


@click.group()
@click.version_option(package_name="telemachus")
def tele():
    """Telemachus CLI (convert/validate/info)."""


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
    click.echo(f"Export OK -> {outdir}")


@tele.command("validate")
@click.argument("path")
@click.option("--level", default="full",
              type=click.Choice(["basic", "strict", "manifest", "full"]),
              help="Validation level (SPEC-03 §4.1)")
@click.option("--legacy", is_flag=True, default=False,
              help="Validate a v0.1 three-table dataset instead of SPEC-01/02")
def validate_cmd(path, level, legacy):
    """Validate a dataset directory, a manifest.yaml, or a parquet file."""
    import telemachus as tele_api

    if legacy:
        ok, report = validate_manifest_legacy(path)
        click.echo(report)
        raise SystemExit(0 if ok else 1)

    p = Path(path)
    if p.is_dir() or (p.suffix in (".yaml", ".yml") and level != "manifest"):
        report = tele_api.validate_dataset(p, level=level)
    elif p.suffix in (".yaml", ".yml"):
        report = tele_api.validate_manifest(p)
    elif p.suffix == ".parquet":
        report = tele_api.validate(tele_api.read(p), level=level)
    else:
        click.echo(f"Cannot validate {p.suffix or 'this path'}: expected a directory, "
                   f"a manifest.yaml or a .parquet file")
        raise SystemExit(2)

    click.echo(str(report))
    raise SystemExit(0 if report.ok else 1)


@tele.command("info")
@click.argument("manifest_path")
def info_cmd(manifest_path):
    """Summarize dataset rows, columns, and tables."""
    click.echo(summarize_dataset(manifest_path))


@tele.command("convert")
@click.argument("adapter_name")
@click.argument("source_path")
@click.option("--outdir", "-o", required=True, help="Output directory for Telemachus parquet + manifest")
@click.option("--mapping", default=None, help="csv: declarative column/unit mapping (YAML)")
@click.option("--extras", default="drop", type=click.Choice(["drop", "keep"]),
              help="csv: carry unmapped source columns as x_csv_* instead of dropping them")
@click.option("--date", default=None, help="nmea: YYYY-MM-DD for a log with GGA but no RMC")
@click.option("--device-id", default=None, help="gpx/nmea: value for the device_id column")
@click.option("--placement", default="dashboard", help="pvs: sensor placement")
@click.option("--side", default="left", help="pvs: MPU sensor side (left/right)")
@click.option("--category", default="driving", help="stride: category (driving/anomalies/all)")
@click.option("--top-n-trips", type=int, default=None, help="aegis: load N longest trips")
def convert_cmd(adapter_name, source_path, outdir, mapping, extras, date, device_id,
                placement, side, category, top_n_trips):
    """Convert a source to Telemachus parquet + manifest.yaml.

    ADAPTER_NAME: csv, gpx, nmea (any source of that format) or
    aegis, pvs, stride (one named research dataset each).

    SOURCE_PATH: the file or directory to read.
    """
    import telemachus as tele_api
    from telemachus.adapters import FORMAT_ADAPTERS, REGISTRY, _module

    if adapter_name not in REGISTRY:
        click.echo(f"Unknown adapter {adapter_name!r}. Available: {sorted(REGISTRY)}")
        raise SystemExit(2)

    if adapter_name == "csv" and not mapping:
        click.echo("The csv adapter needs --mapping: it converts any CSV, which "
                   "means it cannot know what your columns are or what units they "
                   "carry. Start from `tele mapping-template <file.csv>`.")
        raise SystemExit(2)

    account = tele_api.RowAccount(raw_rows_in=0)
    kwargs: dict = {}
    if adapter_name == "csv":
        kwargs = {"mapping": mapping, "extras": extras, "account": account}
    elif adapter_name == "gpx":
        kwargs = {"account": account, "device_id": device_id}
    elif adapter_name == "nmea":
        kwargs = {"account": account, "date": date}
        if device_id:
            kwargs["device_id"] = device_id
    elif adapter_name == "pvs":
        kwargs = {"placement": placement, "side": side}
    elif adapter_name == "stride":
        kwargs = {"category": category}
    elif adapter_name == "aegis" and top_n_trips:
        kwargs = {"top_n_trips": top_n_trips}

    click.echo(f"Converting {adapter_name} from {source_path}")
    module = _module(adapter_name)
    df = module.load(source_path, **kwargs)

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    pq_path = out / f"{adapter_name}.parquet"
    df.to_parquet(pq_path, index=False, compression="zstd")
    click.echo(f"  {len(df)} rows, {len(df.columns)} columns -> {pq_path}")

    # Manifest, with the row accounting this conversion just produced.
    manifest_source = mapping if adapter_name == "csv" else source_path
    if adapter_name in FORMAT_ADAPTERS:
        manifest = module.manifest(manifest_source, account=account, rows_out=len(df))
        manifest.setdefault("data_files", []).append(
            {"path": pq_path.name, "format": "parquet",
             "size_mb": round(pq_path.stat().st_size / 1e6, 3)})
        manifest_path = out / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)
        click.echo(f"  manifest -> {manifest_path}")
        metrics = manifest.get("source", {}).get("metrics", {})
        if metrics.get("raw_rows_dropped"):
            click.echo(f"  dropped {metrics['raw_rows_dropped']} of "
                       f"{metrics['raw_rows_in']} rows: "
                       f"{metrics.get('drop_reasons', {})}")
        report = tele_api.validate_dataset(out, level="full")
    else:
        click.echo("  no manifest: this adapter does not describe its own output "
                   "(SPEC-02 must be written by hand)")
        report = tele_api.validate(df)

    click.echo(str(report))
    raise SystemExit(0 if report.ok else 1)


@tele.command("mapping-template")
@click.argument("source_path", required=False)
def mapping_template_cmd(source_path):
    """Print a CSV mapping skeleton, listing the source's own columns."""
    from telemachus.adapters.csv_mapping import template

    click.echo(template(source_path), nl=False)


@tele.command("check-tables")
@click.argument("manifest_path")
@click.option("--no-align", is_flag=True, default=False, help="Disable trajectory<->IMU temporal alignment check")
@click.option("--tolerance-ns", type=int, default=5_000_000, show_default=True, help="Alignment tolerance in nanoseconds (default 5 ms)")
def check_tables_cmd(manifest_path, no_align, tolerance_ns):
    """Run tabular checks on v0.1 three-table datasets (legacy)."""
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


if __name__ == "__main__":
    tele()
