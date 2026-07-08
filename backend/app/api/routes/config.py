###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add template CRUD endpoints
#              2026Jul04 - Add rule CRUD endpoints (create, delete rule, delete entry)
#              2026Jul07 - Add virtual tag CRUD endpoints
#              2026Jul07 - Add rule and template rename endpoints (cascade)
###################################################

from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError, field_validator

from app.config import Settings, get_app_config, get_settings, save_app_config
from app.models.config import AppConfig, Rule, TemplateMapping, VirtualTagEntry

router = APIRouter(tags=["config"])


class TemplateUpdate(BaseModel):
    rules: list[str]

    @field_validator("rules")
    @classmethod
    def rules_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("A template must reference at least one rule")
        return v


class RenameRequest(BaseModel):
    new_name: str


def _rebuild_config_rules(config: AppConfig, new_rules: list[Rule]) -> AppConfig:
    """Return a validated AppConfig with replaced rules list, raising HTTPException on failure."""
    try:
        return AppConfig(
            target_system=config.target_system,
            rules=new_rules,
            templates=config.templates,
            alarm_defaults=config.alarm_defaults,
        )
    except ValidationError as exc:
        detail = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=422, detail=detail) from exc


def _rebuild_config(config: AppConfig, new_templates: list[TemplateMapping]) -> AppConfig:
    """Return a validated AppConfig with the given templates, raising HTTPException on failure."""
    try:
        return AppConfig(
            target_system=config.target_system,
            rules=config.rules,
            templates=new_templates,
            alarm_defaults=config.alarm_defaults,
        )
    except ValidationError as exc:
        # Extract message strings only — exc.errors() input field may contain non-serializable objects
        detail = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=422, detail=detail) from exc


def _rebuild_full(
    config: AppConfig,
    *,
    rules: list[Rule] | None = None,
    templates: list[TemplateMapping] | None = None,
    virtual_tags: list[VirtualTagEntry] | None = None,
) -> AppConfig:
    """Rebuild AppConfig replacing only the supplied fields; raise HTTPException on validation failure."""
    try:
        return AppConfig(
            target_system=config.target_system,
            rules=rules if rules is not None else config.rules,
            templates=templates if templates is not None else config.templates,
            virtual_tags=virtual_tags if virtual_tags is not None else config.virtual_tags,
            alarm_defaults=config.alarm_defaults,
        )
    except ValidationError as exc:
        detail = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=422, detail=detail) from exc


def _persist(config: AppConfig, settings: Settings) -> None:
    try:
        save_app_config(config, settings.config_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/config", response_model=AppConfig)
async def get_config(
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> AppConfig:
    return config


@router.put("/config", response_model=AppConfig)
async def update_config(
    body: AppConfig,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AppConfig:
    _persist(body, settings)
    return body


# ── Template CRUD ────────────────────────────────────────────────────────────

@router.get("/config/templates", response_model=list[TemplateMapping])
async def list_templates(
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> list[TemplateMapping]:
    return config.templates


@router.post("/config/templates", response_model=TemplateMapping, status_code=201)
async def create_template(
    body: TemplateMapping,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TemplateMapping:
    if any(t.template == body.template for t in config.templates):
        raise HTTPException(status_code=409, detail=f"Template '{body.template}' already exists")
    updated = _rebuild_config(config, [*config.templates, body])
    _persist(updated, settings)
    return body


@router.get("/config/templates/{template_name}", response_model=TemplateMapping)
async def get_template(
    template_name: str,
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> TemplateMapping:
    mapping = next((t for t in config.templates if t.template == template_name), None)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    return mapping


@router.post("/config/templates/{template_name}/rename", response_model=TemplateMapping)
async def rename_template(
    template_name: str,
    body: RenameRequest,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TemplateMapping:
    tmpl = next((t for t in config.templates if t.template == template_name), None)
    if tmpl is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    if template_name != body.new_name and any(t.template == body.new_name for t in config.templates):
        raise HTTPException(status_code=409, detail=f"Template '{body.new_name}' already exists")
    renamed = TemplateMapping(template=body.new_name, rules=tmpl.rules)
    new_templates = [renamed if t.template == template_name else t for t in config.templates]
    new_vt = [
        VirtualTagEntry(**{**vt.model_dump(), "template": body.new_name})
        if vt.template == template_name else vt
        for vt in config.virtual_tags
    ]
    updated = _rebuild_full(config, templates=new_templates, virtual_tags=new_vt)
    _persist(updated, settings)
    return renamed


@router.put("/config/templates/{template_name}", response_model=TemplateMapping)
async def update_template(
    template_name: str,
    body: TemplateUpdate,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TemplateMapping:
    if not any(t.template == template_name for t in config.templates):
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    updated_mapping = TemplateMapping(template=template_name, rules=body.rules)
    new_templates = [
        updated_mapping if t.template == template_name else t
        for t in config.templates
    ]
    updated = _rebuild_config(config, new_templates)
    _persist(updated, settings)
    return updated_mapping


@router.delete("/config/templates/{template_name}", status_code=204)
async def delete_template(
    template_name: str,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not any(t.template == template_name for t in config.templates):
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    new_templates = [t for t in config.templates if t.template != template_name]
    updated = AppConfig(
        target_system=config.target_system,
        rules=config.rules,
        templates=new_templates,
        alarm_defaults=config.alarm_defaults,
    )
    _persist(updated, settings)


# ── Rule CRUD ─────────────────────────────────────────────────────────────────

@router.post("/config/rules", response_model=Rule, status_code=201)
async def create_rule(
    body: Rule,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Rule:
    if any(r.name == body.name for r in config.rules):
        raise HTTPException(status_code=409, detail=f"Rule '{body.name}' already exists")
    updated = _rebuild_config_rules(config, [*config.rules, body])
    _persist(updated, settings)
    return body


@router.delete("/config/rules/{rule_name}", status_code=204)
async def delete_rule(
    rule_name: str,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not any(r.name == rule_name for r in config.rules):
        raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
    referencing = [t.template for t in config.templates if rule_name in t.rules]
    if referencing:
        names = ", ".join(referencing)
        raise HTTPException(
            status_code=409,
            detail=f"Rule '{rule_name}' is referenced by template(s): {names}",
        )
    new_rules = [r for r in config.rules if r.name != rule_name]
    updated = _rebuild_config_rules(config, new_rules)
    _persist(updated, settings)


@router.delete("/config/rules/{rule_name}/entries/{role}", status_code=204)
async def delete_rule_entry(
    rule_name: str,
    role: str,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    rule = next((r for r in config.rules if r.name == rule_name), None)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
    if not any(e.role == role for e in rule.entries):
        raise HTTPException(status_code=404, detail=f"Entry '{role}' not found in rule '{rule_name}'")
    if len(rule.entries) == 1:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot delete the last entry in rule '{rule_name}'",
        )
    new_entries = [e for e in rule.entries if e.role != role]
    new_rule = Rule(
        name=rule.name,
        entries=new_entries,
        condition_code=rule.condition_code,
        function_block=rule.function_block,
    )
    new_rules = [new_rule if r.name == rule_name else r for r in config.rules]
    updated = _rebuild_config_rules(config, new_rules)
    _persist(updated, settings)


@router.post("/config/rules/{rule_name}/rename", response_model=Rule)
async def rename_rule(
    rule_name: str,
    body: RenameRequest,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Rule:
    rule = next((r for r in config.rules if r.name == rule_name), None)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
    if rule_name != body.new_name and any(r.name == body.new_name for r in config.rules):
        raise HTTPException(status_code=409, detail=f"Rule '{body.new_name}' already exists")
    renamed = Rule(
        name=body.new_name,
        entries=rule.entries,
        condition_code=rule.condition_code,
        function_block=rule.function_block,
    )
    new_rules = [renamed if r.name == rule_name else r for r in config.rules]
    new_templates = [
        TemplateMapping(
            template=t.template,
            rules=[body.new_name if r == rule_name else r for r in t.rules],
        )
        for t in config.templates
    ]
    updated = _rebuild_full(config, rules=new_rules, templates=new_templates)
    _persist(updated, settings)
    return renamed


# ── Virtual Tag CRUD ──────────────────────────────────────────────────────────

def _rebuild_config_virtual_tags(config: AppConfig, new_vt: list[VirtualTagEntry]) -> AppConfig:
    try:
        return AppConfig(
            target_system=config.target_system,
            rules=config.rules,
            templates=config.templates,
            virtual_tags=new_vt,
            alarm_defaults=config.alarm_defaults,
        )
    except ValidationError as exc:
        detail = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=422, detail=detail) from exc


@router.get("/config/virtual-tags", response_model=list[VirtualTagEntry])
async def list_virtual_tags(
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> list[VirtualTagEntry]:
    return config.virtual_tags


@router.post("/config/virtual-tags", response_model=VirtualTagEntry, status_code=201)
async def create_virtual_tag(
    body: VirtualTagEntry,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> VirtualTagEntry:
    updated = _rebuild_config_virtual_tags(config, [*config.virtual_tags, body])
    _persist(updated, settings)
    return body


@router.put("/config/virtual-tags/{vt_id}", response_model=VirtualTagEntry)
async def update_virtual_tag(
    vt_id: str,
    body: VirtualTagEntry,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> VirtualTagEntry:
    if not any(vt.id == vt_id for vt in config.virtual_tags):
        raise HTTPException(status_code=404, detail=f"Virtual tag '{vt_id}' not found")
    saved = VirtualTagEntry(**{**body.model_dump(), "id": vt_id})
    new_vt = [saved if vt.id == vt_id else vt for vt in config.virtual_tags]
    updated = _rebuild_config_virtual_tags(config, new_vt)
    _persist(updated, settings)
    return saved


@router.delete("/config/virtual-tags/{vt_id}", status_code=204)
async def delete_virtual_tag(
    vt_id: str,
    config: Annotated[AppConfig, Depends(get_app_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not any(vt.id == vt_id for vt in config.virtual_tags):
        raise HTTPException(status_code=404, detail=f"Virtual tag '{vt_id}' not found")
    new_vt = [vt for vt in config.virtual_tags if vt.id != vt_id]
    updated = _rebuild_config_virtual_tags(config, new_vt)
    _persist(updated, settings)
