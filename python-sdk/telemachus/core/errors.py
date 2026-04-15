

"""
Custom exceptions for Telemachus v0.1 core validations.
"""

class SchemaError(Exception):
    """Raised when a dataset or manifest schema check fails."""


class SemanticError(Exception):
    """Raised when semantic validation fails (timestamps, ranges, etc.)."""


class UnitsError(Exception):
    """Raised when units in manifest are not compatible with v0.1 spec."""


class AlignmentWarning(Warning):
    """Warning for potential misalignment between trajectory/imu/events timestamps."""