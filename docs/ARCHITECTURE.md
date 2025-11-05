# Acoustic Modem Workbench Architecture (Scaffolding)

This document tracks how the implemented scaffolding maps to the system design in `PROPOSAL.md`.

- **GUI Shell (`src/amw/gui`)**: provides the Qt entry point, panels for modem/payload/audio controls, pipeline buttons, and a placeholder debug tab widget.
- **Pipeline (`src/amw/pipeline`)**: defines state models plus a `PipelineOrchestrator` coordinating build → transmit → record → condition → decode. Conditioning currently normalizes input as a stub.
- **I/O (`src/amw/io`)**: contains an `AudioService` abstraction (with simulation fallback) and a payload builder that supports text/file sources with optional CRC append.
- **Plugins (`src/amw/plugins`)**: codifies the modem contract, schema helpers, and dynamic discovery of plugin directories under `modems/`.
- **Reference Modem (`modems/bfsk`)**: ships a minimal BFSK encoder/decoder along with JSON schema/defaults, README, and metadata.
- **Testing (`tests/`)**: mirrors the package tree, adds GUI instantiation checks, exercizes the pipeline orchestrator with a dummy audio service, validates schema utilities, and includes an integration placeholder.

Future work will flesh out DSP algorithms, persist user sessions, and connect the GUI to runtime pipeline services.
