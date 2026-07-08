###################################################
# Project:     IOManager
# Author:      Peter C
# Date:        2026Jul07
# History:     2026Jul07 - Initial creation
#              2026Jul07 - Skip disabled entries during expansion
###################################################

from __future__ import annotations
import re

from app.models.config import VirtualTagEntry
from app.models.io_row import IoIndexRow

_NUMERIC_SUFFIX_RE = re.compile(r'^(.*?)(\d+)$')

# Virtual tag rows are numbered from this base to avoid collision with Excel row numbers.
_VIRTUAL_ROW_BASE = 10_000


def _extract_numeric(tag: str) -> tuple[str, int, int]:
    """Return (prefix, integer_value, zero_pad_width) for the trailing numeric suffix."""
    m = _NUMERIC_SUFFIX_RE.match(tag)
    if not m:
        raise ValueError(f"Tag '{tag}' has no numeric suffix for range expansion")
    return m.group(1), int(m.group(2)), len(m.group(2))


def _expand_entry(entry: VirtualTagEntry) -> list[tuple[str, str]]:
    """Return list of (tag_name, description) pairs for one VirtualTagEntry."""
    tag_to = entry.tag_name_to

    if not tag_to or tag_to == entry.tag_name_from:
        tag = entry.tag_name_from
        m = _NUMERIC_SUFFIX_RE.match(tag)
        counter = int(m.group(2)) if m else 1
        return [(tag, entry.description.replace('#N', str(counter)))]

    try:
        prefix, start, width = _extract_numeric(entry.tag_name_from)
        prefix_to, end, _ = _extract_numeric(tag_to)
    except ValueError:
        return [(entry.tag_name_from, entry.description)]

    if prefix != prefix_to or end < start:
        return [(entry.tag_name_from, entry.description)]

    return [
        (f"{prefix}{i:0{width}d}", entry.description.replace('#N', str(i)))
        for i in range(start, end + 1)
    ]


def expand_virtual_tags(
    entries: list[VirtualTagEntry],
    start_row: int = _VIRTUAL_ROW_BASE,
) -> list[IoIndexRow]:
    """Expand all VirtualTagEntry items into IoIndexRow instances ready for the rule engine."""
    rows: list[IoIndexRow] = []
    row_num = start_row
    for entry in entries:
        if not entry.enabled:
            continue
        for tag_name, description in _expand_entry(entry):
            rows.append(IoIndexRow(
                number=row_num,
                tag_name=tag_name,
                description=description,
                template=entry.template,
                is_alarm=entry.is_alarm,
                alarm_condition=entry.alarm_condition or None,
                alarm_message=entry.alarm_message,
            ))
            row_num += 1
    return rows
