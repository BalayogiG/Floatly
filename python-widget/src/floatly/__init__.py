"""Floatly: a tiny digital charm that hangs and swings from the top of your screen."""

import sys

from PySide6.QtWidgets import QApplication

from .config import CONFIG_PATH, PID_PATH, Config
from .widget import CharmWidget


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Floatly")
    app.aboutToQuit.connect(lambda: PID_PATH.unlink(missing_ok=True))

    is_first_run = not CONFIG_PATH.exists()
    config = Config.load()
    if is_first_run:
        screen = app.primaryScreen()
        if screen is not None:
            config.x = screen.geometry().width() // 2

    widget = CharmWidget(config)
    widget.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
