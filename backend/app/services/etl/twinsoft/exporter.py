###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
import xml.etree.ElementTree as ET

from app.models.alarm import Alarm
from app.models.output import ConditioningEntry, FunctionBlockEntry
from app.models.tag import DataType, Tag
from app.services.etl.twinsoft.parser import datatype_to_format, datatype_to_signed

_XML_DECLARATION = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
_INDENT = "  "


def _text(value: str | int | None) -> str | None:
    """Return str value or None (renders as self-closing element)."""
    if value is None:
        return None
    s = str(value)
    return s if s else None


class TwinsoftExporter:
    """Serialises internal models into Twinsoft-compatible import files."""

    # ------------------------------------------------------------------
    # Tags XML
    # ------------------------------------------------------------------

    def export_tags(self, tags: list[Tag]) -> str:
        root = ET.Element("TWinSoftTags")
        for tag in tags:
            root.append(self._build_tag_element(tag))
        ET.indent(root, space=_INDENT)
        return _XML_DECLARATION + ET.tostring(root, encoding="unicode")

    def _build_tag_element(self, tag: Tag) -> ET.Element:
        elem = ET.Element("Tag", Name=tag.name)

        def sub(name: str, text: str | int | None = None) -> ET.Element:
            el = ET.SubElement(elem, name)
            el.text = _text(text)
            return el

        sub("NewName", tag.effective_new_name)
        sub("Address")  # always blank — Twinsoft assigns on import
        sub("Format", datatype_to_format(tag.data_type))
        sub("ModbusAddress", tag.modbus_address)
        sub("Comment", tag.comment or None)
        sub("InitalValue", tag.initial_value or None)  # typo preserved — Twinsoft format
        sub("Signed", datatype_to_signed(tag.data_type))
        sub(
            "TextTagSize",
            tag.text_tag_size if tag.data_type == DataType.TEXT else None,
        )
        sub("Minimum", tag.minimum or None)
        sub("Maximum", tag.maximum or None)
        sub("Resolution", tag.resolution or None)
        sub("Group", tag.group or None)

        pres = ET.SubElement(elem, "Presentation")
        pres.set("Description", tag.presentation.description)
        pres.set("StateOn", tag.presentation.state_on)
        pres.set("StateOff", tag.presentation.state_off)
        pres.set("Units", tag.presentation.units)
        pres.set("NbrDecimals", tag.presentation.nbr_decimals)
        pres.text = "True" if tag.presentation.enabled else "False"

        wa = ET.SubElement(elem, "WriteAllowed")
        wa.set("WriteAllowed_Minimum", tag.write_allowed.minimum)
        wa.set("WriteAllowed_Maximum", tag.write_allowed.maximum)
        wa.text = "True" if tag.write_allowed.enabled else "False"

        sub("DisplayFormat", "DECIMAL")

        return elem

    # ------------------------------------------------------------------
    # Alarms XML
    # ------------------------------------------------------------------

    def export_alarms(self, alarms: list[Alarm]) -> str:
        root = ET.Element("TWinSoftAlarms")
        for alarm in alarms:
            root.append(self._build_alarm_element(alarm))
        ET.indent(root, space=_INDENT)
        return _XML_DECLARATION + ET.tostring(root, encoding="unicode")

    def _build_alarm_element(self, alarm: Alarm) -> ET.Element:
        elem = ET.Element("Alarm", TagName=alarm.tag_name)

        cond = ET.SubElement(elem, "Condition")
        cond.set("Value", "")
        cond.set("Hysteresis", "")
        cond.text = alarm.condition

        recip = ET.SubElement(elem, "Recipient")
        recip.set("CallAllRecipients", "True" if alarm.call_all_recipients else "")
        recip.text = alarm.recipient

        msg = ET.SubElement(elem, "Message")
        msg.set("IsReport", "True" if alarm.is_report else "False")
        msg.text = alarm.message or None

        filt = ET.SubElement(elem, "Filter")
        filt.set("FilterHour", str(alarm.filter.hours))
        filt.set("FilterMinute", str(alarm.filter.minutes))
        filt.set("FilterSecond", str(alarm.filter.seconds))

        opts = ET.SubElement(elem, "Options")
        opts.set("NotifyEndOfAlarm", "True" if alarm.options.notify_end_of_alarm else "False")
        opts.set("SMSAcknowledge", "True" if alarm.options.sms_acknowledge else "False")
        opts.set("POP3Acknowledge", "True" if alarm.options.pop3_acknowledge else "False")
        opts.set("Handling", alarm.options.handling)

        rtp = ET.SubElement(elem, "RuntimeParameters")
        rtp.set("RTP_Handling", "")
        rtp.set("RTP_Threshold", "")
        rtp.set("RTP_Hysteresis", "")

        return elem

    # ------------------------------------------------------------------
    # Conditioning code text
    # ------------------------------------------------------------------

    def export_conditioning(self, entries: list[ConditioningEntry]) -> str:
        if not entries:
            return ""
        groups: dict[str, list[str]] = {}
        for entry in entries:
            groups.setdefault(entry.rule, []).append(entry.statement)

        parts = []
        for rule_name, statements in groups.items():
            header = f"(* --- {rule_name} CONDITIONING --- *)"
            parts.append("\n".join([header] + statements))

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Function block instantiation text
    # ------------------------------------------------------------------

    def export_function_blocks(self, entries: list[FunctionBlockEntry]) -> str:
        if not entries:
            return ""
        groups: dict[str, list[str]] = {}
        for entry in entries:
            groups.setdefault(entry.rule, []).append(entry.statement)

        parts = []
        for rule_name, statements in groups.items():
            header = f"(* --- {rule_name} FUNCTION BLOCKS --- *)"
            parts.append("\n".join([header] + statements))

        return "\n\n".join(parts)
