###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jun24 - Add download endpoint for updated IO index Excel
#              2026Jul08 - Allow generate with no IO index if virtual tags exist
###################################################

from __future__ import annotations
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.schemas import GenerateResponse
from app.config import Settings, get_app_config, get_settings
from app.models.config import AppConfig
from app.services.etl.excel_reader import ExcelReader, build_log_messages
from app.services.etl.pipeline import run_pipeline
from app.services.session import SessionState

router = APIRouter(tags=["exports"])


def _get_session(request: Request) -> SessionState:
    return request.app.state.session


def _export_dir(settings: Settings) -> Path:
    return settings.data_dir / "export"


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    settings: Annotated[Settings, Depends(get_settings)],
    config: Annotated[AppConfig, Depends(get_app_config)],
    session: Annotated[SessionState, Depends(_get_session)],
) -> GenerateResponse:
    """Run the rule engine against the loaded I/O index and address map."""
    has_enabled_virtual_tags = any(vt.enabled for vt in config.virtual_tags)
    if not session.io_index_loaded and not has_enabled_virtual_tags:
        raise HTTPException(
            status_code=400,
            detail="No I/O index loaded and no enabled virtual tags configured. "
                   "Upload an I/O index via /api/imports/io-index or add virtual tags.",
        )

    result = run_pipeline(
        config=config,
        io_rows=session.io_rows,
        address_map=session.address_map,
        export_dir=_export_dir(settings),
        imported_tags=session.imported_tags,
    )

    session.generation_result = result

    if session.io_index_path and session.io_index_path.exists():
        try:
            logs, error_rows = build_log_messages(result, session.io_rows)
            ExcelReader().write_log(session.io_index_path, logs, error_rows)
        except Exception:
            pass  # write-back failure is non-fatal

    return GenerateResponse(
        tag_count=len(result.tags),
        alarm_count=len(result.alarms),
        conditioning_count=len(result.conditioning),
        function_block_count=len(result.function_blocks),
        error_count=len(result.errors),
        errors=[
            {
                "row_number": e.row_number,
                "tag_name": e.tag_name,
                "template": e.template,
                "message": e.message,
            }
            for e in result.errors
        ],
    )


def _download(settings: Settings, filename: str) -> FileResponse:
    path = _export_dir(settings) / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{filename} not found. Run /api/exports/generate first.",
        )
    return FileResponse(path, filename=filename)


@router.get("/download/io-index")
async def download_io_index(
    session: Annotated[SessionState, Depends(_get_session)],
) -> FileResponse:
    """Download the IO index Excel file with Log column written back."""
    if not session.io_index_path or not session.io_index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No IO index file available. Upload one via /api/imports/io-index.",
        )
    return FileResponse(
        session.io_index_path,
        filename=session.io_index_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/download/tags.xml")
async def download_tags(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    return _download(settings, "tags.xml")


@router.get("/download/alarms.xml")
async def download_alarms(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    return _download(settings, "alarms.xml")


@router.get("/download/conditioning.txt")
async def download_conditioning(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    return _download(settings, "conditioning.txt")


@router.get("/download/function_blocks.txt")
async def download_function_blocks(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    return _download(settings, "function_blocks.txt")
