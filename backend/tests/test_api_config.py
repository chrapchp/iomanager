###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add TestTemplateCRUD test class
#              2026Jul04 - Add TestRuleCRUD test class
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


class TestTemplateCRUD:
    # ── List ────────────────────────────────────────────────────────────────

    def test_list_templates_returns_200(self, client: TestClient):
        assert client.get("/api/config/templates").status_code == 200

    def test_list_templates_returns_all(self, client: TestClient):
        templates = client.get("/api/config/templates").json()
        assert isinstance(templates, list)
        assert len(templates) == 6  # default config has 6 templates

    def test_list_templates_shape(self, client: TestClient):
        templates = client.get("/api/config/templates").json()
        assert all("template" in t and "rules" in t for t in templates)

    # ── Get single ──────────────────────────────────────────────────────────

    def test_get_template_returns_200(self, client: TestClient):
        assert client.get("/api/config/templates/DI").status_code == 200

    def test_get_template_returns_correct_rules(self, client: TestClient):
        t = client.get("/api/config/templates/DI").json()
        assert t["template"] == "DI"
        assert "_DI" in t["rules"]

    def test_get_nonexistent_template_returns_404(self, client: TestClient):
        assert client.get("/api/config/templates/NOTFOUND").status_code == 404

    # ── Create ──────────────────────────────────────────────────────────────

    def test_create_template_returns_201(self, client: TestClient):
        resp = client.post("/api/config/templates", json={"template": "TEST", "rules": ["_DI"]})
        assert resp.status_code == 201

    def test_create_template_returns_body(self, client: TestClient):
        resp = client.post("/api/config/templates", json={"template": "TEST", "rules": ["_DI"]})
        body = resp.json()
        assert body["template"] == "TEST"
        assert body["rules"] == ["_DI"]

    def test_create_template_persists(self, client: TestClient):
        client.post("/api/config/templates", json={"template": "TEST", "rules": ["_DI"]})
        templates = client.get("/api/config/templates").json()
        names = [t["template"] for t in templates]
        assert "TEST" in names

    def test_create_duplicate_template_returns_409(self, client: TestClient):
        client.post("/api/config/templates", json={"template": "TEST", "rules": ["_DI"]})
        resp = client.post("/api/config/templates", json={"template": "TEST", "rules": ["_DI"]})
        assert resp.status_code == 409

    def test_create_template_with_bad_rule_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/config/templates",
            json={"template": "TEST", "rules": ["_DOESNOTEXIST"]},
        )
        assert resp.status_code == 422

    def test_create_template_with_empty_rules_returns_422(self, client: TestClient):
        resp = client.post("/api/config/templates", json={"template": "TEST", "rules": []})
        assert resp.status_code == 422

    # ── Update ──────────────────────────────────────────────────────────────

    def test_update_template_returns_200(self, client: TestClient):
        resp = client.put("/api/config/templates/DI", json={"rules": ["_DI", "_AI"]})
        assert resp.status_code == 200

    def test_update_template_returns_updated_body(self, client: TestClient):
        resp = client.put("/api/config/templates/DI", json={"rules": ["_DI", "_AI"]})
        body = resp.json()
        assert body["template"] == "DI"
        assert "_DI" in body["rules"]
        assert "_AI" in body["rules"]

    def test_update_template_persists(self, client: TestClient):
        client.put("/api/config/templates/DI", json={"rules": ["_DI", "_AI"]})
        t = client.get("/api/config/templates/DI").json()
        assert "_AI" in t["rules"]

    def test_update_nonexistent_template_returns_404(self, client: TestClient):
        resp = client.put("/api/config/templates/NOTFOUND", json={"rules": ["_DI"]})
        assert resp.status_code == 404

    def test_update_template_with_bad_rule_returns_422(self, client: TestClient):
        resp = client.put("/api/config/templates/DI", json={"rules": ["_DOESNOTEXIST"]})
        assert resp.status_code == 422

    def test_update_template_with_empty_rules_returns_422(self, client: TestClient):
        resp = client.put("/api/config/templates/DI", json={"rules": []})
        assert resp.status_code == 422

    # ── Delete ──────────────────────────────────────────────────────────────

    def test_delete_template_returns_204(self, client: TestClient):
        assert client.delete("/api/config/templates/DI").status_code == 204

    def test_delete_template_removes_it(self, client: TestClient):
        client.delete("/api/config/templates/DI")
        assert client.get("/api/config/templates/DI").status_code == 404

    def test_delete_template_reduces_count(self, client: TestClient):
        before = len(client.get("/api/config/templates").json())
        client.delete("/api/config/templates/DI")
        after = len(client.get("/api/config/templates").json())
        assert after == before - 1

    def test_delete_nonexistent_template_returns_404(self, client: TestClient):
        assert client.delete("/api/config/templates/NOTFOUND").status_code == 404


class TestRuleCRUD:
    # ── Helpers ─────────────────────────────────────────────────────────────

    _NEW_RULE = {
        "name": "_TC",
        "entries": [
            {"role": "io", "addr": 5000, "tag_suffix": "_", "data_class": "BOOL",
             "desc_delimiter": "", "desc_suffix": "", "folder": "IO\\TC",
             "write_allowed": False, "write_allowed_min": "", "write_allowed_max": ""}
        ],
        "condition_code": "soft = io",
        "function_block": None,
    }

    # ── Create ──────────────────────────────────────────────────────────────

    def test_create_rule_returns_201(self, client: TestClient):
        resp = client.post("/api/config/rules", json=self._NEW_RULE)
        assert resp.status_code == 201

    def test_create_rule_returns_body(self, client: TestClient):
        resp = client.post("/api/config/rules", json=self._NEW_RULE)
        body = resp.json()
        assert body["name"] == "_TC"
        assert len(body["entries"]) == 1
        assert body["entries"][0]["role"] == "io"

    def test_create_rule_persists(self, client: TestClient):
        client.post("/api/config/rules", json=self._NEW_RULE)
        config = client.get("/api/config").json()
        names = [r["name"] for r in config["rules"]]
        assert "_TC" in names

    def test_create_duplicate_rule_returns_409(self, client: TestClient):
        client.post("/api/config/rules", json=self._NEW_RULE)
        resp = client.post("/api/config/rules", json=self._NEW_RULE)
        assert resp.status_code == 409

    def test_create_rule_with_empty_entries_returns_422(self, client: TestClient):
        bad = {**self._NEW_RULE, "entries": []}
        resp = client.post("/api/config/rules", json=bad)
        assert resp.status_code == 422

    def test_create_rule_increases_count(self, client: TestClient):
        before = len(client.get("/api/config").json()["rules"])
        client.post("/api/config/rules", json=self._NEW_RULE)
        after = len(client.get("/api/config").json()["rules"])
        assert after == before + 1

    # ── Delete rule ──────────────────────────────────────────────────────────

    def test_delete_unreferenced_rule_returns_204(self, client: TestClient):
        # _LVL is not referenced by any template in the fixture config
        assert client.delete("/api/config/rules/_LVL").status_code == 204

    def test_delete_rule_removes_it(self, client: TestClient):
        client.delete("/api/config/rules/_LVL")
        config = client.get("/api/config").json()
        names = [r["name"] for r in config["rules"]]
        assert "_LVL" not in names

    def test_delete_rule_reduces_count(self, client: TestClient):
        before = len(client.get("/api/config").json()["rules"])
        client.delete("/api/config/rules/_LVL")
        after = len(client.get("/api/config").json()["rules"])
        assert after == before - 1

    def test_delete_nonexistent_rule_returns_404(self, client: TestClient):
        assert client.delete("/api/config/rules/_NOTFOUND").status_code == 404

    def test_delete_rule_referenced_by_template_returns_409(self, client: TestClient):
        # _DI is referenced by the DI template
        resp = client.delete("/api/config/rules/_DI")
        assert resp.status_code == 409

    def test_delete_rule_referenced_by_template_error_names_template(self, client: TestClient):
        resp = client.delete("/api/config/rules/_DI")
        assert "DI" in resp.json()["detail"]

    def test_delete_rule_referenced_by_template_does_not_remove_rule(self, client: TestClient):
        client.delete("/api/config/rules/_DI")
        config = client.get("/api/config").json()
        names = [r["name"] for r in config["rules"]]
        assert "_DI" in names

    # ── Delete entry ─────────────────────────────────────────────────────────

    def test_delete_entry_returns_204(self, client: TestClient):
        # _DI has 2 entries: io and soft — delete one
        assert client.delete("/api/config/rules/_DI/entries/soft").status_code == 204

    def test_delete_entry_removes_it(self, client: TestClient):
        client.delete("/api/config/rules/_DI/entries/soft")
        config = client.get("/api/config").json()
        di_rule = next(r for r in config["rules"] if r["name"] == "_DI")
        roles = [e["role"] for e in di_rule["entries"]]
        assert "soft" not in roles

    def test_delete_entry_leaves_other_entries(self, client: TestClient):
        client.delete("/api/config/rules/_DI/entries/soft")
        config = client.get("/api/config").json()
        di_rule = next(r for r in config["rules"] if r["name"] == "_DI")
        roles = [e["role"] for e in di_rule["entries"]]
        assert "io" in roles

    def test_delete_last_entry_returns_422(self, client: TestClient):
        # Remove all but one entry, then try to remove the last one
        client.delete("/api/config/rules/_DI/entries/soft")
        resp = client.delete("/api/config/rules/_DI/entries/io")
        assert resp.status_code == 422

    def test_delete_entry_from_nonexistent_rule_returns_404(self, client: TestClient):
        assert client.delete("/api/config/rules/_NOTFOUND/entries/io").status_code == 404

    def test_delete_nonexistent_entry_returns_404(self, client: TestClient):
        assert client.delete("/api/config/rules/_DI/entries/NOTFOUND").status_code == 404
