from __future__ import annotations

from drb_inspection.plugins.ocr.matcher import match_expected_text
from drb_inspection.plugins.ocr.preprocess import crop_and_rotate_roi


def test_crop_and_rotate_roi_rotates_clockwise_for_sequence_data() -> None:
    frame = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
    ]

    roi_image = crop_and_rotate_roi(frame, (1, 0, 2, 3))

    assert roi_image == [
        [10, 6, 2],
        [11, 7, 3],
    ]


def test_match_expected_text_accepts_forward_variant() -> None:
    result = match_expected_text("AA_IS35R-100_E35_ZZ", "IS35R-100")

    assert result.matched is True
    assert result.canonical_text == "IS35R-100"


def test_match_expected_text_accepts_reversed_variant() -> None:
    result = match_expected_text("AA_001-R53SI_ZZ", "IS35R-100")

    assert result.matched is True
    assert result.canonical_text == "IS35R-100"


def test_match_expected_text_rejects_internal_whitespace_for_forward_match_like_v1() -> None:
    result = match_expected_text("AA_IS35R - 100_ZZ", "IS35R-100")

    assert result.matched is False
    assert result.canonical_text == ""
    assert result.match_mode == ""


def test_match_expected_text_rejects_internal_whitespace_for_reversed_match_like_v1() -> None:
    result = match_expected_text("AA_001 - R53SI_ZZ", "IS35R-100")

    assert result.matched is False
    assert result.canonical_text == ""
    assert result.match_mode == ""
