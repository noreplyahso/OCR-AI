import os

from PyQt5.QtWidgets import QApplication

from drb_inspection.adapters.db.models import ProductRecord, UserRecord
from drb_inspection.app.container import build_container
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.qt.login_widget import LoginScreenWidget
from drb_inspection.ui.shell import DesktopShell


def _app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def test_login_widget_return_pressed_submits_login() -> None:
    app = _app()
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator_enter", password_hash="pw", role="Operator"))
    container.repository.upsert_product(
        ProductRecord(product_name="PRODUCT-A", model_path="models/product_a.pt")
    )
    container.repository.update_session(product_name="PRODUCT-A")
    shell = DesktopShell(container=container)
    shell.launch()
    widget = LoginScreenWidget(shell=shell)
    widget.render()
    emitted: list[str] = []
    widget.navigate.connect(emitted.append)

    widget.user_name_edit.setText("operator_enter")
    widget.password_edit.setText("pw")
    widget._on_return_pressed()
    app.processEvents()

    assert shell.active_screen == ScreenId.MAIN
    assert shell.main_state is not None
    assert emitted == [ScreenId.MAIN.value]
    widget.clock_timer.stop()
    widget.close()


def test_login_widget_return_pressed_moves_focus_to_password_when_missing() -> None:
    app = _app()
    container = build_container()
    shell = DesktopShell(container=container)
    shell.launch()
    widget = LoginScreenWidget(shell=shell)
    widget.show()
    widget.render()
    app.processEvents()

    widget.user_name_edit.setText("operator_enter")
    widget.password_edit.setText("")
    widget._on_return_pressed()
    app.processEvents()

    assert widget.password_edit.hasFocus()
    widget.clock_timer.stop()
    widget.close()
