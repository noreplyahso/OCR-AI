from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.models import ProductRecord
from drb_inspection.application.contracts.context import ProductSettingsResult


@dataclass
class SaveProductSettingsUseCase:
    repository: RepositoryAdapter

    def execute(
        self,
        *,
        product_name: str | None = None,
        model_path: str | None = None,
        exposure: int | None = None,
        default_number: int | None = None,
        threshold_accept: float | None = None,
        threshold_mns: float | None = None,
    ) -> ProductSettingsResult:
        session = self.repository.get_session()
        selected_name = (product_name or session.product_name).strip()
        if not selected_name:
            raise ValueError("Current product is None.")

        current_product = self.repository.get_product(selected_name)
        if current_product is None:
            raise ValueError("Invalid product.")

        updated_product = self.repository.upsert_product(
            ProductRecord(
                product_name=selected_name,
                model_path=(model_path or current_product.model_path).strip(),
                exposure=exposure,
                default_number=default_number,
                threshold_accept=threshold_accept,
                threshold_mns=threshold_mns,
                metadata=dict(current_product.metadata),
            )
        )
        updated_session = self.repository.update_session(product_name=updated_product.product_name)
        self.repository.record_event(
            "Save product settings "
            f"product={updated_product.product_name} "
            "keys=['default_number', 'exposure', 'model_path', 'threshold_accept', 'threshold_mns']"
        )
        return ProductSettingsResult(product=updated_product, session=updated_session)
