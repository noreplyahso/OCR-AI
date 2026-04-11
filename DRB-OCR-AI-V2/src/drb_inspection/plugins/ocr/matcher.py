from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OcrMatchResult:
    matched: bool
    expected_text: str
    detected_text: str
    canonical_text: str
    matched_variant: str = ""
    match_mode: str = ""


def match_expected_text(detected_text: str | None, expected_text: str | None) -> OcrMatchResult:
    detected = str(detected_text or "")
    expected = str(expected_text or "")
    normalized_detected = _normalize_for_match(detected)
    normalized_expected = _normalize_for_match(expected)
    if not normalized_detected or not normalized_expected:
        return OcrMatchResult(
            matched=False,
            expected_text=expected,
            detected_text=detected,
            canonical_text="",
            matched_variant="",
            match_mode="",
        )

    if _pattern_for_text(normalized_expected).search(normalized_detected):
        return OcrMatchResult(
            matched=True,
            expected_text=expected,
            detected_text=detected,
            canonical_text=expected,
            matched_variant=expected,
            match_mode="forward",
        )

    for reverse_variant in _reverse_variants(normalized_expected):
        if _pattern_for_text(reverse_variant).search(normalized_detected):
            return OcrMatchResult(
                matched=True,
                expected_text=expected,
                detected_text=detected,
                canonical_text=expected,
                matched_variant=reverse_variant,
                match_mode="reverse",
            )

    return OcrMatchResult(
        matched=False,
        expected_text=expected,
        detected_text=detected,
        canonical_text="",
        matched_variant="",
        match_mode="",
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


def _normalize_for_match(value: str) -> str:
    return value or ""
