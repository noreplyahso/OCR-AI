import faulthandler
import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler


LOGGER_NAME = "DRB-OCR-AI"
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s: %(message)s"
_logging_ready = False
_fault_handler_stream = None


def get_app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_app_data_dir():
    app_data_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", get_app_base_dir()),
        "DRB-OCR-AI",
    )
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir


def get_log_dir():
    log_dir = os.path.join(get_app_data_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_log_file_path():
    return os.path.join(get_log_dir(), "app.log")


def get_crash_log_file_path():
    return os.path.join(get_log_dir(), "crash.log")


def _install_exception_hooks():
    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger(LOGGER_NAME).error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = _handle_exception

    if hasattr(threading, "excepthook"):
        def _handle_thread_exception(args):
            logging.getLogger(LOGGER_NAME).error(
                "Uncaught thread exception | thread=%s",
                getattr(args.thread, "name", "unknown"),
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        threading.excepthook = _handle_thread_exception


def _enable_fault_handler():
    global _fault_handler_stream

    if _fault_handler_stream is not None:
        return

    try:
        _fault_handler_stream = open(get_crash_log_file_path(), "a", encoding="utf-8")
        faulthandler.enable(_fault_handler_stream, all_threads=True)
    except Exception:
        _fault_handler_stream = None


def setup_logging():
    global _logging_ready

    if _logging_ready:
        return logging.getLogger(LOGGER_NAME)

    log_file_path = os.path.abspath(get_log_file_path())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(
        getattr(handler, "baseFilename", None) == log_file_path
        for handler in root_logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    logging.captureWarnings(True)
    _install_exception_hooks()
    _enable_fault_handler()

    _logging_ready = True
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(
        "Logging initialized | log_file=%s | crash_log=%s | base_dir=%s | cwd=%s | frozen=%s",
        get_log_file_path(),
        get_crash_log_file_path(),
        get_app_base_dir(),
        os.getcwd(),
        getattr(sys, "frozen", False),
    )
    return logger


def get_logger():
    return setup_logging()


def log_info(message, *args, **kwargs):
    get_logger().info(message, *args, **kwargs)


def log_warning(message, *args, **kwargs):
    get_logger().warning(message, *args, **kwargs)


def log_error(message, *args, **kwargs):
    get_logger().error(message, *args, **kwargs)


def log_exception(message, *args, **kwargs):
    get_logger().exception(message, *args, **kwargs)
