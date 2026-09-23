"""Settings dialog: rope horizontal position, rope length, and the charm image."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from .config import Config, quit_running_widget

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.svg *.webp *.gif)"


class _SliderSpin(QHBoxLayout):
    """A slider paired with a spinbox that stay in sync, for direct-manipulation feel."""

    def __init__(self, minimum: int, maximum: int, value: int, suffix: str = "") -> None:
        super().__init__()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)

        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setSuffix(suffix)
        self.spin.setMinimumWidth(90)

        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)

        self.addWidget(self.slider, stretch=1)
        self.addWidget(self.spin)

    @property
    def valueChanged(self):  # noqa: N802 - Qt-style signal name
        return self.slider.valueChanged

    def value(self) -> int:
        return self.slider.value()


class SettingsDialog(QDialog):
    def __init__(self, config: Config, on_apply: Callable[[Config], None]) -> None:
        super().__init__()
        self.setWindowTitle("Floatly Settings")
        self.config = config
        self._on_apply = on_apply
        self._image_path: str | None = config.image_path

        screen_width = 1920
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            screen_width = screen.geometry().width()

        self.x_control = _SliderSpin(0, screen_width, config.x, " px")
        self.x_control.valueChanged.connect(self._live_apply)

        self.length_control = _SliderSpin(20, 800, int(config.rope_length), " px")
        self.length_control.valueChanged.connect(self._live_apply)

        self.click_through_check = QCheckBox(
            "Disable interaction entirely (by default, only the rope and charm\n"
            "itself are clickable — everywhere else already click-through)"
        )
        self.click_through_check.setChecked(config.click_through)
        self.click_through_check.toggled.connect(self._live_apply)

        self.image_label = QLabel(self._image_display_text())
        self.image_label.setWordWrap(True)
        browse_btn = QPushButton("Choose Image…")
        browse_btn.clicked.connect(self._choose_image)
        clear_btn = QPushButton("Use Default Charm")
        clear_btn.clicked.connect(self._clear_image)

        image_buttons = QHBoxLayout()
        image_buttons.addWidget(browse_btn)
        image_buttons.addWidget(clear_btn)

        form = QFormLayout()
        form.addRow("Horizontal position:", self.x_control)
        form.addRow("Rope length:", self.length_control)
        form.addRow("Charm image:", self.image_label)
        form.addRow("", image_buttons)
        form.addRow("", self.click_through_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        buttons.accepted.connect(self.close)

        quit_btn = QPushButton("Quit Floatly")
        quit_btn.clicked.connect(self._quit_widget)
        buttons.addButton(quit_btn, QDialogButtonBox.ButtonRole.DestructiveRole)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        # keep this dialog itself as a normal, focusable, WM-decorated window
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Dialog)

    def _image_display_text(self) -> str:
        return self._image_path if self._image_path else "(none — using default charm)"

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose a charm image", "", IMAGE_FILTER)
        if path:
            self._image_path = path
            self.image_label.setText(self._image_display_text())
            self._live_apply()

    def _clear_image(self) -> None:
        self._image_path = None
        self.image_label.setText(self._image_display_text())
        self._live_apply()

    def _current_config(self) -> Config:
        self.config.x = self.x_control.value()
        self.config.rope_length = float(self.length_control.value())
        self.config.image_path = self._image_path
        self.config.click_through = self.click_through_check.isChecked()
        return self.config

    def _live_apply(self, *_args: object) -> None:
        config = self._current_config()
        config.save()
        self._on_apply(config)

    def _quit_widget(self) -> None:
        found = quit_running_widget()
        if not found:
            QMessageBox.information(self, "Floatly", "Floatly isn't currently running.")
        self.close()
