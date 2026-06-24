###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from app.api.schemas import ImportStatusResponse, IoIndexImportResponse, TwinsoftImportResponse
from app.config import Settings, get_settings
from app.services.etl.excel_reader import ExcelReader
from app.services.etl.twinsoft.importer import TwinsoftImporter
from app.services.session import SessionState

router = APIRouter(tags=["imports"])


def _get_session(request: Request) -> SessionState:
    return request.app.state.session


@router.post("/twinsoft", response_model=TwinsoftImportResponse)
async def import_twinsoft(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[SessionState, Depends(_get_session)],
) -> TwinsoftImportResponse:
    """Upload a Twinsoft export XML and build the occupied address map."""
    import_dir = settings.data_dir / "import"
    import_dir.mkdir(parents=True, exist_ok=True)
    dest = import_dir / "twinsoft_export.xml"

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        importer = TwinsoftImporter()
        address_map = importer.import_address_map(dest)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session.address_map = address_map
    session.twinsoft_loaded = True
    session.reset_generation()

    return TwinsoftImportResponse(
        coil_count=len(session.address_map.coil),
        register_count=len(session.address_map.register),
        message=(
            f"Twinsoft export loaded: "
            f"{len(address_map.coil)} coil address(es), "
            f"{len(address_map.register)} register address(es) occupied"
        ),
    )


@router.post("/io-index", response_model=IoIndexImportResponse)
async def import_io_index(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[SessionState, Depends(_get_session)],
) -> IoIndexImportResponse:
    """Upload an Excel file containing the IO Dist tab."""
    import_dir = settings.data_dir / "import"
    import_dir.mkdir(parents=True, exist_ok=True)
    dest = import_dir / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        reader = ExcelReader()
        rows = reader.read(dest)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session.io_rows = rows
    session.io_index_path = dest
    session.io_index_loaded = True
    session.reset_generation()

    return IoIndexImportResponse(
        row_count=len(rows),
        message=f"I/O index loaded: {len(rows)} row(s) parsed",
    )


@router.get("/status", response_model=ImportStatusResponse)
async def import_status(
    session: Annotated[SessionState, Depends(_get_session)],
) -> ImportStatusResponse:
    """Return what is currently loaded in the session."""
    return ImportStatusResponse(
        twinsoft_loaded=session.twinsoft_loaded,
        io_index_loaded=session.io_index_loaded,
        row_count=len(session.io_rows),
        coil_occupied=len(session.address_map.coil),
        register_occupied=len(session.address_map.register),
    )
