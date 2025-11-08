"""Debug visualization panel for captured and decoded artifacts."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import numpy.typing as npt

from amw.gui import _qt as qt_helpers

from .._qt import QLabel, QTabWidget, QVBoxLayout, QWidget

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
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs.addTab(self._placeholder("Waveform view coming soon"), "Waveform")
        self.tabs.addTab(self._placeholder("Spectrogram view coming soon"), "Spectrogram")
        self.tabs.addTab(self.constellation, "Constellation")
        self.tabs.addTab(self._placeholder("Metrics view coming soon"), "Metrics")

        layout.addWidget(self.tabs)

    def update_constellation(self, samples: Array1D | None, sample_rate: int | None = None) -> None:
        """Update the constellation view with the latest recorded signal."""
        self.constellation.update_samples(samples, sample_rate)

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
