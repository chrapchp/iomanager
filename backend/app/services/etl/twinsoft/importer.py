###################################################
# Project:     IOManager
# Author:      Peter C
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add import_tags / _parse_tag to expose full tag data from XML
###################################################

from __future__ import annotations
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from app.models.address_map import AddressMap
from app.models.tag import DataType, Tag
from app.services.etl.twinsoft.parser import format_to_datatype


class TwinsoftImporter:
    """Parses a Twinsoft tag export XML and returns an occupied AddressMap."""

    def import_address_map(self, file: Path) -> AddressMap:
        tree = ET.parse(file)
        root = tree.getroot()
        am = AddressMap()
        for tag_elem in root.findall("Tag"):
            self._mark_tag(tag_elem, am)
        return am

    def import_address_map_from_string(self, xml_string: str) -> AddressMap:
        root = ET.fromstring(xml_string)
        am = AddressMap()
        for tag_elem in root.findall("Tag"):
            self._mark_tag(tag_elem, am)
        return am

    def import_tags(self, file: Path) -> list[Tag]:
        """Return Tag objects parsed from a Twinsoft export XML."""
        tree = ET.parse(file)
        root = tree.getroot()
        result = []
        for tag_elem in root.findall("Tag"):
            tag = self._parse_tag(tag_elem)
            if tag is not None:
                result.append(tag)
        return result

    def import_tags_from_string(self, xml_string: str) -> list[Tag]:
        root = ET.fromstring(xml_string)
        result = []
        for tag_elem in root.findall("Tag"):
            tag = self._parse_tag(tag_elem)
            if tag is not None:
                result.append(tag)
        return result

    def _parse_tag(self, elem: ET.Element) -> Tag | None:
        name = (elem.get("Name") or "").strip()
        modbus_text = elem.findtext("ModbusAddress", "").strip()
        if not name or not modbus_text:
            return None
        format_str = elem.findtext("Format", "").strip()
        signed_str = (elem.findtext("Signed") or "").strip() or None
        try:
            data_type = format_to_datatype(format_str, signed_str)
            modbus_address = int(modbus_text)
        except (ValueError, KeyError):
            return None
        comment = (elem.findtext("Comment") or "").strip()[:50]
        group = (elem.findtext("Group") or "").strip()
        try:
            return Tag(
                name=name,
                data_type=data_type,
                modbus_address=modbus_address,
                comment=comment,
                group=group,
            )
        except Exception:
            return None

    def _mark_tag(self, elem: ET.Element, am: AddressMap) -> None:
        modbus_text = elem.findtext("ModbusAddress", "").strip()
        if not modbus_text:
            return

        format_str = elem.findtext("Format", "").strip()
        signed_str = elem.findtext("Signed", "").strip() or None
        text_size_str = elem.findtext("TextTagSize", "").strip()

        try:
            data_type = format_to_datatype(format_str, signed_str)
            modbus_address = int(modbus_text)
        except (ValueError, KeyError):
            return

        size_override: int | None = None
        if data_type == DataType.TEXT and text_size_str:
            try:
                size_override = math.ceil(int(text_size_str) / 2)
            except ValueError:
                pass

        am.mark_occupied(data_type, modbus_address, size_override)
