"""主悬浮窗：无边框、圆角、可拖动、可置顶、最小化到托盘。"""

from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QPainter
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QProgressBar,
    QPushButton, QStyle, QStyleOption, QSystemTrayIcon, QToolButton,
    QVBoxLayout, QWidget,
)

from . import config, messages
from .dialogs import HistoryDialog, SettingsDialog
from .icon import make_icon, make_pixmap
from .storage import Settings, save_settings
from .theme import theme_qss
from .tracker import WEEK_CN, Tracker

PILL_TEXT = {"working": "●  上班中", "paused": "●  休息中", "off": "●  未上班"}


def _label(name: str, text: str = "") -> QLabel:
    lab = QLabel(text)
    lab.setObjectName(name)
    return lab


class MainWindow(QWidget):
    def __init__(self, tracker: Tracker, settings: Settings):
        super().__init__()
        self.tracker = tracker
        self.settings = settings
        self._last_status = ""
        self._tray_hinted = False

        self.setObjectName("RootCard")
        self.setWindowTitle(config.APP_NAME)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        if settings.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._build_ui()
        self._build_tray()

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(100)
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_timer.start()

        self.msg_timer = QTimer(self)
        self.msg_timer.setInterval(15000)
        self.msg_timer.timeout.connect(lambda: self._new_message())
        self.msg_timer.start()

        self._rebuild_buttons()
        self._update_static()
        self._new_message()
        self.refresh()

        self.setFixedWidth(352)
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

    # ---------------- UI 构建 ----------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(7)

        # 标题栏
        title = QHBoxLayout()
        title.setSpacing(2)
        logo = QLabel()
        logo.setPixmap(make_pixmap(20, "working"))
        title.addWidget(logo)
        title.addSpacing(4)
        title.addWidget(_label("titleLabel", config.APP_NAME))
        title.addStretch(1)
        self.pinBtn = self._tool_btn("📌", self._toggle_pin, checkable=True)
        self.pinBtn.setChecked(self.settings.always_on_top)
        self.setBtn = self._tool_btn("⚙", self._open_settings)
        self.minBtn = self._tool_btn("—", self.hide)
        self.closeBtn = self._tool_btn("✕", self.hide)
        for b in (self.pinBtn, self.setBtn, self.minBtn, self.closeBtn):
            title.addWidget(b)
        root.addLayout(title)

        # 日期与时钟
        head = QHBoxLayout()
        self.dateLabel = _label("dateLabel")
        self.clockLabel = _label("clockLabel")
        head.addWidget(self.dateLabel)
        head.addStretch(1)
        head.addWidget(self.clockLabel)
        root.addLayout(head)

        # 状态 + 倒计时
        pill_row = QHBoxLayout()
        self.statusPill = _label("statusPill")
        pill_row.addWidget(self.statusPill)
        pill_row.addStretch(1)
        root.addLayout(pill_row)
        self.countdownLabel = _label("countdownLabel")
        root.addWidget(self.countdownLabel)

        # 金额核心区
        root.addSpacing(1)
        root.addWidget(_label("captionLabel", "今日已赚"))
        money_row = QHBoxLayout()
        money_row.setSpacing(3)
        self.moneySymbol = _label("moneySymbol", "¥")
        self.moneyNumber = _label("moneyNumber", "0.0000")
        money_row.addWidget(self.moneySymbol, 0, Qt.AlignmentFlag.AlignBottom)
        money_row.addWidget(self.moneyNumber, 0, Qt.AlignmentFlag.AlignBottom)
        money_row.addStretch(1)
        root.addLayout(money_row)
        self.rateLabel = _label("rateLabel")
        root.addWidget(self.rateLabel)
        self.msgLabel = _label("msgLabel")
        root.addWidget(self.msgLabel)

        # 按钮区
        self.btnRow = QHBoxLayout()
        self.btnRow.setSpacing(8)
        root.addLayout(self.btnRow)

        # 工时进度卡片
        prog = QFrame()
        prog.setObjectName("card")
        pv = QVBoxLayout(prog)
        pv.setContentsMargins(12, 9, 12, 11)
        pv.setSpacing(6)
        prow = QHBoxLayout()
        prow.addWidget(_label("smallLabel", "今日工时进度"))
        prow.addStretch(1)
        self.progressDetail = _label("smallLabel")
        prow.addWidget(self.progressDetail)
        pv.addLayout(prow)
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 1000)
        self.progressBar.setTextVisible(False)
        pv.addWidget(self.progressBar)
        root.addWidget(prog)

        # 月度统计卡片
        mon = QFrame()
        mon.setObjectName("card")
        mv = QVBoxLayout(mon)
        mv.setContentsMargins(12, 9, 12, 11)
        mv.setSpacing(4)
        mrow = QHBoxLayout()
        mrow.addWidget(_label("smallLabel", "本月累计"))
        mrow.addStretch(1)
        self.histBtn = QPushButton("查看历史 >")
        self.histBtn.setProperty("cls", "link")
        self.histBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.histBtn.clicked.connect(self._open_history)
        mrow.addWidget(self.histBtn)
        mv.addLayout(mrow)
        self.monthAmount = _label("monthAmount", "¥ 0.0000")
        mv.addWidget(self.monthAmount)
        self.staticLine = _label("smallLabel")
        mv.addWidget(self.staticLine)
        root.addWidget(mon)

    def _tool_btn(self, text: str, slot, checkable: bool = False) -> QToolButton:
        b = QToolButton()
        b.setText(text)
        b.setCheckable(checkable)
        b.setProperty("tb", "1")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    def _rebuild_buttons(self) -> None:
        while self.btnRow.count():
            item = self.btnRow.takeAt(0)
            w = item.widget()
            if w:
                # 必须脱离父控件，否则旧按钮仍会以残留几何显示在窗口上
                w.hide()
                w.setParent(None)
                w.deleteLater()

        def btn(text: str, cls: str, slot) -> QPushButton:
            b = QPushButton(text)
            b.setProperty("cls", cls)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(33)
            b.clicked.connect(slot)
            return b

        status = self.tracker.st.status
        if status == "off":
            self.btnRow.addWidget(btn("上班打卡", "primary", self.tracker.clock_in))
            self.btnRow.addStretch(1)
        elif status == "working":
            self.btnRow.addWidget(btn("暂停休息", "ghost", self.tracker.pause))
            self.btnRow.addWidget(btn("下班打卡", "primary", self.tracker.clock_out))
        else:
            self.btnRow.addWidget(btn("继续工作", "primary", self.tracker.resume))
            self.btnRow.addWidget(btn("下班打卡", "ghost", self.tracker.clock_out))

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        menu = QMenu()

        self.act_toggle = QAction("显示 / 隐藏窗口", menu)
        self.act_toggle.triggered.connect(self._toggle_visible)
        menu.addAction(self.act_toggle)
        menu.addSeparator()

        self.act_in = QAction("上班打卡", menu)
        self.act_in.triggered.connect(self.tracker.clock_in)
        self.act_pause = QAction("暂停休息", menu)
        self.act_pause.triggered.connect(self.tracker.pause)
        self.act_resume = QAction("继续工作", menu)
        self.act_resume.triggered.connect(self.tracker.resume)
        self.act_out = QAction("下班打卡", menu)
        self.act_out.triggered.connect(self.tracker.clock_out)
        for a in (self.act_in, self.act_pause, self.act_resume, self.act_out):
            menu.addAction(a)
        menu.addSeparator()

        act_set = QAction("设置...", menu)
        act_set.triggered.connect(self._open_settings)
        act_hist = QAction("历史记录...", menu)
        act_hist.triggered.connect(self._open_history)
        act_quit = QAction("退出", menu)
        act_quit.triggered.connect(self._quit)
        for a in (act_set, act_hist, act_quit):
            menu.addAction(a)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self._update_tray_icon()
        self.tray.show()

    # ---------------- 刷新 ----------------
    def _on_tick(self) -> None:
        self.tracker.tick()
        self.refresh()

    def refresh(self) -> None:
        st = self.tracker.st
        now = dt.datetime.now()
        self.clockLabel.setText(now.strftime("%H:%M:%S"))
        self.dateLabel.setText(f"{now:%Y-%m-%d}  {WEEK_CN[now.weekday()]}")

        if st.status != self._last_status:
            self._last_status = st.status
            self._rebuild_buttons()
            self._set_pill()
            self._update_tray_icon()
            self._update_tray_actions()
            self._new_message()

        self.moneyNumber.setText(f"{self.tracker.earned_today():,.4f}")
        self.rateLabel.setText(f"当前赚钱速度  ¥{self.tracker.per_second():.4f} / 秒")
        self.countdownLabel.setText(self.tracker.countdown_text())

        hours = self.tracker.worked_hours()
        target = self.tracker.target_hours()
        pct = hours / target * 100.0
        self.progressDetail.setText(
            f"已工作 {hours:,.2f} / {target:.2f} 小时 · {pct:.1f}%")
        self.progressBar.setValue(int(min(100.0, pct) * 10))
        self.monthAmount.setText(f"¥ {self.tracker.earned_month():,.4f}")
        self.tray.setToolTip(f"{config.APP_NAME} · 今日 ¥{self.tracker.earned_today():,.2f}")

    def _set_pill(self) -> None:
        status = self.tracker.st.status
        self.statusPill.setText(PILL_TEXT[status])
        self.statusPill.setProperty("st", status)
        self.statusPill.style().unpolish(self.statusPill)
        self.statusPill.style().polish(self.statusPill)

    def _update_static(self) -> None:
        s = self.tracker.s
        pay = f"满勤可得 ¥{s.daily_target_hours * s.hourly_wage:,.2f}"
        if s.salary_type == "monthly":
            self.staticLine.setText(
                f"月薪 ¥{s.salary_value:,.0f} · 折合时薪 ¥{s.hourly_wage:,.2f} · {pay}")
        else:
            self.staticLine.setText(f"时薪 ¥{s.hourly_wage:,.2f} · {pay}")

    def _new_message(self) -> None:
        self.msgLabel.setText(messages.pick_message(
            self.tracker.earned_today(),
            self.tracker.per_second(),
            self.tracker.st.status))

    # ---------------- 托盘与窗口行为 ----------------
    def _update_tray_icon(self) -> None:
        self.tray.setIcon(make_icon(self.tracker.st.status))

    def _update_tray_actions(self) -> None:
        status = self.tracker.st.status
        self.act_in.setEnabled(status == "off")
        self.act_pause.setEnabled(status == "working")
        self.act_resume.setEnabled(status == "paused")
        self.act_out.setEnabled(status != "off")

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self._toggle_visible()

    def _toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _toggle_pin(self) -> None:
        self.settings.always_on_top = not self.settings.always_on_top
        save_settings(self.settings)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.settings.always_on_top)
        self.pinBtn.setChecked(self.settings.always_on_top)
        self.show()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self, self.settings)
        if dlg.exec():
            new = dlg.get_settings()
            old_theme = self.settings.theme
            old_top = self.settings.always_on_top
            self.settings = new
            save_settings(new)
            self.tracker.s = new
            if new.theme != old_theme:
                QApplication.instance().setStyleSheet(theme_qss(new.theme))
            if new.always_on_top != old_top:
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, new.always_on_top)
                self.show()
            self.pinBtn.setChecked(new.always_on_top)
            self._update_static()
            self._new_message()

    def _open_history(self) -> None:
        HistoryDialog(self, self.tracker).exec()

    def _quit(self) -> None:
        self.tracker.save(force=True)
        self.tray.hide()
        QApplication.instance().quit()

    def paintEvent(self, e) -> None:
        # 自定义 QWidget 子类必须手动绘制样式表背景，否则 #RootCard 的
        # 背景色/圆角/边框不会生效（Qt 经典陷阱）
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
        super().mousePressEvent(e)

    def closeEvent(self, e) -> None:
        # 点关闭 = 最小化到托盘，真正退出走托盘菜单
        e.ignore()
        self.hide()
        if not self._tray_hinted and self.tray.isVisible():
            self.tray.showMessage(config.APP_NAME,
                                  "已最小化到系统托盘，双击托盘图标可重新打开。",
                                  QSystemTrayIcon.MessageIcon.Information, 2500)
            self._tray_hinted = True
