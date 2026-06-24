###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, field_validator


class DataType(str, Enum):
    BOOL = "BOOL"
    INT16 = "INT16"
    UINT16 = "UINT16"
    INT32 = "INT32"
    UINT32 = "UINT32"
    FLOAT = "FLOAT"
    BYTE = "BYTE"
    TEXT = "TEXT"

    @property
    def register_size(self) -> int:
        """Number of Modbus register units consumed."""
        if self in (DataType.FLOAT, DataType.INT32, DataType.UINT32):
            return 2
        return 1

    @property
    def is_digital(self) -> bool:
        return self == DataType.BOOL

    @property
    def requires_even_boundary(self) -> bool:
        return self in (DataType.FLOAT, DataType.INT32, DataType.UINT32)

    @property
    def is_signed(self) -> bool | None:
        if self in (DataType.FLOAT, DataType.INT16, DataType.INT32):
            return True
        if self in (DataType.UINT16, DataType.UINT32, DataType.BYTE):
            return False
        return None


class PresentationConfig(BaseModel):
    enabled: bool = False
    description: str = ""
    state_on: str = ""
    state_off: str = ""
    units: str = ""
    nbr_decimals: str = ""


class WriteAllowedConfig(BaseModel):
    enabled: bool = False
    minimum: str = ""
    maximum: str = ""


class Tag(BaseModel):
    name: str
    new_name: str | None = None
    data_type: DataType
    modbus_address: int
    text_tag_size: int | None = None
    comment: str = ""
    initial_value: str = ""
    minimum: str = ""
    maximum: str = ""
    resolution: str = ""
    group: str = ""
    presentation: PresentationConfig = PresentationConfig()
    write_allowed: WriteAllowedConfig = WriteAllowedConfig()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        import re
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]{0,14}$", v):
            raise ValueError(
                f"Tag name '{v}' must start with a letter, "
                "contain only alphanumeric characters and underscores, "
                "and be at most 15 characters"
            )
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError(f"Comment exceeds 50 character limit: '{v[:20]}...'")
        return v

    @property
    def effective_new_name(self) -> str:
        return self.new_name if self.new_name else self.name
