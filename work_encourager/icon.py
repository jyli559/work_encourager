"""程序图标：用 QPainter 动态绘制，无需外部图片资源。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap

_STATUS_COLORS = {"working": "#2BD97E", "paused": "#FFB020", "off": "#9AA0B4"}


def make_pixmap(size: int = 64, status: str = "working") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QLinearGradient(0.0, 0.0, 0.0, float(size))
    grad.setColorAt(0.0, QColor("#FF8A3D"))
    grad.setColorAt(1.0, QColor("#FF3D26"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    r = size * 0.28
    p.drawRoundedRect(QRectF(0, 0, size, size), r, r)

    f = QFont("Microsoft YaHei UI")
    f.setBold(True)
    f.setPixelSize(int(size * 0.52))
    p.setFont(f)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(pm.rect().adjusted(0, 0, 0, -size * 0.04), Qt.AlignmentFlag.AlignCenter, "¥")

    # 右下角状态圆点（带白色描边）
    d = size * 0.30
    cx, cy = size - d / 2 - size * 0.03, size - d / 2 - size * 0.03
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QRectF(cx - d / 2 - 1.5, cy - d / 2 - 1.5, d + 3, d + 3))
    p.setBrush(QColor(_STATUS_COLORS.get(status, _STATUS_COLORS["off"])))
    p.drawEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))
    p.end()
    return pm


def make_icon(status: str = "working") -> QIcon:
    icon = QIcon()
    for s in (16, 24, 32, 48, 64):
        icon.addPixmap(make_pixmap(s, status))
    return icon
