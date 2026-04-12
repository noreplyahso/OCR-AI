from __future__ import annotations

import sys
import types

from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.app.bootstrap import _preload_camera_sdk_for_qt, main
from drb_inspection.app.settings import AppRuntimeSettings


def test_preload_camera_sdk_for_qt_imports_pypylon_for_basler(monkeypatch) -> None:
    imported: list[str] = []

    def fake_import_module(name: str):
        imported.append(name)
        return object()

    monkeypatch.setattr("drb_inspection.app.bootstrap.importlib.import_module", fake_import_module)

    _preload_camera_sdk_for_qt(camera_vendor=CameraVendor.BASLER)

    assert imported == ["pypylon.pylon"]


def test_preload_camera_sdk_for_qt_skips_non_basler(monkeypatch) -> None:
    imported: list[str] = []

    def fake_import_module(name: str):
        imported.append(name)
        return object()

    monkeypatch.setattr("drb_inspection.app.bootstrap.importlib.import_module", fake_import_module)

    _preload_camera_sdk_for_qt(camera_vendor=CameraVendor.DEMO)

    assert imported == []


def test_main_preloads_sdk_before_importing_qt(monkeypatch) -> None:
    call_order: list[str] = []
    runtime_settings = AppRuntimeSettings(
        headless=False,
        camera_connection=CameraConnectionSettings(vendor=CameraVendor.BASLER),
    )

    monkeypatch.setattr("drb_inspection.app.bootstrap.load_runtime_settings", lambda: runtime_settings)
    monkeypatch.setattr("drb_inspection.app.bootstrap.build_container", lambda runtime_settings: object())
    monkeypatch.setattr(
        "drb_inspection.app.bootstrap._preload_camera_sdk_for_qt",
        lambda *, camera_vendor: call_order.append(f"preload:{camera_vendor.value}"),
    )

    fake_qt_module = types.ModuleType("drb_inspection.ui.qt")

    def fake_run_qt_app(container) -> int:
        call_order.append("run_qt_app")
        return 123

    fake_qt_module.run_qt_app = fake_run_qt_app
    monkeypatch.setitem(sys.modules, "drb_inspection.ui.qt", fake_qt_module)

    result = main()

    assert result == 123
    assert call_order == ["preload:basler", "run_qt_app"]
