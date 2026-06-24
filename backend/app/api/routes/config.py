###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_app_config, get_settings, save_app_config
from app.models.config import AppConfig

router = APIRouter(tags=["config"])


@router.get("/config", response_model=AppConfig)
async def get_config(
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> AppConfig:
    """Return the current application configuration."""
    return config


@router.put("/config", response_model=AppConfig)
async def update_config(
    body: AppConfig,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AppConfig:
    """Persist a full configuration replacement."""
    try:
        save_app_config(body, settings.config_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return body
