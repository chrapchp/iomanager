###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from dataclasses import dataclass, field

from app.models.alarm import Alarm
from app.models.output import ConditioningEntry, FunctionBlockEntry
from app.models.tag import Tag


@dataclass
class RowError:
    row_number: int
    tag_name: str
    template: str
    message: str


@dataclass
class GenerationResult:
    tags: list[Tag] = field(default_factory=list)
    alarms: list[Alarm] = field(default_factory=list)
    conditioning: list[ConditioningEntry] = field(default_factory=list)
    function_blocks: list[FunctionBlockEntry] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)
