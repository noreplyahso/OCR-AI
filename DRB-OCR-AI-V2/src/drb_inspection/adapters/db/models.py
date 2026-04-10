from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DatabaseSettings:
    host: str = "localhost"
    user: str = "drb"
    password: str = "drb123456"
    database: str = "drb_text"
    autocommit: bool = False


@dataclass
class UserRecord:
    user_name: str
    full_name: str = ""
    password_hash: str = ""
    department: str = ""
    no_id: str = ""
    role: str = "Operator"
    attempt: int = 0
    active: str = "Active"


@dataclass
class ProductRecord:
    product_name: str
    model_path: str = ""
    exposure: int | None = None
    default_number: int | None = None
    threshold_accept: float | None = None
    threshold_mns: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class SessionRecord:
    user_name: str = ""
    product_name: str = ""
    camera_vendor: str = ""
    plc_vendor: str = ""
    plc_ip: str = ""
    plc_port: int | str = ""
    plc_protocol: str = ""
    result_time: int | None = None
    sleep_time: int | None = None
    zoom_factor: float | None = None
    offset_x: int = 0
    offset_y: int = 0
    image_width: int = 0
    image_height: int = 0
