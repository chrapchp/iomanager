###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from app.models.address_map import AddressMap
from app.models.generation import GenerationResult
from app.models.io_row import IoIndexRow


@dataclass
class SessionState:
    """In-memory state for the current working session."""
    address_map: AddressMap = field(default_factory=AddressMap)
    io_rows: list[IoIndexRow] = field(default_factory=list)
    generation_result: GenerationResult | None = None
    io_index_path: Path | None = None   # for Excel write-back
    twinsoft_loaded: bool = False
    io_index_loaded: bool = False

    def reset_generation(self) -> None:
        self.generation_result = None
