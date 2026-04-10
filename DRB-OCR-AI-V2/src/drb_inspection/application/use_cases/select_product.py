from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import ProductSelectionResult


@dataclass
class SelectProductUseCase:
    repository: RepositoryAdapter

    def execute(self, product_name: str) -> ProductSelectionResult:
        selected_name = product_name.strip()
        if not selected_name:
            raise ValueError("Current product is None.")

        product = self.repository.get_product(selected_name)
        if product is None:
            raise ValueError("Invalid product.")
        if not product.model_path:
            raise ValueError("Product has no Model AI.")

        session = self.repository.update_session(product_name=product.product_name)
        self.repository.record_event(f"Select product product={product.product_name}")
        return ProductSelectionResult(product=product, session=session)
