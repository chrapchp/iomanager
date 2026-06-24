###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from app.services.etl.protocols import TagExporter, TagImporter
from app.services.etl.twinsoft.exporter import TwinsoftExporter
from app.services.etl.twinsoft.importer import TwinsoftImporter


def get_exporter(target: str) -> TagExporter:
    match target:
        case "twinsoft":
            return TwinsoftExporter()
        case _:
            raise ValueError(f"Unknown target system: '{target}'")


def get_importer(target: str) -> TagImporter:
    match target:
        case "twinsoft":
            return TwinsoftImporter()
        case _:
            raise ValueError(f"Unknown target system: '{target}'")
