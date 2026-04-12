from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _ensure_src_root_on_path() -> None:
    if __package__:
        return
    src_root = Path(__file__).resolve().parents[2]
    src_root_str = str(src_root)
    if src_root_str not in sys.path:
        sys.path.insert(0, src_root_str)


def _load_runtime_env_file() -> None:
    env_file = Path(os.environ.get("DRB_V2_ENV_FILE", str(_repo_root() / ".env.v2")))
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_ensure_src_root_on_path()
_load_runtime_env_file()

from drb_inspection.app.container import build_container
from drb_inspection.app.settings import load_runtime_settings
from drb_inspection.ui.shell import DesktopShell
from drb_inspection.adapters.camera.models import CameraVendor


def _preload_camera_sdk_for_qt(*, camera_vendor: CameraVendor) -> None:
    if camera_vendor != CameraVendor.BASLER:
        return
    importlib.import_module("pypylon.pylon")


def main() -> int:
    runtime_settings = load_runtime_settings()
    container = build_container(runtime_settings=runtime_settings)
    if runtime_settings.headless:
        shell = DesktopShell(container=container)
        shell.show()
        return 0
    _preload_camera_sdk_for_qt(camera_vendor=runtime_settings.camera_connection.vendor)
    from drb_inspection.ui.qt import run_qt_app

    return run_qt_app(container)


if __name__ == "__main__":
    raise SystemExit(main())
