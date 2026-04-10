from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.models import ProductRecord
from drb_inspection.application.contracts.context import ProductCatalogEntry, ProductCatalogSyncResult


@dataclass
class SyncProductsUseCase:
    repository: RepositoryAdapter

    def execute(self, entries: list[ProductCatalogEntry]) -> ProductCatalogSyncResult:
        products: list[ProductRecord] = []
        for entry in entries:
            products.append(
                self.repository.upsert_product(
                    ProductRecord(
                        product_name=entry.product_name,
                        model_path=entry.model_path,
                        exposure=entry.exposure,
                        default_number=entry.default_number,
                        threshold_accept=entry.threshold_accept,
                        threshold_mns=entry.threshold_mns,
                        metadata=dict(entry.metadata),
                    )
                )
            )
        self.repository.record_event(f"Sync product catalog count={len(products)}")
        return ProductCatalogSyncResult(products=products)
