from __future__ import annotations

import json
from pathlib import Path

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.db.models import SessionRecord
from drb_inspection.application.contracts.inspection import (
    InspectionCycleResult,
    InspectionRunResult,
    InspectionTaskResult,
    InspectionTaskType,
    TaskStatus,
)
from drb_inspection.application.services.inspection_artifact_recorder import InspectionArtifactRecorder


def test_artifact_recorder_saves_summary_frame_and_task_roi_images(tmp_path: Path) -> None:
    recorder = InspectionArtifactRecorder(base_dir=tmp_path)
    cycle_result = InspectionCycleResult(
        image_ref=ImageFrame(frame=[[0, 64], [128, 255]], capture_seconds=0.01),
        inspection=InspectionRunResult(
            recipe_name="inspection-PRODUCT-A",
            overall_status=TaskStatus.PASS,
            task_results=[
                InspectionTaskResult(
                    task_id="ocr_label_1",
                    task_type=InspectionTaskType.OCR,
                    status=TaskStatus.PASS,
                    score=1.0,
                    message="OCR text matched expected product.",
                    outputs={
                        "text": "PRODUCT-A",
                        "expected_text": "PRODUCT-A",
                        "roi_name": "label_roi_1",
                        "roi_rect": (0, 0, 2, 2),
                        "roi_image": [[255, 0], [0, 255]],
                    },
                )
            ],
        ),
        plc_result_sent="OK",
    )

    artifacts = recorder.record_cycle(
        product_name="PRODUCT-A",
        session=SessionRecord(product_name="PRODUCT-A"),
        cycle_result=cycle_result,
    )

    summary_path = Path(artifacts.summary_path)
    frame_path = Path(artifacts.frame_path)
    task_path = Path(artifacts.task_artifacts[0].image_path)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary_path.exists()
    assert frame_path.exists()
    assert task_path.exists()
    assert payload["product_name"] == "PRODUCT-A"
    assert payload["frame_path"] == str(frame_path)
    assert payload["tasks"][0]["artifact_path"] == str(task_path)
    assert "roi_image" not in payload["tasks"][0]["outputs"]
