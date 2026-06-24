###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from app.models.tag import DataType

_FORMAT_MAP: dict[DataType, str] = {
    DataType.BOOL:   "DIGITAL",
    DataType.INT16:  "16BITS",
    DataType.UINT16: "16BITS",
    DataType.INT32:  "32BITS",
    DataType.UINT32: "32BITS",
    DataType.FLOAT:  "FLOAT",
    DataType.BYTE:   "BYTE",
    DataType.TEXT:   "TEXT",
}


def datatype_to_format(dt: DataType) -> str:
    return _FORMAT_MAP[dt]


def datatype_to_signed(dt: DataType) -> str | None:
    """Return 'True', 'False', or None (not applicable) for the Signed XML element."""
    signed = dt.is_signed
    if signed is None:
        return None
    return "True" if signed else "False"


def format_to_datatype(format_str: str, signed_str: str | None) -> DataType:
    """
    Convert Twinsoft Format string + optional Signed string to internal DataType.
    Raises ValueError for unrecognised format strings.
    """
    match format_str.upper():
        case "DIGITAL":
            return DataType.BOOL
        case "FLOAT":
            return DataType.FLOAT
        case "BYTE":
            return DataType.BYTE
        case "TEXT":
            return DataType.TEXT
        case "16BITS":
            return DataType.INT16 if signed_str == "True" else DataType.UINT16
        case "32BITS":
            return DataType.INT32 if signed_str == "True" else DataType.UINT32
        case _:
            raise ValueError(f"Unrecognised Twinsoft format: '{format_str}'")
