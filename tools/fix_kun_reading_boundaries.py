#!/usr/bin/env python3

"""Separate a kanji's kun reading from the okurigana of its example word.

The original source fields retain KANJIDIC's dot boundary (for example
``た.べる``).  Earlier builds removed the dot and accidentally displayed the
whole word reading as the kanji reading.  This migration keeps the complete
word in ``reading_examples`` while displaying only the part before the dot.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LIBRARY_RE = re.compile(
    r'(<script id="library-data" type="application/json">)(.*?)(</script>)', re.S
)

ROMAJI = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "o", "ん": "n", "ゔ": "vu",
}

DIGRAPHS = {
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
}


def normalize(value: str) -> str:
    return re.sub(r"[.\-・\s]", "", value)


def kun_stem(value: str) -> str:
    return normalize(value.split(".", 1)[0])


def kana_to_romaji(value: str) -> str:
    result = []
    geminate = False
    index = 0
    while index < len(value):
        char = value[index]
        if char == "っ":
            geminate = True
            index += 1
            continue
        pair = value[index:index + 2]
        if pair in DIGRAPHS:
            syllable = DIGRAPHS[pair]
            index += 2
        else:
            syllable = ROMAJI[char]
            index += 1
        if geminate:
            syllable = ("t" if syllable.startswith("ch") else syllable[0]) + syllable
            geminate = False
        result.append(syllable)
    return "".join(result).replace("oo", "ō")


def migrate(cards: list[dict]) -> dict:
    changed = 0
    merged = 0
    for card in cards:
        raw_values = [card["reference_reading_kana"]]
        raw_values.extend(
            value.strip()
            for value in card.get("other_readings", "").split(";")
            if value.strip()
        )
        source_map = {
            normalize(value): kun_stem(value)
            for value in raw_values
            if re.search(r"[\u3040-\u309f]", value)
        }
        old_to_new = {}
        rebuilt = []
        seen = set()
        for reading in card.get("kun_readings", []):
            old = reading["kana"]
            new = source_map.get(old, old)
            old_to_new[old] = new
            changed += int(old != new)
            if new in seen:
                merged += 1
                continue
            rebuilt.append({"kana": new, "romaji": kana_to_romaji(new)})
            seen.add(new)
        card["kun_readings"] = rebuilt
        for example in card.get("reading_examples", []):
            if example.get("kind") == "kun":
                example["reading_kana"] = old_to_new[example["reading_kana"]]

    one = next(card for card in cards if card["kanji"] == "一")
    one_example = next(
        example
        for example in one["reading_examples"]
        if example["kind"] == "kun" and example["reading_kana"] == "ひと"
    )
    one_example.clear()
    one_example.update(
        {
            "word": "一つ",
            "reading": "ひとつ",
            "meaning_en": "One thing",
            "advanced": False,
            "word_highlights": [[0, 1]],
            "reading_highlights": [[0, 2]],
            "kind": "kun",
            "reading_kana": "ひと",
        }
    )
    return {"changed": changed, "merged": merged}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    html = args.html.read_text(encoding="utf-8")
    match = LIBRARY_RE.search(html)
    if not match:
        raise SystemExit("Embedded library not found")
    cards = json.loads(match.group(2))
    summary = migrate(cards)
    library = json.dumps(cards, ensure_ascii=False, separators=(", ", ": "))
    args.html.write_text(
        html[:match.start(2)] + library + html[match.end(2):], encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
