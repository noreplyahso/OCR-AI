from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.factory import build_repository
from drb_inspection.adapters.db.models import DatabaseSettings, ProductRecord, RepositoryBackend, SessionRecord, UserRecord
from drb_inspection.adapters.db.mysql import MySqlRepositoryAdapter


@dataclass
class _FakeGateway:
    key_column: str
    rows: dict[object, dict] = field(default_factory=dict)

    def get_all(self):
        return [dict(row) for row in self.rows.values()]

    def get_by(self, column: str, value):
        return [dict(row) for row in self.rows.values() if row.get(column) == value]

    def insert(self, data: dict) -> None:
        self.rows[data[self.key_column]] = dict(data)

    def update(self, column: str, value, updates: dict) -> None:
        for key, row in list(self.rows.items()):
            if row.get(column) == value:
                self.rows[key] = {**row, **updates}
                return
        raise KeyError(value)

    def insert_or_update(self, data: dict) -> None:
        key = data[self.key_column]
        current = self.rows.get(key, {})
        self.rows[key] = {**current, **data}


def test_build_repository_returns_in_memory_backend_by_default() -> None:
    repository = build_repository(backend=RepositoryBackend.MEMORY)

    assert isinstance(repository, RepositoryAdapter)
    assert not isinstance(repository, MySqlRepositoryAdapter)


def test_mysql_repository_roundtrips_legacy_rows_and_v2_overlay_fields() -> None:
    users_gateway = _FakeGateway(
        key_column="UserName",
        rows={
            "operator1": {
                "UserName": "operator1",
                "FullName": "Operator One",
                "Department": "QA",
                "No_id": "001",
                "PasswordHash": "secret",
                "Role": "Operator",
                "Active": "Active",
                "Attempt": 0,
            }
        },
    )
    products_gateway = _FakeGateway(
        key_column="ProductName",
        rows={
            "PRODUCT-A": {
                "ProductName": "PRODUCT-A",
                "DefaultNumber": 160,
                "Exposure": 3500,
                "ThresholdAccept": 0.5,
                "ThresholdMns": 0.5,
            }
        },
    )
    session_gateway = _FakeGateway(
        key_column="ID",
        rows={
            1: {
                "ID": 1,
                "UserName": "operator1",
                "ResultTime": 100,
                "SleepTime": 10,
                "ZoomFactor": 1.0,
                "OffsetX": 12,
                "OffsetY": 34,
                "ImageWidth": 640,
                "ImageHeight": 480,
                "ROIx1": 760,
                "ROIx2": 1250,
                "ROIx3": 1730,
                "ROIx4": 2220,
                "ROIx5": 2710,
                "ROIy1": 1180,
                "ROIy2": 1180,
                "ROIy3": 1180,
                "ROIy4": 1180,
                "ROIy5": 1180,
                "PLCIP": "192.168.0.10",
                "PLCProtocol": "slmp",
                "PLCPort": 5000,
            }
        },
    )
    repository = MySqlRepositoryAdapter(
        settings=DatabaseSettings(),
        users_gateway=users_gateway,
        products_gateway=products_gateway,
        session_gateway=session_gateway,
    )

    repository.save_user(
        UserRecord(
            user_name="operator1",
            full_name="Operator One",
            password_hash="secret2",
            department="QA",
            no_id="001",
            role="Operator",
            attempt=1,
            active="Active",
        )
    )
    repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-A",
            model_path="models/product_a.pt",
            exposure=3600,
            default_number=180,
            threshold_accept=0.7,
            threshold_mns=0.2,
        )
    )
    repository.save_session(
        SessionRecord(
            user_name="operator1",
            product_name="PRODUCT-A",
            camera_vendor="basler",
            plc_vendor="mitsubishi",
            plc_ip="192.168.0.20",
            plc_port=5001,
            plc_protocol="slmp",
            result_time=250,
            sleep_time=15,
            zoom_factor=1.5,
            offset_x=40,
            offset_y=50,
            image_width=1280,
            image_height=1024,
            roi_x1=800,
            roi_x2=1300,
            roi_x3=1800,
            roi_x4=2300,
            roi_x5=2800,
            roi_y1=1200,
            roi_y2=1210,
            roi_y3=1220,
            roi_y4=1230,
            roi_y5=1240,
        )
    )

    user = repository.get_user("operator1")
    product = repository.get_product("PRODUCT-A")
    session = repository.get_session()

    assert user is not None
    assert user.password_hash == "secret2"
    assert user.attempt == 1
    assert product is not None
    assert product.model_path == "models/product_a.pt"
    assert product.exposure == 3600
    assert product.default_number == 180
    assert session.product_name == "PRODUCT-A"
    assert session.camera_vendor == "basler"
    assert session.plc_vendor == "mitsubishi"
    assert session.plc_ip == "192.168.0.20"
    assert session.plc_port == 5001
    assert session.image_width == 1280
    assert session.roi_x1 == 800
    assert session.roi_y5 == 1240
