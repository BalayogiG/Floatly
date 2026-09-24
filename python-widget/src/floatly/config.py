"""Persisted user settings: where the rope hangs, how long it is, what's on it."""

from __future__ import annotations

import json
import os
import signal
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "floatly" / "config.json"
PID_PATH = Path.home() / ".config" / "floatly" / "widget.pid"

DEFAULT_SHAPE = "star"
DEFAULT_COLOR = "#FFB6C1"


@dataclass
class Config:
    x: int = 200  # horizontal position of the rope's anchor, in screen pixels from the left
    rope_length: float = 160.0
    image_path: str | None = None  # custom charm image; None falls back to a drawn shape
    charm_size: float = 40.0  # max dimension in px, for both the drawn shape and a custom image
    shape: str = DEFAULT_SHAPE
    color: str = DEFAULT_COLOR
    click_through: bool = False

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                fields = {f for f in cls.__dataclass_fields__}
                return cls(**{k: v for k, v in data.items() if k in fields})
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return cls()

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2))


def write_pid() -> None:
    """Record the running widget's PID so `floatly-settings` can ask it to quit."""
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()))


def quit_running_widget() -> bool:
    """Ask a running widget process to exit gracefully. Returns whether one was found."""
    if not PID_PATH.exists():
        return False
    try:
        pid = int(PID_PATH.read_text().strip())
        os.kill(pid, signal.SIGTERM)
    except (ValueError, ProcessLookupError, PermissionError):
        return False
    return True
