###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, model_validator

from app.models.alarm import AlarmOptions, FilterConfig
from app.models.tag import DataType


class RuleEntry(BaseModel):
    role: str
    addr: int
    tag_suffix: str = ""
    data_class: DataType
    desc_delimiter: str = ""
    desc_suffix: str = ""
    folder: str = ""


class Rule(BaseModel):
    name: str
    entries: list[RuleEntry]
    condition_code: str | None = None
    function_block: str | None = None

    def entry_by_role(self, role: str) -> RuleEntry | None:
        return next((e for e in self.entries if e.role == role), None)


class TemplateMapping(BaseModel):
    template: str
    rules: list[str]


class AlarmDefaults(BaseModel):
    condition: Literal["POS", "NEG"] = "POS"
    recipient: str = "Default"
    call_all_recipients: bool = False
    is_report: bool = False
    filter: FilterConfig = FilterConfig()
    options: AlarmOptions = AlarmOptions()


class AppConfig(BaseModel):
    target_system: str = "twinsoft"
    rules: list[Rule]
    templates: list[TemplateMapping]
    alarm_defaults: AlarmDefaults = AlarmDefaults()

    @model_validator(mode="after")
    def validate_template_rule_references(self) -> AppConfig:
        rule_names = {r.name for r in self.rules}
        for mapping in self.templates:
            for rule_name in mapping.rules:
                if rule_name not in rule_names:
                    raise ValueError(
                        f"Template '{mapping.template}' references unknown rule '{rule_name}'"
                    )
        return self

    def rule_by_name(self, name: str) -> Rule | None:
        return next((r for r in self.rules if r.name == name), None)

    def rules_for_template(self, template: str) -> list[Rule]:
        mapping = next((t for t in self.templates if t.template == template), None)
        if not mapping:
            return []
        return [r for name in mapping.rules if (r := self.rule_by_name(name))]
