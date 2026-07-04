###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add template CRUD endpoints
###################################################

from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError, field_validator

from app.config import Settings, get_app_config, get_settings, save_app_config
from app.models.config import AppConfig, TemplateMapping

router = APIRouter(tags=["config"])


class TemplateUpdate(BaseModel):
    rules: list[str]

    @field_validator("rules")
    @classmethod
    def rules_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("A template must reference at least one rule")
        return v


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
