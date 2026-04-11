from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from drb_inspection.adapters.db.models import SessionRecord
from drb_inspection.application.contracts.inspection import (
    InspectionCycleArtifacts,
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
    ) -> InspectionCycleArtifacts:
        timestamp = datetime.now()
        cycle_dir = self._build_cycle_dir(
            product_name=product_name,
            status=cycle_result.plc_result_sent,
            timestamp=timestamp,
        )
        cycle_dir.mkdir(parents=True, exist_ok=True)

        frame_path = self._try_save_image(
            cycle_dir / "frame",
            getattr(cycle_result.image_ref, "frame", cycle_result.image_ref),
        )
        task_artifacts = self._record_task_artifacts(
            task_results=cycle_result.inspection.task_results,
            cycle_dir=cycle_dir,
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
    ) -> list[InspectionTaskArtifact]:
        artifacts: list[InspectionTaskArtifact] = []
        for index, task_result in enumerate(task_results, start=1):
            roi_image = task_result.outputs.get("roi_image")
            image_path = self._try_save_image(
                cycle_dir / f"task_{index:02d}_{self._slug(task_result.task_id)}_roi",
                roi_image,
            )
            if image_path is None:
                continue
            artifacts.append(
                InspectionTaskArtifact(
                    task_id=task_result.task_id,
                    image_path=str(image_path),
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
        task_artifacts: list[InspectionTaskArtifact],
    ) -> dict[str, object]:
        artifact_path_by_task = {
            artifact.task_id: artifact.image_path
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
                }
                for task_result in cycle_result.inspection.task_results
            ],
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

    def _try_save_image(self, target_base: Path, image: Any) -> Path | None:
        if image is None or isinstance(image, str):
            return None
        qimage_path = self._try_save_qimage(target_base.with_suffix(".png"), image)
        if qimage_path is not None:
            return qimage_path
        return self._try_save_plain_portable_image(target_base, image)

    def _try_save_qimage(self, path: Path, image: Any) -> Path | None:
        shape = getattr(image, "shape", None)
        data = getattr(image, "data", None)
        strides = getattr(image, "strides", None)
        if shape is None or data is None or strides is None:
            return None

        try:
            from PyQt5.QtGui import QImage

            if len(shape) == 2:
                qimage = QImage(
                    image.data,
                    int(shape[1]),
                    int(shape[0]),
                    int(image.strides[0]),
                    QImage.Format_Grayscale8,
                )
            elif len(shape) == 3 and int(shape[2]) == 3:
                qimage = QImage(
                    image.data,
                    int(shape[1]),
                    int(shape[0]),
                    int(image.strides[0]),
                    QImage.Format_RGB888,
                )
            else:
                return None
            if not qimage.copy().save(str(path), "PNG"):
                return None
            return path
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
