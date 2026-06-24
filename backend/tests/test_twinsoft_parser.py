###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import pytest
from app.models.tag import DataType
from app.services.etl.twinsoft.parser import (
    datatype_to_format,
    datatype_to_signed,
    format_to_datatype,
)


class TestDatatypeToFormat:
    @pytest.mark.parametrize("dt,expected", [
        (DataType.BOOL,   "DIGITAL"),
        (DataType.INT16,  "16BITS"),
        (DataType.UINT16, "16BITS"),
        (DataType.INT32,  "32BITS"),
        (DataType.UINT32, "32BITS"),
        (DataType.FLOAT,  "FLOAT"),
        (DataType.BYTE,   "BYTE"),
        (DataType.TEXT,   "TEXT"),
    ])
    def test_known_types(self, dt, expected):
        assert datatype_to_format(dt) == expected


class TestDatatypeToSigned:
    @pytest.mark.parametrize("dt,expected", [
        (DataType.FLOAT,  "True"),
        (DataType.INT16,  "True"),
        (DataType.INT32,  "True"),
        (DataType.UINT16, "False"),
        (DataType.UINT32, "False"),
        (DataType.BYTE,   "False"),
        (DataType.BOOL,   None),
        (DataType.TEXT,   None),
    ])
    def test_signed_string(self, dt, expected):
        assert datatype_to_signed(dt) == expected


class TestFormatToDatatype:
    @pytest.mark.parametrize("fmt,signed,expected", [
        ("DIGITAL", None,    DataType.BOOL),
        ("DIGITAL", "",      DataType.BOOL),
        ("FLOAT",   None,    DataType.FLOAT),
        ("BYTE",    None,    DataType.BYTE),
        ("TEXT",    None,    DataType.TEXT),
        ("16BITS",  "True",  DataType.INT16),
        ("16BITS",  "False", DataType.UINT16),
        ("16BITS",  None,    DataType.UINT16),
        ("32BITS",  "True",  DataType.INT32),
        ("32BITS",  "False", DataType.UINT32),
    ])
    def test_known_formats(self, fmt, signed, expected):
        assert format_to_datatype(fmt, signed) == expected

    def test_case_insensitive(self):
        assert format_to_datatype("digital", None) == DataType.BOOL
        assert format_to_datatype("Float", None) == DataType.FLOAT

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unrecognised"):
            format_to_datatype("UNKNOWN", None)


class TestRoundTrip:
    @pytest.mark.parametrize("dt", [
        DataType.BOOL, DataType.FLOAT, DataType.BYTE, DataType.TEXT,
        DataType.INT16, DataType.UINT16, DataType.INT32, DataType.UINT32,
    ])
    def test_datatype_survives_round_trip(self, dt):
        fmt = datatype_to_format(dt)
        signed = datatype_to_signed(dt)
        result = format_to_datatype(fmt, signed)
        assert result == dt
