# IOManager — Requirements

## 1. Overview

IOManager is an ETL (Extract, Transform, Load) web application for industrial control system engineers. It reads an I/O index from an Excel spreadsheet, applies configurable tag creation rules, and generates import files compatible with the Ovarro TBox Twinsoft IDE. The tool manages the full tag lifecycle: creation, address allocation, conditioning code generation, and alarm configuration.

The PLC (via Twinsoft export) is the system of record for assigned Modbus addresses. The app reads the current Twinsoft export on each session to understand occupied address space before allocating new addresses.

The scafolding is in place to support other systems.

---

## 2. Users

**Primary user:** Control system engineer

- Works iteratively and incrementally — tags are added over time, not all at once
- Uses Excel as the I/O index (source of truth for physical I/O points)
- Imports generated files into Twinsoft IDE
- Expects write-back of processing status into the Excel file

---

## 3. Use Cases

### UC-01: Import I/O Index
- Engineer uploads an Excel file containing the `IO Dist` tab
- System parses all rows and validates column structure
- Rows with missing or unrecognized `Template` values are flagged with an error in the `Log` column

### UC-02: Import Twinsoft Export (Address Snapshot)
- Engineer uploads a current Twinsoft export XML (tags)
- System parses all existing tags and builds an address occupation map (coil space and register space separately)
- Any address present in the export is marked occupied, regardless of whether the tag appears in the I/O index

### UC-03: Generate Tags
- System applies template → rule mapping for each I/O index row
- For each rule entry, generates one or more Twinsoft tags
- Addresses are allocated from the appropriate pool, skipping occupied addresses
- Conditioning code and function block instantiation code are generated per rule

### UC-04: Generate Alarms
- For rows where `isAlm = 1`, generate a Twinsoft alarm entry
- Only `DIGITAL` format tags are supported in the current version
- Alarm message from `AlmMsg`, condition from `AlmCondition` (defaults to config value if blank)
- All other alarm fields (`Recipient`, `Filter`, `Options`) use config defaults

### UC-05: Export Output Files
- `tags.xml` — Twinsoft tag import
- `alarms.xml` — Twinsoft alarm import
- `conditioning.txt` — PLC conditioning assignment statements
- `function_blocks.txt` — PLC function block instantiation calls

### UC-06: Excel Write-back
- After generation, write processing status back to the `Log` column of the source Excel file
- Success: `Processed at MM/DD/YYYY HH:MM:SS`
- Error: descriptive message (e.g., `Template: (DI) not found`)
- Error rows: cell background highlighted red

### UC-07: Virtual Tag Entries
- Engineer creates tag entries without a corresponding I/O index row
- Supports single tags or name ranges (e.g., `PY_001` → `PY_010`)
- Description supports `#N` auto-increment token
- Uses the same template → rule engine as physical I/O rows
- Stored in app config (JSON), not in Excel

### UC-08: Configuration Management
- All rules, templates, and defaults are configurable via the UI
- Config persisted as JSON files in `config/`
- UI provides forms for editing rules, template mappings, and alarm defaults

---

## 4. I/O Index (Excel — IO Dist Tab)

### 4.1 Column Definitions

| Column | Type | Description |
|---|---|---|
| Number | Integer | Row sequence number |
| Tag Name | String | ISA instrument tag (e.g., `LAL-001`) |
| Description | String | Human-readable description (max 50 chars for Twinsoft Comment) |
| I/O Type | String | `DI`, `DO`, `AI`, `AO`, `TC`, `DI CNT`, `AI HART` |
| Part Number | String | Hardware part number (metadata only, not used in generation) |
| Module | Integer | Weidmueller module number |
| Module Channel | Integer | 0-based channel on module |
| Connector | Integer | Connector number |
| Connector Channel | Integer | Channel on connector |
| Signal | String | `Dry Contact`, `Thermocouple`, `4-20mA`, `HART` |
| Phase | Integer | Electrical phase (1/2/3) |
| Note | String | Free text, ignored during ETL |
| Template | String | Template name to apply (engineer-selected, e.g., `DI`, `DO`, `AI`) |
| Failsafe | Integer | `1` = failsafe — NOT applied in conditioning code |
| hasPresentation | Integer | `1` = Twinsoft `<Presentation>` set to `True` |
| Presentation | String | Twinsoft `Presentation.Description` |
| Units | String | Twinsoft `Presentation.Units` |
| InputMax | Numeric | Twinsoft `<Maximum>` |
| InputMin | Numeric | Twinsoft `<Minimum>` |
| isAlm | Integer | `1` = generate alarm entry for this tag |
| AlmCondition | String | `POS` or `NEG` — defaults to config value if blank |
| AlmMsg | String | Alarm message text (max 120 chars) |
| Log | String | **Written back by app** — processing status or error message |

### 4.2 Tag Name Conversion

- ISA format (e.g., `LAL-001`): hyphens converted to underscores → `LAL_001`
- Physical I/O tag: base name + trailing underscore (e.g., `LAL_001_`)
- Soft tag: base name only (e.g., `LAL_001`)

### 4.3 Hardware Notes

Preferred I/O hardware is Weidmueller. Module, Module Channel, Connector, and Connector Channel columns are Weidmueller-specific terms. The rule engine references these via `#M` and `#C` tokens.

---

## 5. Twinsoft Tag Format

### 5.1 XML Structure

```xml
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftTags>
  <Tag Name="{name}">
    <NewName>{name}</NewName>
    <Address></Address>
    <Format>{format}</Format>
    <ModbusAddress>{modbusAddress}</ModbusAddress>
    <Comment>{comment}</Comment>
    <InitalValue>{initialValue}</InitalValue>
    <Signed>{signed}</Signed>
    <TextTagSize>{textTagSize}</TextTagSize>
    <Minimum>{minimum}</Minimum>
    <Maximum>{maximum}</Maximum>
    <Resolution>{resolution}</Resolution>
    <Group>{group}</Group>
    <Presentation Description="{description}" StateOn="{stateOn}" StateOff="{stateOff}" Units="{units}" NbrDecimals="{nbrDecimals}">{presentation}</Presentation>
    <WriteAllowed WriteAllowed_Minimum="{writeMin}" WriteAllowed_Maximum="{writeMax}">{writeAllowed}</WriteAllowed>
    <DisplayFormat>DECIMAL</DisplayFormat>
  </Tag>
</TWinSoftTags>
```

> **Note:** `<InitalValue>` — this typo exists in the Twinsoft format and **must be preserved** in generated output.

### 5.2 Field Rules

**Name / NewName**
- Pattern: `[A-Za-z][A-Za-z0-9_]{0,14}` (max 15 chars, underscore only separator)
- `NewName` = `Name` unless the engineer is performing a rename operation

**Address**
- Always blank on new tag import — Twinsoft assigns on import
- Pattern when present: `DIV#####` (DIGITAL), `AIV#####` (all register-based types)

**Format**
- Valid values: `FLOAT`, `DIGITAL`, `16BITS`, `32BITS`, `BYTE`, `TEXT`

**ModbusAddress**
- Two independent address spaces:
  - `DIGITAL` → coil/bit space
  - All other formats → register space
- Must be unique within each address space
- `FLOAT` / `32BITS`: must start on even boundary, consume 2 contiguous registers
- `16BITS` / `BYTE`: 1 register
- `TEXT`: `ceil(TextTagSize / 2)` registers

**Class → Format Mapping**

| Class | Format | Signed |
|---|---|---|
| BOOL | DIGITAL | — |
| INT16 | 16BITS | True |
| UINT16 | 16BITS | False |
| INT32 | 32BITS | True |
| UINT32 | 32BITS | False |
| FLOAT | FLOAT | True |

**Format-specific field applicability**

| Field | FLOAT | DIGITAL | 16BITS | 32BITS | BYTE | TEXT |
|---|---|---|---|---|---|---|
| Signed | True | — | True/False | True/False | False | — |
| TextTagSize | — | — | — | — | — | integer |
| Minimum | ✓ | — | ✓ | ✓ | ✓ | — |
| Maximum | ✓ | — | ✓ | ✓ | ✓ | — |
| Resolution | ✓ | — | ✓ | ✓ | ✓ | — |
| StateOn / StateOff | — | ✓ | — | — | — | — |
| Units | ✓ | — | ✓ | ✓ | ✓ | — |
| NbrDecimals | ✓ | — | ✓ | ✓ | ✓ | — |

**Other field rules**
- `Comment`: max 50 chars
- `WriteAllowed`: `True` for DO / AO outputs, `False` for all inputs
- `DisplayFormat`: always `DECIMAL`
- `Group`: maps to the rule's `folder` value

---

## 6. Twinsoft Alarm Format

```xml
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<TWinSoftAlarms>
  <Alarm TagName="{tagName}">
    <Condition Value="" Hysteresis="">{condition}</Condition>
    <Recipient CallAllRecipients="">{recipient}</Recipient>
    <Message IsReport="{isReport}">{message}</Message>
    <Filter FilterHour="{h}" FilterMinute="{m}" FilterSecond="{s}" />
    <Options NotifyEndOfAlarm="{notify}" SMSAcknowledge="{sms}" POP3Acknowledge="{pop3}" Handling="{handling}" />
    <RuntimeParameters RTP_Handling="" RTP_Threshold="" RTP_Hysteresis="" />
  </Alarm>
</TWinSoftAlarms>
```

### 6.1 Field Rules

| Field | Source | Notes |
|---|---|---|
| TagName | Generated tag name | Must reference a DIGITAL format tag |
| Condition | `AlmCondition` column or config default | `POS` (rising edge) or `NEG` (falling edge) |
| Recipient | Config default | Group name (e.g., `Default`) |
| Message | `AlmMsg` column | Max 120 chars |
| IsReport | Config default | `True` / `False` |
| FilterHour/Minute/Second | Config default | Debounce time (default 0/0/0) |
| NotifyEndOfAlarm | Config default | `True` / `False` |
| Handling | Config default | `ENABLED` / `DISABLED` |

### 6.2 Current Limitations

- Alarms are supported for DIGITAL tags only
- `Condition.Value` and `Condition.Hysteresis` are always empty (reserved for future analog alarm support)
- `RuntimeParameters` fields are always empty

---

## 7. Rule Engine

### 7.1 Rule Structure

Rules are stored in `config/app.config.json` and editable via the UI. Each rule contains named-role entries that define the tags to generate and how they relate to each other.

```json
{
  "rule": "_DI",
  "entries": [
    {
      "role": "io",
      "addr": 1000,
      "tagSuffix": "_",
      "class": "BOOL",
      "descDelimiter": "",
      "descSuffix": "M#MC#C",
      "folder": "IO\\DI"
    },
    {
      "role": "soft",
      "addr": 2000,
      "tagSuffix": "",
      "class": "BOOL",
      "descDelimiter": "",
      "descSuffix": "",
      "folder": "SOFT_TAGS\\MAPPED_IO\\DI"
    }
  ],
  "conditionCode": "soft = io",
  "functionBlock": null
}
```

### 7.2 Substitution Tokens

| Token | Resolved From |
|---|---|
| `#M` | `Module` column of I/O index |
| `#C` | `Module Channel` column of I/O index |
| `#N` | Auto-increment counter per rule group (function blocks) or per virtual tag range |
| `#{role}` | Resolved tag name for that role within the same rule group |

### 7.3 Conditioning Code Generation

The `conditionCode` field in the rule definition uses role names to declare the PLC assignment direction. This covers both inputs and outputs — no I/O index column is needed. If a per-row override is ever required, it will be added as a field in the rule definition, not as an I/O index column.

- `"soft = io"` → `XY_001 = XY_001_` (input: hardware drives soft tag)
- `"io = soft"` → `XY_001_ = XY_001` (output: soft tag drives hardware)
- Failsafe (`Failsafe = 1` in I/O index): NOT applied to source → `XY_001 = NOT XY_001_`

### 7.4 Function Block Generation

The `functionBlock` template string uses `#N` (auto-incremented per rule group across the project) and `#{role}` tokens:

```
"Call FB_#N(#hoa_val, #hoa_h, #hoa_o, #hoa_a)"
```

Resolved example for first HOA set:
```
Call FB_1(XY_001_HOA, XY_001_H, XY_001_O, XY_001_A)
```

Any rule with a non-null `functionBlock` template generates entries in `function_blocks.txt`.

### 7.5 Default Rule Table

| Rule | Role | Addr | TagSuffix | Class | DescDelimiter | DescSuffix | Folder |
|---|---|---|---|---|---|---|---|
| _HOA | hoa_val | 3700 | _HOA | UINT16 | - | HOA (H=1,O=0,A=2) | SOFT_TAGS\PROCESS\HOA |
| _HOA | hoa_h | 3700 | _H | BOOL | - | HAND | SOFT_TAGS\PROCESS\HOA |
| _HOA | hoa_o | 3700 | _O | BOOL | - | OFF | SOFT_TAGS\PROCESS\HOA |
| _HOA | hoa_a | 3700 | _A | BOOL | - | AUTO | SOFT_TAGS\PROCESS\HOA |
| _DI | io | 1000 | _ | BOOL | — | M#MC#C | IO\DI |
| _DI | soft | 2000 | — | BOOL | — | — | SOFT_TAGS\MAPPED_IO\DI |
| _DO | io | 1200 | _ | BOOL | — | M#MC#C | IO\DO |
| _DO | soft | 2200 | — | BOOL | — | — | SOFT_TAGS\MAPPED_IO\DO |
| _AI | io | 1400 | _ | INT16 | — | M#MC#C | IO\AI |
| _AI | fault | 5000 | _FLT | BOOL | — | FAULT | SOFT_TAGS\PROCESS\ALARMS |
| _AI | raw | 5500 | _R | INT16 | — | RAW | SOFT_TAGS\MAPPED_IO\AI |
| _AI | scaled | 3024 | — | FLOAT | — | — | SOFT_TAGS\SCALED |
| _SDI | io | 1000 | _#M_#C | BOOL | — | — | IO\DI |
| _SDI | soft | 2000 | _#T_#A | BOOL | — | — | SOFT_TAGS\MAPPED_IO\DI |
| _SDO | io | 1200 | _#M_#C | BOOL | — | — | IO\DO |
| _SDO | soft | 2200 | _#T_#A | BOOL | — | — | SOFT_TAGS\MAPPED_IO\DO |
| _SAI | io | 1400 | _#M_#C | INT16 | — | — | IO\AI |
| _LVL | ahh_sp | 3900 | _AHH_SP | INT16 | - | HI-HI SETPOINT | SOFT_TAGS\SETTINGS |
| _LVL | ah_sp | 3900 | _AH_SP | INT16 | - | HI SETPOINT | SOFT_TAGS\SETTINGS |
| _LVL | al_sp | 3900 | _AL_SP | INT16 | - | LO SETPOINT | SOFT_TAGS\SETTINGS |
| _LVL | all_sp | 3900 | _ALl_SP | INT16 | - | LO-LO SETPOINT | SOFT_TAGS\SETTINGS |

> `_SDI` / `_SDO` / `_SAI` — `#T` and `#A` tokens TBD; rule system designed to accommodate new tokens without code changes.

### 7.6 Default Template → Rule Mapping

| Template | Rules Applied |
|---|---|
| DO | _HOA, _DO |
| DI | _DI |
| AI | _AI |
| SDI | _SDI |
| SDO | _SDO |
| SAI | _SAI |

> `TC`, `AO`, `DI CNT`, `AI HART` templates are not yet defined. The template → rule mapping is flexible enough to accommodate them via config.

---

## 8. Address Space Management

- On each session, engineer imports the current Twinsoft export XML
- System builds two independent occupied address maps: coil space (DIGITAL) and register space (all others)
- Each rule entry specifies a starting address pool; new allocations begin from the next free address above the highest occupied address in that pool segment
- Allocation sizes: BOOL / INT16 / UINT16 / BYTE = 1, FLOAT / INT32 / UINT32 = 2 (even boundary required), TEXT = `ceil(TextTagSize / 2)`
- Occupied addresses from the PLC export are never re-allocated

---

## 9. Virtual Tag Entries

- App-managed list stored in `config/` JSON, not in the Excel file
- Each entry: name pattern or range (`PY_001` → `PY_010`), description pattern, template selection
- `#N` token in name/description auto-increments across the range
- Processed through the same template → rule engine as I/O index rows
- Appear in all output files alongside I/O index tags

---

## 10. Output Files

All outputs written to `data/export/`.

| File | Format | Description |
|---|---|---|
| `tags.xml` | XML | Twinsoft tag import file |
| `alarms.xml` | XML | Twinsoft alarm import file |
| `conditioning.txt` | Text | PLC conditioning assignment statements, grouped by rule |
| `function_blocks.txt` | Text | PLC function block instantiation calls, grouped by rule |

### conditioning.txt Structure

Statements are grouped by rule type with a section comment header per group. Within each group, entries appear in I/O index row order followed by virtual tag entries. Spans both inputs and outputs — direction is determined by the rule's `conditionCode` field.

```
(* --- _DI CONDITIONING --- *)
LSL_001 = LSL_001_
LAL_001 = NOT LAL_001_

(* --- _DO CONDITIONING --- *)
XY_001_ = XY_001

(* --- _AI CONDITIONING --- *)
AI_001_R = AI_001_
```

### function_blocks.txt Structure

Calls are grouped by rule type with a section comment header per group. The FB instance counter (`#N`) increments globally within each rule group in processing order. Only rules with a non-null `functionBlock` template generate a group.

```
(* --- _HOA FUNCTION BLOCKS --- *)
Call FB_1(XY_001_HOA, XY_001_H, XY_001_O, XY_001_A)
Call FB_2(XY_010_HOA, XY_010_H, XY_010_O, XY_010_A)
```

---

## 11. Configuration

Stored in `config/app.config.json`, editable via the UI.

- Tag rules (full rule table with all entries and roles)
- Template → rule mappings
- Alarm defaults (Condition, Recipient, Filter, Options)
- Address pool starting points
- Substitution token definitions

---

## 12. Decoupling Architecture

The rule engine is decoupled from Twinsoft (or any other target system). It always produces **internal semantic models** — never target-system-specific structures. Concrete implementations are selected at runtime via a factory.

### Principle

```
Rule Engine → internal Tag / Alarm models → TagExporter (Protocol) → target-specific output
Target export file → TagImporter (Protocol) → AddressMap → Rule Engine
```

The internal models (`Tag`, `Alarm`, `AddressMap`) capture what a tag *means* — data type, address, description, engineering context — not how any particular system represents it.

### Why This Scope

Full abstraction of the rule engine itself is premature without a second target system to reveal common patterns. VT-SCADA and CodeSys have fundamentally different tag concepts; attempting a universal rule schema now would create a leaky abstraction. The Protocols + Factory pattern is the minimum non-speculative investment:

- Cheap to implement (~30 lines)
- No guesswork about future system schemas
- Adding a new target means implementing two Protocols and registering in the factory — no rule engine changes

### What Stays Target-Specific

Field name quirks (e.g., the `InitalValue` typo), XML structure, address pattern formats (`DIV#####`, `AIV#####`), and any output file format details belong in the concrete implementation only. They must never appear in the internal models or rule engine.

### Target System Configuration

Active target system is set in `config/app.config.json`. Initially `"twinsoft"`. Changing the value selects a different concrete exporter/importer at runtime.

---

## 13. Non-Functional Requirements

- Backend: Python 3.11+, FastAPI
- Frontend: Nuxt 3, Vue 3, TypeScript (Composition API, `<script setup>`)
- Styling: Tailwind CSS v4, dark theme (surveillance/night aesthetic)
- State management: Pinia
- API communication: Nuxt `$fetch` / `useFetch` with base URL from runtime config
- Map: Leaflet via `@vue-leaflet/vue-leaflet`
- Docker: dev (hot reload) and prod compose targets
- Config: JSON files only, never hardcoded values
- All source files: standard file header (see CLAUDE.md)
