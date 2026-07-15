###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul08 - Add tests for Skip column and virtual-tags-only generation
#              2026Jul15 - Add tests for duplicate tag name detection against PLC import
###################################################

import pytest
from fastapi.testclient import TestClient
from tests.conftest import TWINSOFT_XML_SAMPLE, make_excel_bytes


def _upload_io_index(client: TestClient, rows: list[dict]) -> None:
    excel = make_excel_bytes(rows)
    client.post(
        "/api/imports/io-index",
        files={"file": ("io_index.xlsx", excel,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )


def _upload_twinsoft(client: TestClient) -> None:
    client.post(
        "/api/imports/twinsoft",
        files={"file": ("export.xml", TWINSOFT_XML_SAMPLE.encode(), "text/xml")},
    )


def _setup_and_generate(client: TestClient, rows: list[dict]) -> dict:
    _upload_io_index(client, rows)
    resp = client.post("/api/exports/generate")
    return resp


class TestGenerate:
    def test_generate_without_io_index_returns_400(self, client: TestClient):
        resp = client.post("/api/exports/generate")
        assert resp.status_code == 400

    def test_generate_returns_200_after_upload(self, client: TestClient):
        resp = _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        assert resp.status_code == 200

    def test_generate_returns_tag_count(self, client: TestClient):
        resp = _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        assert resp.json()["tag_count"] == 2  # DI → io + soft

    def test_generate_returns_conditioning_count(self, client: TestClient):
        resp = _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        assert resp.json()["conditioning_count"] == 1

    def test_generate_returns_zero_errors_for_valid_row(self, client: TestClient):
        resp = _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        assert resp.json()["error_count"] == 0

    def test_generate_reports_errors_for_bad_template(self, client: TestClient):
        resp = _setup_and_generate(client, [{"Tag Name": "XX-001", "Template": "BADTEMPLATE"}])
        assert resp.json()["error_count"] == 1

    def test_generate_with_alarm_row(self, client: TestClient):
        rows = [{"Tag Name": "LSL-001", "Template": "DI", "isAlm": 1, "AlmMsg": "Low level"}]
        resp = _setup_and_generate(client, rows)
        assert resp.json()["alarm_count"] == 1

    def test_twinsoft_addresses_are_excluded_from_allocation(self, client: TestClient):
        _upload_twinsoft(client)
        _upload_io_index(client, [{"Tag Name": "DIG-001", "Template": "DI"}])
        result = client.post("/api/exports/generate").json()
        # DIG-001 io tag should not get address 1000 (occupied by dig1 in sample XML)
        assert result["tag_count"] > 0


class TestDownloads:
    def test_download_tags_xml_before_generate_returns_404(self, client: TestClient):
        assert client.get("/api/exports/download/tags.xml").status_code == 404

    def test_download_tags_xml_after_generate_returns_200(self, client: TestClient):
        _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        resp = client.get("/api/exports/download/tags.xml")
        assert resp.status_code == 200

    def test_tags_xml_content_type_is_xml(self, client: TestClient):
        _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        resp = client.get("/api/exports/download/tags.xml")
        assert "xml" in resp.headers["content-type"].lower()

    def test_download_alarms_xml_after_generate(self, client: TestClient):
        _setup_and_generate(client, [])
        assert client.get("/api/exports/download/alarms.xml").status_code == 200

    def test_download_conditioning_txt_after_generate(self, client: TestClient):
        _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        resp = client.get("/api/exports/download/conditioning.txt")
        assert resp.status_code == 200

    def test_conditioning_content_has_header(self, client: TestClient):
        _setup_and_generate(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        content = client.get("/api/exports/download/conditioning.txt").text
        assert "_DI CONDITIONING" in content

    def test_download_function_blocks_txt_after_generate(self, client: TestClient):
        rows = [{"Tag Name": "XY-001", "Template": "DO"}]
        _setup_and_generate(client, rows)
        assert client.get("/api/exports/download/function_blocks.txt").status_code == 200


class TestSkipColumn:
    def test_skipped_row_excluded_from_generation(self, client: TestClient):
        excel = make_excel_bytes([
            {"Tag Name": "LSL-001", "Template": "DI", "Skip": 1},
            {"Tag Name": "LAL-001", "Template": "DI"},
        ])
        client.post(
            "/api/imports/io-index",
            files={"file": ("io_index.xlsx", excel,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        result = client.post("/api/exports/generate").json()
        # Only LAL-001 processed; DI rule → 2 tags (io + soft)
        assert result["tag_count"] == 2

    def test_skip_0_row_included_in_generation(self, client: TestClient):
        excel = make_excel_bytes([
            {"Tag Name": "LSL-001", "Template": "DI", "Skip": 0},
        ])
        client.post(
            "/api/imports/io-index",
            files={"file": ("io_index.xlsx", excel,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        result = client.post("/api/exports/generate").json()
        assert result["tag_count"] == 2


class TestVirtualTagsOnlyGeneration:
    def test_generate_without_io_index_but_with_virtual_tag_returns_200(self, client: TestClient):
        client.post("/api/config/virtual-tags", json={
            "tag_name_from": "LSL_001",
            "tag_name_to": None,
            "description": "Virtual level switch",
            "template": "DI",
            "enabled": True,
            "is_alarm": False,
            "alarm_condition": None,
            "alarm_message": "",
        })
        resp = client.post("/api/exports/generate")
        assert resp.status_code == 200

    def test_generate_virtual_tags_only_produces_tags(self, client: TestClient):
        client.post("/api/config/virtual-tags", json={
            "tag_name_from": "LSL_001",
            "tag_name_to": None,
            "description": "",
            "template": "DI",
            "enabled": True,
            "is_alarm": False,
            "alarm_condition": None,
            "alarm_message": "",
        })
        result = client.post("/api/exports/generate").json()
        assert result["tag_count"] > 0

    def test_generate_without_io_index_and_all_disabled_virtual_tags_returns_400(
        self, client: TestClient
    ):
        client.post("/api/config/virtual-tags", json={
            "tag_name_from": "LSL_001",
            "tag_name_to": None,
            "description": "",
            "template": "DI",
            "enabled": False,
            "is_alarm": False,
            "alarm_condition": None,
            "alarm_message": "",
        })
        resp = client.post("/api/exports/generate")
        assert resp.status_code == 400


class TestDuplicateTagDetection:
    """Tag names already in the PLC (from Twinsoft import) must produce errors."""

    def test_duplicate_tag_name_is_reported_as_error(self, client: TestClient):
        # TWINSOFT_XML_SAMPLE contains 'dig1'; DI rule soft entry generates 'dig1' (no suffix)
        _upload_twinsoft(client)
        _upload_io_index(client, [{"Tag Name": "dig1", "Template": "DI"}])
        result = client.post("/api/exports/generate").json()
        assert result["error_count"] == 1

    def test_duplicate_error_message_names_the_tag(self, client: TestClient):
        _upload_twinsoft(client)
        _upload_io_index(client, [{"Tag Name": "dig1", "Template": "DI"}])
        result = client.post("/api/exports/generate").json()
        assert "dig1" in result["errors"][0]["message"]

    def test_duplicate_tag_not_in_generated_output(self, client: TestClient):
        _upload_twinsoft(client)
        _upload_io_index(client, [{"Tag Name": "dig1", "Template": "DI"}])
        result = client.post("/api/exports/generate").json()
        # The entire row failed — no tags from it should appear in output
        assert result["tag_count"] == 0

    def test_non_duplicate_row_unaffected_when_another_row_duplicates(self, client: TestClient):
        _upload_twinsoft(client)
        _upload_io_index(client, [
            {"Tag Name": "dig1", "Template": "DI"},   # duplicate
            {"Tag Name": "LSL-001", "Template": "DI"},  # fine
        ])
        result = client.post("/api/exports/generate").json()
        assert result["error_count"] == 1
        assert result["tag_count"] == 2  # LSL-001 → DI io + soft

    def test_no_duplicate_without_twinsoft_import(self, client: TestClient):
        # Without a Twinsoft import, no existing names → no duplicate errors
        _upload_io_index(client, [{"Tag Name": "dig1", "Template": "DI"}])
        result = client.post("/api/exports/generate").json()
        assert result["error_count"] == 0
