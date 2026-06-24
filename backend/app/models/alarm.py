###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, field_validator


class FilterConfig(BaseModel):
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


class AlarmOptions(BaseModel):
    notify_end_of_alarm: bool = True
    sms_acknowledge: bool = False
    pop3_acknowledge: bool = False
    handling: Literal["ENABLED", "DISABLED"] = "ENABLED"


class Alarm(BaseModel):
    tag_name: str
    condition: Literal["POS", "NEG"] = "POS"
    recipient: str = "Default"
    call_all_recipients: bool = False
    message: str = ""
    is_report: bool = False
    filter: FilterConfig = FilterConfig()
    options: AlarmOptions = AlarmOptions()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if len(v) > 120:
            raise ValueError(f"Alarm message exceeds 120 character limit")
        return v
