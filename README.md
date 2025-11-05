# Acoustic Modem Workbench (AMW)

Acoustic Modem Workbench is a research-oriented desktop application for building, exercising, and debugging acoustic modem signal chains. AMW provides a modular GUI, an orchestrated transmit/receive pipeline, and a plugin architecture that lets modem developers focus on encode/decode algorithms while reusing shared audio I/O, conditioning, and diagnostics.

## Features

- **End-to-end pipeline** – Build payloads, transmit, capture, condition, and decode in one workflow.
- **Plugin architecture** – Drop new modem implementations in `modems/<name>/` with shared schema contracts.
- **GUI instrumentation** – Qt-based panels for modem selection, payload authoring, device setup, and debug tabs.
- **Audio abstraction** – A thin wrapper over `sounddevice` with graceful fallbacks for environments without audio hardware.
- **Extensive tests** – Unit suites cover plugins, pipeline orchestration, GUI scaffolding, and audio utilities with ≥85 % coverage.

## Quick Start (Windows 11)

1. **Install prerequisites**
   - [Python 3.11.x](https://www.python.org/downloads/windows/) – enable “Add python.exe to PATH”.
   - [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) – required for `sounddevice`/`numpy`.
   - [Git for Windows](https://git-scm.com/download/win) (optional but recommended).

2. **Clone the repository**
   ```powershell
   git clone https://github.com/<your-org>/acoustic-modems.git
   cd acoustic-modems
   ```

3. **Create and activate a virtual environment**
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -e .[dev]
   ```
   If the optional Qt type stubs fail (`types-PySide6`), re-run without extras: `python -m pip install -e .`.

5. **Launch the GUI**
   ```powershell
   python -m amw.gui
   ```
   Or use `make gui` when GNU Make is available.

### Windows audio configuration tips

- Ensure your playback and recording devices are visible in *System Settings → Sound*.
- For loopback experiments, route output to input via hardware or software (e.g., VB-Audio Virtual Cable).
- Run the app in “Run as administrator” if exclusive device access is needed.

## Development Workflow

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Key commands:

- `make gui` – start the desktop application against local sources.
- `make test` – run the pytest suite with coverage.
- `make lint` / `make format` – enforce Ruff and Black style guides.
- `make typecheck` – execute `mypy` with the project’s strict settings.
- `make build` – produce the Windows installer via PyInstaller (outputs in `dist/`).

## Repository Layout

```
src/amw/
  gui/          # Qt application, panels, and bootstrap helpers
  io/           # audio I/O services and payload builders
  pipeline/     # orchestrator, conditioning, and artifact tracking
  plugins/      # shared plugin contracts and discovery utilities
modems/
  bfsk/         # reference BFSK modem (schema + defaults)
  template/     # scaffolding for new modem plugins
assets/         # icons, Qt resources, demo waveforms
tests/          # mirrors src/ layout; integration scenarios in tests/integration
scripts/        # helper scripts (e.g., updating golden vectors)
```

## Writing a Modem Plugin

1. Copy `modems/template/` to `modems/<your_modem>/`.
2. Implement `encode(payload: bytes, params: dict) -> EncodeOutput` and `decode(waveform: Array1D, params: dict) -> DecodeOutput`.
3. Provide `schema.py` returning `PARAM_SCHEMA` and `PARAM_DEFAULTS`, plus `schema.json`/`defaults.json`.
4. Update `metadata.json` and `README.md` inside the plugin describing capabilities.
5. Add unit tests that load the schema, encode a sample payload, and decode the simulated waveform.

Plugins are discovered automatically via `PluginRegistry`; surface meaningful metadata so the GUI can populate selectors and device defaults.

## Testing Strategy

- Unit tests live alongside the mirrored package tree (`tests/gui`, `tests/pipeline`, `tests/io`, `tests/plugins`).
- Loopback integration scenarios reside under `tests/integration/` and are gated by the `integration` mark.
- Maintain coverage with `pytest -q` (default args: `--cov=amw --cov-branch --cov-report=term-missing`).
- For audio changes, run `pytest -m integration` with appropriate hardware/virtual loopback.

## Troubleshooting

- **Missing `PySide6` on CI/headless** – The project includes a light stub so tests run without native Qt libraries. For full GUI functionality install the real PySide6 wheels.
- **`sounddevice` import fails** – Install PortAudio backends (`brew install portaudio` on macOS, `choco install portaudio` on Windows) or rely on the simulated paths.
- **SQLite module missing** – `sitecustomize.py` wires in `pysqlite3-binary` when the interpreter lacks sqlite support, enabling coverage reports.

## License

MIT License © Acoustic Modem Workbench Team.
