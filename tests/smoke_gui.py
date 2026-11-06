"""GUI 冒烟测试（offscreen）：python tests/smoke_gui.py"""

import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["WORK_ENCOURAGER_DATA_DIR"] = tempfile.mkdtemp(prefix="we_smoke_")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from work_encourager.storage import load_settings  # noqa: E402
from work_encourager.theme import theme_qss  # noqa: E402
from work_encourager.tracker import Tracker  # noqa: E402
from work_encourager.window import MainWindow  # noqa: E402
from work_encourager.dialogs import HistoryDialog, SettingsDialog  # noqa: E402


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # 两种主题都过一遍
    for theme in ("light", "dark"):
        app.setStyleSheet(theme_qss(theme))
        settings = load_settings()
        settings.theme = theme
        tracker = Tracker(settings)
        # 预置一点数据让显示非零
        tracker.clock_in()
        tracker.st.acc_seconds = 16542.8
        win = MainWindow(tracker, settings)
        win.show()
        win.refresh()
        for _ in range(5):
            app.processEvents()

        expected = f"{16542.8 * settings.hourly_wage / 3600:,.4f}"
        assert win.moneyNumber.text() == expected, (win.moneyNumber.text(), expected)
        assert "上班中" in win.statusPill.text()
        assert win.countdownLabel.text()
        assert win.rateLabel.text()
        assert win.progressDetail.text()
        assert win.monthAmount.text()
        assert win.staticLine.text()
        assert win.msgLabel.text()

        # 状态切换 -> 按钮重建
        tracker.pause()
        win.refresh()
        assert "休息中" in win.statusPill.text()
        tracker.clock_out()
        win.refresh()
        assert "未上班" in win.statusPill.text()

        # 对话框能打开
        dlg1 = SettingsDialog(win, settings)
        dlg1.show()
        s2 = dlg1.get_settings()
        assert s2.hourly_wage == settings.hourly_wage

        # 月薪模式：切换、折算、保存
        dlg1.typeCombo.setCurrentIndex(1)          # 按月薪
        dlg1.paySpin.setValue(10000.0)
        assert "折算" in dlg1.payHint.text() and "时薪" in dlg1.payHint.text()
        s3 = dlg1.get_settings()
        assert s3.salary_type == "monthly" and s3.salary_value == 10000.0
        exp_hourly = 10000.0 / (len(settings.workdays) * 52.0 / 12.0 * settings.daily_target_hours)
        assert abs(s3.hourly_wage - exp_hourly) < 1e-6
        dlg1.typeCombo.setCurrentIndex(0)          # 切回时薪，数值应被保留
        assert abs(dlg1.paySpin.value() - settings.salary_value) < 1e-6

        dlg2 = HistoryDialog(win, tracker)
        dlg2.show()
        for _ in range(5):
            app.processEvents()
        dlg1.close()
        dlg2.close()
        win.close()  # 应该只是隐藏到托盘
        assert not win.isVisible()

        # 主窗口月薪模式信息行
        settings.salary_type = "monthly"
        settings.salary_value = 10000.0
        win._update_static()
        assert "月薪" in win.staticLine.text() and "折合时薪" in win.staticLine.text()
        assert f"{tracker.s.hourly_wage:,.2f}" in win.staticLine.text()
        print(f"  PASS smoke [{theme}]  money={win.moneyNumber.text()}")

    app.quit()
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
