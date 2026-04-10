from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OcrMatchResult:
    matched: bool
    expected_text: str
    detected_text: str
    canonical_text: str


def match_expected_text(detected_text: str | None, expected_text: str | None) -> OcrMatchResult:
    detected = str(detected_text or "")
    expected = str(expected_text or "")
    if not detected or not expected:
        return OcrMatchResult(
            matched=False,
            expected_text=expected,
            detected_text=detected,
            canonical_text="",
        )

    if _pattern_for_text(expected).search(detected):
        return OcrMatchResult(
            matched=True,
            expected_text=expected,
            detected_text=detected,
            canonical_text=expected,
        )

    for reverse_variant in _reverse_variants(expected):
        if _pattern_for_text(reverse_variant).search(detected):
            return OcrMatchResult(
                matched=True,
                expected_text=expected,
                detected_text=detected,
                canonical_text=expected,
            )

    return OcrMatchResult(
        matched=False,
        expected_text=expected,
        detected_text=detected,
        canonical_text="",
    )


def _pattern_for_text(value: str) -> re.Pattern[str]:
    return re.compile(rf"(?:(?<=^)|(?<=[-_])){re.escape(value)}(?:(?=$)|(?=[-_]))")


def _reverse_variants(value: str) -> set[str]:
    reversed_value = value[::-1]
    variants = {reversed_value}
    separator = "-"
    if separator not in value:
        return variants

    parts = value.split(separator)
    if len(parts) != 2:
        return variants

    left, right = parts
    left_reversed = left[::-1]
    right_reversed = right[::-1]
    variants.add(right_reversed + separator + left_reversed)

    if left_reversed:
        variants.add(right_reversed + left_reversed[0] + separator + left_reversed[1:])
    if right_reversed:
        variants.add(right_reversed[:-1] + separator + right_reversed[-1] + left_reversed)
    return variants
