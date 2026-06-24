###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import math
import pytest
from app.models.tag import DataType
from app.services.etl.twinsoft.importer import TwinsoftImporter

SIMPLE_TAGS_XML = """\
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="dig1">
    <Format>DIGITAL</Format>
    <ModbusAddress>0</ModbusAddress>
    <Signed />
    <TextTagSize />
  </Tag>
  <Tag Name="float1">
    <Format>FLOAT</Format>
    <ModbusAddress>0</ModbusAddress>
    <Signed>True</Signed>
    <TextTagSize />
  </Tag>
  <Tag Name="init16">
    <Format>16BITS</Format>
    <ModbusAddress>2</ModbusAddress>
    <Signed>True</Signed>
    <TextTagSize />
  </Tag>
  <Tag Name="unit16">
    <Format>16BITS</Format>
    <ModbusAddress>3</ModbusAddress>
    <Signed>False</Signed>
    <TextTagSize />
  </Tag>
  <Tag Name="test_txt">
    <Format>TEXT</Format>
    <ModbusAddress>10</ModbusAddress>
    <Signed />
    <TextTagSize>246</TextTagSize>
  </Tag>
</TWinSoftTags>"""

TAGS_WITH_BLANK_ADDRESS_XML = """\
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="new_tag">
    <Format>DIGITAL</Format>
    <ModbusAddress></ModbusAddress>
    <Signed />
    <TextTagSize />
  </Tag>
</TWinSoftTags>"""

TAGS_WITH_UNKNOWN_FORMAT_XML = """\
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="weird">
    <Format>PROPRIETARY</Format>
    <ModbusAddress>99</ModbusAddress>
    <Signed />
    <TextTagSize />
  </Tag>
</TWinSoftTags>"""


@pytest.fixture
def importer():
    return TwinsoftImporter()


class TestImportAddressMap:
    def test_digital_tag_goes_to_coil_space(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        # dig1 is DIGITAL at address 0 → coil space
        assert 0 in am.coil
        # float1 is also at address 0 but in register space — independent pools
        assert 0 in am.register

    def test_float_tag_goes_to_register_space(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        assert 0 in am.register
        assert 1 in am.register

    def test_float_occupies_two_registers(self, importer):
        # Use XML with a FLOAT tag only to verify exactly 2 registers are marked
        xml = """\
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="ft"><Format>FLOAT</Format><ModbusAddress>4</ModbusAddress><Signed>True</Signed><TextTagSize /></Tag>
</TWinSoftTags>"""
        am = importer.import_address_map_from_string(xml)
        assert 4 in am.register
        assert 5 in am.register
        assert 3 not in am.register
        assert 6 not in am.register

    def test_int16_occupies_one_register(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        assert 2 in am.register

    def test_uint16_occupies_one_register(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        assert 3 in am.register

    def test_text_occupies_ceil_texttagsize_div_2_registers(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        size = math.ceil(246 / 2)
        for i in range(size):
            assert (10 + i) in am.register
        assert (10 + size) not in am.register

    def test_digital_and_register_same_address_no_conflict(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        assert 0 in am.coil
        assert 0 in am.register

    def test_blank_modbus_address_skipped(self, importer):
        am = importer.import_address_map_from_string(TAGS_WITH_BLANK_ADDRESS_XML)
        assert not am.coil
        assert not am.register

    def test_unknown_format_skipped_gracefully(self, importer):
        am = importer.import_address_map_from_string(TAGS_WITH_UNKNOWN_FORMAT_XML)
        assert 99 not in am.coil
        assert 99 not in am.register

    def test_allocation_after_import_skips_occupied(self, importer):
        am = importer.import_address_map_from_string(SIMPLE_TAGS_XML)
        # FLOAT at 0 and 1 are occupied; next free even address is 2, but 2 and 3 taken
        # next even is 4
        addr = am.allocate(DataType.FLOAT, 0)
        assert addr == 4
