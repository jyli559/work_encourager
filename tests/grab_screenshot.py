"""渲染主窗口并截图（使用真实显示环境），用于视觉检查。"""

import os
import sys
import tempfile

os.environ["WORK_ENCOURAGER_DATA_DIR"] = tempfile.mkdtemp(prefix="we_shot_")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from work_encourager.storage import load_settings  # noqa: E402
from work_encourager.theme import theme_qss  # noqa: E402
from work_encourager.tracker import Tracker  # noqa: E402
from work_encourager.window import MainWindow  # noqa: E402


def main() -> int:
    out_dir = os.path.dirname(os.path.abspath(__file__))
    app = QApplication([])
    for theme in ("light", "dark"):
        app.setStyleSheet(theme_qss(theme))
        settings = load_settings()
        settings.theme = theme
        tracker = Tracker(settings)
        tracker.clock_in()
        tracker.st.acc_seconds = 16542.8  # ~4.59 小时
        win = MainWindow(tracker, settings)
        win.show()
        win.refresh()
        for _ in range(5):
            app.processEvents()
        pm = win.grab()
        path = os.path.join(out_dir, f"window_{theme}.png")
        pm.save(path, "PNG")
        print("saved:", path, pm.width(), "x", pm.height())
        win.hide()
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
