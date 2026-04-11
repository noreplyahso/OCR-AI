from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.db.models import InspectionHistoryRecord, ProductRecord, SessionRecord, UserRecord


@dataclass(frozen=True)
class LoginCommand:
    user_name: str
    password: str


@dataclass(frozen=True)
class LoginResult:
    success: bool
    message: str
    user: UserRecord | None = None
    session: SessionRecord | None = None


@dataclass(frozen=True)
class ProductCatalogEntry:
    product_name: str
    model_path: str = ""
    exposure: int | None = None
    default_number: int | None = None
    threshold_accept: float | None = None
    threshold_mns: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductCatalogSyncResult:
    products: list[ProductRecord]


@dataclass(frozen=True)
class ProductSelectionResult:
    product: ProductRecord
    session: SessionRecord


@dataclass(frozen=True)
class ProductSettingsResult:
    product: ProductRecord
    session: SessionRecord


@dataclass(frozen=True)
class SessionSettingsResult:
    session: SessionRecord


@dataclass(frozen=True)
class AccessProfile:
    can_open_authentication: bool = False
    can_open_report: bool = False
    can_configure_image: bool = False
    can_configure_hardware: bool = False
    can_configure_ai: bool = False
    can_load_model: bool = False
    can_select_image_path: bool = False
    can_open_training_screen: bool = False
    can_update_product_list: bool = False
    can_grab: bool = False
    can_live_camera: bool = False
    can_real_time: bool = False
    can_manual_mode: bool = False
    can_auto_mode: bool = False
    can_change_result_time: bool = False
    can_change_sleep_time: bool = False
    can_toggle_setting: bool = False
    can_run_cycle: bool = False


@dataclass(frozen=True)
class MainScreenContext:
    current_user_name: str
    current_role: str
    session: SessionRecord
    available_products: list[str]
    recent_inspection_history: list[InspectionHistoryRecord] = field(default_factory=list)
    access_profile: AccessProfile = field(default_factory=AccessProfile)
    selected_model_path: str = ""
    selected_product: ProductRecord | None = None
