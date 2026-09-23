"""Standalone entry point for the Settings dialog, launched by the COSMIC panel applet.

Runs as its own process, independent of the charm widget: it edits and saves
`~/.config/floatly/config.json`, and the running widget (if any) picks up
changes live via a file watcher. This lets the panel applet open Settings
without needing its own IPC channel into the widget process.
"""

from __future__ import annotations

import fcntl
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .config import Config
from .settings import SettingsDialog

LOCK_PATH = Path.home() / ".config" / "floatly" / "settings.lock"


def main() -> int:
    # avoid stacking up duplicate Settings windows if the panel icon is clicked
    # repeatedly; the lock file handle must stay open for the life of the process
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_file = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0  # another Settings window is already open

    app = QApplication(sys.argv)
    app.setApplicationName("Floatly Settings")

    config = Config.load()
    dialog = SettingsDialog(config, on_apply=lambda _config: None)
    dialog.finished.connect(app.quit)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
