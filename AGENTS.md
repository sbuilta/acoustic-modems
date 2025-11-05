# Repository Guidelines

## Project Structure & Module Organization
- Keep source under `src/amw/` with subpackages: `gui/`, `pipeline/`, `io/`, and `plugins/`.
- Place modem plugins in `modems/<plugin_name>/` exporting `encode`, `decode`, and `schema.py`.
- Mirror package tree in `tests/` (e.g., `tests/pipeline/test_conditioner.py`) and keep integration scenarios in `tests/integration/`.
- Store Qt assets, icons, and sample audio in `assets/`, grouped by feature to simplify packaging.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates the local workflow environment (target Python 3.11).
- `python -m pip install -e .[dev]` installs runtime plus lint/test tooling.
- `make gui` (or `python -m amw.gui`) launches the desktop app against the current workspace.
- `make test` (shortcut for `pytest -q`) runs the test suite; use `pytest -m integration` before shipping audio-facing changes.
- `make build` packages the Windows installer via PyInstaller with outputs in `dist/`.

## Coding Style & Naming Conventions
- Auto-format with `black` (120-char line width) and lint with `ruff`; run both before every commit.
- Prefer type hints everywhere and keep `mypy` clean; silence issues with local `# pragma: no cover` only when justified.
- Use snake_case for functions, lower_case_with_underscores for module files, and PascalCase for Qt/Pydantic classes.
- Configuration and payload schemas ship as JSON, named `schema.json` and `defaults.json` beside each plugin.

## Testing Guidelines
- Write fast unit tests per module and heavier loopback tests under `tests/integration/`.
- Keep golden vector WAVs in `tests/data/golden_vectors/` with README metadata; regenerate via `python scripts/update_vectors.py`.
- New functionality must include regression tests and maintain ≥85% branch coverage (`pytest --cov=amw --cov-branch`).
- When adding device-specific fixes, capture failing audio traces in `tests/data/devices/<device_id>/`.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (e.g., `feat(gui): add modem selector`) and keep subject ≤72 chars.
- Squash work-in-progress commits locally; leave PRs <500 LOC unless coordinating with maintainers.
- Each PR description states scope, test evidence, and links to tracking issues; attach debug screenshots when UI or plots change.
- Tag reviewers based on area ownership (GUI, pipeline, plugins) and wait for CI green before asking for merge.

## Plugin Development Notes
- Start each plugin from `modems/template/` and document capabilities in `README.md` plus `metadata.json`.
- Surface preamble and conditioning hooks through the shared `PluginContract` so the GUI can arm triggers automatically.
- Provide unit tests that deserialize the plugin’s schema, encode a sample payload, and decode the emitted waveform to parity bytes.
