#!/usr/bin/env python3

"""Focused checks for verified kanji-to-reading highlight offsets."""

from update_reading_examples import add_verified_highlights, parse_furigana_parts


def exact_parts(word, reading, raw_parts, target):
    return [
        part
        for part in parse_furigana_parts(word, reading, raw_parts)
        if part["has_rt"] and part["ruby"] == target and len(part["ruby"]) == 1
    ]


def highlighted(word, reading, raw_parts, target, displayed, allow_variant=False):
    parts = exact_parts(word, reading, raw_parts, target)
    example = {"word": word, "reading": reading}
    add_verified_highlights(
        example,
        target,
        displayed,
        {(word, reading, target): parts},
        allow_variant,
    )
    return example


fire = highlighted(
    "火曜日",
    "かようび",
    [
        {"ruby": "火", "rt": "か"},
        {"ruby": "曜", "rt": "よう"},
        {"ruby": "日", "rt": "び"},
    ],
    "火",
    "カ",
)
assert fire["word_highlights"] == [[0, 1]]
assert fire["reading_highlights"] == [[0, 1]]

rendaku = highlighted(
    "失敗",
    "しっぱい",
    [{"ruby": "失", "rt": "しっ"}, {"ruby": "敗", "rt": "ぱい"}],
    "敗",
    "ハイ",
    allow_variant=True,
)
assert rendaku["word_highlights"] == [[1, 2]]
assert rendaku["reading_highlights"] == [[2, 4]]

repeated = highlighted(
    "色色",
    "いろいろ",
    [{"ruby": "色", "rt": "いろ"}, {"ruby": "色", "rt": "いろ"}],
    "色",
    "いろ",
)
assert repeated["word_highlights"] == [[0, 1], [1, 2]]
assert repeated["reading_highlights"] == [[0, 2], [2, 4]]

grouped = highlighted(
    "上手",
    "じょうず",
    [{"ruby": "上手", "rt": "じょうず"}],
    "上",
    "ジョウ",
    allow_variant=True,
)
assert "word_highlights" not in grouped
assert "reading_highlights" not in grouped

print("highlight alignment: ok")
