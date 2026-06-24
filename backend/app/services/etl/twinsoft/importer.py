###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from app.models.address_map import AddressMap
from app.models.tag import DataType
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
