"""Payload definition panel for text or file based transmissions."""

from __future__ import annotations

from .._qt import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)


class PayloadPanel(QGroupBox):
    """Allows the user to configure the payload contents for transmission."""

    def __init__(self) -> None:
        super().__init__("Payload")
        self.text_radio = QRadioButton("Text")
        self.file_radio = QRadioButton("File")
        self.text_radio.setChecked(True)
        self.mode_buttons = QButtonGroup(self)
        self.mode_buttons.addButton(self.text_radio)
        self.mode_buttons.addButton(self.file_radio)

        self.text_edit = QTextEdit()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select file…")
        self.file_browse_button = QPushButton("Browse…")
        self.crc_checkbox = QCheckBox("CRC")
        self.crc_checkbox.setChecked(True)
        self.length_label = QLabel("Length: 0 bytes")

        self._build_ui()
        self._connect_signals()
        self._update_visibility()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_radio)
        layout.addWidget(self.file_radio)

        layout.addWidget(self.text_edit)

        file_row = QHBoxLayout()
        file_row.addWidget(self.file_path_edit)
        file_row.addWidget(self.file_browse_button)
        layout.addLayout(file_row)

        control_row = QHBoxLayout()
        control_row.addWidget(self.crc_checkbox)
        control_row.addStretch(1)
        control_row.addWidget(self.length_label)
        layout.addLayout(control_row)

    def _connect_signals(self) -> None:
        self.mode_buttons.buttonClicked.connect(self._update_visibility)
        self.file_browse_button.clicked.connect(self._prompt_file)
        self.text_edit.textChanged.connect(self._update_length_label)
        self.file_path_edit.textChanged.connect(self._update_length_label)

    def _update_visibility(self) -> None:
        self.text_edit.setVisible(self.text_radio.isChecked())
        self.file_path_edit.setVisible(self.file_radio.isChecked())
        self.file_browse_button.setVisible(self.file_radio.isChecked())
        self._update_length_label()

    def _prompt_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Payload File")
        if file_path:
            self.file_path_edit.setText(file_path)

    def _update_length_label(self) -> None:
        if self.text_radio.isChecked():
            payload_bytes = len(self.text_edit.toPlainText().encode("utf-8"))
        else:
            payload_bytes = 0 if not self.file_path_edit.text() else "?"
        self.length_label.setText(f"Length: {payload_bytes} bytes")
