import logging
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "lib"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import AppLogger  # noqa: E402


def _reset_app_logger():
    log_path = Path(AppLogger.get_log_file_path()).resolve()
    root_logger = logging.getLogger()

    for handler in list(root_logger.handlers):
        base_filename = getattr(handler, "baseFilename", None)
        if base_filename and Path(base_filename).resolve() == log_path:
            handler.close()
            root_logger.removeHandler(handler)

    if AppLogger._fault_handler_stream is not None:
        AppLogger._fault_handler_stream.close()
        AppLogger._fault_handler_stream = None

    AppLogger._logging_ready = False


def test_log_paths_use_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    _reset_app_logger()

    app_data_dir = Path(AppLogger.get_app_data_dir())
    log_dir = Path(AppLogger.get_log_dir())

    assert app_data_dir == tmp_path / "DRB-OCR-AI"
    assert log_dir == app_data_dir / "logs"


def test_setup_logging_creates_log_and_crash_files(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    _reset_app_logger()

    logger = AppLogger.setup_logging()
    logger.info("ci-smoke-message")

    for handler in logging.getLogger().handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    log_file = Path(AppLogger.get_log_file_path())
    crash_file = Path(AppLogger.get_crash_log_file_path())

    assert log_file.exists()
    assert crash_file.exists()
    assert "ci-smoke-message" in log_file.read_text(encoding="utf-8")

    _reset_app_logger()
