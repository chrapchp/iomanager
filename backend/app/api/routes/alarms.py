###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.alarm import Alarm
from app.services.session import SessionState

router = APIRouter(tags=["alarms"])


def _get_session(request: Request) -> SessionState:
    return request.app.state.session


@router.get("/alarms", response_model=list[Alarm])
async def list_alarms(
    session: Annotated[SessionState, Depends(_get_session)],
) -> list[Alarm]:
    """Return all alarms generated in the last run."""
    if session.generation_result is None:
        raise HTTPException(
            status_code=404,
            detail="No generation result available. Run /api/exports/generate first.",
        )
    return session.generation_result.alarms
