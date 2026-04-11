from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RepositoryBackend(str, Enum):
    MEMORY = "memory"
    MYSQL = "mysql"


LEGACY_ROI_WIDTH = 300
LEGACY_ROI_HEIGHT = 440


@dataclass
class DatabaseSettings:
    host: str = "localhost"
    port: int = 3306
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
    result_time: int | None = 1
    sleep_time: int | None = 10
    zoom_factor: float | None = 0.4
    offset_x: int = 300
    offset_y: int = 1400
    image_width: int = 2500
    image_height: int = 1000
    roi_x1: int = 760
    roi_x2: int = 1250
    roi_x3: int = 1730
    roi_x4: int = 2220
    roi_x5: int = 2710
    roi_y1: int = 1180
    roi_y2: int = 1180
    roi_y3: int = 1180
    roi_y4: int = 1180
    roi_y5: int = 1180

    def roi_points(self) -> list[tuple[int, int]]:
        return [
            (self.roi_x1, self.roi_y1),
            (self.roi_x2, self.roi_y2),
            (self.roi_x3, self.roi_y3),
            (self.roi_x4, self.roi_y4),
            (self.roi_x5, self.roi_y5),
        ]

    def roi_rects(
        self,
        *,
        roi_width: int = LEGACY_ROI_WIDTH,
        roi_height: int = LEGACY_ROI_HEIGHT,
    ) -> list[tuple[int, int, int, int]]:
        return [
            (x - self.offset_x, y - self.offset_y, roi_width, roi_height)
            for x, y in self.roi_points()
        ]


@dataclass(frozen=True)
class InspectionHistoryRecord:
    recorded_at: datetime
    user_name: str = ""
    product_name: str = ""
    recipe_name: str = ""
    overall_status: str = ""
    plc_result_sent: str = ""
    trigger_source: str = ""
    cycle_duration_ms: float = 0.0
    signal_summary: str = ""
    task_count: int = 0
    ok_count: int = 0
    ng_count: int = 0
    message: str = ""
    artifact_dir: str = ""
