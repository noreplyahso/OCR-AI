from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.application.contracts.context import AccessProfile


@dataclass(frozen=True)
class MainScreenState:
    title: str = "Main"
    current_user_name: str = ""
    current_role: str = "Operator"
    available_products: list[str] = field(default_factory=list)
    selected_product_name: str = ""
    model_path: str = ""
    camera_vendor: str = ""
    plc_vendor: str = ""
    plc_ip: str = ""
    plc_port: str = ""
    plc_protocol: str = ""
    result_time: int | None = None
    sleep_time: int | None = None
    zoom_factor: float | None = None
    offset_x: int = 0
    offset_y: int = 0
    image_width: int = 0
    image_height: int = 0
    access_profile: AccessProfile = field(default_factory=AccessProfile)
    camera_connected: bool = False
    plc_connected: bool = False
    plc_last_result: str = ""
    preview_frame: ImageFrame | None = None
    preview_summary: str = ""
    last_cycle_status: str = ""
    task_summaries: list[str] = field(default_factory=list)
    message: str = ""
