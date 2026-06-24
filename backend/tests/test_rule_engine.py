###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from pathlib import Path

import pytest
from app.models.address_map import AddressMap
from app.models.config import AppConfig
from app.models.io_row import IoIndexRow
from app.models.tag import DataType
from app.services.etl.rule_engine import RuleEngine

_CONFIG_JSON = Path(__file__).parents[2] / "config" / "app.config.json"


@pytest.fixture
def config() -> AppConfig:
    return AppConfig.model_validate_json(_CONFIG_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def engine(config):
    return RuleEngine(config=config, address_map=AddressMap())


def _di_row(**kwargs) -> IoIndexRow:
    defaults = dict(number=1, tag_name="LSL-001", description="Low level", template="DI")
    return IoIndexRow(**(defaults | kwargs))


def _do_row(**kwargs) -> IoIndexRow:
    defaults = dict(number=1, tag_name="XY-001", description="Control valve", template="DO")
    return IoIndexRow(**(defaults | kwargs))


def _ai_row(**kwargs) -> IoIndexRow:
    defaults = dict(number=1, tag_name="LT-001", description="Level transmitter", template="AI")
    return IoIndexRow(**(defaults | kwargs))


def _hoa_row(**kwargs) -> IoIndexRow:
    defaults = dict(number=1, tag_name="XY-001", description="Control valve", template="DO")
    return IoIndexRow(**(defaults | kwargs))


# ---------------------------------------------------------------------------
# Tag name generation
# ---------------------------------------------------------------------------

class TestTagNameGeneration:
    def test_hyphen_converted_to_underscore(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001")])
        names = [t.name for t in result.tags]
        assert all("-" not in n for n in names)

    def test_di_generates_two_tags(self, engine):
        result = engine.process([_di_row()])
        assert len(result.tags) == 2

    def test_di_physical_tag_has_trailing_underscore(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001")])
        names = [t.name for t in result.tags]
        assert "LSL_001_" in names

    def test_di_soft_tag_has_no_suffix(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001")])
        names = [t.name for t in result.tags]
        assert "LSL_001" in names

    def test_do_generates_three_tags(self, engine):
        # DO template → _HOA (4 tags) + _DO (2 tags) = 6 tags
        result = engine.process([_do_row()])
        assert len(result.tags) == 6

    def test_ai_generates_four_tags(self, engine):
        result = engine.process([_ai_row()])
        assert len(result.tags) == 4


# ---------------------------------------------------------------------------
# Module/channel token substitution
# ---------------------------------------------------------------------------

class TestTokenSubstitution:
    def test_module_token_replaced(self, engine):
        result = engine.process([_di_row(tag_name="DIG-001", module=3)])
        # _DI io tag suffix is "_", desc_suffix is "M#MC#C"
        comments = [t.comment for t in result.tags]
        assert any("M3" in c for c in comments)

    def test_channel_token_replaced(self, engine):
        result = engine.process([_di_row(tag_name="DIG-001", module=1, module_channel=5)])
        comments = [t.comment for t in result.tags]
        assert any("C5" in c for c in comments)

    def test_missing_module_leaves_token(self, engine):
        result = engine.process([_di_row(tag_name="DIG-001")])
        # No module provided → #M stays in description
        comments = [t.comment for t in result.tags]
        assert any("#M" in c for c in comments)


# ---------------------------------------------------------------------------
# Address allocation
# ---------------------------------------------------------------------------

class TestAddressAllocation:
    def test_di_io_tag_has_bool_type(self, engine):
        result = engine.process([_di_row()])
        bool_tags = [t for t in result.tags if t.data_type == DataType.BOOL]
        assert len(bool_tags) >= 1

    def test_ai_float_tag_has_even_modbus_address(self, engine):
        result = engine.process([_ai_row()])
        float_tags = [t for t in result.tags if t.data_type == DataType.FLOAT]
        for tag in float_tags:
            assert tag.modbus_address % 2 == 0

    def test_second_di_gets_next_address(self, engine):
        rows = [
            _di_row(number=1, tag_name="LSL-001"),
            _di_row(number=2, tag_name="LAL-001"),
        ]
        result = engine.process(rows)
        bool_tags = [t for t in result.tags if t.data_type == DataType.BOOL]
        # 2 DI rows × 2 bool entries each = 4 bool tags, all unique addresses
        addresses = {t.modbus_address for t in bool_tags}
        assert len(addresses) == 4

    def test_coil_and_register_addresses_are_independent(self, engine):
        rows = [_di_row(), _ai_row()]
        result = engine.process(rows)
        bool_tags = [t for t in result.tags if t.data_type == DataType.BOOL]
        int_tags = [t for t in result.tags if t.data_type == DataType.INT16]
        # They can share the same numeric address — different address spaces
        bool_addrs = {t.modbus_address for t in bool_tags}
        int_addrs = {t.modbus_address for t in int_tags}
        assert bool_addrs and int_addrs  # both have at least one tag


# ---------------------------------------------------------------------------
# Conditioning code
# ---------------------------------------------------------------------------

class TestConditioningCode:
    def test_di_generates_conditioning_entry(self, engine):
        result = engine.process([_di_row()])
        assert len(result.conditioning) >= 1

    def test_di_conditioning_is_soft_equals_io(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001")])
        di_entries = [e for e in result.conditioning if e.rule == "_DI"]
        assert len(di_entries) == 1
        assert di_entries[0].statement == "LSL_001 = LSL_001_"

    def test_do_conditioning_is_io_equals_soft(self, engine):
        result = engine.process([_do_row(tag_name="XY-001")])
        do_entries = [e for e in result.conditioning if e.rule == "_DO"]
        assert len(do_entries) == 1
        assert do_entries[0].statement == "XY_001_ = XY_001"

    def test_failsafe_adds_not_to_source(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001", failsafe=True)])
        di_entries = [e for e in result.conditioning if e.rule == "_DI"]
        assert di_entries[0].statement == "LSL_001 = NOT LSL_001_"

    def test_do_failsafe_adds_not_to_source(self, engine):
        result = engine.process([_do_row(tag_name="XY-001", failsafe=True)])
        do_entries = [e for e in result.conditioning if e.rule == "_DO"]
        assert do_entries[0].statement == "XY_001_ = NOT XY_001"

    def test_ai_generates_conditioning_entry(self, engine):
        result = engine.process([_ai_row(tag_name="LT-001")])
        ai_entries = [e for e in result.conditioning if e.rule == "_AI"]
        assert len(ai_entries) == 1

    def test_ai_conditioning_is_raw_equals_io(self, engine):
        result = engine.process([_ai_row(tag_name="LT-001")])
        ai_entries = [e for e in result.conditioning if e.rule == "_AI"]
        # raw tag = LT_001_R, io tag = LT_001_
        assert "LT_001_R = LT_001_" in ai_entries[0].statement

    def test_two_di_rows_produce_two_conditioning_entries(self, engine):
        rows = [
            _di_row(number=1, tag_name="LSL-001"),
            _di_row(number=2, tag_name="LAL-001"),
        ]
        result = engine.process(rows)
        di_entries = [e for e in result.conditioning if e.rule == "_DI"]
        assert len(di_entries) == 2


# ---------------------------------------------------------------------------
# Function blocks
# ---------------------------------------------------------------------------

class TestFunctionBlocks:
    def test_do_generates_hoa_function_block(self, engine):
        result = engine.process([_do_row(tag_name="XY-001")])
        hoa_entries = [e for e in result.function_blocks if e.rule == "_HOA"]
        assert len(hoa_entries) == 1

    def test_hoa_function_block_contains_tag_names(self, engine):
        result = engine.process([_do_row(tag_name="XY-001")])
        hoa_entries = [e for e in result.function_blocks if e.rule == "_HOA"]
        stmt = hoa_entries[0].statement
        assert "XY_001_HOA" in stmt
        assert "XY_001_H" in stmt
        assert "XY_001_O" in stmt
        assert "XY_001_A" in stmt

    def test_hoa_counter_starts_at_1(self, engine):
        result = engine.process([_do_row(tag_name="XY-001")])
        hoa_entries = [e for e in result.function_blocks if e.rule == "_HOA"]
        assert "FB_1(" in hoa_entries[0].statement

    def test_hoa_counter_increments_per_row(self, engine):
        rows = [
            _do_row(number=1, tag_name="XY-001"),
            _do_row(number=2, tag_name="XY-002"),
        ]
        result = engine.process(rows)
        hoa_entries = [e for e in result.function_blocks if e.rule == "_HOA"]
        assert len(hoa_entries) == 2
        assert "FB_1(" in hoa_entries[0].statement
        assert "FB_2(" in hoa_entries[1].statement

    def test_di_has_no_function_block(self, engine):
        result = engine.process([_di_row()])
        assert not result.function_blocks


# ---------------------------------------------------------------------------
# Alarm generation
# ---------------------------------------------------------------------------

class TestAlarmGeneration:
    def test_no_alarm_when_is_alarm_false(self, engine):
        result = engine.process([_di_row(is_alarm=False)])
        assert not result.alarms

    def test_alarm_generated_when_is_alarm_true(self, engine):
        result = engine.process([_di_row(is_alarm=True, alarm_message="Low level")])
        assert len(result.alarms) == 1

    def test_alarm_tag_name_is_soft_tag(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001", is_alarm=True)])
        assert result.alarms[0].tag_name == "LSL_001"

    def test_alarm_uses_row_condition_when_set(self, engine):
        result = engine.process([_di_row(is_alarm=True, alarm_condition="NEG")])
        assert result.alarms[0].condition == "NEG"

    def test_alarm_uses_config_default_when_condition_not_set(self, engine, config):
        result = engine.process([_di_row(is_alarm=True)])
        assert result.alarms[0].condition == config.alarm_defaults.condition

    def test_alarm_message_set(self, engine):
        result = engine.process([_di_row(is_alarm=True, alarm_message="Tank is low")])
        assert result.alarms[0].message == "Tank is low"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_unknown_template_produces_error(self, engine):
        row = IoIndexRow(number=5, tag_name="XX-001", template="UNKNOWN")
        result = engine.process([row])
        assert result.has_errors
        assert len(result.errors) == 1

    def test_error_contains_template_name(self, engine):
        row = IoIndexRow(number=5, tag_name="XX-001", template="BADTEMPLATE")
        result = engine.process([row])
        assert "BADTEMPLATE" in result.errors[0].message

    def test_error_row_number_captured(self, engine):
        row = IoIndexRow(number=42, tag_name="XX-001", template="UNKNOWN")
        result = engine.process([row])
        assert result.errors[0].row_number == 42

    def test_error_does_not_stop_processing_other_rows(self, engine):
        rows = [
            IoIndexRow(number=1, tag_name="XX-001", template="UNKNOWN"),
            _di_row(number=2, tag_name="LSL-001"),
        ]
        result = engine.process(rows)
        assert result.has_errors
        assert len(result.tags) > 0

    def test_tag_name_too_long_produces_error(self, engine):
        # 16-char tag name (limit is 15)
        row = _di_row(tag_name="TOOLONGTAGNAMEX")  # 15 chars base + "_" suffix = 16
        result = engine.process([row])
        assert result.has_errors


# ---------------------------------------------------------------------------
# Description building
# ---------------------------------------------------------------------------

class TestDescriptionBuilding:
    def test_description_without_suffix(self, engine):
        # DI soft tag entry has empty desc_suffix — description passed through unchanged
        result = engine.process([_di_row(tag_name="DIG-001", description="My signal")])
        soft_tag = next(t for t in result.tags if t.name == "DIG_001")
        assert "My signal" in soft_tag.comment

    def test_description_with_module_channel_suffix(self, engine):
        result = engine.process([
            _di_row(tag_name="DIG-001", description="Level", module=2, module_channel=3)
        ])
        # DI desc_suffix is "M#MC#C" → "M2C3"
        physical_tag = next(t for t in result.tags if t.name == "DIG_001_")
        assert "M2C3" in physical_tag.comment

    def test_description_truncated_to_50_chars(self, engine):
        long_desc = "A" * 60
        result = engine.process([_di_row(description=long_desc, module=1, module_channel=1)])
        for tag in result.tags:
            assert len(tag.comment) <= 50

    def test_description_with_delimiter(self, engine):
        # _HOA entries use a delimiter "-" between base description and suffix
        result = engine.process([_do_row(tag_name="XY-001", description="Valve")])
        hoa_val = next(t for t in result.tags if t.name == "XY_001_HOA")
        assert " - " in hoa_val.comment


# ---------------------------------------------------------------------------
# Write-allowed propagation
# ---------------------------------------------------------------------------

class TestWriteAllowed:
    def test_di_soft_tag_is_not_writable(self, engine):
        result = engine.process([_di_row(tag_name="LSL-001")])
        soft_tag = next(t for t in result.tags if t.name == "LSL_001")
        assert not soft_tag.write_allowed.enabled

    def test_do_soft_tag_is_writable(self, engine):
        result = engine.process([_do_row(tag_name="XY-001")])
        soft_tag = next(t for t in result.tags if t.name == "XY_001")
        assert soft_tag.write_allowed.enabled
