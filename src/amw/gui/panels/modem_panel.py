"""Modem selection and parameter management panel."""

from __future__ import annotations

import json
from typing import Any, Iterable

from .._qt import QLabel, QComboBox, QGroupBox, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout


class ModemPanel(QGroupBox):
    """Displays available modem plugins and exposes parameter load/save actions."""

    def __init__(self) -> None:
        super().__init__("Modem")
        self.metadata_label = QLabel("Select a modem to view details.")
        self.metadata_label.setWordWrap(True)
        self.modem_selector = QComboBox()
        self.load_button = QPushButton("Load Params…")
        self.save_button = QPushButton("Save Params…")
        self.param_editor = QTextEdit()
        self.param_editor.setPlainText("{}")
        self._build_ui()

    def _build_ui(self) -> None:
        button_row = QHBoxLayout()
        button_row.addWidget(self.load_button)
        button_row.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.metadata_label)
        layout.addWidget(self.modem_selector)
        layout.addLayout(button_row)
        layout.addWidget(self.param_editor)

    def set_available_modems(self, modem_names: Iterable[str]) -> None:
        """Populate the modem selector with discovered plugin names."""
        self.modem_selector.clear()
        names = list(modem_names)
        self.modem_selector.addItems(names)
        if names:
            self.modem_selector.setCurrentIndex(0)

    def set_metadata(self, *, description: str = "", sample_rate: int | None = None, version: str | None = None) -> None:
        """Update the descriptive label with plugin metadata."""
        segments: list[str] = []
        if version:
            segments.append(f"Version {version}")
        if sample_rate:
            segments.append(f"{sample_rate} Hz sample rate")
        if description:
            segments.append(description)
        self.metadata_label.setText("\n".join(segments) if segments else "Select a modem to view details.")

    def set_params(self, params: dict[str, Any]) -> None:
        """Render modem parameters as JSON for quick editing."""
        try:
            text = json.dumps(params, indent=2, sort_keys=True)
        except TypeError:
            text = "{}"
        self.param_editor.setPlainText(text)

    def current_params(self) -> dict[str, Any]:
        """Return the JSON-decoded parameter dictionary."""
        raw = self.param_editor.toPlainText().strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid parameter JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Modem parameters must be a JSON object.")
        return parsed

    def selected_modem(self) -> str | None:
        """Return the currently highlighted modem name, if any."""
        text = self.modem_selector.currentText().strip()
        return text or None
