###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.models.alarm import Alarm
from app.models.address_map import AddressMap
from app.models.output import ConditioningEntry, FunctionBlockEntry
from app.models.tag import Tag


@runtime_checkable
class TagImporter(Protocol):
    """Reads a target system export file and returns an occupied address map."""

    def import_address_map(self, file: Path) -> AddressMap: ...


@runtime_checkable
class TagExporter(Protocol):
    """Serialises internal models into target system import files."""

    def export_tags(self, tags: list[Tag]) -> str: ...

    def export_alarms(self, alarms: list[Alarm]) -> str: ...

    def export_conditioning(self, entries: list[ConditioningEntry]) -> str: ...

    def export_function_blocks(self, entries: list[FunctionBlockEntry]) -> str: ...
