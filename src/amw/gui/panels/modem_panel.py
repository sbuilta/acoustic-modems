"""Modem selection and parameter management panel."""

from __future__ import annotations

from typing import Iterable

from .._qt import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class ModemPanel(QGroupBox):
    """Displays available modem plugins and exposes parameter load/save actions."""

    def __init__(self) -> None:
        super().__init__("Modem")
        self.modem_selector = QComboBox()
        self.load_button = QPushButton("Load Params…")
        self.save_button = QPushButton("Save Params…")
        self._parameter_form = QWidget()
        self._parameter_form.setLayout(QFormLayout())
        self._build_ui()

    def _build_ui(self) -> None:
        button_row = QHBoxLayout()
        button_row.addWidget(self.load_button)
        button_row.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.modem_selector)
        layout.addLayout(button_row)
        layout.addWidget(self._parameter_form)

    def set_available_modems(self, modem_names: Iterable[str]) -> None:
        """Populate the modem selector with discovered plugin names."""
        self.modem_selector.clear()
        self.modem_selector.addItems(list(modem_names))

    def parameter_form(self) -> QWidget:
        """Return the container widget that will host generated parameter controls."""
        return self._parameter_form
