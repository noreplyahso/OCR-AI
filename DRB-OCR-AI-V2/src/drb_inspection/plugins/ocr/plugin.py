from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import (
    InspectionTaskRequest,
    InspectionTaskResult,
    TaskStatus,
)
from drb_inspection.plugins.ocr.matcher import match_expected_text
from drb_inspection.plugins.ocr.preprocess import crop_and_rotate_roi
from drb_inspection.plugins.ocr.runtime import LegacyOcrRuntimeGateway


@dataclass
class OcrPlugin:
    name: str = "ocr"
    runtime_gateway: LegacyOcrRuntimeGateway | None = None
    model_handle: object | None = None
    loaded_model_path: str | None = None

    def run(self, request: InspectionTaskRequest) -> InspectionTaskResult:
        try:
            image = self._resolve_image(request)
        except ValueError as exc:
            return InspectionTaskResult(
                task_id=request.task_id,
                task_type=request.task_type,
                status=TaskStatus.ERROR,
                score=0.0,
                message=str(exc),
                outputs={
                    "text": "",
                    "matched_text": "",
                    "expected_text": str(request.parameters.get("expected_text", "")),
                    "roi_name": request.roi_name,
                },
            )
        model_path = request.parameters.get("model_path")
        expected_text = str(request.parameters.get("expected_text", ""))
        detected_text = str(request.parameters.get("detected_text", ""))

        if self.runtime_gateway and image is not None and model_path:
            resolved_model_path = str(model_path)
            if self.model_handle is None or self.loaded_model_path != resolved_model_path:
                self.model_handle = self.runtime_gateway.load_model(resolved_model_path)
                self.loaded_model_path = resolved_model_path
            prediction = self.runtime_gateway.predict(
                image,
                self.model_handle,
                acceptance_threshold=float(request.parameters.get("acceptance_threshold", 0.8)),
                duplication_threshold=float(request.parameters.get("duplication_threshold", 0.5)),
                row_threshold=float(request.parameters.get("row_threshold", 0.2)),
            )
            if prediction.error == "exception: stack overflow":
                return InspectionTaskResult(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    status=TaskStatus.ERROR,
                    score=0.0,
                    message="Legacy OCR runtime failed with stack overflow.",
                    outputs={
                        "text": prediction.text,
                        "raw_result": prediction.raw,
                        "error": prediction.error,
                    },
                )
            detected_text = prediction.text

        if expected_text and not detected_text:
            if image is None:
                return InspectionTaskResult(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    status=TaskStatus.ERROR,
                    score=0.0,
                    message="OCR image is not available.",
                    outputs={
                        "text": "",
                        "matched_text": "",
                        "expected_text": expected_text,
                        "roi_name": request.roi_name,
                    },
                )
            if self.runtime_gateway is None:
                return InspectionTaskResult(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    status=TaskStatus.ERROR,
                    score=0.0,
                    message="OCR runtime gateway is not configured.",
                    outputs={
                        "text": "",
                        "matched_text": "",
                        "expected_text": expected_text,
                        "roi_name": request.roi_name,
                    },
                )
            if not model_path:
                return InspectionTaskResult(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    status=TaskStatus.ERROR,
                    score=0.0,
                    message="OCR model path is not configured.",
                    outputs={
                        "text": "",
                        "matched_text": "",
                        "expected_text": expected_text,
                        "roi_name": request.roi_name,
                    },
                )

        if expected_text:
            match_result = match_expected_text(detected_text, expected_text)
            return InspectionTaskResult(
                task_id=request.task_id,
                task_type=request.task_type,
                status=TaskStatus.PASS if match_result.matched else TaskStatus.FAIL,
                score=1.0 if match_result.matched else 0.0,
                message="OCR text matched expected product." if match_result.matched else "OCR text did not match expected product.",
                outputs={
                    "text": detected_text,
                    "matched_text": match_result.canonical_text,
                    "expected_text": expected_text,
                    "roi_name": request.roi_name,
                },
            )

        return InspectionTaskResult(
            task_id=request.task_id,
            task_type=request.task_type,
            status=TaskStatus.PASS if detected_text else TaskStatus.FAIL,
            score=1.0 if detected_text else 0.0,
            message="OCR text extracted." if detected_text else "OCR text was empty.",
            outputs={
                "text": detected_text,
                "matched_text": "",
                "expected_text": expected_text,
                "roi_name": request.roi_name,
            },
        )

    def _resolve_image(self, request: InspectionTaskRequest):
        if "image" in request.parameters:
            return request.parameters.get("image")

        frame = request.parameters.get("frame")
        roi_rect = request.parameters.get("roi_rect")
        if frame is None:
            return None
        if roi_rect is None:
            return frame
        return crop_and_rotate_roi(
            frame,
            roi_rect,
            rotate_clockwise=bool(request.parameters.get("rotate_clockwise", True)),
        )
