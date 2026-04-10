from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CameraVendor(str, Enum):
    DEMO = "demo"
    BASLER = "basler"
    HIKROBOT = "hikrobot"
    IRAYPLE = "irayple"
    OPT = "opt"


@dataclass
class CameraSettings:
    exposure_time: int = 3000
    offset_x: int = 0
    offset_y: int = 0
    width: int = 0
    height: int = 0


@dataclass(frozen=True)
class CameraConnectionSettings:
    vendor: CameraVendor = CameraVendor.DEMO
    serial_number: str = ""
    ip_address: str = ""
    user_set: str = ""
    sdk_path: str = ""
    acquisition_mode: str = "continuous"


@dataclass
class ImageFrame:
    frame: Any
    capture_seconds: float
