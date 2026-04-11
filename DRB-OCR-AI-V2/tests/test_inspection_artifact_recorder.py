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
    annotated_frame_path = Path(artifacts.annotated_frame_path)
    task_path = Path(artifacts.task_artifacts[0].image_path)
    debug_path = Path(artifacts.task_artifacts[0].debug_path)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    task_debug_payload = json.loads(debug_path.read_text(encoding="utf-8"))

    assert summary_path.exists()
    assert frame_path.exists()
    assert artifacts.annotated_frame_path
    assert annotated_frame_path.exists()
    assert task_path.exists()
    assert debug_path.exists()
    assert payload["product_name"] == "PRODUCT-A"
    assert payload["frame_path"] == str(frame_path)
    assert payload["annotated_frame_path"] == str(annotated_frame_path)
    assert payload["tasks"][0]["artifact_path"] == str(task_path)
    assert payload["tasks"][0]["debug_path"] == str(debug_path)
    assert task_debug_payload["task_id"] == "ocr_label_1"
    assert task_debug_payload["image_path"] == str(task_path)
    assert task_debug_payload["outputs"]["text"] == "PRODUCT-A"
    assert "roi_image" not in payload["tasks"][0]["outputs"]


def test_artifact_recorder_hides_mismatched_ocr_text_in_overlay_annotations(tmp_path: Path) -> None:
    recorder = InspectionArtifactRecorder(base_dir=tmp_path)
    task_result = InspectionTaskResult(
        task_id="ocr_label_1",
        task_type=InspectionTaskType.OCR,
        status=TaskStatus.FAIL,
        score=0.0,
        message="OCR text did not match expected product.",
        outputs={
            "text": "WRONG-TEXT",
            "matched_text": "",
            "expected_text": "PRODUCT-A",
            "roi_name": "label_roi_1",
            "roi_rect": (0, 0, 2, 2),
            "roi_image": [[255, 0], [0, 255]],
        },
    )

    annotations = recorder._build_task_annotations([task_result])

    assert len(annotations) == 1
    assert annotations[0]["status"] == "fail"
    assert annotations[0]["label"] == ""


def test_artifact_recorder_preserves_raw_text_in_debug_payload(tmp_path: Path) -> None:
    recorder = InspectionArtifactRecorder(base_dir=tmp_path)
    task_result = InspectionTaskResult(
        task_id="ocr_label_1",
        task_type=InspectionTaskType.OCR,
        status=TaskStatus.PASS,
        score=1.0,
        message="OCR text matched expected product.",
        outputs={
            "text": "PRODUCT-A",
            "raw_text": ["PRODUCT-", "A"],
            "text_was_normalized": False,
            "matched_text": "PRODUCT-A",
            "expected_text": "PRODUCT-A",
            "roi_name": "label_roi_1",
            "roi_rect": (0, 0, 2, 2),
            "roi_image": [[255, 0], [0, 255]],
        },
    )

    payload = recorder._build_task_debug_payload(task_result, image_path=None)

    assert payload["outputs"]["raw_text"] == ["PRODUCT-", "A"]
    assert payload["outputs"]["text_was_normalized"] is False
