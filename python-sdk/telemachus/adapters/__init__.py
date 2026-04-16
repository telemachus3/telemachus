"""
Telemachus Adapters — convert Open datasets to Telemachus format.

Each adapter is a module with a `load()` function that returns a
Telemachus-conformant pandas DataFrame with SI units.
"""

REGISTRY = {
    "aegis": "telemachus.adapters.aegis",
    "pvs": "telemachus.adapters.pvs",
    "stride": "telemachus.adapters.stride",
}


def load(name: str, source_path, **kwargs):
    """Load an Open dataset by adapter name.

    Parameters
    ----------
    name : str
        Adapter name (aegis, pvs, stride).
    source_path : str or Path
        Path to raw dataset directory.
    **kwargs
        Adapter-specific options.

    Returns
    -------
    pd.DataFrame
        Telemachus-conformant DataFrame.
    """
    import importlib

    if name not in REGISTRY:
        raise ValueError(f"Unknown adapter {name!r}. Available: {sorted(REGISTRY)}")
    mod = importlib.import_module(REGISTRY[name])
    return mod.load(source_path, **kwargs)
