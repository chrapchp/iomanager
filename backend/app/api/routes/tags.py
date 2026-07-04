###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul04 - Add GET /tags/imported endpoint
###################################################

from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.tag import Tag
from app.services.session import SessionState

router = APIRouter(tags=["tags"])


def _get_session(request: Request) -> SessionState:
    return request.app.state.session


@router.get("/tags", response_model=list[Tag])
async def list_tags(
    session: Annotated[SessionState, Depends(_get_session)],
) -> list[Tag]:
    """Return all tags generated in the last run."""
    if session.generation_result is None:
        raise HTTPException(
            status_code=404,
            detail="No generation result available. Run /api/exports/generate first.",
        )
    return session.generation_result.tags


@router.get("/tags/imported", response_model=list[Tag])
async def list_imported_tags(
    session: Annotated[SessionState, Depends(_get_session)],
) -> list[Tag]:
    """Return tags parsed from the last Twinsoft export import."""
    return session.imported_tags
