from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.db.models import InspectionHistoryRecord, ProductRecord, SessionRecord, UserRecord


@dataclass
class RepositoryAdapter:
    events: list[str] = field(default_factory=list)
    users: dict[str, UserRecord] = field(default_factory=dict)
    products: dict[str, ProductRecord] = field(default_factory=dict)
    session: SessionRecord = field(default_factory=SessionRecord)
    inspection_history: list[InspectionHistoryRecord] = field(default_factory=list)

    def record_event(self, message: str) -> None:
        self.events.append(message)

    def save_user(self, user: UserRecord) -> UserRecord:
        self.users[user.user_name] = user
        return user

    def get_user(self, user_name: str) -> UserRecord | None:
        return self.users.get(user_name)

    def upsert_product(self, product: ProductRecord) -> ProductRecord:
        existing = self.products.get(product.product_name)
        if existing is not None:
            merged = ProductRecord(
                product_name=product.product_name,
                model_path=product.model_path or existing.model_path,
                exposure=product.exposure if product.exposure is not None else existing.exposure,
                default_number=product.default_number if product.default_number is not None else existing.default_number,
                threshold_accept=product.threshold_accept if product.threshold_accept is not None else existing.threshold_accept,
                threshold_mns=product.threshold_mns if product.threshold_mns is not None else existing.threshold_mns,
                metadata={**existing.metadata, **product.metadata},
            )
            self.products[product.product_name] = merged
            return merged
        self.products[product.product_name] = product
        return product

    def get_product(self, product_name: str) -> ProductRecord | None:
        return self.products.get(product_name)

    def list_products(self) -> list[ProductRecord]:
        return [self.products[key] for key in sorted(self.products)]

    def get_session(self) -> SessionRecord:
        return self.session

    def save_session(self, session: SessionRecord) -> SessionRecord:
        self.session = session
        return session

    def update_session(self, **updates) -> SessionRecord:
        self.session = SessionRecord(
            user_name=str(updates.get("user_name", self.session.user_name)),
            product_name=str(updates.get("product_name", self.session.product_name)),
            camera_vendor=str(updates.get("camera_vendor", self.session.camera_vendor)),
            plc_vendor=str(updates.get("plc_vendor", self.session.plc_vendor)),
            plc_ip=str(updates.get("plc_ip", self.session.plc_ip)),
            plc_port=updates.get("plc_port", self.session.plc_port),
            plc_protocol=str(updates.get("plc_protocol", self.session.plc_protocol)),
            result_time=updates.get("result_time", self.session.result_time),
            sleep_time=updates.get("sleep_time", self.session.sleep_time),
            zoom_factor=updates.get("zoom_factor", self.session.zoom_factor),
            offset_x=int(updates.get("offset_x", self.session.offset_x)),
            offset_y=int(updates.get("offset_y", self.session.offset_y)),
            image_width=int(updates.get("image_width", self.session.image_width)),
            image_height=int(updates.get("image_height", self.session.image_height)),
            roi_x1=int(updates.get("roi_x1", self.session.roi_x1)),
            roi_x2=int(updates.get("roi_x2", self.session.roi_x2)),
            roi_x3=int(updates.get("roi_x3", self.session.roi_x3)),
            roi_x4=int(updates.get("roi_x4", self.session.roi_x4)),
            roi_x5=int(updates.get("roi_x5", self.session.roi_x5)),
            roi_y1=int(updates.get("roi_y1", self.session.roi_y1)),
            roi_y2=int(updates.get("roi_y2", self.session.roi_y2)),
            roi_y3=int(updates.get("roi_y3", self.session.roi_y3)),
            roi_y4=int(updates.get("roi_y4", self.session.roi_y4)),
            roi_y5=int(updates.get("roi_y5", self.session.roi_y5)),
        )
        return self.session

    def save_inspection_history(self, entry: InspectionHistoryRecord) -> InspectionHistoryRecord:
        self.inspection_history.insert(0, entry)
        return entry

    def list_recent_inspection_history(self, limit: int = 10) -> list[InspectionHistoryRecord]:
        return list(self.inspection_history[: max(0, int(limit))])
