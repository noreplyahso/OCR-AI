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
    default_number: int | None = None
    exposure: int | None = None
    threshold_accept: float | None = None
    threshold_mns: float | None = None
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
    roi_summary: str = ""
    roi_points: list[tuple[int, int]] = field(default_factory=list)
    roi_rects: list[tuple[int, int, int, int]] = field(default_factory=list)
    access_profile: AccessProfile = field(default_factory=AccessProfile)
    camera_connected: bool = False
    plc_connected: bool = False
    plc_last_result: str = ""
    plc_signal_summary: str = ""
    plc_poll_action: str = ""
    plc_cycle_triggered: bool = False
    auto_mode_enabled: bool = False
    inspection_enabled: bool = False
    recording_enabled: bool = False
    inspection_total_count: int = 0
    inspection_counter_value: int = 0
    inspection_batch_value: int = 0
    last_quantity: int = 0
    last_ok_count: int = 0
    last_ng_count: int = 0
    last_result_label: str = ""
    last_cycle_duration_ms: float = 0.0
    last_trigger_source: str = ""
    artifact_summary: str = ""
    last_artifact_dir: str = ""
    recent_history_summaries: list[str] = field(default_factory=list)
    preview_frame: ImageFrame | None = None
    preview_summary: str = ""
    last_cycle_status: str = ""
    task_summaries: list[str] = field(default_factory=list)
    message: str = ""
