"""Telemachus Adapters — convert source data to the Telemachus format.

Each adapter is a module with a ``load()`` function returning a
Telemachus-conformant DataFrame in canonical units, and optionally a
``manifest()`` returning the SPEC-02 sidecar (SPEC-03 §2.2).

Two families live here, and the difference matters to a newcomer:

**Dataset adapters** — ``aegis``, ``pvs``, ``stride`` — target one named
research dataset each. They exist to reproduce a published result, and they
know that dataset's file layout, its column names and its units by heart.

**Format adapters** — ``csv``, ``gpx``, ``nmea`` — target a *format* rather
than a dataset, and therefore work on data this project has never seen. The CSV
one takes its column and unit mapping as a declaration rather than as code
(see :mod:`telemachus.adapters.csv_mapping`), which is what lets someone
convert their own export without writing Python and without this library
guessing what their columns mean.
"""

REGISTRY = {
    # Format adapters — any source of this shape
    "csv": "telemachus.adapters.csv_mapping",
    "gpx": "telemachus.adapters.gpx",
    "nmea": "telemachus.adapters.nmea",
    # Dataset adapters — one named research dataset each
    "aegis": "telemachus.adapters.aegis",
    "pvs": "telemachus.adapters.pvs",
    "stride": "telemachus.adapters.stride",
}

FORMAT_ADAPTERS = ("csv", "gpx", "nmea")


def _module(name: str):
    import importlib

    if name not in REGISTRY:
        raise ValueError(f"Unknown adapter {name!r}. Available: {sorted(REGISTRY)}")
    return importlib.import_module(REGISTRY[name])


def load(name: str, source_path, **kwargs):
    """Load a dataset by adapter name.

    Parameters
    ----------
    name : str
        One of :data:`REGISTRY`.
    source_path : str or Path
        Path to the raw data.
    **kwargs
        Adapter-specific options. ``csv`` requires ``mapping=``; the format
        adapters accept ``account=`` to receive the SPEC-02 §3.5 row
        accounting.

    Returns
    -------
    pd.DataFrame
        Telemachus-conformant DataFrame.
    """
    return _module(name).load(source_path, **kwargs)


def manifest(name: str, source_path_or_mapping, **kwargs) -> dict:
    """Build the SPEC-02 manifest for an adapter, when it provides one.

    Raises
    ------
    NotImplementedError
        For an adapter that does not describe its own output. Silently
        returning an empty manifest would produce a dataset that looks
        documented and is not.
    """
    mod = _module(name)
    if not hasattr(mod, "manifest"):
        raise NotImplementedError(
            f"Adapter {name!r} does not build a manifest; write one by hand "
            f"against SPEC-02")
    return mod.manifest(source_path_or_mapping, **kwargs)
