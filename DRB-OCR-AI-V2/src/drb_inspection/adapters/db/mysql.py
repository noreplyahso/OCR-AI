from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.models import DatabaseSettings, ProductRecord, SessionRecord, UserRecord


@dataclass
class MySqlConnection:
    settings: DatabaseSettings
    connection: object | None = None
    cursor: object | None = None

    def connect(self) -> None:
        try:
            import pymysql
        except ModuleNotFoundError as exc:
            raise RuntimeError("PyMySQL is required for the MySQL repository backend.") from exc

        self.connection = pymysql.connect(
            host=self.settings.host,
            port=self.settings.port,
            user=self.settings.user,
            password=self.settings.password,
            database=self.settings.database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=self.settings.autocommit,
        )
        self.cursor = self.connection.cursor()

    def execute(self, query: str, params=None) -> None:
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        self.cursor.execute(query, params or ())
        self.connection.commit()

    def fetchall(self):
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        return self.cursor.fetchall()

    def fetchone(self):
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        return self.cursor.fetchone()

    def close(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None


@dataclass
class SqlTableGateway:
    connection: MySqlConnection
    table_name: str

    def get_all(self):
        self.connection.execute(f"SELECT * FROM {self.table_name}")
        return self.connection.fetchall()

    def get_by(self, column: str, value):
        self.connection.execute(f"SELECT * FROM {self.table_name} WHERE {column}=%s", (value,))
        return self.connection.fetchall()

    def get_columns_by(self, select_cols: list[str], where: dict):
        columns = ", ".join(select_cols)
        where_clause = " AND ".join(["%s=%%s" % key for key in where.keys()])
        self.connection.execute(
            f"SELECT {columns} FROM {self.table_name} WHERE {where_clause}",
            tuple(where.values()),
        )
        return self.connection.fetchall()

    def insert(self, data: dict) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        self.connection.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            tuple(data.values()),
        )

    def update(self, column: str, value, updates: dict) -> None:
        set_clause = ", ".join(["`%s`=%%s" % key for key in updates.keys()])
        params = list(updates.values()) + [value]
        self.connection.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE `{column}`=%s",
            tuple(params),
        )

    def insert_or_update(self, data: dict) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        updates = ", ".join(["%s=VALUES(%s)" % (key, key) for key in data.keys()])
        self.connection.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {updates}",
            tuple(data.values()),
        )


@dataclass
class MySqlRepositoryAdapter(RepositoryAdapter):
    settings: DatabaseSettings = field(default_factory=DatabaseSettings)
    connection: MySqlConnection | None = None
    users_gateway: SqlTableGateway | None = None
    products_gateway: SqlTableGateway | None = None
    session_gateway: SqlTableGateway | None = None
    product_overlays: dict[str, ProductRecord] = field(default_factory=dict)
    session_overlay: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.users_gateway and self.products_gateway and self.session_gateway:
            return
        self.connection = self.connection or MySqlConnection(settings=self.settings)
        self.connection.connect()
        self.users_gateway = SqlTableGateway(connection=self.connection, table_name="users")
        self.products_gateway = SqlTableGateway(connection=self.connection, table_name="product")
        self.session_gateway = SqlTableGateway(connection=self.connection, table_name="current_session")
        self._ensure_session_row()

    def record_event(self, message: str) -> None:
        self.events.append(message)

    def save_user(self, user: UserRecord) -> UserRecord:
        self.users_gateway.insert_or_update(
            {
                "UserName": user.user_name,
                "FullName": user.full_name or user.user_name,
                "Department": user.department or None,
                "No_id": user.no_id or None,
                "PasswordHash": user.password_hash,
                "Role": user.role,
                "Active": user.active,
                "Attempt": user.attempt,
            }
        )
        return user

    def get_user(self, user_name: str) -> UserRecord | None:
        rows = self.users_gateway.get_by("UserName", user_name)
        if not rows:
            return None
        row = rows[0]
        return UserRecord(
            user_name=str(row.get("UserName") or ""),
            full_name=str(row.get("FullName") or ""),
            password_hash=str(row.get("PasswordHash") or ""),
            department=str(row.get("Department") or ""),
            no_id=str(row.get("No_id") or ""),
            role=str(row.get("Role") or "Operator"),
            attempt=int(row.get("Attempt") or 0),
            active=str(row.get("Active") or "Active"),
        )

    def upsert_product(self, product: ProductRecord) -> ProductRecord:
        existing = self.get_product(product.product_name)
        merged = self._merge_product(existing, product) if existing else product
        self.products_gateway.insert_or_update(
            {
                "ProductName": merged.product_name,
                "DefaultNumber": merged.default_number,
                "Exposure": merged.exposure,
                "ThresholdAccept": merged.threshold_accept,
                "ThresholdMns": merged.threshold_mns,
            }
        )
        if merged.model_path or merged.metadata:
            self.product_overlays[merged.product_name] = merged
        return merged

    def get_product(self, product_name: str) -> ProductRecord | None:
        rows = self.products_gateway.get_by("ProductName", product_name)
        if not rows:
            return self.product_overlays.get(product_name)
        return self._merge_product_overlay(self._map_product(rows[0]))

    def list_products(self) -> list[ProductRecord]:
        rows = self.products_gateway.get_all()
        products = {
            product.product_name: product for product in (self._merge_product_overlay(self._map_product(row)) for row in rows)
        }
        for product_name, overlay in self.product_overlays.items():
            products[product_name] = self._merge_product(products.get(product_name), overlay) if product_name in products else overlay
        return [products[key] for key in sorted(products)]

    def get_session(self) -> SessionRecord:
        rows = self.session_gateway.get_by("ID", 1)
        if not rows:
            self._ensure_session_row()
            rows = self.session_gateway.get_by("ID", 1)
        base_session = self._map_session(rows[0]) if rows else SessionRecord()
        session = self._merge_session_overlay(base_session)
        self.session = session
        return session

    def save_session(self, session: SessionRecord) -> SessionRecord:
        self.session_gateway.insert_or_update(
            {
                "ID": 1,
                "UserName": session.user_name or None,
                "ResultTime": session.result_time,
                "SleepTime": session.sleep_time,
                "ZoomFactor": session.zoom_factor,
                "OffsetX": session.offset_x,
                "OffsetY": session.offset_y,
                "ImageWidth": session.image_width,
                "ImageHeight": session.image_height,
                "ROIx1": session.roi_x1,
                "ROIx2": session.roi_x2,
                "ROIx3": session.roi_x3,
                "ROIx4": session.roi_x4,
                "ROIx5": session.roi_x5,
                "ROIy1": session.roi_y1,
                "ROIy2": session.roi_y2,
                "ROIy3": session.roi_y3,
                "ROIy4": session.roi_y4,
                "ROIy5": session.roi_y5,
                "PLCIP": session.plc_ip or None,
                "PLCProtocol": session.plc_protocol or None,
                "PLCPort": session.plc_port or None,
            }
        )
        self.session_overlay = {
            "product_name": session.product_name,
            "camera_vendor": session.camera_vendor,
            "plc_vendor": session.plc_vendor,
        }
        self.session = session
        return self.get_session()

    def update_session(self, **updates) -> SessionRecord:
        current = self.get_session()
        return self.save_session(
            SessionRecord(
                user_name=str(updates.get("user_name", current.user_name)),
                product_name=str(updates.get("product_name", current.product_name)),
                camera_vendor=str(updates.get("camera_vendor", current.camera_vendor)),
                plc_vendor=str(updates.get("plc_vendor", current.plc_vendor)),
                plc_ip=str(updates.get("plc_ip", current.plc_ip)),
                plc_port=updates.get("plc_port", current.plc_port),
                plc_protocol=str(updates.get("plc_protocol", current.plc_protocol)),
                result_time=updates.get("result_time", current.result_time),
                sleep_time=updates.get("sleep_time", current.sleep_time),
                zoom_factor=updates.get("zoom_factor", current.zoom_factor),
                offset_x=int(updates.get("offset_x", current.offset_x)),
                offset_y=int(updates.get("offset_y", current.offset_y)),
                image_width=int(updates.get("image_width", current.image_width)),
                image_height=int(updates.get("image_height", current.image_height)),
                roi_x1=int(updates.get("roi_x1", current.roi_x1)),
                roi_x2=int(updates.get("roi_x2", current.roi_x2)),
                roi_x3=int(updates.get("roi_x3", current.roi_x3)),
                roi_x4=int(updates.get("roi_x4", current.roi_x4)),
                roi_x5=int(updates.get("roi_x5", current.roi_x5)),
                roi_y1=int(updates.get("roi_y1", current.roi_y1)),
                roi_y2=int(updates.get("roi_y2", current.roi_y2)),
                roi_y3=int(updates.get("roi_y3", current.roi_y3)),
                roi_y4=int(updates.get("roi_y4", current.roi_y4)),
                roi_y5=int(updates.get("roi_y5", current.roi_y5)),
            )
        )

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _ensure_session_row(self) -> None:
        rows = self.session_gateway.get_by("ID", 1)
        if not rows:
            self.session_gateway.insert_or_update({"ID": 1})

    def _map_product(self, row: dict) -> ProductRecord:
        return ProductRecord(
            product_name=str(row.get("ProductName") or ""),
            model_path=str(row.get("ModelPath") or ""),
            exposure=self._int_or_none(row.get("Exposure")),
            default_number=self._int_or_none(row.get("DefaultNumber")),
            threshold_accept=self._float_or_none(row.get("ThresholdAccept")),
            threshold_mns=self._float_or_none(row.get("ThresholdMns")),
        )

    def _map_session(self, row: dict) -> SessionRecord:
        return SessionRecord(
            user_name=str(row.get("UserName") or ""),
            plc_ip=str(row.get("PLCIP") or ""),
            plc_port=row.get("PLCPort") or "",
            plc_protocol=str(row.get("PLCProtocol") or ""),
            result_time=self._int_or_none(row.get("ResultTime")),
            sleep_time=self._int_or_none(row.get("SleepTime")),
            zoom_factor=self._float_or_none(row.get("ZoomFactor")),
            offset_x=int(row.get("OffsetX") or 0),
            offset_y=int(row.get("OffsetY") or 0),
            image_width=int(row.get("ImageWidth") or 0),
            image_height=int(row.get("ImageHeight") or 0),
            roi_x1=int(row.get("ROIx1") or 0),
            roi_x2=int(row.get("ROIx2") or 0),
            roi_x3=int(row.get("ROIx3") or 0),
            roi_x4=int(row.get("ROIx4") or 0),
            roi_x5=int(row.get("ROIx5") or 0),
            roi_y1=int(row.get("ROIy1") or 0),
            roi_y2=int(row.get("ROIy2") or 0),
            roi_y3=int(row.get("ROIy3") or 0),
            roi_y4=int(row.get("ROIy4") or 0),
            roi_y5=int(row.get("ROIy5") or 0),
        )

    def _merge_product_overlay(self, product: ProductRecord) -> ProductRecord:
        overlay = self.product_overlays.get(product.product_name)
        return self._merge_product(product, overlay) if overlay is not None else product

    def _merge_product(self, base: ProductRecord | None, override: ProductRecord) -> ProductRecord:
        if base is None:
            return override
        return ProductRecord(
            product_name=override.product_name or base.product_name,
            model_path=override.model_path or base.model_path,
            exposure=override.exposure if override.exposure is not None else base.exposure,
            default_number=override.default_number if override.default_number is not None else base.default_number,
            threshold_accept=override.threshold_accept if override.threshold_accept is not None else base.threshold_accept,
            threshold_mns=override.threshold_mns if override.threshold_mns is not None else base.threshold_mns,
            metadata={**base.metadata, **override.metadata},
        )

    def _merge_session_overlay(self, session: SessionRecord) -> SessionRecord:
        return SessionRecord(
            user_name=session.user_name,
            product_name=str(self.session_overlay.get("product_name", session.product_name)),
            camera_vendor=str(self.session_overlay.get("camera_vendor", session.camera_vendor)),
            plc_vendor=str(self.session_overlay.get("plc_vendor", session.plc_vendor)),
            plc_ip=session.plc_ip,
            plc_port=session.plc_port,
            plc_protocol=session.plc_protocol,
            result_time=session.result_time,
            sleep_time=session.sleep_time,
            zoom_factor=session.zoom_factor,
            offset_x=session.offset_x,
            offset_y=session.offset_y,
            image_width=session.image_width,
            image_height=session.image_height,
            roi_x1=session.roi_x1,
            roi_x2=session.roi_x2,
            roi_x3=session.roi_x3,
            roi_x4=session.roi_x4,
            roi_x5=session.roi_x5,
            roi_y1=session.roi_y1,
            roi_y2=session.roi_y2,
            roi_y3=session.roi_y3,
            roi_y4=session.roi_y4,
            roi_y5=session.roi_y5,
        )

    @staticmethod
    def _int_or_none(value: object) -> int | None:
        return int(value) if value is not None else None

    @staticmethod
    def _float_or_none(value: object) -> float | None:
        return float(value) if value is not None else None
