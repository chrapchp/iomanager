###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import xml.etree.ElementTree as ET
import pytest
from app.models.alarm import Alarm, AlarmOptions, FilterConfig
from app.models.output import ConditioningEntry, FunctionBlockEntry
from app.models.tag import DataType, PresentationConfig, Tag, WriteAllowedConfig
from app.services.etl.twinsoft.exporter import TwinsoftExporter


@pytest.fixture
def exporter():
    return TwinsoftExporter()


def _make_bool_tag(**kwargs) -> Tag:
    defaults = dict(name="DIG_001", data_type=DataType.BOOL, modbus_address=0)
    return Tag(**(defaults | kwargs))


def _make_float_tag(**kwargs) -> Tag:
    defaults = dict(name="AI_001", data_type=DataType.FLOAT, modbus_address=0)
    return Tag(**(defaults | kwargs))


def _parse_tag_xml(xml_str: str) -> ET.Element:
    root = ET.fromstring(xml_str.split("\n", 1)[1])  # strip declaration
    return root.find("Tag")


def _parse_alarm_xml(xml_str: str) -> ET.Element:
    root = ET.fromstring(xml_str.split("\n", 1)[1])
    return root.find("Alarm")


# ---------------------------------------------------------------------------
# XML declaration
# ---------------------------------------------------------------------------

class TestXmlDeclaration:
    def test_tags_xml_has_declaration(self, exporter):
        out = exporter.export_tags([_make_bool_tag()])
        assert out.startswith('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')

    def test_alarms_xml_has_declaration(self, exporter):
        out = exporter.export_alarms([Alarm(tag_name="DIG_001")])
        assert out.startswith('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')


# ---------------------------------------------------------------------------
# Tag XML structure
# ---------------------------------------------------------------------------

class TestTagXmlStructure:
    def test_root_element_is_twinsofttags(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        root = ET.fromstring(xml.split("\n", 1)[1])
        assert root.tag == "TWinSoftTags"

    def test_tag_name_attribute(self, exporter):
        xml = exporter.export_tags([_make_bool_tag(name="LSL_001")])
        tag = _parse_tag_xml(xml)
        assert tag.get("Name") == "LSL_001"

    def test_new_name_matches_name_by_default(self, exporter):
        xml = exporter.export_tags([_make_bool_tag(name="LSL_001")])
        tag = _parse_tag_xml(xml)
        assert tag.findtext("NewName") == "LSL_001"

    def test_new_name_uses_explicit_new_name(self, exporter):
        t = _make_bool_tag(name="LSL_001", new_name="LSL_002")
        xml = exporter.export_tags([t])
        tag = _parse_tag_xml(xml)
        assert tag.findtext("NewName") == "LSL_002"

    def test_address_is_always_empty(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        tag = _parse_tag_xml(xml)
        addr = tag.find("Address")
        assert addr is not None
        assert not (addr.text or "").strip()

    def test_display_format_is_always_decimal(self, exporter):
        xml = exporter.export_tags([_make_float_tag()])
        tag = _parse_tag_xml(xml)
        assert tag.findtext("DisplayFormat") == "DECIMAL"

    def test_inital_value_typo_preserved(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        tag = _parse_tag_xml(xml)
        assert tag.find("InitalValue") is not None
        assert tag.find("InitialValue") is None


# ---------------------------------------------------------------------------
# Format-specific field mapping
# ---------------------------------------------------------------------------

class TestDigitalTagFields:
    def test_format_is_digital(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        assert _parse_tag_xml(xml).findtext("Format") == "DIGITAL"

    def test_signed_is_empty(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        tag = _parse_tag_xml(xml)
        signed = tag.find("Signed")
        assert not (signed.text or "").strip()

    def test_minimum_is_empty_when_not_set(self, exporter):
        # BOOL tags have no minimum by default; exporter should render self-closing element
        xml = exporter.export_tags([_make_bool_tag()])
        tag = _parse_tag_xml(xml)
        assert not (tag.find("Minimum").text or "").strip()

    def test_modbus_address_set(self, exporter):
        xml = exporter.export_tags([_make_bool_tag(modbus_address=42)])
        assert _parse_tag_xml(xml).findtext("ModbusAddress") == "42"


class TestFloatTagFields:
    def test_format_is_float(self, exporter):
        xml = exporter.export_tags([_make_float_tag()])
        assert _parse_tag_xml(xml).findtext("Format") == "FLOAT"

    def test_signed_is_true(self, exporter):
        xml = exporter.export_tags([_make_float_tag()])
        assert _parse_tag_xml(xml).findtext("Signed") == "True"

    def test_minimum_and_maximum_populated(self, exporter):
        t = _make_float_tag(minimum="0", maximum="100")
        xml = exporter.export_tags([t])
        tag = _parse_tag_xml(xml)
        assert tag.findtext("Minimum") == "0"
        assert tag.findtext("Maximum") == "100"

    def test_text_tag_size_empty(self, exporter):
        xml = exporter.export_tags([_make_float_tag()])
        tag = _parse_tag_xml(xml)
        assert not (tag.find("TextTagSize").text or "").strip()


class TestInt16TagFields:
    def test_format_is_16bits(self, exporter):
        t = Tag(name="AI_001", data_type=DataType.INT16, modbus_address=0)
        xml = exporter.export_tags([t])
        assert _parse_tag_xml(xml).findtext("Format") == "16BITS"

    def test_signed_true_for_int16(self, exporter):
        t = Tag(name="AI_001", data_type=DataType.INT16, modbus_address=0)
        xml = exporter.export_tags([t])
        assert _parse_tag_xml(xml).findtext("Signed") == "True"

    def test_signed_false_for_uint16(self, exporter):
        t = Tag(name="AI_001", data_type=DataType.UINT16, modbus_address=0)
        xml = exporter.export_tags([t])
        assert _parse_tag_xml(xml).findtext("Signed") == "False"


# ---------------------------------------------------------------------------
# Presentation element
# ---------------------------------------------------------------------------

class TestPresentationElement:
    def test_presentation_true_when_enabled(self, exporter):
        t = _make_bool_tag(presentation=PresentationConfig(enabled=True, description="Level low"))
        xml = exporter.export_tags([t])
        pres = _parse_tag_xml(xml).find("Presentation")
        assert pres.text == "True"
        assert pres.get("Description") == "Level low"

    def test_presentation_false_by_default(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        pres = _parse_tag_xml(xml).find("Presentation")
        assert pres.text == "False"

    def test_presentation_state_on_off_for_digital(self, exporter):
        t = _make_bool_tag(
            presentation=PresentationConfig(state_on="HI", state_off="OK")
        )
        xml = exporter.export_tags([t])
        pres = _parse_tag_xml(xml).find("Presentation")
        assert pres.get("StateOn") == "HI"
        assert pres.get("StateOff") == "OK"

    def test_presentation_units_for_float(self, exporter):
        t = _make_float_tag(presentation=PresentationConfig(units="C"))
        xml = exporter.export_tags([t])
        pres = _parse_tag_xml(xml).find("Presentation")
        assert pres.get("Units") == "C"


# ---------------------------------------------------------------------------
# WriteAllowed element
# ---------------------------------------------------------------------------

class TestWriteAllowedElement:
    def test_write_allowed_false_by_default(self, exporter):
        xml = exporter.export_tags([_make_bool_tag()])
        wa = _parse_tag_xml(xml).find("WriteAllowed")
        assert wa.text == "False"

    def test_write_allowed_true_with_range(self, exporter):
        t = _make_float_tag(
            write_allowed=WriteAllowedConfig(enabled=True, minimum="10", maximum="90")
        )
        xml = exporter.export_tags([t])
        wa = _parse_tag_xml(xml).find("WriteAllowed")
        assert wa.text == "True"
        assert wa.get("WriteAllowed_Minimum") == "10"
        assert wa.get("WriteAllowed_Maximum") == "90"


# ---------------------------------------------------------------------------
# Multiple tags
# ---------------------------------------------------------------------------

class TestMultipleTags:
    def test_multiple_tags_in_one_xml(self, exporter):
        tags = [_make_bool_tag(name="DIG_001"), _make_bool_tag(name="DIG_002")]
        root = ET.fromstring(exporter.export_tags(tags).split("\n", 1)[1])
        assert len(root.findall("Tag")) == 2

    def test_empty_tag_list_produces_empty_root(self, exporter):
        root = ET.fromstring(exporter.export_tags([]).split("\n", 1)[1])
        assert len(root.findall("Tag")) == 0


# ---------------------------------------------------------------------------
# Alarm XML
# ---------------------------------------------------------------------------

class TestAlarmXml:
    def test_root_element_is_twinsoftalarms(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="DIG_001")])
        root = ET.fromstring(xml.split("\n", 1)[1])
        assert root.tag == "TWinSoftAlarms"

    def test_alarm_tag_name_attribute(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="LSL_001")])
        alarm = _parse_alarm_xml(xml)
        assert alarm.get("TagName") == "LSL_001"

    def test_condition_text(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="DIG_001", condition="NEG")])
        alarm = _parse_alarm_xml(xml)
        assert alarm.find("Condition").text == "NEG"

    def test_condition_value_and_hysteresis_empty(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="DIG_001")])
        cond = _parse_alarm_xml(xml).find("Condition")
        assert cond.get("Value") == ""
        assert cond.get("Hysteresis") == ""

    def test_message_text(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="DIG_001", message="Low level alarm")])
        assert _parse_alarm_xml(xml).find("Message").text == "Low level alarm"

    def test_filter_attributes(self, exporter):
        alarm = Alarm(tag_name="DIG_001", filter=FilterConfig(hours=0, minutes=1, seconds=30))
        xml = exporter.export_alarms([alarm])
        filt = _parse_alarm_xml(xml).find("Filter")
        assert filt.get("FilterHour") == "0"
        assert filt.get("FilterMinute") == "1"
        assert filt.get("FilterSecond") == "30"

    def test_options_attributes(self, exporter):
        alarm = Alarm(
            tag_name="DIG_001",
            options=AlarmOptions(
                notify_end_of_alarm=True,
                sms_acknowledge=False,
                handling="DISABLED"
            )
        )
        xml = exporter.export_alarms([alarm])
        opts = _parse_alarm_xml(xml).find("Options")
        assert opts.get("NotifyEndOfAlarm") == "True"
        assert opts.get("SMSAcknowledge") == "False"
        assert opts.get("Handling") == "DISABLED"

    def test_runtime_parameters_all_empty(self, exporter):
        xml = exporter.export_alarms([Alarm(tag_name="DIG_001")])
        rtp = _parse_alarm_xml(xml).find("RuntimeParameters")
        assert rtp.get("RTP_Handling") == ""
        assert rtp.get("RTP_Threshold") == ""
        assert rtp.get("RTP_Hysteresis") == ""


# ---------------------------------------------------------------------------
# Conditioning text output
# ---------------------------------------------------------------------------

class TestConditioningOutput:
    def test_empty_entries_returns_empty_string(self, exporter):
        assert exporter.export_conditioning([]) == ""

    def test_single_group_has_header(self, exporter):
        entries = [ConditioningEntry(rule="_DI", statement="LSL_001 = LSL_001_")]
        out = exporter.export_conditioning(entries)
        assert "(* --- _DI CONDITIONING --- *)" in out
        assert "LSL_001 = LSL_001_" in out

    def test_multiple_statements_same_group(self, exporter):
        entries = [
            ConditioningEntry(rule="_DI", statement="LSL_001 = LSL_001_"),
            ConditioningEntry(rule="_DI", statement="LAL_001 = NOT LAL_001_"),
        ]
        out = exporter.export_conditioning(entries)
        assert out.count("_DI CONDITIONING") == 1
        assert "LSL_001 = LSL_001_" in out
        assert "LAL_001 = NOT LAL_001_" in out

    def test_two_groups_separated_by_blank_line(self, exporter):
        entries = [
            ConditioningEntry(rule="_DI", statement="LSL_001 = LSL_001_"),
            ConditioningEntry(rule="_DO", statement="XY_001_ = XY_001"),
        ]
        out = exporter.export_conditioning(entries)
        assert "(* --- _DI CONDITIONING --- *)" in out
        assert "(* --- _DO CONDITIONING --- *)" in out
        assert "\n\n" in out

    def test_group_order_preserved(self, exporter):
        entries = [
            ConditioningEntry(rule="_DI", statement="A = A_"),
            ConditioningEntry(rule="_DO", statement="B_ = B"),
        ]
        out = exporter.export_conditioning(entries)
        assert out.index("_DI") < out.index("_DO")


# ---------------------------------------------------------------------------
# Function block text output
# ---------------------------------------------------------------------------

class TestFunctionBlockOutput:
    def test_empty_entries_returns_empty_string(self, exporter):
        assert exporter.export_function_blocks([]) == ""

    def test_single_group_has_header(self, exporter):
        entries = [FunctionBlockEntry(rule="_HOA", statement="Call FB_1(X_HOA, X_H, X_O, X_A)")]
        out = exporter.export_function_blocks(entries)
        assert "(* --- _HOA FUNCTION BLOCKS --- *)" in out
        assert "Call FB_1" in out

    def test_counter_increments_across_group(self, exporter):
        entries = [
            FunctionBlockEntry(rule="_HOA", statement="Call FB_1(XY_001_HOA, XY_001_H, XY_001_O, XY_001_A)"),
            FunctionBlockEntry(rule="_HOA", statement="Call FB_2(XY_010_HOA, XY_010_H, XY_010_O, XY_010_A)"),
        ]
        out = exporter.export_function_blocks(entries)
        assert "FB_1" in out
        assert "FB_2" in out
        assert out.count("_HOA FUNCTION BLOCKS") == 1
