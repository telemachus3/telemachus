"""
Telemachus — Open Telematics Pivot Format.

Bridges high-frequency scientific kinematics and scalable fleet
analytics in a single, Parquet-native format.

The library is in two tiers, and the import path says which one you are in
(SPEC-04 §5.3):

``telemachus`` and ``telemachus.metrics``
    The normative tier. Everything here fills a manifest field or serves a
    validation rule, so it is bound to the specification version and does not
    change quietly.

``telemachus.analysis``
    The convenience tier. Useful, maintained, outside the specified perimeter,
    free to evolve without a spec revision. What lives here answers a question
    by making a decision — where a trip begins, what counts as a stop — rather
    than by reading a property of the data.
"""

__version__ = "1.0.0a3"

#: Specification version this library implements (SPEC-04 §2).
__spec_version__ = "telemachus-1.0"

from telemachus._api import (
    has_gps,
    has_gyro,
    has_imu,
    has_io,
    has_magneto,
    has_obd,
    is_full_imu,
    is_gps_only,
    read,
    sensor_profile,
    validate,
    validate_dataset,
    validate_manifest,
)
from telemachus.core.accounting import RowAccount, check_row_accounting, drop_duplicate_ts
from telemachus.core.breaks import (
    REGISTERED_KINDS,
    AcquisitionBreak,
    resolve_acquisition_breaks,
)
from telemachus.core.carrier import (
    REGISTERED_PROFILES,
    CarrierProfile,
    resolve_carrier_profile,
)
from telemachus.core.corrections import (
    Correction,
    resolve_corrections,
    strip_corrections,
)
from telemachus.core.multirate import merge_multirate
from telemachus.core.plausibility import check_timestamps, check_units
from telemachus.core.privacy import check_pii, strip_pii
from telemachus.core.provenance import (
    check_provenance_declaration,
    resolve_column_provenance,
)
from telemachus.core.units import convert as convert_unit

__all__ = [
    "__version__",
    "__spec_version__",
    # reading
    "read",
    # validation
    "validate",
    "validate_manifest",
    "validate_dataset",
    "check_units",
    "check_timestamps",
    "check_row_accounting",
    "check_provenance_declaration",
    "resolve_column_provenance",
    "check_pii",
    "strip_pii",
    # carrier profiles
    "CarrierProfile",
    "resolve_carrier_profile",
    "REGISTERED_PROFILES",
    # acquisition breaks (D0.5)
    "AcquisitionBreak",
    "resolve_acquisition_breaks",
    "REGISTERED_KINDS",
    # corrections (a corrected value never replaces its source)
    "Correction",
    "resolve_corrections",
    "strip_corrections",
    # building a conformant dataset
    "merge_multirate",
    "convert_unit",
    "RowAccount",
    "drop_duplicate_ts",
    # sensor introspection
    "has_gps",
    "has_imu",
    "has_gyro",
    "has_magneto",
    "has_obd",
    "has_io",
    "sensor_profile",
    "is_gps_only",
    "is_full_imu",
]
