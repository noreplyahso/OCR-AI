from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.db.models import ProductRecord
from drb_inspection.app.container import build_container


class _SpyCamera(CameraAdapter):
    def __init__(self):
        super().__init__()
        self.applied_settings = []

    def apply_settings(self, settings):
        super().apply_settings(settings)
        self.applied_settings.append(settings)


def test_configure_camera_uses_product_exposure_and_session_roi() -> None:
    container = build_container()
    camera = _SpyCamera()
    container.configure_camera.camera = camera
    container.repository.upsert_product(
        ProductRecord(product_name="PRODUCT-A", model_path="models/product_a.pt", exposure=3500)
    )
    container.repository.update_session(
        product_name="PRODUCT-A",
        offset_x=12,
        offset_y=34,
        image_width=640,
        image_height=480,
    )

    result = container.configure_camera.execute()

    assert result.settings.exposure_time == 3500
    assert result.settings.offset_x == 12
    assert result.settings.offset_y == 34
    assert result.settings.width == 640
    assert result.settings.height == 480
    assert camera.applied_settings[-1] == result.settings
