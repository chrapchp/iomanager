###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import pytest
from pydantic import ValidationError
from app.models.tag import DataType, Tag


# ---------------------------------------------------------------------------
# DataType properties
# ---------------------------------------------------------------------------

class TestDataTypeProperties:
    @pytest.mark.parametrize("dtype,expected", [
        (DataType.FLOAT,  2),
        (DataType.INT32,  2),
        (DataType.UINT32, 2),
        (DataType.INT16,  1),
        (DataType.UINT16, 1),
        (DataType.BYTE,   1),
        (DataType.BOOL,   1),
        (DataType.TEXT,   1),
    ])
    def test_register_size(self, dtype, expected):
        assert dtype.register_size == expected

    @pytest.mark.parametrize("dtype,expected", [
        (DataType.BOOL,   True),
        (DataType.INT16,  False),
        (DataType.FLOAT,  False),
    ])
    def test_is_digital(self, dtype, expected):
        assert dtype.is_digital == expected

    @pytest.mark.parametrize("dtype,expected", [
        (DataType.FLOAT,  True),
        (DataType.INT32,  True),
        (DataType.UINT32, True),
        (DataType.INT16,  False),
        (DataType.UINT16, False),
        (DataType.BOOL,   False),
    ])
    def test_requires_even_boundary(self, dtype, expected):
        assert dtype.requires_even_boundary == expected

    @pytest.mark.parametrize("dtype,expected", [
        (DataType.FLOAT,  True),
        (DataType.INT16,  True),
        (DataType.INT32,  True),
        (DataType.UINT16, False),
        (DataType.UINT32, False),
        (DataType.BYTE,   False),
        (DataType.BOOL,   None),
        (DataType.TEXT,   None),
    ])
    def test_is_signed(self, dtype, expected):
        assert dtype.is_signed == expected


# ---------------------------------------------------------------------------
# Tag name validation
# ---------------------------------------------------------------------------

def _make_tag(**kwargs) -> Tag:
    defaults = dict(name="TAG_001", data_type=DataType.BOOL, modbus_address=0)
    return Tag(**(defaults | kwargs))


class TestTagNameValidation:
    @pytest.mark.parametrize("name", [
        "TAG_001",
        "A",
        "Z" * 15,
        "LAL_001",
        "GBL_ALWAYS_OFF",
        "X1",
    ])
    def test_valid_names_accepted(self, name):
        tag = _make_tag(name=name)
        assert tag.name == name

    def test_name_max_15_chars_accepted(self):
        name = "A" * 15
        assert _make_tag(name=name).name == name

    def test_name_16_chars_rejected(self):
        with pytest.raises(ValidationError):
            _make_tag(name="A" * 16)

    @pytest.mark.parametrize("name", [
        "1TAG",
        "_TAG",
        "9ABC",
    ])
    def test_name_must_start_with_alpha(self, name):
        with pytest.raises(ValidationError):
            _make_tag(name=name)

    @pytest.mark.parametrize("name", [
        "TAG-001",
        "TAG 001",
        "TAG.001",
        "TAG/001",
    ])
    def test_invalid_separators_rejected(self, name):
        with pytest.raises(ValidationError):
            _make_tag(name=name)

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            _make_tag(name="")


# ---------------------------------------------------------------------------
# Tag comment validation
# ---------------------------------------------------------------------------

class TestTagCommentValidation:
    def test_comment_at_50_chars_accepted(self):
        tag = _make_tag(comment="A" * 50)
        assert len(tag.comment) == 50

    def test_comment_at_51_chars_rejected(self):
        with pytest.raises(ValidationError):
            _make_tag(comment="A" * 51)

    def test_empty_comment_accepted(self):
        tag = _make_tag(comment="")
        assert tag.comment == ""


# ---------------------------------------------------------------------------
# Tag defaults and derived properties
# ---------------------------------------------------------------------------

class TestTagDefaults:
    def test_new_name_defaults_to_none(self):
        tag = _make_tag()
        assert tag.new_name is None

    def test_effective_new_name_returns_name_when_new_name_is_none(self):
        tag = _make_tag(name="LAL_001")
        assert tag.effective_new_name == "LAL_001"

    def test_effective_new_name_returns_new_name_when_set(self):
        tag = _make_tag(name="LAL_001", new_name="LAL_002")
        assert tag.effective_new_name == "LAL_002"
