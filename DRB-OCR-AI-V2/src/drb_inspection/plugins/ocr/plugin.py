from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

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
        has_detected_override = "detected_text" in request.parameters
        explicit_detected_text = request.parameters.get("detected_text", "")
        expected_text = self._normalize_text(request.parameters.get("expected_text", ""))
        detected_text = self._normalize_text(explicit_detected_text)
        roi_rect = request.parameters.get("roi_rect")
        acceptance_threshold = float(request.parameters.get("acceptance_threshold", 0.8))
        duplication_threshold = float(request.parameters.get("duplication_threshold", 0.5))
        row_threshold = float(request.parameters.get("row_threshold", 20))
        if has_detected_override:
            return self._build_text_result(
                request=request,
                detected_text=detected_text,
                raw_detected_text=explicit_detected_text,
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
                warning="",
                reason="",
                source="detected_override",
            )

        try:
            image = self._resolve_image(request)
        except ValueError as exc:
            return self._build_error_result(
                request=request,
                message=str(exc),
                detected_text="",
                raw_detected_text=explicit_detected_text,
                expected_text=expected_text,
                roi_rect=roi_rect,
                roi_image=None,
                raw_result=None,
                error=str(exc),
                detection_boxes=None,
                detection_points=None,
                acceptance_threshold=acceptance_threshold,
                duplication_threshold=duplication_threshold,
                row_threshold=row_threshold,
                warning="",
                reason="invalid_roi",
                source="detected_override",
            )

        model_path = request.parameters.get("model_path")
        detected_text = ""
        prediction_raw = None
        prediction_error = ""
        prediction_warning = ""
        prediction_boxes = None
        prediction_points = None
        prediction_text_raw = None

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
            prediction_text_raw = prediction.text
            if prediction.error == "exception: stack overflow":
                return self._build_error_result(
                    request=request,
                    message="Legacy OCR runtime failed with stack overflow.",
                    detected_text=self._normalize_text(prediction.text),
                    raw_detected_text=prediction.text,
                    expected_text=expected_text,
                    roi_rect=roi_rect,
                    roi_image=image,
                    raw_result=prediction.raw,
                    error=prediction.error,
                    detection_boxes=prediction_boxes,
                    detection_points=prediction_points,
                    acceptance_threshold=acceptance_threshold,
                    duplication_threshold=duplication_threshold,
                    row_threshold=row_threshold,
                    warning="",
                    reason="runtime_stack_overflow",
                    source="runtime",
                )
            if prediction_error and not prediction.text:
                return self._build_error_result(
                    request=request,
                    message=f"Legacy OCR runtime failed: {prediction_error}",
                    detected_text="",
                    raw_detected_text=prediction.text,
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
                    warning="",
                    reason="runtime_error",
                    source="runtime",
                )
            if prediction_error and prediction.text:
                prediction_warning = prediction_error
                prediction_error = ""
            detected_text = self._normalize_text(prediction.text)

        if expected_text and not detected_text:
            if image is None:
                return self._build_error_result(
                    request=request,
                    message="OCR image is not available.",
                    detected_text="",
                    raw_detected_text=prediction_text_raw,
                    expected_text=expected_text,
                    roi_rect=roi_rect,
                    roi_image=None,
                    raw_result=prediction_raw,
                    error="OCR image is not available.",
                    detection_boxes=prediction_boxes,
                    detection_points=prediction_points,
                    acceptance_threshold=acceptance_threshold,
                    duplication_threshold=duplication_threshold,
                    row_threshold=row_threshold,
                    warning="",
                    reason="missing_image",
                    source="image_input",
                )
            if self.runtime_gateway is None:
                return self._build_error_result(
                    request=request,
                    message="OCR runtime gateway is not configured.",
                    detected_text="",
                    raw_detected_text=prediction_text_raw,
                    expected_text=expected_text,
                    roi_rect=roi_rect,
                    roi_image=image,
                    raw_result=prediction_raw,
                    error="OCR runtime gateway is not configured.",
                    detection_boxes=prediction_boxes,
                    detection_points=prediction_points,
                    acceptance_threshold=acceptance_threshold,
                    duplication_threshold=duplication_threshold,
                    row_threshold=row_threshold,
                    warning="",
                    reason="missing_runtime_gateway",
                    source="image_input",
                )
            if not model_path:
                return self._build_error_result(
                    request=request,
                    message="OCR model path is not configured.",
                    detected_text="",
                    raw_detected_text=prediction_text_raw,
                    expected_text=expected_text,
                    roi_rect=roi_rect,
                    roi_image=image,
                    raw_result=prediction_raw,
                    error="OCR model path is not configured.",
                    detection_boxes=prediction_boxes,
                    detection_points=prediction_points,
                    acceptance_threshold=acceptance_threshold,
                    duplication_threshold=duplication_threshold,
                    row_threshold=row_threshold,
                    warning="",
                    reason="missing_model_path",
                    source="image_input",
                )

        source = "runtime" if self.runtime_gateway and image is not None and model_path else "image_input"
        return self._build_text_result(
            request=request,
            detected_text=detected_text,
            raw_detected_text=prediction_text_raw,
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
            warning=prediction_warning,
            reason="",
            source=source,
        )

    def _build_text_result(
        self,
        *,
        request: InspectionTaskRequest,
        detected_text: str,
        raw_detected_text,
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
        warning: str,
        reason: str,
        source: str,
    ) -> InspectionTaskResult:
        raw_match_text = self._raw_text_for_match(raw_detected_text)
        has_raw_text = bool(raw_match_text)
        if expected_text:
            match_result = match_expected_text(raw_match_text or detected_text, expected_text)
            matched = match_result.matched
            result_reason = reason or ("text_match" if matched else "empty_text" if not has_raw_text else "text_mismatch")
            message = (
                "OCR text matched expected product."
                if matched
                else "OCR text was empty for expected product."
                if not has_raw_text
                else "OCR text did not match expected product."
            )
            status = (
                TaskStatus.PASS
                if matched
                else TaskStatus.SKIPPED
                if not has_raw_text
                else TaskStatus.FAIL
            )
            return InspectionTaskResult(
                task_id=request.task_id,
                task_type=request.task_type,
                status=status,
                score=1.0 if matched else 0.0,
                message=message,
                outputs=self._build_outputs(
                    request=request,
                    detected_text=detected_text,
                    raw_detected_text=raw_detected_text,
                    matched_text=match_result.canonical_text,
                    expected_text=expected_text,
                    matched_variant=match_result.matched_variant,
                    match_mode=match_result.match_mode,
                    raw_result=raw_result,
                    error=error,
                    detection_boxes=detection_boxes,
                    detection_points=detection_points,
                    acceptance_threshold=acceptance_threshold,
                    duplication_threshold=duplication_threshold,
                    row_threshold=row_threshold,
                    warning=warning,
                    roi_rect=roi_rect,
                    roi_image=roi_image,
                    reason=result_reason,
                    source=source,
                ),
            )

        result_reason = reason or ("text_extracted" if has_raw_text else "empty_text")
        status = TaskStatus.PASS if has_raw_text else TaskStatus.SKIPPED
        return InspectionTaskResult(
            task_id=request.task_id,
            task_type=request.task_type,
            status=status,
            score=1.0 if has_raw_text else 0.0,
            message="OCR text extracted." if has_raw_text else "OCR text was empty.",
            outputs=self._build_outputs(
                request=request,
                detected_text=detected_text,
                raw_detected_text=raw_detected_text,
                matched_text="",
                expected_text=expected_text,
                matched_variant="",
                match_mode="",
                raw_result=raw_result,
                error=error,
                detection_boxes=detection_boxes,
                detection_points=detection_points,
                acceptance_threshold=acceptance_threshold,
                duplication_threshold=duplication_threshold,
                row_threshold=row_threshold,
                warning=warning,
                roi_rect=roi_rect,
                roi_image=roi_image,
                reason=result_reason,
                source=source,
            ),
        )

    def _build_error_result(
        self,
        *,
        request: InspectionTaskRequest,
        message: str,
        detected_text: str,
        raw_detected_text,
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
        warning: str,
        reason: str,
        source: str,
    ) -> InspectionTaskResult:
        return InspectionTaskResult(
            task_id=request.task_id,
            task_type=request.task_type,
            status=TaskStatus.ERROR,
            score=0.0,
            message=message,
            outputs=self._build_outputs(
                request=request,
                detected_text=detected_text,
                raw_detected_text=raw_detected_text,
                matched_text="",
                expected_text=expected_text,
                matched_variant="",
                match_mode="",
                raw_result=raw_result,
                error=error,
                detection_boxes=detection_boxes,
                detection_points=detection_points,
                acceptance_threshold=acceptance_threshold,
                duplication_threshold=duplication_threshold,
                row_threshold=row_threshold,
                warning=warning,
                roi_rect=roi_rect,
                roi_image=roi_image,
                reason=reason,
                source=source,
            ),
        )

    def _build_outputs(
        self,
        *,
        request: InspectionTaskRequest,
        detected_text: str,
        raw_detected_text,
        matched_text: str,
        expected_text: str,
        matched_variant: str,
        match_mode: str,
        raw_result,
        error: str,
        detection_boxes,
        detection_points,
        acceptance_threshold: float,
        duplication_threshold: float,
        row_threshold: float,
        warning: str,
        roi_rect,
        roi_image,
        reason: str,
        source: str,
    ) -> dict[str, object]:
        raw_match_text = self._raw_text_for_match(raw_detected_text)
        has_text = bool(raw_match_text)
        text_was_normalized = self._normalize_text(raw_detected_text) != self._stringify_raw_text(raw_detected_text)
        return {
            "text": detected_text,
            "raw_text": raw_detected_text,
            "text_was_normalized": text_was_normalized,
            "matched_text": matched_text,
            "expected_text": expected_text,
            "matched_variant": matched_variant,
            "match_mode": match_mode,
            "raw_result": raw_result,
            "error": error,
            "warning": warning,
            "reason": reason,
            "source": source,
            "has_text": has_text,
            "counted_quantity": has_text,
            "detection_boxes": detection_boxes,
            "detection_points": detection_points,
            "acceptance_threshold": acceptance_threshold,
            "duplication_threshold": duplication_threshold,
            "row_threshold": row_threshold,
            "roi_name": request.roi_name,
            "roi_rect": roi_rect,
            "roi_image": roi_image,
        }

    def _normalize_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return (
                value.replace("\x00", "")
                .replace("\r", "")
                .replace("\n", "")
                .replace("\t", "")
                .strip()
            )
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            parts = [self._normalize_text(item) for item in value]
            return "".join(part for part in parts if part)
        return str(value).strip()

    def _stringify_raw_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            return "".join(self._stringify_raw_text(item) for item in value if item is not None)
        return str(value)

    def _raw_text_for_match(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            return "".join(self._raw_text_for_match(item) for item in value if item is not None)
        return str(value)

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
