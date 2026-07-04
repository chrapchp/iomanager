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
from app.services.etl.pipeline import run_pipeline

_CONFIG_JSON = Path(__file__).parent / "fixtures" / "app.config.json"


@pytest.fixture
def config():
    return AppConfig.model_validate_json(_CONFIG_JSON.read_text(encoding="utf-8"))


def _di_row(number: int, tag_name: str) -> IoIndexRow:
    return IoIndexRow(number=number, tag_name=tag_name, description="Level", template="DI")


class TestRunPipeline:
    def test_creates_export_dir(self, config, tmp_path):
        export_dir = tmp_path / "export"
        run_pipeline(config, [], AddressMap(), export_dir)
        assert export_dir.exists()

    def test_writes_tags_xml(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        assert (tmp_path / "export" / "tags.xml").exists()

    def test_writes_alarms_xml(self, config, tmp_path):
        run_pipeline(config, [], AddressMap(), tmp_path / "export")
        assert (tmp_path / "export" / "alarms.xml").exists()

    def test_writes_conditioning_txt(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        assert (tmp_path / "export" / "conditioning.txt").exists()

    def test_writes_function_blocks_txt(self, config, tmp_path):
        run_pipeline(config, [], AddressMap(), tmp_path / "export")
        assert (tmp_path / "export" / "function_blocks.txt").exists()

    def test_returns_generation_result(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        result = run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        assert len(result.tags) == 2  # DI → 2 tags

    def test_tags_xml_has_xml_declaration(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        content = (tmp_path / "export" / "tags.xml").read_text()
        assert content.startswith("<?xml")

    def test_conditioning_file_has_rule_header(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        content = (tmp_path / "export" / "conditioning.txt").read_text()
        assert "(* --- _DI CONDITIONING --- *)" in content

    def test_conditioning_statement_correct(self, config, tmp_path):
        rows = [_di_row(1, "LSL-001")]
        run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        content = (tmp_path / "export" / "conditioning.txt").read_text()
        assert "LSL_001 = LSL_001_" in content

    def test_pre_occupied_addresses_skipped(self, config, tmp_path):
        am = AddressMap()
        # manually occupy DI io pool range (1000–1005) in coil space
        am.coil.update(range(1000, 1006))
        rows = [_di_row(1, "LSL-001")]
        result = run_pipeline(config, rows, am, tmp_path / "export")
        io_tag = next(t for t in result.tags if t.name == "LSL_001_")
        assert io_tag.modbus_address not in range(1000, 1006)

    def test_empty_rows_produces_empty_files(self, config, tmp_path):
        result = run_pipeline(config, [], AddressMap(), tmp_path / "export")
        assert result.tags == []
        assert result.alarms == []

    def test_error_rows_reported_not_raised(self, config, tmp_path):
        rows = [
            IoIndexRow(number=1, tag_name="XX-001", template="BADTEMPLATE"),
            _di_row(2, "LSL-001"),
        ]
        result = run_pipeline(config, rows, AddressMap(), tmp_path / "export")
        assert len(result.errors) == 1
        assert len(result.tags) > 0
