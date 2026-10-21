#!/usr/bin/env python3

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "PocketKanji.html"
html = HTML_PATH.read_text(encoding="utf-8")

match = re.search(
    r'<script id="library-data" type="application/json">(.*?)</script>',
    html,
    re.S,
)
assert match, "Libreria JSON non trovata"
cards = json.loads(match.group(1))

assert len(cards) == 500, f"Attese 500 carte, trovate {len(cards)}"
assert [card["id"] for card in cards] == [f"pk{index:04d}" for index in range(1, 501)]
assert len({card["kanji"] for card in cards}) == 500

romaji_pattern = re.compile(r"^[a-zāīūēō']+$")
kun_pattern = re.compile(r"^[\u3040-\u309f]+$")
on_pattern = re.compile(r"^[\u30a0-\u30ff]+$")

for card in cards:
    assert isinstance(card.get("kun_readings"), list), f"kun_readings assente: {card['id']}"
    assert isinstance(card.get("on_readings"), list), f"on_readings assente: {card['id']}"
    assert card["kun_readings"] or card["on_readings"], f"Carta senza letture: {card['id']}"
    for field, pattern in (("kun_readings", kun_pattern), ("on_readings", on_pattern)):
        kana_seen = set()
        for reading in card[field]:
            assert set(reading) == {"kana", "romaji"}, f"Struttura lettura errata: {card['id']}"
            assert pattern.fullmatch(reading["kana"]), f"Kana errato: {card['id']} {reading['kana']}"
            assert romaji_pattern.fullmatch(reading["romaji"]), f"Romaji errato: {card['id']} {reading['romaji']}"
            assert reading["kana"] not in kana_seen, f"Lettura duplicata: {card['id']} {reading['kana']}"
            kana_seen.add(reading["kana"])

day = next(card for card in cards if card["kanji"] == "日")
assert day["meaning_en"] == "day / sun"
assert day["kun_readings"] == [
    {"kana": "ひ", "romaji": "hi"},
    {"kana": "か", "romaji": "ka"},
]
assert day["on_readings"] == [
    {"kana": "ニチ", "romaji": "nichi"},
    {"kana": "ジツ", "romaji": "jitsu"},
]
assert [item["word"] for item in day["reading_examples"]] == ["日", "日曜日", "毎日"]

assert "pocketkanji.prototype.v1" in html
assert "const sameLibrary=" in html
assert "function readingBlock" in html
assert "@media(max-width:720px){.reading-sections{grid-template-columns:1fr}" in html
assert all(f'data-rate="{rating}"' in html for rating in ("again", "hard", "good"))

print(
    json.dumps(
        {
            "cards": len(cards),
            "readings": sum(len(c["kun_readings"]) + len(c["on_readings"]) for c in cards),
            "ids": "pk0001-pk0500",
            "day_card": "ok",
            "backup_compatibility": "ok",
            "responsive_layout": "ok",
            "quiz_controls": "ok",
        },
        ensure_ascii=False,
        indent=2,
    )
)
