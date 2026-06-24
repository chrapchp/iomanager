###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from pydantic import BaseModel


class ConditioningEntry(BaseModel):
    rule: str
    statement: str


class FunctionBlockEntry(BaseModel):
    rule: str
    statement: str
