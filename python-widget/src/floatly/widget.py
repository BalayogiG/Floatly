"""A single charm hanging from the very top of the screen."""

from __future__ import annotations

import signal

from PySide6.QtCore import QFileSystemWatcher, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from .charms import Charm
from .config import CONFIG_PATH, Config, write_pid
from .xshape import InputShaper

FRAME_MS = 16  # ~60fps
ANCHOR_Y = 2  # sits right at the top edge of the screen
MIN_WIDTH = 120
SWING_PADDING = 24  # extra px of slack beyond the worst-case swing extent


class CharmWidget(QWidget):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.charm = self._build_charm()

        self._drag_origin: QPointF | None = None
        self._drag_moved = False
        self._dragging_charm = False
        self._pressed_on_bob = False

        try:
            self._shaper: InputShaper | None = InputShaper()
        except RuntimeError:
            self._shaper = None  # degrade to a fully-interactive window

        self._relayout()
        self.set_click_through(config.click_through)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(FRAME_MS)

        # so `floatly-settings`, a separate process, can push live edits to us
        self.config.save()
        write_pid()
        self._watcher = QFileSystemWatcher([str(CONFIG_PATH)], self)
        self._watcher.fileChanged.connect(self._on_config_file_changed)

        # let Python's own signal handler for SIGTERM actually run despite the Qt event loop
        self._signal_wakeup = QTimer(self)
        self._signal_wakeup.timeout.connect(lambda: None)
        self._signal_wakeup.start(200)
        signal.signal(signal.SIGTERM, lambda *_: QApplication.instance().quit())

    # -- construction from config -----------------------------------------------------
    def _build_charm(self) -> Charm:
        image = None
        size = self.config.charm_size
        if self.config.image_path:
            pixmap = QPixmap(self.config.image_path)
            if not pixmap.isNull():
                target = int(self.config.charm_size)
                image = pixmap.scaled(
                    target,
                    target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                size = max(image.width(), image.height())
        return Charm(
            anchor_x=0.0,  # set by _relayout
            string_length=self.config.rope_length,
            shape=self.config.shape,
            color=QColor(self.config.color),
            size=size,
            image=image,
        )

    def apply_config(self, config: Config) -> None:
        """Re-read config (rope length / image / shape / color may have changed) and re-layout."""
        self.config = config
        angle, angular_velocity = self.charm.angle, self.charm.angular_velocity
        self.charm = self._build_charm()
        self.charm.angle, self.charm.angular_velocity = angle, angular_velocity
        self._relayout()
        self.set_click_through(config.click_through)

    def _on_config_file_changed(self, path: str) -> None:
        # some editors/writers replace the file rather than modify it in place,
        # which drops it from the watch list — re-add if needed
        if path not in self._watcher.files() and CONFIG_PATH.exists():
            self._watcher.addPath(path)
        self.apply_config(Config.load())

    # -- layout -----------------------------------------------------
    def _relayout(self) -> None:
        # the bob can swing out to a full sin(angle)=1, i.e. a full string_length
        # to either side of the anchor, so the window must be wide enough to hold
        # that plus the charm's own radius or it clips (hides) the charm mid-swing
        half_width = self.config.rope_length + self.charm.bob_radius() + SWING_PADDING
        width = max(MIN_WIDTH, int(half_width * 2))
        height = int(ANCHOR_Y + self.config.rope_length + self.charm.size + 24)
        self.charm.anchor_x = width / 2
        self.charm.string_length = self.config.rope_length
        self.setFixedSize(width, height)
        self._place_at_x(self.config.x)

    def _place_at_x(self, x: int) -> None:
        screen = QGuiApplication.primaryScreen()
        top = 0
        if screen is not None:
            top = screen.geometry().top()
        self.move(int(x - self.width() / 2), top)

    # -- animation ----------------------------------------------------
    def _tick(self) -> None:
        dt = FRAME_MS / 1000.0
        self.charm.step(dt)
        self.update()
        self._update_mask()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.charm.draw(painter, ANCHOR_Y)

    # -- click-through everywhere except the rope + charm --------------------
    def _update_mask(self) -> None:
        if self.config.click_through or self._shaper is None:
            return
        region_path = self.charm.interactive_region(ANCHOR_Y)
        polygon = region_path.toFillPolygon().toPolygon()
        points = [(p.x(), p.y()) for p in polygon]
        if len(points) >= 3:
            self._shaper.set_input_polygon(int(self.winId()), points)

    # -- interaction ----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        self._drag_origin = pos
        self._drag_moved = False
        self._pressed_on_bob = self.charm.hit_test(pos, ANCHOR_Y)
        # the input mask already keeps us from receiving events outside the
        # string/bob, so any press here is fair game to start a drag
        self._dragging_charm = True

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is None or not self._dragging_charm:
            return
        delta = event.position() - self._drag_origin
        if abs(delta.x()) > 4:
            self._drag_moved = True
            new_x = self.config.x + int(delta.x())
            self.config.x = new_x
            self._place_at_x(new_x)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._drag_moved and self._pressed_on_bob:
            self.charm.nudge()
        elif self._drag_moved:
            self.config.save()
        self._drag_origin = None
        self._drag_moved = False
        self._dragging_charm = False
        self._pressed_on_bob = False

    # -- public actions ----------------------------------------------------
    def nudge(self) -> None:
        self.charm.nudge()

    def set_click_through(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        self.show()
        self._update_mask()

