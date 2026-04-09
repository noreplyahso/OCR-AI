import ctypes
import os
import sys


if getattr(sys, "frozen", False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

module_path = os.path.join(base_path, "lib")
if module_path not in sys.path:
    sys.path.append(module_path)

from AppLogger import get_log_file_path, log_exception, log_info, setup_logging

setup_logging()


def should_run_smoke_test():
    return os.environ.get("DRB_OCR_AI_SMOKE_TEST", "").strip() == "1"


def show_startup_error(message):
    if should_run_smoke_test():
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except Exception:
            pass
        return
    try:
        ctypes.windll.user32.MessageBoxW(0, message, "DRB-OCR-AI Error", 0x10)
    except Exception:
        pass


# ===== SAFE IMPORT ZONE for PyInstaller =====
# Keep these imports explicit so PyInstaller collects the required runtime modules.
try:
    # --- Core system ---
    import ast
    import csv
    import datetime
    import io
    import math
    import multiprocessing
    import pathlib
    import random
    import re
    import shutil
    import subprocess
    import threading
    import time
    import yaml
    import psutil

    # --- Data & AI ---
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.utils.data
    import torchvision
    from sklearn.model_selection import train_test_split
    from torchinfo import summary
    from torchvision import datasets, models, transforms
    from ultralytics import YOLO
    import tqdm

    # --- Communication / PLC / Database ---
    import pymcprotocol
    import pymodbus
    import pymysql
    from pymodbus.client import ModbusSerialClient, ModbusTcpClient
    from pymysql.err import MySQLError

    # --- Windows API (Single Instance) ---
    import win32api
    import win32event
    import winerror

    # --- Image / Vision ---
    import cv2
    import cvzone
    from cvzone.Utils import putTextRect
    from PIL import Image, ImageTk
    from pypylon import pylon

    # --- GUI (PyQt5 + PyQtGraph) ---
    import pyqtgraph as pg
    from PyQt5 import QtCore, QtGui, QtWidgets, uic
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *

    # --- XML / ETC ---
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
except Exception:
    log_exception("Failed to import runtime dependencies during startup")
    show_startup_error(
        "Phan mem khong the tai day du dependency khi khoi dong.\n"
        f"Vui long kiem tra log tai:\n{get_log_file_path()}"
    )
    raise

# ===== END SAFE IMPORT ZONE =====


if should_run_smoke_test():
    log_info("Smoke test mode passed after runtime dependency imports")
    sys.exit(0)


try:
    import StackUI
    from StackUI import StackedWidget
except Exception:
    log_exception("Failed to import application modules during startup")
    show_startup_error(
        "Phan mem khong the khoi dong.\n"
        f"Vui long kiem tra log tai:\n{get_log_file_path()}"
    )
    raise


if __name__ == "__main__":
    try:
        log_info(
            "Application startup requested | executable=%s | base_path=%s | cwd=%s",
            sys.executable if getattr(sys, "frozen", False) else __file__,
            base_path,
            os.getcwd(),
        )

        multiprocessing.freeze_support()

        mutex = win32event.CreateMutex(None, False, "Global\\AHSO_DRB_OCR_AI_Metalcore")
        last_error = win32api.GetLastError()

        if last_error == winerror.ERROR_ALREADY_EXISTS:
            log_info("Another application instance is already running")
            sys.exit(0)

        app = QtWidgets.QApplication(sys.argv)
        window = StackedWidget()
        window.setCurrentIndex(0)
        window.showFullScreen()
        exit_code = app.exec_()
        log_info("Application exited normally | exit_code=%s", exit_code)
        sys.exit(exit_code)
    except Exception:
        log_exception("Fatal startup failure")
        show_startup_error(
            "Phan mem gap loi khi khoi dong.\n"
            f"Vui long kiem tra log tai:\n{get_log_file_path()}"
        )
        raise
