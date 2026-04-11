from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drb_inspection.application.contracts.context import ProductCatalogSyncResult
from drb_inspection.application.services.product_catalog_loader import ProductCatalogLoader
from drb_inspection.application.use_cases.sync_products import SyncProductsUseCase


@dataclass
class ImportProductCatalogUseCase:
    loader: ProductCatalogLoader
    sync_products: SyncProductsUseCase

    def execute(self, path: str | Path) -> ProductCatalogSyncResult:
        catalog_path = str(path).strip()
        if not catalog_path:
            raise ValueError("Product catalog path is required.")
        entries = self.loader.load_from_file(catalog_path)
        return self.sync_products.execute(entries)
