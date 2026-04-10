from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import (
    InspectionTaskRequest,
    InspectionTaskType,
    TaskStatus,
)
from drb_inspection.plugins.ocr.plugin import OcrPlugin


@dataclass
class _FakeLegacyGateway:
    loaded_model_path: str | None = None
    load_count: int = 0

    def load_model(self, model_path: str):
        self.loaded_model_path = model_path
        self.load_count += 1
        return {"model_path": model_path}

    def predict(self, image, model, **kwargs):
        return type(
            "_Prediction",
            (),
            {"text": "OCR-RESULT", "error": "", "raw": (None, "OCR-RESULT", None, "")},
        )()


def test_ocr_plugin_uses_legacy_runtime_gateway_when_available() -> None:
    gateway = _FakeLegacyGateway()
    plugin = OcrPlugin(runtime_gateway=gateway)
    request = InspectionTaskRequest(
        task_id="ocr_runtime",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://runtime",
        roi_name="label_roi",
        parameters={
            "image": object(),
            "model_path": "models/ocr.pt",
            "expected_text": "OCR-RESULT",
        },
    )

    result = plugin.run(request)

    assert gateway.loaded_model_path == "models/ocr.pt"
    assert result.outputs["text"] == "OCR-RESULT"
    assert result.outputs["matched_text"] == "OCR-RESULT"
    assert result.status == TaskStatus.PASS


def test_ocr_plugin_reloads_model_when_model_path_changes() -> None:
    gateway = _FakeLegacyGateway()
    plugin = OcrPlugin(runtime_gateway=gateway)

    first = InspectionTaskRequest(
        task_id="ocr_runtime_1",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://runtime-1",
        roi_name="label_roi",
        parameters={
            "image": object(),
            "model_path": "models/ocr_a.pt",
            "expected_text": "OCR-RESULT",
        },
    )
    second = InspectionTaskRequest(
        task_id="ocr_runtime_2",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://runtime-2",
        roi_name="label_roi",
        parameters={
            "image": object(),
            "model_path": "models/ocr_b.pt",
            "expected_text": "OCR-RESULT",
        },
    )

    plugin.run(first)
    plugin.run(second)

    assert gateway.load_count == 2
    assert gateway.loaded_model_path == "models/ocr_b.pt"


def test_ocr_plugin_crops_roi_and_matches_expected_text_without_runtime() -> None:
    plugin = OcrPlugin()
    request = InspectionTaskRequest(
        task_id="ocr_match",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://roi",
        roi_name="label_roi",
        parameters={
            "frame": [
                ["x", "I", "S", "3"],
                ["x", "5", "R", "-"],
                ["x", "1", "0", "0"],
            ],
            "roi_rect": (1, 0, 3, 3),
            "detected_text": "IS35R-100",
            "expected_text": "IS35R-100",
        },
    )

    result = plugin.run(request)

    assert result.status == TaskStatus.PASS
    assert result.outputs["matched_text"] == "IS35R-100"


def test_ocr_plugin_returns_error_when_legacy_runtime_reports_stack_overflow() -> None:
    gateway = _FakeLegacyGateway()
    gateway.predict = lambda *args, **kwargs: type(
        "_Prediction",
        (),
        {"text": "", "error": "exception: stack overflow", "raw": ()},
    )()
    plugin = OcrPlugin(runtime_gateway=gateway)
    request = InspectionTaskRequest(
        task_id="ocr_stack_overflow",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://runtime",
        roi_name="label_roi",
        parameters={
            "image": object(),
            "model_path": "models/ocr.pt",
            "expected_text": "IS35R-100",
        },
    )

    result = plugin.run(request)

    assert result.status == TaskStatus.ERROR
    assert result.outputs["error"] == "exception: stack overflow"


def test_ocr_plugin_returns_error_when_expected_text_has_no_runtime_or_detected_input() -> None:
    plugin = OcrPlugin()
    request = InspectionTaskRequest(
        task_id="ocr_missing_runtime",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://missing",
        roi_name="label_roi",
        parameters={
            "expected_text": "IS35R-100",
        },
    )

    result = plugin.run(request)

    assert result.status == TaskStatus.ERROR
    assert "image is not available" in result.message.lower()
