###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul08 - Add skip field for Skip column support
###################################################

from __future__ import annotations
from pydantic import BaseModel


class IoIndexRow(BaseModel):
    number: int
    tag_name: str
    description: str = ""
    io_type: str = ""
    part_number: str = ""
    module: int | None = None
    module_channel: int | None = None
    connector: int | None = None
    connector_channel: int | None = None
    signal: str = ""
    phase: int | None = None
    note: str = ""
    template: str
    failsafe: bool = False
    has_presentation: bool = False
    presentation: str = ""
    units: str = ""
    input_max: str = ""
    input_min: str = ""
    skip: bool = False
    is_alarm: bool = False
    alarm_condition: str | None = None  # None → use config default
    alarm_message: str = ""

    @property
    def twinsoft_base_name(self) -> str:
        """ISA tag name with hyphens replaced by underscores."""
        return self.tag_name.replace("-", "_")
