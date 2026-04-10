from __future__ import annotations

from collections.abc import Sequence


def crop_and_rotate_roi(image, roi_rect: Sequence[int], *, rotate_clockwise: bool = True):
    if image is None:
        raise ValueError("OCR frame is empty.")

    x, y, width, height = _parse_roi_rect(roi_rect)
    cropped = _crop_image(image, x=x, y=y, width=width, height=height)
    if _is_empty_image(cropped):
        raise ValueError("OCR ROI crop is empty.")
    if not rotate_clockwise:
        return cropped
    return _rotate_90_clockwise(cropped)


def _parse_roi_rect(roi_rect: Sequence[int]) -> tuple[int, int, int, int]:
    if len(roi_rect) < 4:
        raise ValueError("ROI rectangle must contain at least x, y, width, height.")

    x, y, width, height = (int(roi_rect[0]), int(roi_rect[1]), int(roi_rect[2]), int(roi_rect[3]))
    if width <= 0 or height <= 0:
        raise ValueError("ROI width and height must be positive.")
    return x, y, width, height


def _is_empty_image(image) -> bool:
    size = getattr(image, "size", None)
    if isinstance(size, int):
        return size == 0
    if isinstance(image, Sequence):
        return len(image) == 0
    return False


def _crop_image(image, *, x: int, y: int, width: int, height: int):
    if hasattr(image, "shape"):
        return image[y : y + height, x : x + width]

    if isinstance(image, Sequence):
        rows = image[y : y + height]
        return [list(row[x : x + width]) for row in rows]

    raise ValueError("Unsupported OCR frame type for ROI crop.")


def _rotate_90_clockwise(image):
    if hasattr(image, "shape"):
        try:
            import cv2  # type: ignore

            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        except Exception:
            pass

    rows = [list(row) for row in image]
    if not rows or not rows[0]:
        raise ValueError("OCR ROI crop is empty.")
    return [list(row) for row in zip(*rows[::-1])]
