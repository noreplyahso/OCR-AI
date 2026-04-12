from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from drb_inspection.adapters.db.models import SessionRecord
from drb_inspection.application.contracts.inspection import (
    InspectionCycleArtifacts,
    InspectionTaskResult,
    InspectionCycleResult,
    InspectionTaskArtifact,
)


@dataclass(frozen=True)
class InspectionArtifactRecorder:
    base_dir: Path

    def record_cycle(
        self,
        *,
        product_name: str,
        session: SessionRecord,
        cycle_result: InspectionCycleResult,
        include_task_artifacts: bool = True,
    ) -> InspectionCycleArtifacts:
        timestamp = datetime.now()
        cycle_dir = self._build_cycle_dir(
            product_name=product_name,
            status=cycle_result.plc_result_sent,
            timestamp=timestamp,
        )
        cycle_dir.mkdir(parents=True, exist_ok=True)

        source_frame = getattr(cycle_result.image_ref, "frame", cycle_result.image_ref)
        frame_path = self._try_save_image(
            cycle_dir / "frame",
            source_frame,
        )
        annotated_frame_path = self._try_save_annotated_frame(
            cycle_dir / "frame_annotated.png",
            source_frame,
            cycle_result.inspection.task_results,
        )
        task_artifacts = self._record_task_artifacts(
            task_results=cycle_result.inspection.task_results,
            cycle_dir=cycle_dir,
            include_task_artifacts=include_task_artifacts,
        )
        summary_path = cycle_dir / "summary.json"
        summary_path.write_text(
            json.dumps(
                self._build_summary_payload(
                    product_name=product_name,
                    session=session,
                    cycle_result=cycle_result,
                    timestamp=timestamp,
                    frame_path=frame_path,
                    annotated_frame_path=annotated_frame_path,
                    task_artifacts=task_artifacts,
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return InspectionCycleArtifacts(
            root_dir=str(cycle_dir),
            summary_path=str(summary_path),
            frame_path=str(frame_path) if frame_path else "",
            annotated_frame_path=str(annotated_frame_path) if annotated_frame_path else "",
            task_artifacts=task_artifacts,
        )

    def _build_cycle_dir(self, *, product_name: str, status: str, timestamp: datetime) -> Path:
        safe_product_name = self._slug(product_name or "unknown-product")
        safe_status = self._slug(status or "unknown")
        return (
            Path(self.base_dir)
            / timestamp.strftime("%Y-%m-%d")
            / safe_product_name
            / safe_status.upper()
            / timestamp.strftime("%H%M%S_%f")
        )

    def _record_task_artifacts(
        self,
        *,
        task_results,
        cycle_dir: Path,
        include_task_artifacts: bool,
    ) -> list[InspectionTaskArtifact]:
        if not include_task_artifacts:
            return []
        artifacts: list[InspectionTaskArtifact] = []
        for index, task_result in enumerate(task_results, start=1):
            task_slug = self._slug(task_result.task_id)
            roi_image = task_result.outputs.get("roi_image")
            image_path = self._try_save_image(
                cycle_dir / f"task_{index:02d}_{task_slug}_roi",
                roi_image,
            )
            debug_path = cycle_dir / f"task_{index:02d}_{task_slug}_debug.json"
            debug_path.write_text(
                json.dumps(
                    self._build_task_debug_payload(task_result, image_path=image_path),
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            artifacts.append(
                InspectionTaskArtifact(
                    task_id=task_result.task_id,
                    image_path=str(image_path) if image_path else "",
                    debug_path=str(debug_path),
                )
            )
        return artifacts

    def _build_summary_payload(
        self,
        *,
        product_name: str,
        session: SessionRecord,
        cycle_result: InspectionCycleResult,
        timestamp: datetime,
        frame_path: Path | None,
        annotated_frame_path: Path | None,
        task_artifacts: list[InspectionTaskArtifact],
    ) -> dict[str, object]:
        artifact_path_by_task = {
            artifact.task_id: artifact.image_path
            for artifact in task_artifacts
        }
        debug_path_by_task = {
            artifact.task_id: artifact.debug_path
            for artifact in task_artifacts
        }
        return {
            "recorded_at": timestamp.isoformat(),
            "product_name": product_name,
            "recipe_name": cycle_result.inspection.recipe_name,
            "overall_status": cycle_result.inspection.overall_status.value,
            "plc_result_sent": cycle_result.plc_result_sent,
            "message": cycle_result.inspection.message,
            "frame_path": str(frame_path) if frame_path else "",
            "annotated_frame_path": str(annotated_frame_path) if annotated_frame_path else "",
            "session": {
                "offset_x": session.offset_x,
                "offset_y": session.offset_y,
                "image_width": session.image_width,
                "image_height": session.image_height,
                "roi_rects": session.roi_rects(),
            },
            "tasks": [
                {
                    "task_id": task_result.task_id,
                    "task_type": task_result.task_type.value,
                    "status": task_result.status.value,
                    "score": task_result.score,
                    "message": task_result.message,
                    "outputs": self._sanitize_outputs(task_result.outputs),
                    "artifact_path": artifact_path_by_task.get(task_result.task_id, ""),
                    "debug_path": debug_path_by_task.get(task_result.task_id, ""),
                }
                for task_result in cycle_result.inspection.task_results
            ],
        }

    def _build_task_debug_payload(
        self,
        task_result: InspectionTaskResult,
        *,
        image_path: Path | None,
    ) -> dict[str, object]:
        outputs = self._sanitize_outputs(task_result.outputs)
        raw_result = task_result.outputs.get("raw_result")
        return {
            "task_id": task_result.task_id,
            "task_type": task_result.task_type.value,
            "status": task_result.status.value,
            "score": task_result.score,
            "message": task_result.message,
            "roi_name": task_result.outputs.get("roi_name", ""),
            "roi_rect": outputs.get("roi_rect", []),
            "image_path": str(image_path) if image_path else "",
            "raw_summary": self._summarize_raw_result(raw_result),
            "outputs": outputs,
        }

    def _sanitize_outputs(self, outputs: dict[str, object]) -> dict[str, object]:
        sanitized: dict[str, object] = {}
        for key, value in outputs.items():
            if key == "roi_image":
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
                continue
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                try:
                    sanitized[key] = list(value)
                    continue
                except TypeError:
                    pass
            sanitized[key] = str(value)
        return sanitized

    def _summarize_raw_result(self, value: object) -> str:
        if value is None:
            return "<none>"
        if isinstance(value, tuple):
            return f"tuple[{len(value)}]"
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return f"seq[{len(value)}]"
        text = str(value).strip()
        return text or "<none>"

    def _try_save_annotated_frame(
        self,
        path: Path,
        image: Any,
        task_results: Sequence[InspectionTaskResult],
    ) -> Path | None:
        qimage = self._build_qimage_from_array(image)
        annotations = self._build_task_annotations(task_results)
        if qimage is not None:
            try:
                from PyQt5.QtGui import QFont, QPainter, QPen

                annotated = qimage.copy()
                painter = QPainter(annotated)
                painter.setRenderHint(QPainter.Antialiasing)
                line_width = max(2, int(max(1, annotated.width()) / 500))
                label_font = QFont("Segoe UI", max(10, int(max(1, annotated.width()) / 95)))
                label_font.setBold(True)
                painter.setFont(label_font)
                for index, annotation in enumerate(annotations, start=1):
                    x_value, y_value, rect_width, rect_height = annotation["roi_rect"]
                    painter.setPen(QPen(self._annotation_color(annotation["status"]), line_width))
                    painter.drawRect(int(x_value), int(y_value), int(rect_width), int(rect_height))
                    painter.drawText(
                        int(x_value),
                        max(28, int(y_value) - 12),
                        annotation["label"] or f"ROI {index}",
                    )
                painter.end()
                if not annotated.save(str(path), "PNG"):
                    return None
                return path
            except Exception:
                pass
        rows = self._normalize_rows(image)
        if not rows:
            return None
        annotated_rows = self._draw_annotations_on_rows(rows, annotations)
        first_row = annotated_rows[0]
        if not first_row:
            return None
        if isinstance(first_row[0], Sequence) and not isinstance(first_row[0], (str, bytes, bytearray)):
            fallback_path = path.with_suffix(".ppm")
            self._write_ppm(fallback_path, annotated_rows)
            return fallback_path
        fallback_path = path.with_suffix(".pgm")
        self._write_pgm(fallback_path, annotated_rows)
        return fallback_path

    def _build_task_annotations(
        self,
        task_results: Sequence[InspectionTaskResult],
    ) -> list[dict[str, object]]:
        annotations: list[dict[str, object]] = []
        for task_result in task_results:
            roi_rect = task_result.outputs.get("roi_rect")
            if not isinstance(roi_rect, (list, tuple)) or len(roi_rect) < 4:
                continue
            annotations.append(
                {
                    "roi_rect": (
                        int(roi_rect[0]),
                        int(roi_rect[1]),
                        int(roi_rect[2]),
                        int(roi_rect[3]),
                    ),
                    "label": self._build_annotation_label(task_result),
                    "status": task_result.status.value,
                }
            )
        return annotations

    def _build_annotation_label(self, task_result: InspectionTaskResult) -> str:
        outputs = task_result.outputs
        if task_result.task_type.value != "ocr":
            return (
                str(outputs.get("matched_text", "")).strip()
                or str(outputs.get("text", "")).strip()
                or str(outputs.get("expected_text", "")).strip()
                or str(outputs.get("roi_name", "")).strip()
                or task_result.task_id
            )
        if task_result.status.value == "pass":
            return (
                str(outputs.get("matched_text", "")).strip()
                or str(outputs.get("expected_text", "")).strip()
                or str(outputs.get("text", "")).strip()
            )
        return ""

    def _annotation_color(self, status: str):
        from PyQt5.QtGui import QColor

        normalized = (status or "").strip().lower()
        if normalized == "pass":
            return QColor("#00b050")
        if normalized == "fail":
            return QColor("#ff3b30")
        if normalized == "error":
            return QColor("#ff9500")
        return QColor("#38c172")

    def _draw_annotations_on_rows(
        self,
        rows: list[list[Any]],
        annotations: Sequence[dict[str, object]],
    ) -> list[list[Any]]:
        annotated_rows = self._copy_rows(rows)
        if not annotated_rows or not annotated_rows[0]:
            return annotated_rows
        height = len(annotated_rows)
        width = len(annotated_rows[0])
        rgb_mode = isinstance(annotated_rows[0][0], Sequence) and not isinstance(
            annotated_rows[0][0],
            (str, bytes, bytearray),
        )
        for annotation in annotations:
            x_value, y_value, rect_width, rect_height = annotation["roi_rect"]
            color = self._annotation_channels(str(annotation["status"]), rgb_mode=rgb_mode)
            left = max(0, int(x_value))
            top = max(0, int(y_value))
            right = min(width - 1, max(left, int(x_value) + int(rect_width) - 1))
            bottom = min(height - 1, max(top, int(y_value) + int(rect_height) - 1))
            for x_index in range(left, right + 1):
                annotated_rows[top][x_index] = color
                annotated_rows[bottom][x_index] = color
            for y_index in range(top, bottom + 1):
                annotated_rows[y_index][left] = color
                annotated_rows[y_index][right] = color
        return annotated_rows

    def _copy_rows(self, rows: list[list[Any]]) -> list[list[Any]]:
        copied_rows: list[list[Any]] = []
        for row in rows:
            copied_row: list[Any] = []
            for value in row:
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                    copied_row.append(list(value))
                else:
                    copied_row.append(value)
            copied_rows.append(copied_row)
        return copied_rows

    def _annotation_channels(self, status: str, *, rgb_mode: bool) -> Any:
        normalized = (status or "").strip().lower()
        if rgb_mode:
            if normalized == "pass":
                return [0, 176, 80]
            if normalized == "fail":
                return [255, 59, 48]
            if normalized == "error":
                return [255, 149, 0]
            return [56, 193, 114]
        if normalized == "pass":
            return 255
        if normalized == "fail":
            return 192
        if normalized == "error":
            return 224
        return 160

    def _try_save_image(self, target_base: Path, image: Any) -> Path | None:
        if image is None or isinstance(image, str):
            return None
        qimage_path = self._try_save_qimage(target_base.with_suffix(".png"), image)
        if qimage_path is not None:
            return qimage_path
        return self._try_save_plain_portable_image(target_base, image)

    def _try_save_qimage(self, path: Path, image: Any) -> Path | None:
        qimage = self._build_qimage_from_array(image)
        if qimage is None:
            return None
        try:
            if not qimage.copy().save(str(path), "PNG"):
                return None
            return path
        except Exception:
            return None

    def _build_qimage_from_array(self, image: Any):
        shape = getattr(image, "shape", None)
        data = getattr(image, "data", None)
        strides = getattr(image, "strides", None)
        if shape is None or data is None or strides is None:
            return None

        try:
            from PyQt5.QtGui import QImage

            if len(shape) == 2:
                return QImage(
                    image.data,
                    int(shape[1]),
                    int(shape[0]),
                    int(image.strides[0]),
                    QImage.Format_Grayscale8,
                )
            if len(shape) == 3 and int(shape[2]) == 3:
                return QImage(
                    image.data,
                    int(shape[1]),
                    int(shape[0]),
                    int(image.strides[0]),
                    QImage.Format_RGB888,
                )
            return None
        except Exception:
            return None

    def _try_save_plain_portable_image(self, target_base: Path, image: Any) -> Path | None:
        rows = self._normalize_rows(image)
        if not rows:
            return None

        first_row = rows[0]
        if not first_row:
            return None

        if isinstance(first_row[0], Sequence) and not isinstance(first_row[0], (str, bytes, bytearray)):
            path = target_base.with_suffix(".ppm")
            self._write_ppm(path, rows)
            return path

        path = target_base.with_suffix(".pgm")
        self._write_pgm(path, rows)
        return path

    def _normalize_rows(self, image: Any) -> list[list[Any]]:
        if hasattr(image, "tolist"):
            try:
                rows = image.tolist()
            except Exception:
                rows = image
        else:
            rows = image
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
            return []
        normalized = []
        for row in rows:
            if not isinstance(row, Sequence) or isinstance(row, (str, bytes, bytearray)):
                return []
            normalized.append(list(row))
        return normalized

    def _write_pgm(self, path: Path, rows: list[list[Any]]) -> None:
        width = len(rows[0])
        height = len(rows)
        pixels = bytearray()
        for row in rows:
            for value in row[:width]:
                pixels.append(self._clamp_channel(value))
        with path.open("wb") as handle:
            handle.write(f"P5\n{width} {height}\n255\n".encode("ascii"))
            handle.write(pixels)

    def _write_ppm(self, path: Path, rows: list[list[Any]]) -> None:
        width = len(rows[0])
        height = len(rows)
        pixels = bytearray()
        for row in rows:
            for value in row[:width]:
                channels = list(value)[:3]
                while len(channels) < 3:
                    channels.append(channels[-1] if channels else 0)
                for channel in channels:
                    pixels.append(self._clamp_channel(channel))
        with path.open("wb") as handle:
            handle.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
            handle.write(pixels)

    def _clamp_channel(self, value: Any) -> int:
        return max(0, min(255, int(float(value))))

    def _slug(self, value: str) -> str:
        normalized = "".join(
            char if char.isalnum() or char in {"-", "_"} else "-"
            for char in value.strip()
        )
        compact = normalized.strip("-_")
        return compact or "item"
