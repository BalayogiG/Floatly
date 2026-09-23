"""Charm shapes and their pendulum physics."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QPixmap

GRAVITY = 900.0  # px/s^2 equivalent, tuned for a pleasant swing speed
DAMPING = 0.6  # velocity damping so charms settle instead of swinging forever
GUST_CHANCE = 0.004  # per-frame probability of a small ambient air current
GUST_STRENGTH = 1.4
STRING_HIT_WIDTH = 10.0  # generous grab width for a visually 1.4px-thin string


@dataclass
class Charm:
    anchor_x: float
    string_length: float
    shape: str
    color: QColor
    size: float
    image: QPixmap | None = None
    angle: float = field(default_factory=lambda: random.uniform(-0.25, 0.25))
    angular_velocity: float = 0.0

    def bob_position(self, anchor_y: float) -> QPointF:
        x = self.anchor_x + self.string_length * math.sin(self.angle)
        y = anchor_y + self.string_length * math.cos(self.angle)
        return QPointF(x, y)

    def step(self, dt: float) -> None:
        # simple damped pendulum
        accel = -(GRAVITY / self.string_length) * math.sin(self.angle)
        accel -= DAMPING * self.angular_velocity
        self.angular_velocity += accel * dt
        self.angle += self.angular_velocity * dt

        if random.random() < GUST_CHANCE:
            self.angular_velocity += random.uniform(-GUST_STRENGTH, GUST_STRENGTH) * 0.05

    def nudge(self, strength: float = 2.2) -> None:
        self.angular_velocity += random.choice((-1, 1)) * strength

    def bob_radius(self) -> float:
        return self.size * 0.75 + 6

    def hit_test(self, point: QPointF, anchor_y: float) -> bool:
        bob = self.bob_position(anchor_y)
        r = self.bob_radius()
        dx = point.x() - bob.x()
        dy = point.y() - bob.y()
        return (dx * dx + dy * dy) <= r * r

    def interactive_region(self, anchor_y: float) -> QPainterPath:
        """The string + bob outline, in local widget coordinates.

        Used as the window's input mask so only these pixels receive mouse
        events and everything else (all the fully-transparent surrounding
        space in the window's bounding box) is click-through automatically.
        """
        anchor = QPointF(self.anchor_x, anchor_y)
        bob = self.bob_position(anchor_y)

        line = QPainterPath()
        line.moveTo(anchor)
        line.lineTo(bob)
        stroker = QPainterPathStroker()
        stroker.setWidth(STRING_HIT_WIDTH)
        region = stroker.createStroke(line)

        bob_path = QPainterPath()
        r = self.bob_radius()
        bob_path.addEllipse(bob, r, r)

        return region.united(bob_path)

    def draw(self, painter: QPainter, anchor_y: float) -> None:
        anchor = QPointF(self.anchor_x, anchor_y)
        bob = self.bob_position(anchor_y)

        string_pen = QPen(QColor(255, 255, 255, 150))
        string_pen.setWidthF(1.4)
        painter.setPen(string_pen)
        painter.drawLine(anchor, bob)

        painter.save()
        painter.translate(bob)
        rotation_deg = math.degrees(self.angle) * 0.5
        painter.rotate(rotation_deg)
        if self.image is not None and not self.image.isNull():
            w, h = self.image.width(), self.image.height()
            painter.drawPixmap(QPointF(-w / 2, -h / 2), self.image)
        else:
            _draw_shape(painter, self.shape, self.color, self.size)
        painter.restore()


def _draw_shape(painter: QPainter, shape: str, color: QColor, size: float) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    glow = QColor(color)
    glow.setAlpha(70)
    painter.setPen(QPen(glow, size * 0.12))

    half = size / 2

    if shape == "star":
        painter.drawPath(_star_path(half))
    elif shape == "heart":
        painter.drawPath(_heart_path(half))
    elif shape == "moon":
        painter.drawPath(_moon_path(half))
    elif shape == "drop":
        painter.drawPath(_drop_path(half))
    elif shape == "flower":
        _draw_flower(painter, half, color)
    else:  # gem / diamond fallback
        painter.drawPath(_gem_path(half))


def _star_path(r: float) -> QPainterPath:
    path = QPainterPath()
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.42
        points.append(QPointF(radius * math.cos(angle), -radius * math.sin(angle)))
    path.moveTo(points[0])
    for p in points[1:]:
        path.lineTo(p)
    path.closeSubpath()
    return path


def _heart_path(r: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(0, r * 0.35)
    path.cubicTo(-r * 1.3, -r * 0.6, -r * 0.4, -r * 1.3, 0, -r * 0.3)
    path.cubicTo(r * 0.4, -r * 1.3, r * 1.3, -r * 0.6, 0, r * 0.35)
    path.closeSubpath()
    return path


def _moon_path(r: float) -> QPainterPath:
    outer = QPainterPath()
    outer.addEllipse(QRectF(-r, -r, 2 * r, 2 * r))
    inner = QPainterPath()
    inner.addEllipse(QRectF(-r + r * 0.55, -r, 2 * r, 2 * r))
    return outer.subtracted(inner)


def _drop_path(r: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(0, -r)
    path.cubicTo(r * 1.1, r * 0.2, r * 0.75, r, 0, r)
    path.cubicTo(-r * 0.75, r, -r * 1.1, r * 0.2, 0, -r)
    path.closeSubpath()
    return path


def _gem_path(r: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(0, -r)
    path.lineTo(r, -r * 0.15)
    path.lineTo(r * 0.55, r)
    path.lineTo(-r * 0.55, r)
    path.lineTo(-r, -r * 0.15)
    path.closeSubpath()
    return path


def _draw_flower(painter: QPainter, r: float, color: QColor) -> None:
    petal = r * 0.6
    for i in range(5):
        angle = i * (2 * math.pi / 5)
        cx = petal * 0.65 * math.cos(angle)
        cy = petal * 0.65 * math.sin(angle)
        painter.drawEllipse(QRectF(cx - petal / 2, cy - petal / 2, petal, petal))
    center = QColor(255, 240, 200)
    painter.setBrush(center)
    painter.drawEllipse(QRectF(-r * 0.3, -r * 0.3, r * 0.6, r * 0.6))


SHAPES = ("star", "heart", "moon", "drop", "flower", "gem")
