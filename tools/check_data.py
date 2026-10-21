#!/usr/bin/env python3

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "PocketKanji.html"
FONT_PATH = ROOT / "assets" / "NotoSansJP-Variable.ttf"
WINDOWS_LAUNCHER_PATH = ROOT / "Avvia-PocketKanji.ps1"
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
example_reading_pattern = re.compile(r"^[\u3040-\u309fー]+$")
example_count = 0
advanced_count = 0
highlighted_count = 0
sentence_lengths = []


def validate_spans(value, spans, label):
    assert isinstance(spans, list) and spans, f"Intervalli evidenziazione assenti: {label}"
    previous_end = 0
    for span in spans:
        assert isinstance(span, list) and len(span) == 2, f"Intervallo errato: {label}"
        start, end = span
        assert isinstance(start, int) and isinstance(end, int), f"Offset non intero: {label}"
        assert previous_end <= start < end <= len(value), f"Offset fuori limite: {label}"
        previous_end = end

for card in cards:
    assert all(card.get(field) for field in ("example_ja", "example_kana", "example_en")), f"Frase incompleta: {card['id']}"
    assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", card["example_kana"]), f"Kanji nella lettura della frase: {card['id']}"
    assert card["example_ja"].endswith(("。", "！", "？")), f"Punteggiatura frase: {card['id']}"
    sentence_lengths.append(len(card["example_ja"]))
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
    expected_examples = {
        (kind, reading["kana"])
        for kind, field in (("kun", "kun_readings"), ("on", "on_readings"))
        for reading in card[field]
    }
    examples = card.get("reading_examples")
    assert isinstance(examples, list), f"reading_examples assente: {card['id']}"
    actual_examples = []
    for example in examples:
        required = {"kind", "reading_kana", "word", "reading", "meaning_en", "advanced"}
        assert required <= set(example), f"Esempio incompleto: {card['id']} {example}"
        assert set(example) <= required | {"usage_note", "word_highlights", "reading_highlights"}, f"Campo esempio inatteso: {card['id']}"
        assert example["kind"] in {"kun", "on"}, f"Tipo esempio errato: {card['id']}"
        assert example_reading_pattern.fullmatch(example["reading"]), f"Lettura esempio non hiragana: {card['id']} {example['reading']}"
        assert card["kanji"] in example["word"], f"Kanji assente dall'esempio: {card['id']} {example['word']}"
        assert isinstance(example["advanced"], bool), f"Flag Advanced errato: {card['id']}"
        if "usage_note" in example:
            assert example["usage_note"].strip(), f"Nota d'uso vuota: {card['id']}"
        has_word_highlights = "word_highlights" in example
        assert has_word_highlights == ("reading_highlights" in example), f"Evidenziazione parziale: {card['id']}"
        if has_word_highlights:
            validate_spans(example["word"], example["word_highlights"], f"{card['id']} parola")
            validate_spans(example["reading"], example["reading_highlights"], f"{card['id']} lettura")
            assert len(example["word_highlights"]) == len(example["reading_highlights"]), f"Coppie non allineate: {card['id']}"
            assert all(
                example["word"][start:end] == card["kanji"]
                for start, end in example["word_highlights"]
            ), f"Kanji evidenziato errato: {card['id']}"
            highlighted_count += 1
        actual_examples.append((example["kind"], example["reading_kana"]))
        advanced_count += int(example["advanced"])
    assert set(actual_examples) == expected_examples, f"Copertura esempi errata: {card['id']}"
    assert len(actual_examples) == len(expected_examples), f"Esempio duplicato: {card['id']}"
    example_count += len(examples)

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
assert [(item["kind"], item["reading_kana"], item["word"], item["reading"]) for item in day["reading_examples"]] == [
    ("kun", "ひ", "日", "ひ"),
    ("kun", "か", "三日", "みっか"),
    ("on", "ニチ", "日曜日", "にちようび"),
    ("on", "ジツ", "本日", "ほんじつ"),
]
fire = next(card for card in cards if card["kanji"] == "火")
fire_tuesday = next(item for item in fire["reading_examples"] if item["word"] == "火曜日")
assert fire_tuesday["word_highlights"] == [[0, 1]]
assert fire_tuesday["reading_highlights"] == [[0, 1]]
third_day = next(item for item in day["reading_examples"] if item["word"] == "三日")
assert third_day["word_highlights"] == [[1, 2]]
assert third_day["reading_highlights"] == [[2, 3]]
skilled = next(card for card in cards if card["kanji"] == "上")
skilled_example = next(item for item in skilled["reading_examples"] if item["word"] == "上手")
assert "word_highlights" not in skilled_example, "Un ruby di gruppo ambiguo non deve essere suddiviso"

assert "pocketkanji.prototype.v1" in html
assert FONT_PATH.exists() and FONT_PATH.stat().st_size > 1_000_000, "Font Noto Sans JP assente o incompleto"
assert FONT_PATH.read_bytes()[:4] == b"\x00\x01\x00\x00", "File font TrueType non valido"
assert "@font-face{font-family:'Noto Sans JP';src:url('assets/NotoSansJP-Variable.ttf')" in html
assert ".flashcard .big-kanji{font:400 145px/1.5 'Noto Sans JP',sans-serif}" in html
assert '<div class="big-kanji" lang="ja">${esc(c.kanji)}</div>' in html
assert html.count("@font-face{font-family:'Noto Sans JP'") == 1
windows_launcher = WINDOWS_LAUNCHER_PATH.read_text(encoding="utf-8")
assert "/assets/NotoSansJP-Variable.ttf" in windows_launcher
assert "font/ttf" in windows_launcher
assert "const sameLibrary=" in html
assert "function readingBlock" in html
assert "function readingExample" in html
assert "function highlightRanges" in html
assert "highlightRanges(x.word,x.word_highlights)" in html
assert "highlightRanges(x.reading,x.reading_highlights)" in html
assert ".reading-focus{color:var(--orange);font-weight:700}" in html
assert ".reading-linked-examples{" in html
assert "@media(max-width:720px){.reading-sections{grid-template-columns:1fr}" in html
assert all(f'data-rate="{rating}"' in html for rating in ("again", "hard", "good"))

print(
    json.dumps(
        {
            "cards": len(cards),
            "readings": sum(len(c["kun_readings"]) + len(c["on_readings"]) for c in cards),
            "reading_examples": example_count,
            "advanced_examples": advanced_count,
            "highlighted_examples": highlighted_count,
            "unhighlighted_ambiguous_examples": example_count - highlighted_count,
            "sentence_length_max": max(sentence_lengths),
            "main_kanji_font": "Noto Sans JP (bundled)",
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
