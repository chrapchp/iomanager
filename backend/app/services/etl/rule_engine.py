###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul15 - Detect duplicate tag names against existing PLC tags
###################################################

from __future__ import annotations
from pydantic import ValidationError

from app.models.address_map import AddressMap
from app.models.alarm import Alarm
from app.models.config import AppConfig, Rule, RuleEntry
from app.models.generation import GenerationResult, RowError
from app.models.io_row import IoIndexRow
from app.models.output import ConditioningEntry, FunctionBlockEntry
from app.models.tag import DataType, PresentationConfig, Tag, WriteAllowedConfig


class _RowProcessingError(Exception):
    pass


class RuleEngine:
    def __init__(
        self,
        config: AppConfig,
        address_map: AddressMap,
        existing_tag_names: frozenset[str] = frozenset(),
    ) -> None:
        self._config = config
        self._address_map = address_map
        self._existing_tag_names = existing_tag_names
        self._fb_counters: dict[str, int] = {}

    def process(self, rows: list[IoIndexRow]) -> GenerationResult:
        result = GenerationResult()
        for row in rows:
            try:
                self._process_row(row, result)
            except _RowProcessingError as exc:
                result.errors.append(
                    RowError(
                        row_number=row.number,
                        tag_name=row.tag_name,
                        template=row.template,
                        message=str(exc),
                    )
                )
        return result

    # ------------------------------------------------------------------
    # Row processing
    # ------------------------------------------------------------------

    def _process_row(self, row: IoIndexRow, result: GenerationResult) -> None:
        rules = self._config.rules_for_template(row.template)
        if not rules:
            raise _RowProcessingError(f"Template: ({row.template}) not found")

        # Buffer all outputs so a mid-row failure leaves result unchanged.
        pending_tags: list[Tag] = []
        pending_conditioning: list[ConditioningEntry] = []
        pending_fbs: list[FunctionBlockEntry] = []

        for rule in rules:
            role_to_tag: dict[str, Tag] = {}

            for entry in rule.entries:
                tag = self._generate_tag(row, entry)
                role_to_tag[entry.role] = tag
                pending_tags.append(tag)

            if rule.condition_code:
                stmt = self._resolve_condition_code(
                    rule.condition_code, role_to_tag, row.failsafe
                )
                pending_conditioning.append(
                    ConditioningEntry(rule=rule.name, statement=stmt)
                )

            if rule.function_block:
                fb_num = self._next_fb_counter(rule.name)
                stmt = self._resolve_function_block(
                    rule.function_block, role_to_tag, fb_num
                )
                pending_fbs.append(
                    FunctionBlockEntry(rule=rule.name, statement=stmt)
                )

        result.tags.extend(pending_tags)
        result.conditioning.extend(pending_conditioning)
        result.function_blocks.extend(pending_fbs)

        if row.is_alarm:
            result.alarms.append(self._generate_alarm(row))

    # ------------------------------------------------------------------
    # Tag generation
    # ------------------------------------------------------------------

    def _generate_tag(self, row: IoIndexRow, entry: RuleEntry) -> Tag:
        tag_name = row.twinsoft_base_name + self._resolve_tokens(
            entry.tag_suffix, row
        )

        if tag_name in self._existing_tag_names:
            raise _RowProcessingError(
                f"Duplicate: '{tag_name}' already exists in the PLC"
            )

        comment = self._build_description(
            row.description, entry.desc_delimiter, entry.desc_suffix, row
        )[:50]

        is_numeric = entry.data_class not in (DataType.BOOL, DataType.TEXT)

        presentation = PresentationConfig(
            enabled=row.has_presentation,
            description=row.presentation,
            units=row.units if is_numeric else "",
        )

        write_allowed = WriteAllowedConfig(
            enabled=entry.write_allowed,
            minimum=entry.write_allowed_min,
            maximum=entry.write_allowed_max,
        )

        try:
            return Tag(
                name=tag_name,
                data_type=entry.data_class,
                modbus_address=self._address_map.allocate(
                    entry.data_class, entry.addr
                ),
                comment=comment,
                group=entry.folder,
                presentation=presentation,
                write_allowed=write_allowed,
                minimum=row.input_min if is_numeric else "",
                maximum=row.input_max if is_numeric else "",
            )
        except ValidationError as exc:
            first_msg = exc.errors()[0]["msg"]
            raise _RowProcessingError(
                f"Invalid tag '{tag_name}': {first_msg}"
            ) from exc

    # ------------------------------------------------------------------
    # Alarm generation
    # ------------------------------------------------------------------

    def _generate_alarm(self, row: IoIndexRow) -> Alarm:
        defaults = self._config.alarm_defaults
        condition = row.alarm_condition or defaults.condition
        return Alarm(
            tag_name=row.twinsoft_base_name,
            condition=condition,  # type: ignore[arg-type]
            recipient=defaults.recipient,
            call_all_recipients=defaults.call_all_recipients,
            message=row.alarm_message,
            is_report=defaults.is_report,
            filter=defaults.filter,
            options=defaults.options,
        )

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    def _resolve_tokens(self, template: str, row: IoIndexRow) -> str:
        result = template
        if row.module is not None:
            result = result.replace("#M", str(row.module))
        if row.module_channel is not None:
            result = result.replace("#C", str(row.module_channel))
        if row.connector is not None:
            result = result.replace("#T", str(row.connector))
        if row.connector_channel is not None:
            result = result.replace("#A", str(row.connector_channel))
        return result

    def _build_description(
        self, base: str, delimiter: str, suffix: str, row: IoIndexRow
    ) -> str:
        resolved = self._resolve_tokens(suffix, row)
        if not resolved:
            return base
        if delimiter:
            return f"{base} {delimiter} {resolved}"
        return f"{base} {resolved}"

    # ------------------------------------------------------------------
    # Conditioning + function block resolution
    # ------------------------------------------------------------------

    def _resolve_condition_code(
        self,
        condition_code: str,
        role_to_tag: dict[str, Tag],
        failsafe: bool,
    ) -> str:
        dest_role, src_role = (s.strip() for s in condition_code.split("=", 1))
        dest = role_to_tag[dest_role].name
        src = role_to_tag[src_role].name
        return f"{dest} = NOT {src}" if failsafe else f"{dest} = {src}"

    def _resolve_function_block(
        self,
        template: str,
        role_to_tag: dict[str, Tag],
        fb_num: int,
    ) -> str:
        result = template.replace("#N", str(fb_num))
        for role, tag in sorted(
            role_to_tag.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            result = result.replace(f"#{role}", tag.name)
        return result

    def _next_fb_counter(self, rule_name: str) -> int:
        count = self._fb_counters.get(rule_name, 0) + 1
        self._fb_counters[rule_name] = count
        return count
