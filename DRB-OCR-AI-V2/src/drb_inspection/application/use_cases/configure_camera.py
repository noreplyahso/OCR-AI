from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import CameraSettings
from drb_inspection.adapters.db.base import RepositoryAdapter


@dataclass(frozen=True)
class ConfigureCameraResult:
    settings: CameraSettings
    message: str


@dataclass
class ConfigureCurrentCameraUseCase:
    camera: CameraAdapter
    repository: RepositoryAdapter

    def execute(self) -> ConfigureCameraResult:
        session = self.repository.get_session()
        product = self.repository.get_product(session.product_name) if session.product_name else None

        settings = CameraSettings(
            exposure_time=int(product.exposure if product and product.exposure is not None else self.camera.settings.exposure_time),
            offset_x=int(session.offset_x),
            offset_y=int(session.offset_y),
            width=int(session.image_width),
            height=int(session.image_height),
        )
        self.camera.apply_settings(settings)
        self.repository.record_event(
            "Configure camera "
            f"exposure={settings.exposure_time} "
            f"roi=({settings.offset_x},{settings.offset_y},{settings.width},{settings.height})"
        )
        return ConfigureCameraResult(
            settings=settings,
            message="Camera settings applied.",
        )
