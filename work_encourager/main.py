"""程序入口。"""

from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from . import config
from .icon import make_icon
from .storage import load_settings
from .theme import theme_qss
from .tracker import Tracker
from .window import MainWindow


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.APP_ID)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationDisplayName(config.APP_NAME)
    app.setWindowIcon(make_icon("working"))
    app.setQuitOnLastWindowClosed(False)

    # 单实例保护：避免两个进程同时写状态文件
    lock = QLockFile(os.path.join(tempfile.gettempdir(), f"{config.APP_ID}.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, config.APP_NAME, "上班鼓励器已经在运行啦，看看系统托盘。")
        return 0

    settings = load_settings()
    app.setStyleSheet(theme_qss(settings.theme))

    tracker = Tracker(settings)
    win = MainWindow(tracker, settings)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
