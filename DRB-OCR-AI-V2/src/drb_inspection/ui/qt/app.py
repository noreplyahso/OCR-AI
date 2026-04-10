from __future__ import annotations

import os
import sys

from PyQt5.QtWidgets import QApplication

from drb_inspection.app.container import AppContainer
from drb_inspection.ui.qt.theme import apply_app_theme
from drb_inspection.ui.qt.window import DesktopStackedWindow
from drb_inspection.ui.shell import DesktopShell


def run_qt_app(container: AppContainer) -> int:
    if os.environ.get("QT_QPA_PLATFORM") is None and os.environ.get("DRB_V2_QT_OFFSCREEN") == "1":
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    shell = DesktopShell(container=container)
    window = DesktopStackedWindow(shell=shell)
    window.start()

    if os.environ.get("DRB_V2_QT_NO_EXEC") == "1":
        app.processEvents()
        window.close()
        return 0
    return app.exec_()
