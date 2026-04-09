# ===== SAFE IMPORT ZONE for PyInstaller =====
# Ensure PyInstaller collects the runtime dependencies used by the app.

# --- Core system ---
import os, sys, re, math, time, random, threading, multiprocessing, csv, shutil, datetime, pathlib, io, ast, yaml, ctypes, subprocess, psutil

# --- Data & AI ---
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data
import torchvision
from torchvision import datasets, transforms, models
from sklearn.model_selection import train_test_split
from torchinfo import summary
from ultralytics import YOLO
import tqdm

# --- Communication / PLC / Database ---
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import pymodbus
import pymcprotocol
import pymysql
from pymysql.err import MySQLError

# --- Windows API (Single Instance) ---
import win32event
import win32api
import winerror

# --- Image / Vision ---
import cv2
import cvzone
from cvzone.Utils import putTextRect
from PIL import Image, ImageTk
from pypylon import pylon

# --- GUI (PyQt5 + PyQtGraph) ---
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg

# --- XML / ETC ---
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ===== END SAFE IMPORT ZONE =====


if getattr(sys, "frozen", False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

module_path = os.path.join(base_path, "lib")
sys.path.append(module_path)

from AppLogger import get_log_file_path, log_exception, log_info, setup_logging

setup_logging()


def show_startup_error(message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, "DRB-OCR-AI Error", 0x10)
    except Exception:
        pass


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
