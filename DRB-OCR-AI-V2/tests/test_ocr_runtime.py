from __future__ import annotations

from drb_inspection.plugins.ocr.runtime import _parse_prediction_result


def test_parse_prediction_result_preserves_raw_tuple_text_like_v1() -> None:
    prediction = _parse_prediction_result((["box"], "IS35R-\n100\x00", ["pt"], ""))

    assert prediction.text == "IS35R-\n100\x00"
    assert prediction.error == ""
    assert prediction.raw == (["box"], "IS35R-\n100\x00", ["pt"], "")
    assert prediction.boxes == ["box"]
    assert prediction.box_points == ["pt"]


def test_parse_prediction_result_preserves_sequence_text_like_v1() -> None:
    prediction = _parse_prediction_result((["box"], ["IS35R-", "100"], ["pt"], ""))

    assert prediction.text == ["IS35R-", "100"]
    assert prediction.error == ""
    assert prediction.raw == (["box"], ["IS35R-", "100"], ["pt"], "")
