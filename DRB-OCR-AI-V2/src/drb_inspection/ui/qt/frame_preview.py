from __future__ import annotations

from typing import Any

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap


def build_preview_pixmap(frame: Any, summary: str, width: int = 520, height: int = 300) -> QPixmap:
    if frame is not None:
        pixmap = _try_build_pixmap_from_array(frame, width, height)
        if pixmap is not None:
            return pixmap
    return _build_placeholder_pixmap(summary=summary or "No preview available.", width=width, height=height)


def _try_build_pixmap_from_array(frame: Any, width: int, height: int) -> QPixmap | None:
    shape = getattr(frame, "shape", None)
    data = getattr(frame, "data", None)
    if shape is None or data is None:
        return None

    try:
        if len(shape) == 2:
            image = QImage(
                frame.data,
                int(shape[1]),
                int(shape[0]),
                int(frame.strides[0]),
                QImage.Format_Grayscale8,
            )
        elif len(shape) == 3 and int(shape[2]) == 3:
            image = QImage(
                frame.data,
                int(shape[1]),
                int(shape[0]),
                int(frame.strides[0]),
                QImage.Format_RGB888,
            )
        else:
            return None
        return QPixmap.fromImage(image.copy()).scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None


def _build_placeholder_pixmap(summary: str, width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#f8fbff"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QPen(QColor("#d7e3f2"), 1))
    painter.drawRoundedRect(8, 8, width - 16, height - 16, 16, 16)

    painter.setPen(QColor("#274064"))
    title_font = QFont("Segoe UI", 14)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.drawText(QRect(24, 24, width - 48, 40), Qt.AlignLeft | Qt.AlignVCenter, "Camera Preview")

    painter.setPen(QColor("#61738f"))
    body_font = QFont("Segoe UI", 10)
    painter.setFont(body_font)
    painter.drawText(
        QRect(24, 78, width - 48, height - 110),
        Qt.AlignLeft | Qt.TextWordWrap,
        summary,
    )
    painter.end()
    return pixmap
