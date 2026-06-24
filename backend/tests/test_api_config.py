###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import pytest
from fastapi.testclient import TestClient


class TestGetConfig:
    def test_get_config_returns_200(self, client: TestClient):
        assert client.get("/api/config").status_code == 200

    def test_config_has_rules(self, client: TestClient):
        config = client.get("/api/config").json()
        assert "rules" in config
        assert len(config["rules"]) > 0

    def test_config_has_templates(self, client: TestClient):
        config = client.get("/api/config").json()
        assert "templates" in config
        assert len(config["templates"]) > 0

    def test_config_has_target_system(self, client: TestClient):
        config = client.get("/api/config").json()
        assert config["target_system"] == "twinsoft"

    def test_config_has_alarm_defaults(self, client: TestClient):
        config = client.get("/api/config").json()
        assert "alarm_defaults" in config


class TestUpdateConfig:
    def test_put_config_returns_200(self, client: TestClient):
        current = client.get("/api/config").json()
        resp = client.put("/api/config", json=current)
        assert resp.status_code == 200

    def test_put_config_persists(self, client: TestClient):
        current = client.get("/api/config").json()
        current["target_system"] = "twinsoft"  # safe no-op
        client.put("/api/config", json=current)
        reloaded = client.get("/api/config").json()
        assert reloaded["target_system"] == "twinsoft"

    def test_put_invalid_config_returns_422(self, client: TestClient):
        resp = client.put("/api/config", json={"target_system": "bad", "rules": "not-a-list"})
        assert resp.status_code == 422

    def test_put_config_with_bad_template_ref_returns_422(self, client: TestClient):
        current = client.get("/api/config").json()
        # Add a template that references a non-existent rule
        current["templates"].append({"template": "BAD", "rules": ["_DOESNOTEXIST"]})
        resp = client.put("/api/config", json=current)
        assert resp.status_code == 422


class TestTagsAndAlarms:
    def _generate(self, client: TestClient) -> None:
        from tests.conftest import make_excel_bytes
        excel = make_excel_bytes([
            {"Tag Name": "LSL-001", "Template": "DI", "Description": "Low level"},
            {"Tag Name": "LAL-001", "Template": "DI", "isAlm": 1, "AlmMsg": "Low alarm"},
        ])
        client.post(
            "/api/imports/io-index",
            files={"file": ("io.xlsx", excel,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        client.post("/api/exports/generate")

    def test_get_tags_before_generate_returns_404(self, client: TestClient):
        assert client.get("/api/tags").status_code == 404

    def test_get_tags_after_generate_returns_200(self, client: TestClient):
        self._generate(client)
        assert client.get("/api/tags").status_code == 200

    def test_get_tags_returns_list(self, client: TestClient):
        self._generate(client)
        tags = client.get("/api/tags").json()
        assert isinstance(tags, list)
        assert len(tags) == 4  # 2 DI rows × 2 tags each

    def test_tag_has_expected_fields(self, client: TestClient):
        self._generate(client)
        tag = client.get("/api/tags").json()[0]
        assert "name" in tag
        assert "data_type" in tag
        assert "modbus_address" in tag

    def test_get_alarms_before_generate_returns_404(self, client: TestClient):
        assert client.get("/api/alarms").status_code == 404

    def test_get_alarms_after_generate_returns_200(self, client: TestClient):
        self._generate(client)
        assert client.get("/api/alarms").status_code == 200

    def test_get_alarms_returns_list(self, client: TestClient):
        self._generate(client)
        alarms = client.get("/api/alarms").json()
        assert isinstance(alarms, list)
        assert len(alarms) == 1  # only LAL-001 has isAlm=1
