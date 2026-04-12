from __future__ import annotations

from typing import Any, Sequence

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap

from drb_inspection.ui.screens.main.state import PreviewAnnotation


def build_preview_pixmap(
    frame: Any,
    summary: str,
    width: int = 520,
    height: int = 300,
    roi_rects: Sequence[tuple[int, int, int, int]] | None = None,
    annotations: Sequence[PreviewAnnotation] | None = None,
) -> QPixmap:
    if frame is not None:
        pixmap = _try_build_pixmap_from_array(
            frame,
            roi_rects=roi_rects or [],
            annotations=annotations or [],
        )
        if pixmap is not None:
            return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return _build_placeholder_pixmap(summary=summary or "No preview available.", width=width, height=height)


def _try_build_pixmap_from_array(
    frame: Any,
    *,
    roi_rects: Sequence[tuple[int, int, int, int]],
    annotations: Sequence[PreviewAnnotation],
) -> QPixmap | None:
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
        pixmap = QPixmap.fromImage(image.copy())
        if annotations or roi_rects:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            line_width = max(2, int(max(1, pixmap.width()) / 500))
            label_font = QFont("Segoe UI", max(10, int(max(1, pixmap.width()) / 95)))
            label_font.setBold(True)
            painter.setFont(label_font)
            if annotations:
                for index, annotation in enumerate(annotations, start=1):
                    x_value, y_value, rect_width, rect_height = annotation.roi_rect
                    color = _annotation_color(annotation.status)
                    painter.setPen(QPen(color, line_width))
                    painter.drawRect(int(x_value), int(y_value), int(rect_width), int(rect_height))
                    label = annotation.label or f"ROI {index}"
                    painter.drawText(int(x_value), max(28, int(y_value) - 12), label)
            else:
                painter.setPen(QPen(QColor("#38c172"), line_width))
                for index, (x_value, y_value, rect_width, rect_height) in enumerate(roi_rects, start=1):
                    painter.drawRect(int(x_value), int(y_value), int(rect_width), int(rect_height))
                    painter.drawText(
                        int(x_value),
                        max(28, int(y_value) - 12),
                        f"ROI {index}",
                    )
            painter.end()
        return pixmap
    except Exception:
        return None


def _annotation_color(status: str) -> QColor:
    normalized = (status or "").strip().lower()
    if normalized == "pass":
        return QColor("#00b050")
    if normalized == "fail":
        return QColor("#ff3b30")
    if normalized == "error":
        return QColor("#ff9500")
    return QColor("#38c172")


def _build_placeholder_pixmap(summary: str, width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#eef3f7"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QPen(QColor("#c6d1db"), 2))
    painter.drawRoundedRect(10, 10, width - 20, height - 20, 8, 8)

    painter.setPen(QColor("#5f7694"))
    body_font = QFont("Segoe UI", 11)
    body_font.setBold(True)
    painter.setFont(body_font)
    painter.drawText(
        QRect(28, 28, width - 56, height - 56),
        Qt.AlignCenter | Qt.TextWordWrap,
        summary,
    )
    painter.end()
    return pixmap
