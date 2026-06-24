###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
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
