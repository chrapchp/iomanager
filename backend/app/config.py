###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jun23 - Add get_app_config FastAPI dependency; save_app_config accepts explicit path
###################################################

from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.config import AppConfig


class Settings(BaseSettings):
    config_dir: Path = Path("/app/config")
    data_dir: Path = Path("/app/data")

    model_config = SettingsConfigDict(env_prefix="IOMANAGER_", env_file=".env")

    @field_validator("config_dir", "data_dir", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_app_config(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AppConfig:
    """FastAPI dependency — returns current config, honouring injected settings."""
    path = settings.config_dir / "app.config.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at {path}. "
            "Ensure the config directory is mounted and app.config.json exists."
        )
    return AppConfig.model_validate_json(path.read_text(encoding="utf-8"))


def save_app_config(config: AppConfig, config_dir: Path) -> None:
    path = config_dir / "app.config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
