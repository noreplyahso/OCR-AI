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
        expected_text = str(request.parameters.get("expected_text", ""))
        detected_text = str(request.parameters.get("detected_text", ""))
        roi_rect = request.parameters.get("roi_rect")
        acceptance_threshold = float(request.parameters.get("acceptance_threshold", 0.8))
        duplication_threshold = float(request.parameters.get("duplication_threshold", 0.5))
        row_threshold = float(request.parameters.get("row_threshold", 20))
        if detected_text:
            return self._build_text_result(
                request=request,
                detected_text=detected_text,
                expected_text=expected_text,
                roi_rect=roi_rect,
                roi_image=None,
                raw_result=None,
                error="",
                detection_boxes=None,
                detection_points=None,
                acceptance_threshold=acceptance_threshold,
                duplication_threshold=duplication_threshold,
                row_threshold=row_threshold,
            )

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
                    "roi_rect": roi_rect,
                },
            )
        model_path = request.parameters.get("model_path")
        detected_text = ""
        prediction_raw = None
        prediction_error = ""
        prediction_boxes = None
        prediction_points = None

        if self.runtime_gateway and image is not None and model_path:
            resolved_model_path = str(model_path)
            if self.model_handle is None or self.loaded_model_path != resolved_model_path:
                self.model_handle = self.runtime_gateway.load_model(resolved_model_path)
                self.loaded_model_path = resolved_model_path
            prediction = self.runtime_gateway.predict(
                image,
                self.model_handle,
                acceptance_threshold=acceptance_threshold,
                duplication_threshold=duplication_threshold,
                row_threshold=row_threshold,
            )
            prediction_raw = prediction.raw
            prediction_error = prediction.error
            prediction_boxes = getattr(prediction, "boxes", None)
            prediction_points = getattr(prediction, "box_points", None)
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
                        "detection_boxes": prediction_boxes,
                        "detection_points": prediction_points,
                        "acceptance_threshold": acceptance_threshold,
                        "duplication_threshold": duplication_threshold,
                        "row_threshold": row_threshold,
                        "roi_name": request.roi_name,
                        "roi_rect": roi_rect,
                        "roi_image": image,
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

        return self._build_text_result(
            request=request,
            detected_text=detected_text,
            expected_text=expected_text,
            roi_rect=roi_rect,
            roi_image=image,
            raw_result=prediction_raw,
            error=prediction_error,
            detection_boxes=prediction_boxes,
            detection_points=prediction_points,
            acceptance_threshold=acceptance_threshold,
            duplication_threshold=duplication_threshold,
            row_threshold=row_threshold,
        )

    def _build_text_result(
        self,
        *,
        request: InspectionTaskRequest,
        detected_text: str,
        expected_text: str,
        roi_rect,
        roi_image,
        raw_result,
        error: str,
        detection_boxes,
        detection_points,
        acceptance_threshold: float,
        duplication_threshold: float,
        row_threshold: float,
    ) -> InspectionTaskResult:
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
                    "matched_variant": match_result.matched_variant,
                    "match_mode": match_result.match_mode,
                    "raw_result": raw_result,
                    "error": error,
                    "detection_boxes": detection_boxes,
                    "detection_points": detection_points,
                    "acceptance_threshold": acceptance_threshold,
                    "duplication_threshold": duplication_threshold,
                    "row_threshold": row_threshold,
                    "roi_name": request.roi_name,
                    "roi_rect": roi_rect,
                    "roi_image": roi_image,
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
                "matched_variant": "",
                "match_mode": "",
                "raw_result": raw_result,
                "error": error,
                "detection_boxes": detection_boxes,
                "detection_points": detection_points,
                "acceptance_threshold": acceptance_threshold,
                "duplication_threshold": duplication_threshold,
                "row_threshold": row_threshold,
                "roi_name": request.roi_name,
                "roi_rect": roi_rect,
                "roi_image": roi_image,
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
