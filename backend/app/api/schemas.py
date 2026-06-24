###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from pydantic import BaseModel


class TwinsoftImportResponse(BaseModel):
    coil_count: int
    register_count: int
    message: str


class IoIndexImportResponse(BaseModel):
    row_count: int
    message: str


class ImportStatusResponse(BaseModel):
    twinsoft_loaded: bool
    io_index_loaded: bool
    row_count: int
    coil_occupied: int
    register_occupied: int


class GenerateResponse(BaseModel):
    tag_count: int
    alarm_count: int
    conditioning_count: int
    function_block_count: int
    error_count: int
    errors: list[dict]


class ErrorDetail(BaseModel):
    row_number: int
    tag_name: str
    template: str
    message: str
