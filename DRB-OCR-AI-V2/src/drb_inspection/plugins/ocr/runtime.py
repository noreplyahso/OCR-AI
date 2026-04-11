from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LegacyOcrPrediction:
    text: str
    error: str
    raw: object
    boxes: object | None = None
    box_points: object | None = None


@dataclass
class LegacyOcrRuntimeGateway:
    runtime_dir: str | None = None
    _ocr_tool: object | None = field(default=None, init=False)

    def load_model(self, model_path: str):
        self._ensure_tool()
        return self._ocr_tool.Load_Model_OCR(model_path)

    def predict(
        self,
        image,
        model,
        *,
        acceptance_threshold=0.8,
        duplication_threshold=0.5,
        row_threshold=0.2,
    ) -> LegacyOcrPrediction:
        raw_result = self.predict_text(
            image,
            model,
            acceptance_threshold=acceptance_threshold,
            duplication_threshold=duplication_threshold,
            row_threshold=row_threshold,
        )
        return _parse_prediction_result(raw_result)

    def predict_text(self, image, model, *, acceptance_threshold=0.8, duplication_threshold=0.5, row_threshold=0.2):
        self._ensure_tool()
        return self._ocr_tool.Prediction_OCR_None_Img_E(
            image,
            model,
            acceptance_threshold,
            duplication_threshold,
            row_threshold,
        )

    def _ensure_tool(self) -> None:
        if self._ocr_tool is not None:
            return

        if self.runtime_dir:
            runtime_path = str(Path(self.runtime_dir).resolve())
            if runtime_path not in sys.path:
                sys.path.append(runtime_path)

        from Deep_Learning_Tool import OCR_DEEP_LEARNING

        self._ocr_tool = OCR_DEEP_LEARNING()


def _parse_prediction_result(raw_result: object) -> LegacyOcrPrediction:
    if raw_result is None:
        return LegacyOcrPrediction(text="", error="", raw=raw_result)

    if isinstance(raw_result, tuple):
        if len(raw_result) >= 4:
            boxes, text, box_points, error = raw_result[:4]
            return LegacyOcrPrediction(
                text="" if text is None else str(text),
                error="" if error is None else str(error),
                raw=raw_result,
                boxes=boxes,
                box_points=box_points,
            )
        if len(raw_result) >= 3:
            boxes, text, box_points = raw_result[:3]
            return LegacyOcrPrediction(
                text="" if text is None else str(text),
                error="",
                raw=raw_result,
                boxes=boxes,
                box_points=box_points,
            )

    return LegacyOcrPrediction(text=str(raw_result), error="", raw=raw_result)
