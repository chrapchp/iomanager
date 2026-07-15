# IOManager

ETL tool for generating Twinsoft PLC tag and alarm import files from an Excel I/O index.

---

## Prerequisites

**Docker Desktop for Windows** — download and install from https://docs.docker.com/desktop/install/windows-install/

Start Docker Desktop before running any commands below. You will see the Docker whale icon in the system tray when it is ready.

---

## Installation

1. Unzip this package to a permanent location, for example `C:\iomanager`
2. Open **PowerShell** or **Command Prompt** in that folder
   - Windows 11: right-click the folder in Explorer → *Open in Terminal*
   - Windows 10: hold Shift, right-click → *Open PowerShell window here*
3. Run:
   ```
   docker compose up -d
   ```
   The first run downloads the application images (~200 MB) and may take a few minutes depending on your connection. Subsequent starts are instant.
4. Open **http://localhost:3000** in your browser

---

## Folder layout

```
iomanager\
├── docker-compose.yml        ← do not edit unless changing ports
├── config\
│   └── app.config.json       ← rules and templates (editable via the Settings UI)
├── data\
│   ├── import\               ← DROP YOUR FILES HERE before importing in the app
│   └── export\               ← GENERATED FILES APPEAR HERE after running Generate
└── README.md
```

**Your data lives in the `data\` and `config\` folders on your PC, not inside Docker.** Updating the app or removing Docker never deletes these files.

---

## Daily workflow

1. Copy your Excel I/O index (`.xlsx`) into `data\import\`
2. Copy your Twinsoft export XML into `data\import\` *(optional — needed for address allocation)*
3. Open http://localhost:3000
4. Use the **Import** page to load both files
5. Use the **Export** page to generate output
6. Retrieve the results from `data\export\`:
   - `tags.xml` — Twinsoft tag import
   - `alarms.xml` — Twinsoft alarm import
   - `conditioning.txt` — PLC conditioning statements
   - `function_blocks.txt` — PLC function block calls

---

## Common commands

Open PowerShell in the `iomanager` folder and run:

| What | Command |
|---|---|
| Start the app | `docker compose up -d` |
| Stop the app | `docker compose down` |
| View live logs | `docker compose logs -f` |
| Restart after a crash | `docker compose restart` |

---

## Changing ports or timezone

Create a file called `.env` next to `docker-compose.yml` with any of these lines:

```
BACKEND_PORT=8000
FRONTEND_PORT=3000
TZ=America/Edmonton
```

Then restart:
```
docker compose down
docker compose up -d
```

---

## Updating to a new version

1. Stop the running app: `docker compose down`
2. Download the new release zip from https://github.com/chrapchp/iomanager/releases
3. Unzip it to a **new** folder (e.g. `C:\iomanager-v1.1.0`)
4. Copy your existing `data\` and `config\` folders into the new folder
5. Open PowerShell in the new folder and run: `docker compose up -d`

Your rules, templates, and data files are preserved because they live in those two folders.

---

## Troubleshooting

**The page at localhost:3000 does not load**
- Make sure Docker Desktop is running (whale icon in system tray)
- Run `docker compose logs frontend` to check for errors

**Import or export fails silently**
- Run `docker compose logs backend` to see the error message

**Port 3000 or 8000 is already in use**
- Add a `.env` file (see above) and change the conflicting port, then restart

**Clock in logs is wrong**
- Add `TZ=America/Edmonton` to your `.env` file and restart
