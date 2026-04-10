from __future__ import annotations

from PyQt5.QtWidgets import QApplication


APP_STYLESHEET = """
QWidget {
    background: #f4f7fb;
    color: #162133;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QStackedWidget#desktopWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f7fafc,
        stop: 1 #e6eef7
    );
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #d9e2ef;
    border-radius: 16px;
}

QLabel#screenTitle {
    font-size: 24px;
    font-weight: 700;
    color: #0f1728;
    background: transparent;
}

QLabel#screenSubtitle {
    font-size: 11pt;
    color: #5a6b85;
    background: transparent;
}

QLabel#messageLabel {
    color: #9b1c1c;
    background: transparent;
    font-weight: 600;
}

QLabel#successMessageLabel {
    color: #166534;
    background: transparent;
    font-weight: 600;
}

QLabel#mutedLabel {
    color: #61738f;
    background: transparent;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background: #fbfdff;
    border: 1px solid #c5d2e3;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 22px;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 1px solid #2f6fed;
}

QPushButton {
    border-radius: 10px;
    padding: 10px 16px;
    background: #dbe6f5;
    color: #12243b;
    border: 1px solid #bfcfe4;
    font-weight: 600;
}

QPushButton:hover {
    background: #cfddf0;
}

QPushButton:disabled {
    background: #e8eef6;
    color: #92a1b5;
    border: 1px solid #d7e0eb;
}

QPushButton#primaryButton {
    background: #1858d6;
    color: #ffffff;
    border: 1px solid #1449b1;
}

QPushButton#primaryButton:hover {
    background: #1249bb;
}

QPushButton#dangerButton {
    background: #fff1f2;
    color: #9f1239;
    border: 1px solid #fecdd3;
}

QPushButton#dangerButton:hover {
    background: #ffe4e6;
}

QPushButton#successButton {
    background: #e8f7ee;
    color: #166534;
    border: 1px solid #b7e0c5;
}

QPushButton#successButton:hover {
    background: #dff1e6;
}

QLabel#statusPill {
    background: #eef4ff;
    color: #1d4ed8;
    border: 1px solid #c7d8ff;
    border-radius: 999px;
    padding: 6px 12px;
    font-weight: 600;
}

QLabel#sectionTitle {
    font-size: 12pt;
    font-weight: 700;
    color: #142235;
    background: transparent;
}
"""


def apply_app_theme(app: QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
