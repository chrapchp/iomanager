###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add TestTemplateCRUD test class
#              2026Jul04 - Add TestRuleCRUD test class
#              2026Jul07 - Add TestVirtualTagCRUD and TestVirtualTagExpansion test classes
#              2026Jul07 - Add TestRuleRename and TestTemplateRename test classes
#              2026Jul08 - Add TestRuleDescription and TestTemplateDescription test classes
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


class TestVirtualTagCRUD:
    _NEW_VT = {
        "tag_name_from": "PY-001",
        "tag_name_to": "PY-010",
        "description": "Outlet Pump - #N",
        "template": "DI",
        "is_alarm": False,
        "alarm_condition": None,
        "alarm_message": "",
    }

    # ── List ────────────────────────────────────────────────────────────────

    def test_list_virtual_tags_returns_200(self, client: TestClient):
        assert client.get("/api/config/virtual-tags").status_code == 200

    def test_list_virtual_tags_empty_by_default(self, client: TestClient):
        vts = client.get("/api/config/virtual-tags").json()
        assert isinstance(vts, list)
        assert len(vts) == 0

    # ── Create ──────────────────────────────────────────────────────────────

    def test_create_virtual_tag_returns_201(self, client: TestClient):
        assert client.post("/api/config/virtual-tags", json=self._NEW_VT).status_code == 201

    def test_create_virtual_tag_returns_body(self, client: TestClient):
        body = client.post("/api/config/virtual-tags", json=self._NEW_VT).json()
        assert body["tag_name_from"] == "PY-001"
        assert body["tag_name_to"] == "PY-010"
        assert body["template"] == "DI"

    def test_create_virtual_tag_assigns_id(self, client: TestClient):
        body = client.post("/api/config/virtual-tags", json=self._NEW_VT).json()
        assert "id" in body
        assert len(body["id"]) == 8

    def test_create_virtual_tag_persists(self, client: TestClient):
        client.post("/api/config/virtual-tags", json=self._NEW_VT)
        vts = client.get("/api/config/virtual-tags").json()
        assert any(vt["tag_name_from"] == "PY-001" for vt in vts)

    def test_create_virtual_tag_with_unknown_template_returns_422(self, client: TestClient):
        bad = {**self._NEW_VT, "template": "BADTEMPLATE"}
        assert client.post("/api/config/virtual-tags", json=bad).status_code == 422

    def test_create_single_virtual_tag_no_range(self, client: TestClient):
        single = {**self._NEW_VT, "tag_name_from": "LSL-099", "tag_name_to": None}
        resp = client.post("/api/config/virtual-tags", json=single)
        assert resp.status_code == 201
        assert resp.json()["tag_name_to"] is None

    # ── Update ──────────────────────────────────────────────────────────────

    def _create_and_get_id(self, client: TestClient) -> str:
        return client.post("/api/config/virtual-tags", json=self._NEW_VT).json()["id"]

    def test_update_virtual_tag_returns_200(self, client: TestClient):
        vt_id = self._create_and_get_id(client)
        updated = {**self._NEW_VT, "description": "Updated desc"}
        assert client.put(f"/api/config/virtual-tags/{vt_id}", json=updated).status_code == 200

    def test_update_virtual_tag_persists(self, client: TestClient):
        vt_id = self._create_and_get_id(client)
        updated = {**self._NEW_VT, "description": "Updated desc"}
        client.put(f"/api/config/virtual-tags/{vt_id}", json=updated)
        vts = client.get("/api/config/virtual-tags").json()
        match = next(vt for vt in vts if vt["id"] == vt_id)
        assert match["description"] == "Updated desc"

    def test_update_preserves_id(self, client: TestClient):
        vt_id = self._create_and_get_id(client)
        updated = {**self._NEW_VT, "id": "different", "description": "X"}
        body = client.put(f"/api/config/virtual-tags/{vt_id}", json=updated).json()
        assert body["id"] == vt_id

    def test_update_nonexistent_virtual_tag_returns_404(self, client: TestClient):
        assert client.put("/api/config/virtual-tags/notfound", json=self._NEW_VT).status_code == 404

    # ── Delete ──────────────────────────────────────────────────────────────

    def test_delete_virtual_tag_returns_204(self, client: TestClient):
        vt_id = self._create_and_get_id(client)
        assert client.delete(f"/api/config/virtual-tags/{vt_id}").status_code == 204

    def test_delete_virtual_tag_removes_it(self, client: TestClient):
        vt_id = self._create_and_get_id(client)
        client.delete(f"/api/config/virtual-tags/{vt_id}")
        vts = client.get("/api/config/virtual-tags").json()
        assert not any(vt["id"] == vt_id for vt in vts)

    def test_delete_nonexistent_virtual_tag_returns_404(self, client: TestClient):
        assert client.delete("/api/config/virtual-tags/notfound").status_code == 404


class TestVirtualTagExpansion:
    from app.services.etl.virtual_tags import expand_virtual_tags
    from app.models.config import VirtualTagEntry

    def _entry(self, **kwargs):
        from app.models.config import VirtualTagEntry
        return VirtualTagEntry(template="DI", **kwargs)

    def test_single_tag_produces_one_row(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([self._entry(tag_name_from="LSL-001")])
        assert len(rows) == 1
        assert rows[0].tag_name == "LSL-001"

    def test_range_produces_correct_count(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([self._entry(tag_name_from="PY-001", tag_name_to="PY-010")])
        assert len(rows) == 10

    def test_range_tag_names_are_correct(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([self._entry(tag_name_from="PY-001", tag_name_to="PY-003")])
        assert [r.tag_name for r in rows] == ["PY-001", "PY-002", "PY-003"]

    def test_range_preserves_zero_padding(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([self._entry(tag_name_from="PY-001", tag_name_to="PY-010")])
        assert rows[0].tag_name == "PY-001"
        assert rows[9].tag_name == "PY-010"

    def test_description_token_replaced(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-001", tag_name_to="PY-003", description="Pump #N")
        ])
        assert [r.description for r in rows] == ["Pump 1", "Pump 2", "Pump 3"]

    def test_single_tag_description_token_uses_suffix(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-005", description="Pump #N")
        ])
        assert rows[0].description == "Pump 5"

    def test_row_numbers_start_at_10000(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([self._entry(tag_name_from="PY-001", tag_name_to="PY-003")])
        assert rows[0].number == 10000
        assert rows[2].number == 10002

    def test_template_propagated(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-001", tag_name_to="PY-002")
        ])
        assert all(r.template == "DI" for r in rows)

    def test_alarm_fields_propagated(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(
                tag_name_from="PY-001",
                is_alarm=True,
                alarm_message="Pump fault",
                alarm_condition="POS",
            )
        ])
        assert rows[0].is_alarm is True
        assert rows[0].alarm_message == "Pump fault"
        assert rows[0].alarm_condition == "POS"

    def test_multiple_entries_row_numbers_are_sequential(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-001", tag_name_to="PY-002"),
            self._entry(tag_name_from="LSL-001"),
        ])
        assert len(rows) == 3
        assert rows[2].number == 10002

class TestRuleRename:
    def test_rename_rule_returns_200(self, client: TestClient):
        resp = client.post("/api/config/rules/_LVL/rename", json={"new_name": "_LEVEL"})
        assert resp.status_code == 200

    def test_rename_rule_returns_new_name(self, client: TestClient):
        resp = client.post("/api/config/rules/_LVL/rename", json={"new_name": "_LEVEL"})
        assert resp.json()["name"] == "_LEVEL"

    def test_rename_rule_persists_in_rules_list(self, client: TestClient):
        client.post("/api/config/rules/_LVL/rename", json={"new_name": "_LEVEL"})
        names = [r["name"] for r in client.get("/api/config").json()["rules"]]
        assert "_LEVEL" in names
        assert "_LVL" not in names

    def test_rename_rule_cascades_to_template_references(self, client: TestClient):
        # _DI is referenced by the DI template in the fixture
        client.post("/api/config/rules/_DI/rename", json={"new_name": "_DIMOD"})
        config = client.get("/api/config").json()
        di_tmpl = next(t for t in config["templates"] if t["template"] == "DI")
        assert "_DIMOD" in di_tmpl["rules"]
        assert "_DI" not in di_tmpl["rules"]

    def test_rename_rule_does_not_affect_other_rules(self, client: TestClient):
        before = {r["name"] for r in client.get("/api/config").json()["rules"]}
        client.post("/api/config/rules/_LVL/rename", json={"new_name": "_LEVEL"})
        after = {r["name"] for r in client.get("/api/config").json()["rules"]}
        # All original rules except _LVL should still be present
        assert (before - {"_LVL"}).issubset(after)

    def test_rename_rule_to_same_name_returns_200(self, client: TestClient):
        resp = client.post("/api/config/rules/_LVL/rename", json={"new_name": "_LVL"})
        assert resp.status_code == 200

    def test_rename_rule_404_for_unknown(self, client: TestClient):
        assert client.post("/api/config/rules/_NOTFOUND/rename", json={"new_name": "_X"}).status_code == 404

    def test_rename_rule_409_for_duplicate(self, client: TestClient):
        # _LVL → _DI conflicts because _DI already exists
        resp = client.post("/api/config/rules/_LVL/rename", json={"new_name": "_DI"})
        assert resp.status_code == 409


class TestTemplateRename:
    def test_rename_template_returns_200(self, client: TestClient):
        resp = client.post("/api/config/templates/DI/rename", json={"new_name": "DI_V2"})
        assert resp.status_code == 200

    def test_rename_template_returns_new_name(self, client: TestClient):
        resp = client.post("/api/config/templates/DI/rename", json={"new_name": "DI_V2"})
        assert resp.json()["template"] == "DI_V2"

    def test_rename_template_persists_in_templates_list(self, client: TestClient):
        client.post("/api/config/templates/DI/rename", json={"new_name": "DI_V2"})
        names = [t["template"] for t in client.get("/api/config").json()["templates"]]
        assert "DI_V2" in names
        assert "DI" not in names

    def test_rename_template_preserves_rules(self, client: TestClient):
        client.post("/api/config/templates/DI/rename", json={"new_name": "DI_V2"})
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "DI_V2")
        assert "_DI" in tmpl["rules"]

    def test_rename_template_cascades_to_virtual_tags(self, client: TestClient):
        vt = client.post("/api/config/virtual-tags", json={
            "tag_name_from": "PY_001", "description": "test", "template": "DI",
            "enabled": True, "is_alarm": False, "alarm_message": "",
        }).json()
        client.post("/api/config/templates/DI/rename", json={"new_name": "DI_V2"})
        config = client.get("/api/config").json()
        updated_vt = next(v for v in config["virtual_tags"] if v["id"] == vt["id"])
        assert updated_vt["template"] == "DI_V2"

    def test_rename_template_to_same_name_returns_200(self, client: TestClient):
        resp = client.post("/api/config/templates/DI/rename", json={"new_name": "DI"})
        assert resp.status_code == 200

    def test_rename_template_404_for_unknown(self, client: TestClient):
        assert client.post("/api/config/templates/NOTFOUND/rename", json={"new_name": "X"}).status_code == 404

    def test_rename_template_409_for_duplicate(self, client: TestClient):
        # DI → DO conflicts because DO already exists
        resp = client.post("/api/config/templates/DI/rename", json={"new_name": "DO"})
        assert resp.status_code == 409


class TestRuleDescription:
    def test_create_rule_with_description_persists(self, client: TestClient):
        client.post("/api/config/rules", json={
            "name": "_TC", "description": "Thermocouple input",
            "entries": [{"role": "io", "addr": 1000, "data_class": "BOOL"}],
        })
        rule = next(r for r in client.get("/api/config").json()["rules"] if r["name"] == "_TC")
        assert rule["description"] == "Thermocouple input"

    def test_description_defaults_to_empty_string(self, client: TestClient):
        client.post("/api/config/rules", json={
            "name": "_TC",
            "entries": [{"role": "io", "addr": 1000, "data_class": "BOOL"}],
        })
        rule = next(r for r in client.get("/api/config").json()["rules"] if r["name"] == "_TC")
        assert rule["description"] == ""

    def test_description_max_30_chars_accepted(self, client: TestClient):
        resp = client.post("/api/config/rules", json={
            "name": "_TC", "description": "A" * 30,
            "entries": [{"role": "io", "addr": 1000, "data_class": "BOOL"}],
        })
        assert resp.status_code == 201

    def test_description_over_30_chars_rejected(self, client: TestClient):
        resp = client.post("/api/config/rules", json={
            "name": "_TC", "description": "A" * 31,
            "entries": [{"role": "io", "addr": 1000, "data_class": "BOOL"}],
        })
        assert resp.status_code == 422

    def test_description_preserved_through_rename(self, client: TestClient):
        client.post("/api/config/rules", json={
            "name": "_TC", "description": "Thermocouple",
            "entries": [{"role": "io", "addr": 1000, "data_class": "BOOL"}],
        })
        client.post("/api/config/rules/_TC/rename", json={"new_name": "_TC2"})
        rule = next(r for r in client.get("/api/config").json()["rules"] if r["name"] == "_TC2")
        assert rule["description"] == "Thermocouple"

    def test_description_preserved_through_entry_delete(self, client: TestClient):
        client.post("/api/config/rules", json={
            "name": "_TC", "description": "Thermocouple",
            "entries": [
                {"role": "io", "addr": 1000, "data_class": "BOOL"},
                {"role": "soft", "addr": 2000, "data_class": "BOOL"},
            ],
        })
        client.delete("/api/config/rules/_TC/entries/soft")
        rule = next(r for r in client.get("/api/config").json()["rules"] if r["name"] == "_TC")
        assert rule["description"] == "Thermocouple"


class TestTemplateDescription:
    def test_create_template_with_description_persists(self, client: TestClient):
        client.post("/api/config/templates", json={
            "template": "TC", "description": "Thermocouple channel", "rules": ["_DI"],
        })
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "TC")
        assert tmpl["description"] == "Thermocouple channel"

    def test_description_defaults_to_empty_string(self, client: TestClient):
        client.post("/api/config/templates", json={"template": "TC", "rules": ["_DI"]})
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "TC")
        assert tmpl["description"] == ""

    def test_description_max_30_chars_accepted(self, client: TestClient):
        resp = client.post("/api/config/templates", json={
            "template": "TC", "description": "A" * 30, "rules": ["_DI"],
        })
        assert resp.status_code == 201

    def test_description_over_30_chars_rejected(self, client: TestClient):
        resp = client.post("/api/config/templates", json={
            "template": "TC", "description": "A" * 31, "rules": ["_DI"],
        })
        assert resp.status_code == 422

    def test_description_preserved_through_rename(self, client: TestClient):
        client.post("/api/config/templates", json={
            "template": "TC", "description": "Thermocouple", "rules": ["_DI"],
        })
        client.post("/api/config/templates/TC/rename", json={"new_name": "TC2"})
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "TC2")
        assert tmpl["description"] == "Thermocouple"

    def test_update_template_sets_description(self, client: TestClient):
        client.put("/api/config/templates/DI", json={"description": "Digital input", "rules": ["_DI"]})
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "DI")
        assert tmpl["description"] == "Digital input"

    def test_description_preserved_in_rename_rule_cascade(self, client: TestClient):
        # When a rule is renamed, template descriptions must survive the cascade
        client.put("/api/config/templates/DI", json={"description": "DI mapping", "rules": ["_DI"]})
        client.post("/api/config/rules/_DI/rename", json={"new_name": "_DIMOD"})
        tmpl = next(t for t in client.get("/api/config").json()["templates"] if t["template"] == "DI")
        assert tmpl["description"] == "DI mapping"


class TestVirtualTagExpansionEnabled:
    from app.models.config import VirtualTagEntry

    def _entry(self, **kwargs):
        from app.models.config import VirtualTagEntry
        defaults = dict(tag_name_from="PY-001", description="", template="DI", enabled=True, is_alarm=False, alarm_message="")
        return VirtualTagEntry(**{**defaults, **kwargs})

    def test_disabled_entry_is_skipped(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-001", tag_name_to="PY-003", enabled=False),
            self._entry(tag_name_from="LSL-001"),
        ])
        assert len(rows) == 1
        assert rows[0].tag_name == "LSL-001"

    def test_enabled_entry_is_included(self):
        from app.services.etl.virtual_tags import expand_virtual_tags
        rows = expand_virtual_tags([
            self._entry(tag_name_from="PY-001", tag_name_to="PY-002", enabled=True),
        ])
        assert len(rows) == 2
