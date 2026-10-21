#!/usr/bin/env python3

import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


HTML_PATH = Path(sys.argv[1])
KANJIDIC_PATH = Path(sys.argv[2])


def normalize_reading(value):
    return re.sub(r"[.\-・\s]", "", value)


def reading_kind(value):
    if re.search(r"[\u30a0-\u30ff]", value):
        return "on"
    if re.search(r"[\u3040-\u309f]", value):
        return "kun"
    raise ValueError(f"Lettura senza kana: {value}")


def katakana_to_hiragana(value):
    result = []
    for char in value:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(char)
    return "".join(result)


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


def kana_to_romaji(value, kind):
    kana = katakana_to_hiragana(normalize_reading(value))
    parts = []
    geminate = False
    index = 0
    while index < len(kana):
        char = kana[index]
        if char == "っ":
            geminate = True
            index += 1
            continue
        pair = kana[index:index + 2]
        if pair in DIGRAPHS:
            syllable = DIGRAPHS[pair]
            index += 2
        else:
            if char not in ROMAJI:
                raise ValueError(f"Kana non supportato nella romanizzazione: {char} ({value})")
            syllable = ROMAJI[char]
            index += 1
        if geminate:
            if syllable.startswith("ch"):
                syllable = "t" + syllable
            elif syllable[0] not in "aeioun":
                syllable = syllable[0] + syllable
            geminate = False
        parts.append(syllable)
    result = "".join(parts)
    if kind == "on":
        result = result.replace("ou", "ō").replace("oo", "ō").replace("uu", "ū")
    else:
        result = result.replace("oo", "ō")
    return result


def load_kanjidic(path):
    with gzip.open(path, "rb") as stream:
        root = ET.parse(stream).getroot()
    result = {}
    for character in root.findall("character"):
        literal = character.findtext("literal")
        readings = {"kun": [], "on": []}
        for node in character.findall("./reading_meaning/rmgroup/reading"):
            if node.get("r_type") == "ja_kun":
                readings["kun"].append(node.text)
            elif node.get("r_type") == "ja_on":
                readings["on"].append(node.text)
        result[literal] = readings
    return result


def make_reading_items(card, kanjidic):
    grouped = {"kun": [], "on": []}
    source_values = [card["reference_reading_kana"]]
    source_values.extend(
        value.strip()
        for value in card.get("other_readings", "").split(";")
        if value.strip()
    )
    for value in source_values:
        kind = reading_kind(value)
        display = normalize_reading(value)
        if display not in grouped[kind]:
            grouped[kind].append(display)

    preferred = {
        "日": {"kun": ["ひ", "か"], "on": ["ニチ", "ジツ"]},
        "今": {"kun": ["いま"], "on": ["コン"]},
        "何": {"kun": ["なに", "なん"], "on": []},
    }
    if card["kanji"] in preferred:
        grouped = preferred[card["kanji"]]

    dictionary_entry = kanjidic.get(card["kanji"])
    if not dictionary_entry:
        raise ValueError(f"Kanji non trovato in KANJIDIC2: {card['kanji']}")

    items = {"kun": [], "on": []}
    reference_normalized = normalize_reading(card["reference_reading_kana"])
    for kind in ("kun", "on"):
        accepted = {normalize_reading(value) for value in dictionary_entry[kind]}
        for value in grouped[kind]:
            if normalize_reading(value) not in accepted:
                raise ValueError(
                    f"Lettura non verificata per {card['kanji']}: {kind} {value}"
                )
            if value == reference_normalized:
                romaji = card["reference_reading_romaji"]
            else:
                romaji = kana_to_romaji(value, kind)
            items[kind].append({"kana": value, "romaji": romaji})
    return items


html = HTML_PATH.read_text(encoding="utf-8")
library_match = re.search(
    r'(<script id="library-data" type="application/json">)(.*?)(</script>)',
    html,
    re.S,
)
if not library_match:
    raise SystemExit("Dati della libreria non trovati nell'HTML")

cards = json.loads(library_match.group(2))
kanjidic = load_kanjidic(KANJIDIC_PATH)
updated_cards = []

for card in cards:
    readings = make_reading_items(card, kanjidic)
    if card["kanji"] == "日":
        card["meaning_en"] = "day / sun"
    rebuilt = {}
    for key, value in card.items():
        if key in {"kun_readings", "on_readings", "reading_examples"}:
            continue
        rebuilt[key] = value
        if key == "reference_reading_romaji":
            rebuilt["kun_readings"] = readings["kun"]
            rebuilt["on_readings"] = readings["on"]
        if key == "other_readings" and card["kanji"] == "日":
            rebuilt["reading_examples"] = [
                {"word": "日", "reading": "ひ", "meaning_en": "Day"},
                {"word": "日曜日", "reading": "にちようび", "meaning_en": "Sunday"},
                {"word": "毎日", "reading": "まいにち", "meaning_en": "Every day"},
            ]
    updated_cards.append(rebuilt)

library_json = json.dumps(updated_cards, ensure_ascii=False, separators=(", ", ": "))
html = (
    html[:library_match.start(2)]
    + library_json
    + html[library_match.end(2):]
)

css = (
    ".reading-sections{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0}"
    ".reading-block{border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:#f8fafc;text-align:left}"
    ".reading-block.kun{border-top:3px solid #bc6547}.reading-block.on{border-top:3px solid #426d9c}"
    ".reading-title{font-size:10px;font-weight:700;letter-spacing:1.5px;color:var(--muted);margin-bottom:10px}"
    ".reading-list{display:flex;flex-wrap:wrap;gap:8px}.reading-item{min-width:72px;background:var(--white);border:1px solid var(--line);border-radius:7px;padding:8px 10px;text-align:center}"
    ".reading-kana{display:block;font-size:23px;line-height:1.25}.reading-romaji{display:block;margin-top:3px;font-size:12px;color:var(--muted);font-style:italic}"
    ".reading-empty{display:block;color:var(--muted);font-size:13px;padding:8px 0}"
    ".reading-examples{margin:13px 0 17px;padding:13px 16px;background:#eaf0f6;border-radius:9px;text-align:left}"
    ".reading-examples-title{font-size:10px;font-weight:700;letter-spacing:1.4px;color:var(--muted);margin-bottom:6px}"
    ".reading-example{display:flex;justify-content:space-between;gap:16px;padding:6px 0;border-bottom:1px solid #d5dfeb;font-size:13px}"
    ".reading-example:last-child{border-bottom:0}.reading-example-word{font-size:17px}.reading-example-kana{font-size:13px;color:var(--muted)}"
    ".reference-word-label{display:block;font-size:10px;text-transform:uppercase;letter-spacing:1.4px;color:var(--muted);margin-bottom:4px}"
)
if ".reading-sections{" not in html:
    html = html.replace("@media(min-width:1500px)", css + "@media(min-width:1500px)", 1)

mobile_css = "@media(max-width:720px){.reading-sections{grid-template-columns:1fr}.reading-example{display:block}.reading-example [lang='en']{display:block;margin-top:2px}}"
if mobile_css not in html:
    html = html.replace("</style>", mobile_css + "</style>", 1)

answer_replacement = r'''function readingBlock(label,readings,kind){return `<section class="reading-block ${kind}" aria-label="${label}"><div class="reading-title">${label}</div>${readings.length?`<div class="reading-list">${readings.map(r=>`<div class="reading-item"><span class="reading-kana" lang="ja">${esc(r.kana)}</span>${data.settings.romaji?`<span class="reading-romaji">${esc(r.romaji)}</span>`:''}</div>`).join('')}</div>`:'<span class="reading-empty">Nessuna lettura essenziale selezionata</span>'}</section>`;}
function readingExamples(c){return c.reading_examples?.length?`<div class="reading-examples"><div class="reading-examples-title">ESEMPI D’USO</div>${c.reading_examples.map(x=>`<div class="reading-example"><span class="reading-example-word" lang="ja">${esc(x.word)} <span class="reading-example-kana">（${esc(x.reading)}）</span></span><span lang="en">${esc(x.meaning_en)}</span></div>`).join('')}</div>`:'';}
function answer(c){return `<h2 class="answer-meaning" lang="en">${esc(c.meaning_en)}</h2><div class="reading-sections">${readingBlock("KUN'YOMI",c.kun_readings||[],'kun')}${readingBlock("ON'YOMI",c.on_readings||[],'on')}</div>${readingExamples(c)}<div class="word-line"><span class="reference-word-label">Parola di riferimento</span><span lang="ja">${esc(c.reference_word)}</span> · <span lang="ja">${esc(c.reference_word_reading_kana)}</span>${data.settings.romaji?` · ${esc(c.reference_word_romaji)}`:''}<br><span lang="en">${esc(c.reference_word_meaning_en)}</span></div><div class="example"><p class="jp" lang="ja">${esc(c.example_ja)}</p><p class="kana" lang="ja">${esc(c.example_kana)}</p><p class="en" lang="en">${esc(c.example_en)}</p></div>${c.notes_it?`<details><summary>Note</summary><p>${esc(c.notes_it)}</p></details>`:''}`;}
function startSession'''

html, answer_count = re.subn(
    r"function answer\(c\)\{.*?\nfunction startSession",
    answer_replacement,
    html,
    count=1,
    flags=re.S,
)
if answer_count != 1:
    raise SystemExit(f"Impossibile aggiornare la scheda delle letture: {answer_count}")

old_import_check = "if(raw.app!=='PocketKanji'||!Array.isArray(raw.library)||raw.library.length!==CARDS.length||!raw.library.every((c,i)=>Object.keys(CARDS[i]).every(k=>c[k]===CARDS[i][k])))throw Error('La libreria del backup non corrisponde a questa versione di PocketKanji.');"
new_import_check = "const sameLibrary=Array.isArray(raw.library)&&raw.library.length===CARDS.length&&raw.library.every((c,i)=>c&&c.id===CARDS[i].id&&String(c.order)===String(CARDS[i].order)&&c.kanji===CARDS[i].kanji);\nif(raw.app!=='PocketKanji'||!sameLibrary)throw Error('La libreria del backup non corrisponde a questa versione di PocketKanji.');"
if old_import_check not in html:
    if new_import_check not in html:
        raise SystemExit("Controllo di compatibilità dei backup non trovato")
else:
    html = html.replace(old_import_check, new_import_check, 1)

HTML_PATH.write_text(html, encoding="utf-8")

kun_count = sum(len(card["kun_readings"]) for card in updated_cards)
on_count = sum(len(card["on_readings"]) for card in updated_cards)
both_count = sum(bool(card["kun_readings"]) and bool(card["on_readings"]) for card in updated_cards)
print(
    json.dumps(
        {
            "cards": len(updated_cards),
            "kun_readings": kun_count,
            "on_readings": on_count,
            "cards_with_both": both_count,
            "cards_with_kun_only": sum(bool(c["kun_readings"]) and not c["on_readings"] for c in updated_cards),
            "cards_with_on_only": sum(bool(c["on_readings"]) and not c["kun_readings"] for c in updated_cards),
        },
        ensure_ascii=False,
        indent=2,
    )
)
