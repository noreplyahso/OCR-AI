from __future__ import annotations

from drb_inspection.application.services.product_catalog_loader import ProductCatalogLoader


def test_product_catalog_loader_reads_csv_rows(tmp_path) -> None:
    catalog_path = tmp_path / "product_catalog.csv"
    catalog_path.write_text(
        "Product name,Model path,Exposure,Default number,Threshold accept,MNS threshold,Department\n"
        "PRODUCT-X,models/product_x.pt,4000,150,0.6,0.2,QA\n"
        "PRODUCT-Y,models/product_y.pt,4200,180,0.8,0.3,QA\n",
        encoding="utf-8",
    )

    entries = ProductCatalogLoader().load_from_file(catalog_path)

    assert len(entries) == 2
    assert entries[0].product_name == "PRODUCT-X"
    assert entries[0].model_path == "models/product_x.pt"
    assert entries[0].exposure == 4000
    assert entries[0].default_number == 150
    assert entries[0].threshold_accept == 0.6
    assert entries[0].threshold_mns == 0.2
    assert entries[0].metadata["Department"] == "QA"
