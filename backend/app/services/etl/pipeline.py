###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
#              2026Jul07 - Merge expanded virtual tags into io_rows before rule engine
###################################################

from __future__ import annotations
from pathlib import Path

from app.models.address_map import AddressMap
from app.models.config import AppConfig
from app.models.generation import GenerationResult
from app.models.io_row import IoIndexRow
from app.services.etl.rule_engine import RuleEngine
from app.services.etl.twinsoft.exporter import TwinsoftExporter
from app.services.etl.virtual_tags import expand_virtual_tags


def run_pipeline(
    config: AppConfig,
    io_rows: list[IoIndexRow],
    address_map: AddressMap,
    export_dir: Path,
) -> GenerationResult:
    """
    Run the full ETL pipeline:
      1. Append expanded virtual tag rows to io_rows
      2. Execute the rule engine against all rows and the pre-loaded address_map
      3. Write the four output files into export_dir
      4. Return the GenerationResult (tags, alarms, conditioning, FBs, errors)
    """
    export_dir.mkdir(parents=True, exist_ok=True)

    all_rows = [*io_rows, *expand_virtual_tags(config.virtual_tags)]
    engine = RuleEngine(config=config, address_map=address_map)
    result = engine.process(all_rows)

    exporter = TwinsoftExporter()

    (export_dir / "tags.xml").write_text(
        exporter.export_tags(result.tags), encoding="utf-8"
    )
    (export_dir / "alarms.xml").write_text(
        exporter.export_alarms(result.alarms), encoding="utf-8"
    )
    (export_dir / "conditioning.txt").write_text(
        exporter.export_conditioning(result.conditioning), encoding="utf-8"
    )
    (export_dir / "function_blocks.txt").write_text(
        exporter.export_function_blocks(result.function_blocks), encoding="utf-8"
    )

    return result
