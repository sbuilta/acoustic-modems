"""Debug visualization panel for captured and decoded artifacts."""

from __future__ import annotations

from collections import deque
import json
from typing import Any, Iterable

import numpy as np
import numpy.typing as npt

from amw.gui import _qt as qt_helpers

from .._qt import QLabel, QFormLayout, QGroupBox, QTabWidget, QVBoxLayout, QWidget

try:  # pragma: no cover - pyqtgraph exercised only when the real Qt stack is available
    if getattr(qt_helpers, "_use_stub", False):
        raise ImportError("Qt stubs active")
    import pyqtgraph as pg
except Exception:  # pragma: no cover - exercised in headless tests
    pg = None

try:  # pragma: no cover - scipy is optional during tests
    from scipy.signal import hilbert as _hilbert
except Exception:  # pragma: no cover - exercised when SciPy is unavailable
    _hilbert = None

Array1D = npt.NDArray[np.float32]
ComplexArray = npt.NDArray[np.complex64]


class DebugPanel(QWidget):
    """Contains tabs for waveform, spectrogram, constellation, and metrics."""

    def __init__(self) -> None:
        super().__init__()
        self.tabs = QTabWidget()
        self.constellation = ConstellationView()
        self.metrics = MetricsView()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs.addTab(self._placeholder("Waveform view coming soon"), "Waveform")
        self.tabs.addTab(self._placeholder("Spectrogram view coming soon"), "Spectrogram")
        self.tabs.addTab(self.constellation, "Constellation")
        self.tabs.addTab(self.metrics, "Metrics")

        layout.addWidget(self.tabs)

    def update_constellation(self, samples: Array1D | None, sample_rate: int | None = None) -> None:
        """Update the constellation view with the latest recorded signal."""
        self.constellation.update_samples(samples, sample_rate)

    def log_status(self, level: str, message: str) -> None:
        """Append a status entry to the metrics view."""
        self.metrics.log_status(level, message)

    def record_transmit(self, sample_count: int | None, sample_rate: int | None = None) -> None:
        """Update transmit metrics after a playback event."""
        self.metrics.record_transmit(sample_count, sample_rate)

    def record_receive(
        self,
        sample_count: int,
        sample_rate: int,
        *,
        triggered: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update receive metrics after capturing audio."""
        self.metrics.record_receive(sample_count, sample_rate, triggered=triggered, metadata=metadata)

    def record_decode_attempt(
        self,
        *,
        success: bool,
        payload_bytes: int | None = None,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Track decode attempt statistics."""
        self.metrics.record_decode_attempt(success=success, payload_bytes=payload_bytes, metrics=metrics, error=error)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        widget = QWidget()
        placeholder = QLabel(text)
        placeholder.setObjectName("placeholder")
        placeholder.setWordWrap(True)
        child_layout = QVBoxLayout(widget)
        child_layout.addWidget(placeholder)
        child_layout.addStretch(1)
        return widget


class ConstellationView(QWidget):
    """Scatter plot helper that monitors recorded signals."""

    _max_points = 5000

    def __init__(self) -> None:
        super().__init__()
        self._status = QLabel("Awaiting recording...")
        self._scatter: object | None = None
        self._plot_widget: QWidget | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        plot = self._build_plot()
        if plot is not None:
            layout.addWidget(plot)
        else:
            placeholder = QLabel("Constellation plotting requires PySide6 + pyqtgraph.")
            placeholder.setWordWrap(True)
            placeholder.setObjectName("constellation-placeholder")
            layout.addWidget(placeholder)

        self._status.setObjectName("constellation-status")
        layout.addWidget(self._status)

    def _build_plot(self) -> QWidget | None:
        if pg is None:
            return None

        plot = pg.PlotWidget()
        plot.setBackground("k")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel("left", "Q (imag)")
        plot.setLabel("bottom", "I (real)")
        plot.setAspectLocked(False)

        scatter = pg.ScatterPlotItem(
            pen=None,
            brush=pg.mkBrush("#4BA0DC"),
            size=5.0,
            symbol="o",
            pxMode=True,
        )
        plot.addItem(scatter)
        self._scatter = scatter
        self._plot_widget = plot
        return plot

    def update_samples(self, samples: Array1D | None, sample_rate: int | None = None) -> None:
        """Render a new constellation from the provided samples."""
        if samples is None or samples.size == 0:
            self._clear_plot("No recording available yet.")
            return

        complex_samples = _to_complex(samples)
        if complex_samples.size == 0:
            self._clear_plot("Signal too short for constellation view.")
            return

        real, imag, stride = _decimate_points(complex_samples, self._max_points)
        if real.size == 0:
            self._clear_plot("Signal too short for constellation view.")
            return

        if self._scatter is not None:
            self._scatter.setData(real, imag)

        sr_msg = f" @ {sample_rate} Hz" if sample_rate else ""
        self._status.setText(f"Showing {real.size} pts (stride {stride}){sr_msg}")

    def _clear_plot(self, message: str) -> None:
        if self._scatter is not None:
            self._scatter.clear()
        self._status.setText(message)

    def status_text(self) -> str:
        """Expose the current status for tests and debug labels."""
        return self._status.text()


def _to_complex(samples: Array1D) -> ComplexArray:
    """Convert a real waveform into an analytic complex representation."""
    data = np.asarray(samples, dtype=np.float32)
    if data.size < 2:
        return np.array([], dtype=np.complex64)

    if _hilbert is not None and data.size >= 4:
        analytic = _hilbert(data)
        return np.asarray(analytic, dtype=np.complex64)

    even = data[: data.size - (data.size % 2)]
    if even.size == 0:
        return np.array([], dtype=np.complex64)
    iq = even.reshape(-1, 2)
    complex_samples = iq[:, 0].astype(np.float32) + 1j * iq[:, 1].astype(np.float32)
    return np.asarray(complex_samples, dtype=np.complex64)


def _decimate_points(points: Iterable[complex], max_points: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Down-sample the complex samples to a manageable scatter size."""
    complex_array = np.asarray(points, dtype=np.complex64)
    if complex_array.size == 0:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32), 1

    stride = max(1, int(np.ceil(complex_array.size / max_points))) if max_points > 0 else 1
    decimated = complex_array[::stride]
    return decimated.real.astype(np.float32), decimated.imag.astype(np.float32), stride


class MetricsView(QWidget):
    """Summarizes pipeline status messages and key transmit/receive metrics."""

    _status_limit = 10

    def __init__(self) -> None:
        super().__init__()
        self._status_entries: deque[str] = deque(maxlen=self._status_limit)
        self._tx_runs = 0
        self._rx_runs = 0
        self._decode_attempts = 0
        self._decode_successes = 0
        self._decode_failures = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self._status_label = QLabel("No status updates yet.")
        self._status_label.setWordWrap(True)
        status_layout.addWidget(self._status_label)

        txrx_group = QGroupBox("Transmit / Receive")
        txrx_form = QFormLayout(txrx_group)
        self._tx_label = QLabel("No transmits yet.")
        self._rx_label = QLabel("No captures yet.")
        txrx_form.addRow("Transmit", self._tx_label)
        txrx_form.addRow("Receive", self._rx_label)

        decode_group = QGroupBox("Decode")
        decode_form = QFormLayout(decode_group)
        self._decode_summary = QLabel("No attempts yet.")
        self._decode_metrics = QLabel("—")
        self._decode_metrics.setWordWrap(True)
        decode_form.addRow("Attempts", self._decode_summary)
        decode_form.addRow("Metrics", self._decode_metrics)

        layout.addWidget(status_group)
        layout.addWidget(txrx_group)
        layout.addWidget(decode_group)
        layout.addStretch(1)

    def log_status(self, level: str, message: str) -> None:
        """Track status messages with bounded history."""
        entry = f"[{level.upper()}] {message}"
        self._status_entries.append(entry)
        combined = "\n".join(self._status_entries) if self._status_entries else "No status updates yet."
        self._status_label.setText(combined)

    def record_transmit(self, sample_count: int | None, sample_rate: int | None = None) -> None:
        """Update transmit summary."""
        self._tx_runs += 1
        samples = int(sample_count or 0)
        sr = f" @ {sample_rate} Hz" if sample_rate else ""
        self._tx_label.setText(f"{self._tx_runs} event(s); last waveform {samples} samples{sr}")

    def record_receive(
        self,
        sample_count: int,
        sample_rate: int,
        *,
        triggered: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update receive summary."""
        self._rx_runs += 1
        flags: list[str] = []
        if triggered:
            flags.append("triggered")
        if metadata:
            if metadata.get("simulated"):
                flags.append("simulated")
            channels = metadata.get("channels")
            if channels:
                flags.append(f"{channels}ch")
        suffix = f" ({', '.join(flags)})" if flags else ""
        self._rx_label.setText(
            f"{self._rx_runs} capture(s); last {int(sample_count)} samples @ {sample_rate} Hz{suffix}"
        )

    def record_decode_attempt(
        self,
        *,
        success: bool,
        payload_bytes: int | None = None,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Update decode attempt statistics."""
        self._decode_attempts += 1
        if success:
            self._decode_successes += 1
        else:
            self._decode_failures += 1

        payload_info = f"; last payload {int(payload_bytes or 0)} bytes" if success else ""
        error_info = f"; last error: {error}" if (not success and error) else ""
        summary = (
            f"{self._decode_attempts} attempt(s); "
            f"{self._decode_successes} success, {self._decode_failures} failure{payload_info}{error_info}"
        )
        self._decode_summary.setText(summary)

        if metrics:
            self._decode_metrics.setText(_stringify_metrics(metrics))
        elif not success and error:
            self._decode_metrics.setText(error)
        else:
            self._decode_metrics.setText("—")

    def status_text(self) -> str:
        """Expose status feed content for tests."""
        return self._status_label.text()

    def tx_summary(self) -> str:
        """Expose latest transmit summary for tests."""
        return self._tx_label.text()

    def rx_summary(self) -> str:
        """Expose latest receive summary for tests."""
        return self._rx_label.text()

    def decode_summary(self) -> str:
        """Expose decode summary for tests."""
        return self._decode_summary.text()

    def decode_metrics_text(self) -> str:
        """Expose decode metrics text for tests."""
        return self._decode_metrics.text()


def _stringify_metrics(metrics: dict[str, Any]) -> str:
    """Serialize plugin metrics into a readable string."""
    try:
        return json.dumps(metrics, sort_keys=True, default=str)
    except Exception:
        return str(metrics)
