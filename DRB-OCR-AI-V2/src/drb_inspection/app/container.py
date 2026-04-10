from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.factory import build_camera_adapter
from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.models import ProductRecord, SessionRecord, UserRecord
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.factory import build_plc_adapter
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.get_access_profile import GetAccessProfileUseCase
from drb_inspection.application.use_cases.grab_preview import GrabPreviewUseCase
from drb_inspection.application.use_cases.load_main_screen_context import LoadMainScreenContextUseCase
from drb_inspection.application.use_cases.load_runtime_status import LoadRuntimeStatusUseCase
from drb_inspection.application.use_cases.load_session_settings import LoadSessionSettingsUseCase
from drb_inspection.application.use_cases.login_user import LoginUserUseCase
from drb_inspection.application.use_cases.logout_user import LogoutUserUseCase
from drb_inspection.application.use_cases.perform_cycle import PerformInspectionCycleUseCase
from drb_inspection.application.use_cases.run_current_product_cycle import RunCurrentProductCycleUseCase
from drb_inspection.application.use_cases.run_inspection import RunInspectionUseCase
from drb_inspection.application.use_cases.save_session_settings import SaveSessionSettingsUseCase
from drb_inspection.application.use_cases.select_product import SelectProductUseCase
from drb_inspection.application.use_cases.sync_products import SyncProductsUseCase
from drb_inspection.domain.inspection.pipeline import InspectionPipeline
from drb_inspection.plugins.classify.plugin import ClassifyPlugin
from drb_inspection.plugins.ocr.plugin import OcrPlugin
from drb_inspection.plugins.ocr.runtime import LegacyOcrRuntimeGateway
from drb_inspection.plugins.registry import PluginRegistry
from drb_inspection.plugins.segment.plugin import SegmentPlugin
from drb_inspection.workers.local_ai_worker import LocalAiWorker


@dataclass
class AppContainer:
    camera: CameraAdapter
    plc: PlcAdapter
    repository: RepositoryAdapter
    worker: LocalAiWorker
    pipeline: InspectionPipeline
    run_inspection: RunInspectionUseCase
    perform_cycle: PerformInspectionCycleUseCase
    login_user: LoginUserUseCase
    logout_user: LogoutUserUseCase
    sync_products: SyncProductsUseCase
    select_product: SelectProductUseCase
    load_session_settings: LoadSessionSettingsUseCase
    save_session_settings: SaveSessionSettingsUseCase
    get_access_profile: GetAccessProfileUseCase
    load_main_screen_context: LoadMainScreenContextUseCase
    load_runtime_status: LoadRuntimeStatusUseCase
    configure_camera: ConfigureCurrentCameraUseCase
    grab_preview: GrabPreviewUseCase
    run_current_product_cycle: RunCurrentProductCycleUseCase


def build_container(runtime_settings: AppRuntimeSettings | None = None) -> AppContainer:
    settings = runtime_settings or AppRuntimeSettings()
    camera = build_camera_adapter(settings.camera_connection)
    plc = build_plc_adapter(settings.plc_connection)
    repository = RepositoryAdapter()
    repository.save_user(UserRecord(user_name="admin", password_hash="admin", role="Administrator"))
    repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-A",
            model_path="models/product_a.pt",
            exposure=3500,
            default_number=160,
            threshold_accept=0.5,
            threshold_mns=0.5,
        )
    )
    repository.save_session(
        SessionRecord(
            product_name="PRODUCT-A",
            camera_vendor=settings.camera_connection.vendor.value,
            plc_vendor=settings.plc_connection.vendor.value,
            plc_ip=settings.plc_connection.ip,
            plc_port=settings.plc_connection.port,
            plc_protocol=settings.plc_connection.protocol_type.value,
            result_time=100,
            sleep_time=10,
            zoom_factor=1.0,
        )
    )
    worker = LocalAiWorker()
    runtime_gateway = (
        LegacyOcrRuntimeGateway(runtime_dir=settings.ocr_runtime_dir)
        if settings.use_legacy_ocr_runtime
        else None
    )
    plugin_registry = PluginRegistry(
        {
            "ocr": OcrPlugin(runtime_gateway=runtime_gateway),
            "classify": ClassifyPlugin(),
            "segment": SegmentPlugin(),
        }
    )
    pipeline = InspectionPipeline(worker=worker, plugin_registry=plugin_registry)
    run_inspection = RunInspectionUseCase(pipeline=pipeline, repository=repository)
    perform_cycle = PerformInspectionCycleUseCase(
        camera=camera,
        plc=plc,
        run_inspection=run_inspection,
    )
    login_user = LoginUserUseCase(repository=repository)
    logout_user = LogoutUserUseCase(repository=repository)
    sync_products = SyncProductsUseCase(repository=repository)
    select_product = SelectProductUseCase(repository=repository)
    load_session_settings = LoadSessionSettingsUseCase(repository=repository)
    save_session_settings = SaveSessionSettingsUseCase(repository=repository)
    get_access_profile = GetAccessProfileUseCase()
    load_main_screen_context = LoadMainScreenContextUseCase(
        repository=repository,
        get_access_profile=get_access_profile,
    )
    load_runtime_status = LoadRuntimeStatusUseCase(camera=camera, plc=plc)
    configure_camera = ConfigureCurrentCameraUseCase(camera=camera, repository=repository)
    grab_preview = GrabPreviewUseCase(camera=camera)
    run_current_product_cycle = RunCurrentProductCycleUseCase(
        repository=repository,
        configure_camera=configure_camera,
        perform_cycle=perform_cycle,
        runtime_settings=settings,
    )
    return AppContainer(
        camera=camera,
        plc=plc,
        repository=repository,
        worker=worker,
        pipeline=pipeline,
        run_inspection=run_inspection,
        perform_cycle=perform_cycle,
        login_user=login_user,
        logout_user=logout_user,
        sync_products=sync_products,
        select_product=select_product,
        load_session_settings=load_session_settings,
        save_session_settings=save_session_settings,
        get_access_profile=get_access_profile,
        load_main_screen_context=load_main_screen_context,
        load_runtime_status=load_runtime_status,
        configure_camera=configure_camera,
        grab_preview=grab_preview,
        run_current_product_cycle=run_current_product_cycle,
    )
