## Project Proposal — **Acoustic Modem Workbench (AMW)**

**Goal.** Build a Python desktop application for **fast iteration** on acoustic modem designs communicating between two Windows PCs through speakers/microphones (or loopback). The app exposes **modem selection**, **data payload definition**, and **Tx/Rx audio interfaces**, and provides a one‑click pipeline: **Build → Transmit → Record/Condition → Decode → Debug**.

### 1) Users & Primary Use Cases

* **DSP/Comm engineers & researchers** prototyping new modems (FSK, PSK, OFDM variants).
* **Lab/field testers** sending short packets PC‑to‑PC to evaluate robustness, throughput, BER, and latency.
* **Educators** demonstrating digital communications over audio.

### 2) Success Criteria (what “done” looks like)

* Swap modem plugins without code changes; load/save parameter sets via the GUI.
* Send text or file payload; generate, play, record, condition, and decode packets end‑to‑end.
* Select Windows audio devices for playback/recording.
* Observe detailed debug artifacts (time waveform, spectrogram, metrics, logs) per step.
* Reasonable defaults so a new user can **send/receive a packet within 5 minutes**.

---

## Functional Requirements → Design Mapping

| Requirement (yours)                                            | Proposed Design                                                                                                                 |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Dropdown + buttons to load/save modem parameters               | **Modem Panel** with dropdown of discovered plugins; **Load/Save** buttons persist JSON parameter sets (with schema & version). |
| Expose relevant modem parameters for review/edit               | **Auto‑generated parameter forms** from each plugin’s JSON schema (types, ranges, tooltips).                                    |
| Data definition: Text or File payload                          | **Payload Panel**: radio buttons “Text / File”, text box or file picker; length displayed; optional CRC toggle.                 |
| Create transmit waveforms from selected modem/settings/payload | **Tx Engine**: `plugin.encode(payload, params) → np.ndarray` @ selected Fs; writes *.wav* and sends to Audio I/O.               |
| “Tx” button plays audio packet                                 | **Tx Button**: synchronous playback via PortAudio (shared mode) with gain control and optional pre‑TX calibration tone.         |
| “Rx Arm” (sound‑trigger) + “Rx Now” (immediate record)         | **Rx Engine**: energy/preamble trigger path for Arm; immediate capture path for Now; both write raw *.wav*.                     |
| Select Windows playback/recording devices                      | **Audio Panel**: enumerates PortAudio devices (WASAPI), sample rates, channels; persists user choices.                          |
| “Condition” button normalizes & trims to packet                | **Conditioner**: band‑limit → envelope → preamble cross‑correlation → trim → RMS normalize → save *.wav*.                       |
| “Decode” button uses current modem                             | **Decoder**: `plugin.decode(wav, params) → bytes, metrics`, verifies CRC; shows text preview; saves file output.                |
| Debug screen showing results                                   | **Debug Panel**: time series, spectrogram, constellation (if provided), trigger markers, logs, metrics (SNR/BER/Packet time).   |

---

## System Architecture

```
┌──────────────────────── GUI (Qt for Python / PySide6) ───────────────────────┐
│ Modem Panel  | Payload Panel | Audio Panel | Transport Buttons | Debug Panel │
└──────────────────────────────────────────────────────────────────────────────┘
                 │             │             │            │         ▲
                 ▼             ▼             ▼            ▼         │
          ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐   │
          │ Modem API │  │ Payload   │  │ Audio I/O │  │ Tx/Rx  │   │
          │  Plugins  │  │ Builder   │  │ (sounddevice/PortAudio) │ │
          └────┬──────┘  └────┬──────┘  └───┬───────┘  └──┬─────┘   │
               │              │               │             │        │
               │        ┌─────▼──────┐  ┌─────▼──────┐  ┌───▼────┐  │
               │        │ Conditioner│  │ Decoder    │  │ Logger  │  │
               │        └────────────┘  └────────────┘  └─────────┘  │
               └──────────────────────────────────────────────────────┘
```

### Key Components

* **GUI:** PySide6 (Qt for Python) for robust widgets, async signals/slots, and embeddable matplotlib plots.
* **Audio I/O:** `sounddevice` (PortAudio backend). Enumerate WASAPI devices, sample rates (e.g., 48 kHz default), channels (mono Rx recommended).
* **Modem Plugin API:** Python entry points or plugin directory (`/modems`). Each plugin bundles:

  * `PARAMS_SCHEMA` (JSON Schema)
  * `default_params()`
  * `encode(payload_bytes, params, fs) -> waveform_float32`
  * `detect_start(rx_wav, params, fs) -> sample_index, metrics` *(optional; override default trigger)*
  * `decode(rx_wav, params, fs) -> bytes, metrics, (optional) viz data`
* **Payload Builder:** Handles “Text/File”, header (type, length, checksum), optional whitening, **CRC32**.
* **Conditioner:** Optional band‑pass (plugin‑hinted), Hilbert envelope or moving‑RMS, **preamble correlation** (e.g., Barker/LFM), trim to [start, start+Tpacket], normalize to target RMS.
* **Debug & Logging:** JSONL per run (params, device IDs, metrics), plus saved PNGs of plots. Exportable zipped “experiment bundle”.

---

## UX / Screen Layout

* **Top Bar:** Project file, **Load/Save Parameters**, **Modem** dropdown, **Sample Rate**, **Tx Gain**, **Record Level Meter**.
* **Left Pane (Modem Panel):** Auto‑generated modem parameters with validation and tooltips; **Revert to Defaults** button.
* **Center (Payload Panel):** Radio “Text / File”; text box or file picker; show payload bytes & CRC; **Build Only** button.
* **Right (Audio Panel & Transport):** Playback & Recording device dropdowns; buffer size; **Tx**, **Rx Arm**, **Rx Now**, **Condition**, **Decode** buttons; progress/status line.
* **Bottom (Debug Panel):** Tabs: **Timeline** (with trigger markers), **Spectrogram**, **Constellation** (if provided), **Logs & Metrics** (SNR, BER, timing), **Decoded Output** (text preview or file path).

---

## Data & File Conventions

* **Waveforms:** 32‑bit float internally; 16‑bit PCM *.wav* on disk for compatibility.
* **Project:** `*.amw.json` capturing current modem id, parameter set, device IDs, Fs, last payload path, and version.
* **Runs:** `/runs/YYYYMMDD_HHMMSS/` with `tx.wav`, `rx_raw.wav`, `rx_conditioned.wav`, `decode.json`, `debug/*.png`, `params.json`.

---

## Proposed Tech Stack

* Python 3.11+
* **PySide6** (Qt for Python), **matplotlib** (embedded plots)
* **numpy/scipy**, **numba** (optional acceleration)
* **sounddevice** (PortAudio) for WASAPI device control
* **pydantic** or **jsonschema** for parameter validation
* **pytest** for tests; **mypy** for type hints

---

## Example Plugin Skeleton (illustrative)

```python
# modems/bfsk/__init__.py
PARAMS_SCHEMA = {
  "title": "BFSK Params",
  "type": "object",
  "properties": {
    "f0": {"type": "number", "minimum": 100, "maximum": 18000, "default": 1200},
    "f1": {"type": "number", "minimum": 100, "maximum": 18000, "default": 2200},
    "baud": {"type": "number", "minimum": 10, "maximum": 2000, "default": 200},
    "preamble": {"type": "string", "default": "10101010"},
    "rolloff_ms": {"type": "number", "default": 5.0}
  },
  "required": ["f0","f1","baud"]
}

def default_params():
    return {k: v.get("default") for k, v in PARAMS_SCHEMA["properties"].items()}

def encode(payload_bytes, params, fs):
    # 1) build bitstream with preamble + header + CRC
    # 2) map bits to f0/f1, shape with raised-cosine edges (rolloff_ms)
    # 3) return float32 waveform
    ...

def detect_start(rx, params, fs):
    # Optional: correlate to BFSK preamble energy; return start index & metrics
    ...

def decode(rx_packet, params, fs):
    # 1) symbol timing recovery
    # 2) BFSK demod (goertzel or quadrature)
    # 3) dewhiten, verify CRC; return (bytes, {"ber":..., "snr_est":...})
    ...
```

---

## Triggers & Conditioning (algorithms at a glance)

* **Rx Arm trigger (default):**
  Short‑time energy (20–40 ms window), Schmitt thresholds, minimum hold time; optional band‑limit first. If the modem defines a **preamble correlator**, prefer that for robust start detection.

* **Condition:**

  1. Optional band‑pass (plugin hint).
  2. Envelope (Hilbert or moving RMS).
  3. Preamble cross‑correlation → start index; trim [start, start + Tpacket * (1+margin)].
  4. Normalize to target RMS (e.g., −12 dBFS).
  5. Save `rx_conditioned.wav` and mark cut points in debug plot.

---

## Non‑Functional Considerations

* **Determinism & Reproducibility:** All parameters saved with each run; seed whitening/LFSR.
* **Latency vs. Simplicity:** Start with blocking playback/record; move to callback streams only if needed.
* **Safety:** Output gain limiter; prevent large DC offsets; show clipping indicator.
* **Extensibility:** Hot reload plugins during runtime (dev mode) to shorten iteration loops.

---

## Testing Strategy

* **Unit tests:** payload pack/unpack, CRC, parameter validation, conditioning functions.
* **Integration tests:** loopback via **Virtual Audio Cable** and via a real speaker/mic in a quiet room.
* **Golden vectors:** known waveforms per modem with expected decoded bytes.
* **Device matrix:** at least 2 common sample rates (44.1/48 kHz), mono vs stereo capture.

---

## Risks & Mitigations

* **Device quirks / resampling:** Use WASAPI shared mode first; verify actual Fs; warn if host-resampled.
* **Room acoustics & multipath:** Keep preamble robust (Barker/LFM) and make its detector overridable per plugin.
* **Clock drift between PCs:** Include preamble and (optional) pilot for timing; keep packets short in v1.
* **User gain staging:** Provide input meter and auto‑level hints; keep target RMS normalization consistent.

---

## Phased Delivery (without dates)

**Phase 1 — Scaffold & One Modem**

* App shell, device selection, parameter load/save, Text payload, BFSK plugin, Tx/Rx Now, simple trigger, Condition, Decode, Debug plots.

**Phase 2 — Robustness & Files**

* File payload support, CRC, preamble correlator, improved conditioning, Arm trigger, run bundles, metrics dashboard.

**Phase 3 — Extensibility & QoL**

* Second modem (e.g., QPSK with costas/timing), plugin hot‑reload (dev mode), parameter validation UI polish, export debug report.

**Phase 4 — Advanced (optional)**

* FEC (e.g., Hamming), OFDM modem, parameter sweep runner, simulation mode (AWGN/multipath) without audio hardware.

---

## Deliverables

* Installable app (PyInstaller) for Windows 10/11.
* Source code repository with README, developer docs, and examples.
* At least **two reference modem plugins** (BFSK; QPSK or 4FSK).
* Automated tests and a few “golden vector” waveforms.
* Sample parameter packs and demo projects.

---

## Scope Refinement — 5 Practical Suggestions

1. **Start with one reference modem (BFSK) and a fixed sample rate (48 kHz).**
   Keeping v1 to a single, robust modem and one Fs reduces UI and DSP edge cases while you harden the pipeline (triggering, conditioning, decode).

2. **Require each modem to provide a JSON Schema for its parameters.**
   This enables **automatic, validated UI forms** and portable parameter packs. It’s a small discipline that pays off immediately.

3. **Make the preamble contract explicit and mandatory in the plugin API.**
   Define a standard “preamble bytes → waveform” and “preamble correlate()” hook. Conditioning and triggering become reliable across modems.

4. **Defer FEC and advanced equalization to a later phase.**
   Keep v1 focused on clean packet delivery with CRC only. Add FEC/ISI handling once the baseline toolchain is stable and measurable.

5. **Include a Simulation/Loopback mode early.**
   Support “no hardware” testing (file‑in/file‑out and/or Virtual Audio Cable). This speeds iteration on encode/decode logic without fighting room acoustics.
