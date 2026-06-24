# CLAUDE.md — IOManager

## Project Overview

IOManager is an ETL web application for industrial control system engineers. It reads an I/O index from an Excel spreadsheet (`IO Dist` tab), applies configurable tag creation rules, and generates Twinsoft-compatible import files for Ovation TBox PLCs. It is not a general-purpose tool — it is purpose-built for the Twinsoft tag/alarm import XML format.

See `requirements.md` for full functional specification.

---

## Build Status

| Phase | Description | Status |
|---|---|---|
| 1 | Internal models (`Tag`, `Alarm`, `AddressMap`, `Output`), ETL Protocols | ✅ Done — 94 tests |
| 2 | Config models, JSON loader, default `app.config.json` with full rule table | ✅ Done — 136 tests |
| 3 | Rule engine, Twinsoft importer (address map), Twinsoft exporter (XML + txt), factory | ✅ Done — 269 tests |
| 4 | FastAPI app, all routes | ✅ Done — 338 tests |
| 5 | Dockerfiles, compose files | ✅ Done |

**Test command:** `.venv/bin/pytest -q` (run from `backend/`)

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Frontend | Nuxt 3, Vue 3, TypeScript |
| Styling | Tailwind CSS v4 — dark theme (surveillance/night aesthetic) |
| State | Pinia |
| API calls | `$fetch` / `useFetch`, base URL from Nuxt runtime config |
| Map | Leaflet via `@vue-leaflet/vue-leaflet` |
| Config | JSON files in `config/` |
| Data I/O | `data/import/` and `data/export/` |

---

## Directory Structure

```
iomanager/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI entry point
│   │   ├── config.py                      # JSON config load/save
│   │   ├── api/routes/
│   │   │   ├── tags.py
│   │   │   ├── alarms.py
│   │   │   ├── imports.py
│   │   │   ├── exports.py
│   │   │   └── config.py
│   │   ├── models/                        # Pydantic models
│   │   │   ├── tag.py
│   │   │   ├── alarm.py
│   │   │   └── config.py
│   │   └── services/etl/
│   │       ├── protocols.py               # TagExporter / TagImporter Protocol definitions
│   │       ├── factory.py                 # Maps target system name → concrete implementation
│   │       └── twinsoft/                  # Twinsoft implementation — add other vendors as siblings
│   │           ├── importer.py            # Parse Twinsoft export XML → AddressMap
│   │           ├── exporter.py            # Internal Tag/Alarm models → Twinsoft XML
│   │           └── parser.py              # Shared XML parsing utilities
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── assets/css/main.css
│   ├── components/
│   │   ├── layout/
│   │   │   ├── SidebarNav.vue             # Visible ≥ lg
│   │   │   └── BottomTabNav.vue           # Visible < lg
│   │   ├── tags/
│   │   ├── alarms/
│   │   └── common/                        # DataTable, Modal, StatusBadge, etc.
│   ├── composables/
│   ├── layouts/default.vue
│   ├── pages/
│   │   ├── index.vue
│   │   ├── tags/index.vue
│   │   ├── alarms/index.vue
│   │   ├── import/index.vue
│   │   ├── export/index.vue
│   │   └── settings/index.vue
│   ├── stores/                            # Pinia stores
│   ├── types/                             # Shared TypeScript interfaces
│   ├── nuxt.config.ts
│   └── Dockerfile
├── data/
│   ├── import/                            # Drop zone for Excel and Twinsoft export files
│   └── export/                            # Generated output files
├── config/
│   └── app.config.json                    # UI-editable, JSON-persisted
├── docker-compose.yml
├── docker-compose.dev.yml
├── CLAUDE.md
├── requirements.md
└── .gitignore
```

---

## Git Policy — CRITICAL

- **NEVER** run `git commit`, `git push`, `git branch`, or any other write git command
- Read-only git operations are permitted: `git status`, `git diff`, `git log`
- Suggest commit messages as inline comments only — the developer commits manually
- One logical change per suggested commit message
- Never create or switch branches

---

## File Headers — CRITICAL

Every source file must include a standard header. **Before writing any file, add or update the header first.**

- **Author:** `Peter Chrapchynski`
- **Project:** `IOManager`
- **Date format:** `yyyyMMMdd` with 3-letter month abbreviation (e.g., `2026Jun23`)
- **Date field:** Original creation date — never changes
- **History:** Append a new line on each modification; never remove or reorder existing entries

### Python (.py)

```python
###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################
```

### TypeScript / JavaScript (.ts, .tsx, .js)

```ts
/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/
```

### Vue (.vue) — place before the first `<template>` tag

```vue
<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->
```

### CSS (.css) — global stylesheets only, not scoped component styles

```css
/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/
```

### Enforcement Rules

- New file → generate full header before writing any code
- Modified file → check for existing header:
  - Missing: add full header before proceeding
  - Present: append new History line with current date and brief description
- Never modify `Project`, `Author`, or `Date` fields on existing files
- Never add headers to scoped `<style>` blocks in `.vue` files
- No headers required for `.md`, `.json`, `.gitignore`, or config files

---

## Code Style

### Frontend

- Composition API with `<script setup>` — no Options API
- TypeScript throughout
- One component per file, PascalCase filenames
- Tailwind utility classes only — no custom CSS unless unavoidable
- Responsive nav: sidebar ≥ lg, bottom tab nav < lg

### Backend

- Python type hints throughout
- Pydantic models for all data shapes
- FastAPI dependency injection patterns

---

## Run Locally

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
uv venv
uv pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

## Docker

```bash
# Development (hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production build
docker compose up --build

# Tear down
docker compose down

# Logs
docker compose logs -f backend
docker compose logs -f frontend
```

---

## Architecture — ETL Pipeline

Three input sources feed the same rule engine:

```
1. Excel I/O index (IO Dist tab)      ─┐
2. Virtual tag entries (config JSON)  ─┼──► Template → Rule(s) → Internal Tag/Alarm models → Exporter → Output files
3. Target system export (address map) ─┘  (address-only, read via Importer before allocation)
```

### Decoupling Architecture

The rule engine is decoupled from any target system. It always produces **internal Pydantic models** (`Tag`, `Alarm`, `AddressMap`) — never target-system-specific structures. Concrete exporters/importers implement Protocols and are selected by a factory.

**Internal models** (`app/models/`):

```python
class Tag(BaseModel):
    name: str
    data_type: DataType          # BOOL, INT16, UINT16, INT32, UINT32, FLOAT, TEXT
    modbus_address: int
    description: str
    group: str
    engineering_units: str | None
    minimum: float | None
    maximum: float | None
    resolution: float | None
    initial_value: str | None
    presentation: PresentationConfig | None
    write_allowed: WriteAllowedConfig | None

class Alarm(BaseModel):
    tag_name: str
    condition: Literal["POS", "NEG"]
    message: str
    ...
```

**Protocols** (`app/services/etl/protocols.py`):

```python
class TagExporter(Protocol):
    def export_tags(self, tags: list[Tag]) -> str: ...
    def export_alarms(self, alarms: list[Alarm]) -> str: ...
    def export_conditioning(self, entries: list[ConditioningEntry]) -> str: ...
    def export_function_blocks(self, entries: list[FunctionBlockEntry]) -> str: ...

class TagImporter(Protocol):
    def import_address_map(self, file: Path) -> AddressMap: ...
```

**Factory** (`app/services/etl/factory.py`):

```python
def get_exporter(target: str) -> TagExporter:
    match target:
        case "twinsoft": return TwinsoftExporter()
        case _: raise ValueError(f"Unknown target system: {target}")

def get_importer(target: str) -> TagImporter:
    match target:
        case "twinsoft": return TwinsoftImporter()
        case _: raise ValueError(f"Unknown target system: {target}")
```

Target system is set in `config/app.config.json`. Adding a new target (e.g., VT-SCADA, CodeSys) means implementing the two Protocols and registering them in the factory — no changes to the rule engine.

**What stays target-specific:** Field name quirks (`InitalValue` typo), XML structure, address pattern formats (`DIV#####`, `AIV#####`). These belong in the concrete implementation, never in the internal model or rule engine.

### Output Files (written to `data/export/`)

| File | Description |
|---|---|
| `tags.xml` | Twinsoft tag import |
| `alarms.xml` | Twinsoft alarm import |
| `conditioning.txt` | PLC conditioning assignments, grouped by rule with `(* --- _XX CONDITIONING --- *)` headers |
| `function_blocks.txt` | PLC function block calls, grouped by rule with `(* --- _XX FUNCTION BLOCKS --- *)` headers |

### Address Space

Two independent Modbus pools:
- **Coil space** — DIGITAL / BOOL tags only
- **Register space** — FLOAT, 16BITS, 32BITS, BYTE, TEXT tags

Allocation sizes: BOOL / INT16 / UINT16 / BYTE = 1 unit, FLOAT / INT32 / UINT32 = 2 units (even boundary required), TEXT = `ceil(TextTagSize / 2)` units.

On each session, import the Twinsoft export XML first. Mark all addresses as occupied before allocating any new addresses. Tags in the PLC but absent from the I/O index still occupy their addresses.

### Rule Engine

Rules are data-driven (stored in `config/app.config.json`, editable via UI). Each rule has named-role entries. The named roles decouple the conditioning direction from index positions:

```json
{
  "rule": "_DI",
  "entries": [
    { "role": "io",   "addr": 1000, "tagSuffix": "_",  "class": "BOOL", "descSuffix": "M#MC#C", "folder": "IO\\DI" },
    { "role": "soft", "addr": 2000, "tagSuffix": "",   "class": "BOOL", "descSuffix": "",        "folder": "SOFT_TAGS\\MAPPED_IO\\DI" }
  ],
  "conditionCode": "soft = io",
  "functionBlock": null
}
```

**Conditioning code** — resolved from `conditionCode` using role names. Covers both inputs and outputs; direction is defined in the rule, not the I/O index:
- `"soft = io"` → `XY_001 = XY_001_` (input)
- `"io = soft"` → `XY_001_ = XY_001` (output)
- When `Failsafe = 1` in I/O index → NOT applied to source: `XY_001 = NOT XY_001_`

Output grouped by rule type with comment headers:
```
(* --- _DI CONDITIONING --- *)
LSL_001 = LSL_001_
(* --- _DO CONDITIONING --- *)
XY_001_ = XY_001
```

**Function block code** — `#N` auto-increments per rule group across the whole project; `#{role}` resolves to the tag name for that role. Any rule with a non-null `functionBlock` generates a group.

Output grouped by rule type with comment headers:
```
(* --- _HOA FUNCTION BLOCKS --- *)
Call FB_1(XY_001_HOA, XY_001_H, XY_001_O, XY_001_A)
Call FB_2(XY_010_HOA, XY_010_H, XY_010_O, XY_010_A)
```

**Substitution tokens:**

| Token | Resolved From |
|---|---|
| `#M` | `Module` column of I/O index |
| `#C` | `Module Channel` column of I/O index |
| `#N` | Auto-increment counter per rule group |
| `#{role}` | Tag name for that role within the same rule group |

### Excel Write-back

After generation, write the `Log` column back into the source Excel file using `openpyxl`:
- Success: `Processed at MM/DD/YYYY HH:MM:SS`
- Error: descriptive message (e.g., `Template: (DI) not found`)
- Error rows: set cell background to red

---

## Twinsoft Tag XML Reference

Key invariants that must be respected in generated output:
- `<InitalValue>` — the typo is part of the Twinsoft format; preserve it exactly
- `<Address>` — always empty for new tags; Twinsoft assigns the value on import
- `<DisplayFormat>` — always `DECIMAL`
- DIGITAL tags → coil address space, `DIV#####` address pattern (when present)
- All other formats → register address space, `AIV#####` address pattern (when present)

For full field rules, format tables, and XML examples see `requirements.md` Section 5.

## Twinsoft Alarm XML Reference

- DIGITAL tags only (current version)
- `Condition` content: `POS` (rising edge) or `NEG` (falling edge)
- `<Message>` max 120 chars
- `Condition.Value`, `Condition.Hysteresis`, and all `RuntimeParameters` fields are always empty

For full field rules and XML examples see `requirements.md` Section 6.
