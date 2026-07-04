###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.config import AppConfig, Rule, RuleEntry, TemplateMapping
from app.models.tag import DataType

CONFIG_JSON = Path(__file__).parent / "fixtures" / "app.config.json"


@pytest.fixture
def default_config() -> AppConfig:
    return AppConfig.model_validate_json(CONFIG_JSON.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Default config file integrity
# ---------------------------------------------------------------------------

class TestDefaultConfigLoads:
    def test_config_file_exists(self):
        assert CONFIG_JSON.exists(), f"Config file missing at {CONFIG_JSON}"

    def test_config_parses_without_error(self, default_config):
        assert default_config is not None

    def test_target_system_is_twinsoft(self, default_config):
        assert default_config.target_system == "twinsoft"

    def test_all_expected_rules_present(self, default_config):
        names = {r.name for r in default_config.rules}
        expected = {"_HOA", "_DI", "_DO", "_AI", "_SDI", "_SDO", "_SAI", "_LVL"}
        assert expected == names

    def test_all_expected_templates_present(self, default_config):
        templates = {t.template for t in default_config.templates}
        expected = {"DO", "DI", "AI", "SDI", "SDO", "SAI"}
        assert expected == templates

    def test_template_rule_references_are_valid(self, default_config):
        rule_names = {r.name for r in default_config.rules}
        for mapping in default_config.templates:
            for rule_name in mapping.rules:
                assert rule_name in rule_names, (
                    f"Template '{mapping.template}' references missing rule '{rule_name}'"
                )


# ---------------------------------------------------------------------------
# Rule entry counts
# ---------------------------------------------------------------------------

class TestRuleEntries:
    @pytest.mark.parametrize("rule_name,expected_count", [
        ("_HOA", 4),
        ("_DI",  2),
        ("_DO",  2),
        ("_AI",  4),
        ("_SDI", 2),
        ("_SDO", 2),
        ("_SAI", 1),
        ("_LVL", 4),
    ])
    def test_rule_entry_count(self, default_config, rule_name, expected_count):
        rule = default_config.rule_by_name(rule_name)
        assert rule is not None
        assert len(rule.entries) == expected_count

    def test_all_entry_data_classes_are_valid_datatypes(self, default_config):
        for rule in default_config.rules:
            for entry in rule.entries:
                assert isinstance(entry.data_class, DataType)


# ---------------------------------------------------------------------------
# Specific rule structure
# ---------------------------------------------------------------------------

class TestHOARule:
    def test_has_function_block(self, default_config):
        rule = default_config.rule_by_name("_HOA")
        assert rule.function_block is not None
        assert "FB_#N" in rule.function_block

    def test_no_condition_code(self, default_config):
        rule = default_config.rule_by_name("_HOA")
        assert rule.condition_code is None

    def test_roles(self, default_config):
        rule = default_config.rule_by_name("_HOA")
        roles = {e.role for e in rule.entries}
        assert roles == {"hoa_val", "hoa_h", "hoa_o", "hoa_a"}

    def test_hoa_val_is_uint16(self, default_config):
        rule = default_config.rule_by_name("_HOA")
        entry = rule.entry_by_role("hoa_val")
        assert entry.data_class == DataType.UINT16

    def test_hoa_bools_are_bool(self, default_config):
        rule = default_config.rule_by_name("_HOA")
        for role in ("hoa_h", "hoa_o", "hoa_a"):
            assert rule.entry_by_role(role).data_class == DataType.BOOL


class TestDIRule:
    def test_condition_code_is_soft_equals_io(self, default_config):
        assert default_config.rule_by_name("_DI").condition_code == "soft = io"

    def test_no_function_block(self, default_config):
        assert default_config.rule_by_name("_DI").function_block is None

    def test_io_entry_addr_1000(self, default_config):
        rule = default_config.rule_by_name("_DI")
        assert rule.entry_by_role("io").addr == 1000

    def test_soft_entry_addr_2000(self, default_config):
        rule = default_config.rule_by_name("_DI")
        assert rule.entry_by_role("soft").addr == 2000

    def test_io_tag_suffix_is_underscore(self, default_config):
        rule = default_config.rule_by_name("_DI")
        assert rule.entry_by_role("io").tag_suffix == "_"


class TestDORule:
    def test_condition_code_is_io_equals_soft(self, default_config):
        assert default_config.rule_by_name("_DO").condition_code == "io = soft"


class TestAIRule:
    def test_condition_code_is_raw_equals_io(self, default_config):
        assert default_config.rule_by_name("_AI").condition_code == "raw = io"

    def test_scaled_entry_is_float(self, default_config):
        rule = default_config.rule_by_name("_AI")
        assert rule.entry_by_role("scaled").data_class == DataType.FLOAT

    def test_scaled_addr_is_3024(self, default_config):
        rule = default_config.rule_by_name("_AI")
        assert rule.entry_by_role("scaled").addr == 3024

    def test_fault_entry_is_bool(self, default_config):
        rule = default_config.rule_by_name("_AI")
        assert rule.entry_by_role("fault").data_class == DataType.BOOL


class TestLVLRule:
    def test_has_four_setpoint_roles(self, default_config):
        rule = default_config.rule_by_name("_LVL")
        roles = {e.role for e in rule.entries}
        assert roles == {"ahh_sp", "ah_sp", "al_sp", "all_sp"}

    def test_all_entries_are_int16(self, default_config):
        rule = default_config.rule_by_name("_LVL")
        for entry in rule.entries:
            assert entry.data_class == DataType.INT16

    def test_all_entries_start_at_3900(self, default_config):
        rule = default_config.rule_by_name("_LVL")
        for entry in rule.entries:
            assert entry.addr == 3900


# ---------------------------------------------------------------------------
# Template lookups
# ---------------------------------------------------------------------------

class TestTemplateLookup:
    def test_do_template_returns_hoa_and_do_rules(self, default_config):
        rules = default_config.rules_for_template("DO")
        names = [r.name for r in rules]
        assert names == ["_HOA", "_DO"]

    def test_di_template_returns_di_rule(self, default_config):
        rules = default_config.rules_for_template("DI")
        assert [r.name for r in rules] == ["_DI"]

    def test_unknown_template_returns_empty_list(self, default_config):
        assert default_config.rules_for_template("UNKNOWN") == []


# ---------------------------------------------------------------------------
# Alarm defaults
# ---------------------------------------------------------------------------

class TestAlarmDefaults:
    def test_default_condition_is_pos(self, default_config):
        assert default_config.alarm_defaults.condition == "POS"

    def test_default_recipient_is_default(self, default_config):
        assert default_config.alarm_defaults.recipient == "Default"

    def test_default_handling_is_enabled(self, default_config):
        assert default_config.alarm_defaults.options.handling == "ENABLED"


# ---------------------------------------------------------------------------
# Validation — template references unknown rule
# ---------------------------------------------------------------------------

class TestConfigValidation:
    def test_invalid_template_rule_reference_raises(self):
        with pytest.raises(ValidationError, match="unknown rule"):
            AppConfig(
                rules=[],
                templates=[TemplateMapping(template="DI", rules=["_NONEXISTENT"])],
            )

    def test_valid_config_with_matching_rule_passes(self):
        config = AppConfig(
            rules=[
                Rule(
                    name="_DI",
                    entries=[
                        RuleEntry(role="io", addr=1000, data_class=DataType.BOOL)
                    ],
                )
            ],
            templates=[TemplateMapping(template="DI", rules=["_DI"])],
        )
        assert config.rules_for_template("DI")[0].name == "_DI"


# ---------------------------------------------------------------------------
# Round-trip serialisation
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_serialize_and_reload_produces_identical_config(self, default_config):
        json_str = default_config.model_dump_json()
        reloaded = AppConfig.model_validate_json(json_str)
        assert reloaded == default_config
