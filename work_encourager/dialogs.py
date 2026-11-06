"""设置对话框与历史记录对话框。"""

from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QTableWidget,
    QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget,
)

from .storage import Settings
from .tracker import WEEK_CN, Tracker

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, settings: Settings):
        super().__init__(parent)
        self.setWindowTitle("设置 · 上班鼓励器")
        self.setMinimumWidth(380)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 14)
        v.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ---- 先创建全部控件，再按顺序加入表单 ----
        # 收入类型 + 金额（切换时保留两种模式各自输入的数值）
        self.typeCombo = QComboBox()
        self.typeCombo.addItem("按时薪", "hourly")
        self.typeCombo.addItem("按月薪", "monthly")
        self.typeCombo.setCurrentIndex(max(0, self.typeCombo.findData(settings.salary_type)))

        self.paySpin = QDoubleSpinBox()
        self.paySpin.setRange(0.01, 9999999.0)
        self.paySpin.setDecimals(2)
        self.paySpin.setPrefix("¥ ")

        mwd = settings.monthly_workdays
        if settings.salary_type == "monthly":
            self._val_hourly = settings.hourly_wage
            self._val_monthly = settings.salary_value
        else:
            self._val_hourly = settings.salary_value
            self._val_monthly = settings.hourly_wage * mwd * max(0.5, settings.daily_target_hours)

        self.payHint = QLabel()
        self.payHint.setObjectName("smallLabel")
        self.payHint.setWordWrap(True)

        self.hoursSpin = QDoubleSpinBox()
        self.hoursSpin.setRange(0.5, 24.0)
        self.hoursSpin.setDecimals(1)
        self.hoursSpin.setSingleStep(0.5)
        self.hoursSpin.setSuffix(" 小时")
        self.hoursSpin.setValue(settings.daily_target_hours)

        sh, sm = (int(x) for x in settings.start_time.split(":")[:2])
        eh, em = (int(x) for x in settings.end_time.split(":")[:2])
        self.startEdit = QTimeEdit(QTime(sh, sm))
        self.startEdit.setDisplayFormat("HH:mm")
        self.endEdit = QTimeEdit(QTime(eh, em))
        self.endEdit.setDisplayFormat("HH:mm")

        days_widget = QWidget()
        dl = QHBoxLayout(days_widget)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(7)
        self.dayChecks: list[QCheckBox] = []
        for i, name in enumerate(DAY_NAMES):
            cb = QCheckBox(name)
            cb.setChecked(i in settings.workdays)
            self.dayChecks.append(cb)
            dl.addWidget(cb)
        dl.addStretch(1)

        self.themeCombo = QComboBox()
        self.themeCombo.addItem("浅色", "light")
        self.themeCombo.addItem("深色", "dark")
        self.themeCombo.setCurrentIndex(max(0, self.themeCombo.findData(settings.theme)))

        self.topCheck = QCheckBox("窗口始终置顶")
        self.topCheck.setChecked(settings.always_on_top)

        # ---- 信号连接（全部控件就绪后再连，折算提示跟随工作日/工时联动）----
        self.typeCombo.currentIndexChanged.connect(self._on_type_changed)
        self.paySpin.valueChanged.connect(self._on_value_changed)
        self.hoursSpin.valueChanged.connect(lambda _: self._update_pay_hint())
        for cb in self.dayChecks:
            cb.toggled.connect(self._update_pay_hint)
        self._apply_salary_mode()

        # ---- 表单布局 ----
        form.addRow("收入类型", self.typeCombo)
        form.addRow("收入金额", self.paySpin)
        form.addRow("", self.payHint)
        form.addRow("每日目标工时", self.hoursSpin)
        form.addRow("上班时间", self.startEdit)
        form.addRow("下班时间", self.endEdit)
        form.addRow("工作日", days_widget)
        form.addRow("主题", self.themeCombo)
        form.addRow("", self.topCheck)
        v.addLayout(form)

        tip = QLabel("修改收入立即生效；历史记录按各天结算时的时薪保存。月薪按下方工作日与工时自动折算。")
        tip.setObjectName("smallLabel")
        tip.setWordWrap(True)
        v.addWidget(tip)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    # ---- 收入类型切换 ----
    def _on_type_changed(self) -> None:
        self._apply_salary_mode()

    def _on_value_changed(self, value: float) -> None:
        if self.typeCombo.currentData() == "monthly":
            self._val_monthly = value
        else:
            self._val_hourly = value
        self._update_pay_hint()

    def _apply_salary_mode(self) -> None:
        monthly = self.typeCombo.currentData() == "monthly"
        self.paySpin.blockSignals(True)
        self.paySpin.setSuffix(" 元/月" if monthly else " 元/小时")
        self.paySpin.setValue(self._val_monthly if monthly else self._val_hourly)
        self.paySpin.blockSignals(False)
        self._update_pay_hint()

    def _update_pay_hint(self) -> None:
        """折算说明基于对话框中当前的工作日 / 工时实时计算。"""
        if not hasattr(self, "dayChecks"):
            return
        days = [i for i, cb in enumerate(self.dayChecks) if cb.isChecked()]
        mwd = (len(days) * 52.0 / 12.0) if days else 21.75
        hours = max(0.5, self.hoursSpin.value())
        if self.typeCombo.currentData() == "monthly":
            hourly = self._val_monthly / (mwd * hours)
            self.payHint.setText(
                f"按每月 {mwd:.1f} 个工作日 × {hours:g} 小时折算，时薪约 ¥{hourly:,.2f}")
        else:
            self.payHint.setText("")

    def get_settings(self) -> Settings:
        s = Settings()
        s.salary_type = self.typeCombo.currentData() or "hourly"
        s.salary_value = self._val_monthly if s.salary_type == "monthly" else self._val_hourly
        s.daily_target_hours = self.hoursSpin.value()
        s.start_time = self.startEdit.time().toString("HH:mm")
        s.end_time = self.endEdit.time().toString("HH:mm")
        s.workdays = [i for i, cb in enumerate(self.dayChecks) if cb.isChecked()]
        s.theme = self.themeCombo.currentData() or "light"
        s.always_on_top = self.topCheck.isChecked()
        return s


class HistoryDialog(QDialog):
    MAX_ROWS = 200

    def __init__(self, parent: QWidget, tracker: Tracker):
        super().__init__(parent)
        self.setWindowTitle("收入历史 · 上班鼓励器")
        self.resize(430, 500)

        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 12)
        v.setSpacing(10)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["日期", "星期", "工时（小时）", "收入（元）"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 52)
        self.table.setColumnWidth(2, 110)
        v.addWidget(self.table)

        self.summary = QLabel()
        self.summary.setObjectName("smallLabel")
        v.addWidget(self.summary)

        self._load(tracker)

    def _load(self, tracker: Tracker) -> None:
        data = dict(tracker.st.history)
        today = tracker.st.date
        if tracker.st.acc_seconds > 0 and today:
            data[today] = {"seconds": tracker.st.acc_seconds, "earned": tracker.earned_today()}

        rows = [(d, rec.get("seconds", 0.0), rec.get("earned", 0.0))
                for d, rec in sorted(data.items(), reverse=True)
                if rec.get("seconds", 0.0) > 0 or rec.get("earned", 0.0) > 0]

        self.table.setRowCount(len(rows[: self.MAX_ROWS]))
        for i, (d, seconds, earned) in enumerate(rows[: self.MAX_ROWS]):
            try:
                week = WEEK_CN[dt.date.fromisoformat(d).weekday()]
            except ValueError:
                week = "-"
            mark = "（今天）" if d == today else ""
            texts = [d + mark, week, f"{seconds / 3600:,.2f}", f"{earned:,.4f}"]
            for col, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, col, item)

        ym = (today or "0000-00")[:7]
        month_earned = sum(e for d, _, e in rows if d.startswith(ym))
        all_earned = sum(e for _, _, e in rows)
        all_hours = sum(s for _, s, _ in rows) / 3600
        self.summary.setText(
            f"本月累计 ¥{month_earned:,.2f} · 全部累计 ¥{all_earned:,.2f} · 总工时 {all_hours:,.1f} 小时")
