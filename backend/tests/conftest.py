###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
import io
import shutil
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

_DEFAULT_CONFIG = Path(__file__).parent / "fixtures" / "app.config.json"

IO_HEADERS = [
    "Number", "Tag Name", "Description", "I/O Type", "Part Number",
    "Module", "Module Channel", "Connector", "Connector Channel",
    "Signal", "Phase", "Note", "Template", "Failsafe",
    "hasPresentation", "Presentation", "Units", "InputMax", "InputMin",
    "isAlm", "AlmCondition", "AlmMsg", "Skip", "Log",
]


def make_excel_bytes(rows: list[dict]) -> bytes:
    """Build a minimal IO Dist Excel file in memory."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "IO Dist"
    ws.append(IO_HEADERS)
    for row in rows:
        ws.append([row.get(h) for h in IO_HEADERS])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


TWINSOFT_XML_SAMPLE = """\
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="dig1">
    <Format>DIGITAL</Format>
    <ModbusAddress>1000</ModbusAddress>
    <Signed />
    <TextTagSize />
  </Tag>
  <Tag Name="ai1">
    <Format>FLOAT</Format>
    <ModbusAddress>2000</ModbusAddress>
    <Signed>True</Signed>
    <TextTagSize />
  </Tag>
</TWinSoftTags>"""


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data_dir = tmp_path / "data"
    (data_dir / "import").mkdir(parents=True)
    (data_dir / "export").mkdir(parents=True)

    shutil.copy(_DEFAULT_CONFIG, config_dir / "app.config.json")

    return Settings(config_dir=config_dir, data_dir=data_dir)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    application = create_app(settings=settings)
    with TestClient(application) as c:
        yield c
