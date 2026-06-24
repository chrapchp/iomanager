###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import io
import pytest
from fastapi.testclient import TestClient
from tests.conftest import TWINSOFT_XML_SAMPLE, make_excel_bytes


class TestTwinsoftImport:
    def test_upload_valid_xml_returns_200(self, client: TestClient):
        resp = client.post(
            "/api/imports/twinsoft",
            files={"file": ("export.xml", TWINSOFT_XML_SAMPLE.encode(), "text/xml")},
        )
        assert resp.status_code == 200

    def test_response_contains_coil_count(self, client: TestClient):
        resp = client.post(
            "/api/imports/twinsoft",
            files={"file": ("export.xml", TWINSOFT_XML_SAMPLE.encode(), "text/xml")},
        )
        assert "coil_count" in resp.json()
        assert resp.json()["coil_count"] == 1  # dig1

    def test_response_contains_register_count(self, client: TestClient):
        resp = client.post(
            "/api/imports/twinsoft",
            files={"file": ("export.xml", TWINSOFT_XML_SAMPLE.encode(), "text/xml")},
        )
        assert resp.json()["register_count"] == 2  # ai1 is FLOAT → 2 registers

    def test_status_updates_after_upload(self, client: TestClient):
        client.post(
            "/api/imports/twinsoft",
            files={"file": ("export.xml", TWINSOFT_XML_SAMPLE.encode(), "text/xml")},
        )
        status = client.get("/api/imports/status").json()
        assert status["twinsoft_loaded"] is True
        assert status["coil_occupied"] == 1
        assert status["register_occupied"] == 2


class TestIoIndexImport:
    def _upload(self, client: TestClient, rows: list[dict]) -> dict:
        excel = make_excel_bytes(rows)
        resp = client.post(
            "/api/imports/io-index",
            files={"file": ("io_index.xlsx", excel,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        return resp

    def test_upload_valid_excel_returns_200(self, client: TestClient):
        resp = self._upload(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        assert resp.status_code == 200

    def test_response_contains_row_count(self, client: TestClient):
        rows = [
            {"Tag Name": "LSL-001", "Template": "DI"},
            {"Tag Name": "LAL-001", "Template": "DI"},
        ]
        resp = self._upload(client, rows)
        assert resp.json()["row_count"] == 2

    def test_status_updates_after_upload(self, client: TestClient):
        self._upload(client, [{"Tag Name": "LSL-001", "Template": "DI"}])
        status = client.get("/api/imports/status").json()
        assert status["io_index_loaded"] is True
        assert status["row_count"] == 1

    def test_skips_rows_without_template(self, client: TestClient):
        rows = [
            {"Tag Name": "LSL-001", "Template": "DI"},
            {"Tag Name": "LAL-001", "Template": None},
        ]
        resp = self._upload(client, rows)
        assert resp.json()["row_count"] == 1


class TestImportStatus:
    def test_initial_status_nothing_loaded(self, client: TestClient):
        status = client.get("/api/imports/status").json()
        assert status["twinsoft_loaded"] is False
        assert status["io_index_loaded"] is False
        assert status["row_count"] == 0

    def test_status_200(self, client: TestClient):
        assert client.get("/api/imports/status").status_code == 200
