#!/usr/bin/env python3

"""Build one verified vocabulary example for every displayed kanji reading.

Sources:
- JMdict_e for spellings, readings, English glosses and frequency-priority tags.
- JmdictFurigana for word-level furigana alignment.

The script keeps PocketKanji's card IDs and learning-state schema untouched.  Run
without ``--write`` to audit coverage; add ``--write`` to update the embedded
library and the reading-example renderer in PocketKanji.html.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path


LIBRARY_RE = re.compile(
    r'(<script id="library-data" type="application/json">)(.*?)(</script>)', re.S
)
KANJI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
KANA_RE = re.compile(r"^[\u3040-\u30ffー]+$")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

N5_CORE_KANJI = set(
    "一二三四五六七八九十百千万円日月火水木金土曜年時分半午今毎週前後間"
    "上下中外左右東西南北口入出人男女子父母先生友名学校本語文字"
    "大小高安新古長多少白黒赤青山川天空気雨雪電車駅家店会社国町道"
    "行来帰見聞読書話言食飲買売休立何手足目耳"
)

# A compact seed from the app's N5 teaching brief.  It is deliberately a
# pedagogical preference list, not an "official JLPT vocabulary list".
N5_VOCAB_SEED = set(
    "先生 学生 本 私 人 男 女 名前 日本 日本人 会社員 友だち 一 二 百 千 円 今 "
    "今日 明日 昨日 時 分 半 月曜日 毎日 朝 夜 家 部屋 台所 机 椅子 上 下 中 "
    "外 右 左 前 後 近く 行く 来る 帰る 起きる 寝る 食べる 飲む 見る 聞く "
    "読む 書く 話す 会う 勉強する 働く 水 お茶 ご飯 肉 魚 野菜 果物 店 買う "
    "売る 高い 安い 父 母 兄 姉 弟 妹 家族 頭 目 耳 手 足 病院 元気 電車 駅 "
    "車 自転車 道 旅行 切符 乗る 降りる 東 西 南 北 天気 雨 雪 山 川 海 "
    "大きい 小さい 新しい 古い 学校 大学 会社 仕事 授業 宿題 映画 音楽 写真 "
    "四月 七時 九月 月曜日 一月 火曜日 水曜日 木曜日 金曜日 土曜日 一年 午前 "
    "午後 朝食 今夜 三人 有名 男子 女子 帽子 外国 上手 地下 左右 東京 西洋 "
    "南極 北西 空港 来週 辞書 会話 言語 家族 住所"
    .split()
)

REJECT_LABELS = {
    "archaic", "obsolete term", "dated term", "historical term",
    "rare term", "obscure term", "vulgar expression or word",
    "derogatory", "offensive term", "surname", "given name or forename",
    "place name", "company name", "product name", "unclassified name",
}


def kata_to_hira(value: str) -> str:
    chars = []
    for char in value:
        code = ord(char)
        chars.append(chr(code - 0x60) if 0x30A1 <= code <= 0x30F6 else char)
    return "".join(chars)


def normalize_reading(value: str) -> str:
    return re.sub(r"[.\-・\s]", "", value)


def priority_score(tags: set[str]) -> int:
    score = 0
    weights = {
        "ichi1": 800, "spec1": 760, "news1": 700, "gai1": 650,
        "spec2": 260, "ichi2": 220, "news2": 180, "gai2": 150,
    }
    for tag in tags:
        score = max(score, weights.get(tag, 0))
        if tag.startswith("nf") and tag[2:].isdigit():
            score = max(score, 620 - int(tag[2:]) * 10)
    return score


def is_strong_common(tags: set[str]) -> bool:
    if tags & {"ichi1", "spec1", "news1", "gai1"}:
        return True
    return any(tag.startswith("nf") and tag[2:].isdigit() and int(tag[2:]) <= 20 for tag in tags)


def load_jmdict(path: Path) -> dict[tuple[str, str], dict]:
    result: dict[tuple[str, str], dict] = {}
    with gzip.open(path, "rb") as source:
        for _, entry in ET.iterparse(source, events=("end",)):
            if entry.tag != "entry":
                continue
            spellings = []
            for node in entry.findall("k_ele"):
                word = node.findtext("keb") or ""
                spellings.append((word, {x.text for x in node.findall("ke_pri") if x.text}))
            senses = []
            for sense in entry.findall("sense"):
                labels = {
                    x.text for name in ("misc", "field", "dial")
                    for x in sense.findall(name) if x.text
                }
                glosses = [
                    x.text for x in sense.findall("gloss")
                    if x.text and x.get(XML_LANG, "eng") == "eng"
                ]
                if glosses and not (labels & REJECT_LABELS):
                    senses.append((glosses[0], labels))
            if not senses:
                entry.clear()
                continue
            gloss, labels = senses[0]
            for reading_node in entry.findall("r_ele"):
                if reading_node.find("re_nokanji") is not None:
                    continue
                reading = reading_node.findtext("reb") or ""
                restrictions = {x.text for x in reading_node.findall("re_restr") if x.text}
                reading_pri = {x.text for x in reading_node.findall("re_pri") if x.text}
                for word, spelling_pri in spellings:
                    if restrictions and word not in restrictions:
                        continue
                    meta = {
                        "meaning_en": gloss,
                        "priority": spelling_pri | reading_pri,
                        "spelling_priority": spelling_pri,
                        "reading_priority": reading_pri,
                        "labels": labels,
                    }
                    key = (word, reading)
                    if key not in result or priority_score(meta["priority"]) > priority_score(result[key]["priority"]):
                        result[key] = meta
            entry.clear()
    return result


def parse_furigana_parts(word: str, reading: str, parts: list[dict]) -> list[dict]:
    """Return source-backed offsets for each furigana part.

    Offsets are accepted only when the source reconstructs both the spelling and
    its complete reading exactly. This prevents the UI from guessing a reading
    segment with substring matching.
    """
    parsed = []
    word_pos = 0
    reading_pos = 0
    for part in parts:
        ruby = part.get("ruby", "")
        if not ruby:
            return []
        spoken = kata_to_hira(part.get("rt") or ruby)
        parsed.append(
            {
                "ruby": ruby,
                "segment": spoken,
                "word_span": [word_pos, word_pos + len(ruby)],
                "reading_span": [reading_pos, reading_pos + len(spoken)],
                "has_rt": bool(part.get("rt")),
            }
        )
        word_pos += len(ruby)
        reading_pos += len(spoken)
    if "".join(part["ruby"] for part in parsed) != word:
        return []
    if "".join(part["segment"] for part in parsed) != reading:
        return []
    return parsed


def load_furigana_candidates(
    path: Path, wanted: set[str], lexical: dict
) -> tuple[dict[str, list[dict]], dict[tuple[str, str, str], list[dict]]]:
    with zipfile.ZipFile(path) as archive:
        with archive.open("JmdictFurigana.json") as source:
            entries = json.load(source)
    candidate_maps: dict[str, dict[tuple, dict]] = defaultdict(dict)
    alignments: dict[tuple[str, str, str], list[dict]] = {}
    for entry in entries:
        word = entry.get("text", "")
        reading = kata_to_hira(entry.get("reading", ""))
        meta = lexical.get((word, entry.get("reading", ""))) or lexical.get((word, reading))
        if not meta:
            continue
        parts = parse_furigana_parts(word, reading, entry.get("furigana") or [])
        if not parts:
            continue
        for target in set(word) & wanted:
            exact = [
                part for part in parts
                if part["has_rt"] and part["ruby"] == target and len(part["ruby"]) == 1
            ]
            if exact:
                key = (word, reading, target)
                if key not in alignments or len(exact) > len(alignments[key]):
                    alignments[key] = exact
        for pos, part in enumerate(parts):
            ruby = part["ruby"]
            if not part["has_rt"] or len(ruby) != 1 or ruby not in wanted:
                continue
            suffix = ""
            next_pos = pos + 1
            while next_pos < len(parts) and not parts[next_pos]["has_rt"]:
                plain = parts[next_pos]["ruby"]
                if not KANA_RE.fullmatch(plain):
                    break
                suffix += kata_to_hira(plain)
                next_pos += 1
            segment = part["segment"]
            same_reading_parts = [
                item for item in parts
                if item["has_rt"] and item["ruby"] == ruby and item["segment"] == segment
            ]
            candidate_key = (word, reading, segment, segment + suffix)
            candidate_maps[ruby][candidate_key] = {
                "word": word,
                "reading": reading,
                "segment": segment,
                "kun_form": segment + suffix,
                "word_highlights": [item["word_span"] for item in same_reading_parts],
                "reading_highlights": [item["reading_span"] for item in same_reading_parts],
                **meta,
            }
    index = {target: list(values.values()) for target, values in candidate_maps.items()}
    return index, alignments


def add_verified_highlights(
    picked: dict,
    target: str,
    display_reading: str,
    alignments: dict[tuple[str, str, str], list[dict]],
    allow_verified_variant: bool,
) -> None:
    """Attach only source-backed word/reading spans to an example.

    A manually verified or reference-word example may use rendaku, gemination
    or another sound change. In that case a unique source alignment is accepted.
    Ambiguous group ruby is never split.
    """
    parts = alignments.get((picked["word"], picked["reading"], target), [])
    if not parts:
        return
    expected = kata_to_hira(normalize_reading(display_reading))
    matches = [part for part in parts if part["segment"] == expected]
    if not matches and allow_verified_variant:
        if len(parts) == 1 or len({part["segment"] for part in parts}) == 1:
            matches = parts
    if not matches:
        return
    picked["word_highlights"] = [part["word_span"] for part in matches]
    picked["reading_highlights"] = [part["reading_span"] for part in matches]


def candidate_score(candidate: dict, target: str, used_words: set[str], preferred_words: set[str]) -> int:
    word = candidate["word"]
    score = priority_score(candidate["priority"])
    if word in N5_VOCAB_SEED:
        score += 1400
    if word in preferred_words:
        score += 1800
    score += priority_score(candidate.get("reading_priority", set()))
    score += 260 if len(word) <= 3 else 0
    score -= 75 * max(0, len(word) - 2)
    score -= 110 * max(0, len(KANJI_RE.findall(word)) - 2)
    if word in used_words:
        score -= 900
    if word == target:
        score += 180
    return score


MANUAL = {
    ("日", "kun", "ひ"): {
        "word": "日", "reading": "ひ", "meaning_en": "Day", "advanced": False,
    },
    ("日", "kun", "か"): {
        "word": "三日", "reading": "みっか", "meaning_en": "Third day / Three days",
        "advanced": False,
        "usage_note": "Contextual reading used in day counters",
    },
    ("日", "on", "ニチ"): {
        "word": "日曜日", "reading": "にちようび", "meaning_en": "Sunday", "advanced": False,
    },
    ("日", "on", "ジツ"): {
        "word": "本日", "reading": "ほんじつ", "meaning_en": "Today (formal)",
        "advanced": True, "usage_note": "Formal vocabulary",
    },
    ("男", "kun", "おとこ"): {
        "word": "男", "reading": "おとこ", "meaning_en": "Man / Male", "advanced": False,
    },
    ("女", "kun", "おんな"): {
        "word": "女", "reading": "おんな", "meaning_en": "Woman / Female", "advanced": False,
    },
    ("子", "kun", "こ"): {
        "word": "子", "reading": "こ", "meaning_en": "Child", "advanced": False,
    },
    ("友", "kun", "とも"): {
        "word": "友", "reading": "とも", "meaning_en": "Friend", "advanced": False,
    },
    ("田", "kun", "た"): {
        "word": "田", "reading": "た", "meaning_en": "Rice field", "advanced": False,
    },
    ("屋", "kun", "や"): {
        "word": "本屋", "reading": "ほんや", "meaning_en": "Bookstore", "advanced": False,
    },
    ("事", "kun", "こと"): {
        "word": "事", "reading": "こと", "meaning_en": "Thing / Matter", "advanced": False,
    },
    ("筆", "on", "ヒツ"): {
        "word": "鉛筆", "reading": "えんぴつ", "meaning_en": "Pencil", "advanced": False,
        "usage_note": "ヒツ becomes ぴつ in this compound",
    },
    ("符", "on", "フ"): {
        "word": "切符", "reading": "きっぷ", "meaning_en": "Ticket", "advanced": False,
        "usage_note": "フ becomes ぷ in this compound",
    },
    ("計", "on", "ケイ"): {
        "word": "計画", "reading": "けいかく", "meaning_en": "Plan", "advanced": False,
    },
    ("雑", "on", "ザツ"): {
        "word": "雑誌", "reading": "ざっし", "meaning_en": "Magazine", "advanced": False,
        "usage_note": "ザツ becomes ざっ in this compound",
    },
    ("結", "on", "ケツ"): {
        "word": "結婚", "reading": "けっこん", "meaning_en": "Marriage", "advanced": False,
        "usage_note": "ケツ becomes けっ in this compound",
    },
    ("失", "on", "シツ"): {
        "word": "失敗", "reading": "しっぱい", "meaning_en": "Failure / Mistake", "advanced": False,
        "usage_note": "シツ becomes しっ in this compound",
    },
    ("敗", "on", "ハイ"): {
        "word": "失敗", "reading": "しっぱい", "meaning_en": "Failure / Mistake", "advanced": False,
        "usage_note": "ハイ becomes ぱい in this compound",
    },
    ("個", "on", "コ"): {
        "word": "一個", "reading": "いっこ", "meaning_en": "One item", "advanced": False,
        "usage_note": "Counter for small objects",
    },
    ("杯", "on", "ハイ"): {
        "word": "一杯", "reading": "いっぱい", "meaning_en": "One cup / One glass", "advanced": False,
        "usage_note": "ハイ becomes ぱい after 一 in this counter",
    },
    ("匹", "kun", "ひき"): {
        "word": "一匹", "reading": "いっぴき", "meaning_en": "One small animal", "advanced": False,
        "usage_note": "ひき becomes ぴき after 一 in this counter",
    },
    ("月", "on", "ゲツ"): {
        "word": "月曜日", "reading": "げつようび", "meaning_en": "Monday", "advanced": False,
    },
    ("月", "on", "ガツ"): {
        "word": "一月", "reading": "いちがつ", "meaning_en": "January", "advanced": False,
    },
    ("火", "on", "カ"): {
        "word": "火曜日", "reading": "かようび", "meaning_en": "Tuesday", "advanced": False,
    },
    ("水", "on", "スイ"): {
        "word": "水曜日", "reading": "すいようび", "meaning_en": "Wednesday", "advanced": False,
    },
    ("木", "on", "モク"): {
        "word": "木曜日", "reading": "もくようび", "meaning_en": "Thursday", "advanced": False,
    },
    ("金", "on", "キン"): {
        "word": "金曜日", "reading": "きんようび", "meaning_en": "Friday", "advanced": False,
    },
    ("土", "on", "ド"): {
        "word": "土曜日", "reading": "どようび", "meaning_en": "Saturday", "advanced": False,
    },
    ("前", "on", "ゼン"): {
        "word": "午前", "reading": "ごぜん", "meaning_en": "A.M. / Morning", "advanced": False,
    },
    ("後", "on", "ゴ"): {
        "word": "午後", "reading": "ごご", "meaning_en": "P.M. / Afternoon", "advanced": False,
    },
    ("朝", "on", "チョウ"): {
        "word": "朝食", "reading": "ちょうしょく", "meaning_en": "Breakfast", "advanced": True,
    },
    ("夜", "on", "ヤ"): {
        "word": "今夜", "reading": "こんや", "meaning_en": "Tonight", "advanced": False,
    },
    ("人", "on", "ジン"): {
        "word": "日本人", "reading": "にほんじん", "meaning_en": "Japanese person", "advanced": False,
    },
    ("人", "on", "ニン"): {
        "word": "三人", "reading": "さんにん", "meaning_en": "Three people", "advanced": False,
        "usage_note": "Counter for people",
    },
    ("名", "on", "メイ"): {
        "word": "有名", "reading": "ゆうめい", "meaning_en": "Famous", "advanced": False,
    },
    ("私", "on", "シ"): {
        "word": "私立", "reading": "しりつ", "meaning_en": "Private (institution)", "advanced": True,
    },
    ("男", "on", "ダン"): {
        "word": "男子", "reading": "だんし", "meaning_en": "Boy / Male", "advanced": False,
    },
    ("女", "on", "ジョ"): {
        "word": "女子", "reading": "じょし", "meaning_en": "Girl / Female", "advanced": False,
    },
    ("子", "on", "シ"): {
        "word": "帽子", "reading": "ぼうし", "meaning_en": "Hat", "advanced": False,
    },
    ("父", "on", "フ"): {
        "word": "義父", "reading": "ぎふ", "meaning_en": "Father-in-law", "advanced": True,
    },
    ("母", "on", "ボ"): {
        "word": "義母", "reading": "ぎぼ", "meaning_en": "Mother-in-law", "advanced": True,
    },
    ("国", "on", "コク"): {
        "word": "外国", "reading": "がいこく", "meaning_en": "Foreign country", "advanced": False,
    },
    ("上", "on", "ジョウ"): {
        "word": "上手", "reading": "じょうず", "meaning_en": "Skillful / Good at", "advanced": False,
    },
    ("下", "on", "カ"): {
        "word": "地下", "reading": "ちか", "meaning_en": "Underground", "advanced": False,
    },
    ("左", "on", "サ"): {
        "word": "左右", "reading": "さゆう", "meaning_en": "Left and right", "advanced": False,
    },
    ("右", "on", "ウ"): {
        "word": "右折", "reading": "うせつ", "meaning_en": "Right turn", "advanced": True,
    },
    ("右", "on", "ユウ"): {
        "word": "左右", "reading": "さゆう", "meaning_en": "Left and right", "advanced": False,
    },
    ("東", "on", "トウ"): {
        "word": "東京", "reading": "とうきょう", "meaning_en": "Tokyo", "advanced": False,
    },
    ("西", "on", "セイ"): {
        "word": "西洋", "reading": "せいよう", "meaning_en": "The West / Western countries", "advanced": True,
    },
    ("南", "on", "ナン"): {
        "word": "南極", "reading": "なんきょく", "meaning_en": "South Pole", "advanced": True,
    },
    ("北", "on", "ホク"): {
        "word": "北西", "reading": "ほくせい", "meaning_en": "Northwest", "advanced": False,
    },
    ("空", "on", "クウ"): {
        "word": "空港", "reading": "くうこう", "meaning_en": "Airport", "advanced": False,
    },
    ("来", "on", "ライ"): {
        "word": "来週", "reading": "らいしゅう", "meaning_en": "Next week", "advanced": False,
    },
    ("書", "on", "ショ"): {
        "word": "辞書", "reading": "じしょ", "meaning_en": "Dictionary", "advanced": False,
    },
    ("話", "on", "ワ"): {
        "word": "会話", "reading": "かいわ", "meaning_en": "Conversation", "advanced": False,
    },
    ("言", "on", "ゲン"): {
        "word": "言語", "reading": "げんご", "meaning_en": "Language", "advanced": False,
    },
    ("家", "on", "カ"): {
        "word": "家族", "reading": "かぞく", "meaning_en": "Family", "advanced": False,
    },
    ("住", "on", "ジュウ"): {
        "word": "住所", "reading": "じゅうしょ", "meaning_en": "Address", "advanced": False,
    },
}


def choose_examples(
    cards: list[dict],
    lexical: dict,
    candidates: dict,
    alignments: dict[tuple[str, str, str], list[dict]],
) -> tuple[list[dict], list[dict]]:
    missing = []
    audit = []
    preferred_words = {c["reference_word"] for c in cards}
    elementary_words = {
        c["reference_word"] for c in cards
        if c["kanji"] in N5_CORE_KANJI or int(c["order"]) <= 130
    }
    for card in cards:
        examples = []
        used_words: set[str] = set()
        reference_normalized = normalize_reading(card["reference_reading_kana"])
        reference_kind = card.get("reference_reading_type")
        reference_word = card["reference_word"]
        reference_reading = kata_to_hira(card["reference_word_reading_kana"])
        reference_meta = lexical.get((reference_word, reference_reading), {})

        for kind, field in (("kun", "kun_readings"), ("on", "on_readings")):
            for item in card.get(field, []):
                display = item["kana"]
                key = (card["kanji"], kind, display)
                if key in MANUAL:
                    picked = dict(MANUAL[key])
                    source = "manual"
                elif kind == reference_kind and normalize_reading(display) == reference_normalized:
                    tags = set(reference_meta.get("priority", set()))
                    picked = {
                        "word": reference_word,
                        "reading": reference_reading,
                        "meaning_en": card["reference_word_meaning_en"],
                        "advanced": reference_word not in N5_VOCAB_SEED
                        and reference_word not in elementary_words
                        and not (
                            card["kanji"] in N5_CORE_KANJI
                            and is_strong_common(reference_meta.get("reading_priority", set()))
                        ),
                    }
                    source = "reference"
                else:
                    target = kata_to_hira(normalize_reading(display))
                    pool = []
                    for candidate in candidates.get(card["kanji"], []):
                        actual = candidate["kun_form"] if kind == "kun" else candidate["segment"]
                        if actual == target:
                            pool.append(candidate)
                    if not pool:
                        missing.append({"kanji": card["kanji"], "kind": kind, "reading": display})
                        continue
                    candidate = max(
                        pool,
                        key=lambda x: candidate_score(
                            x, card["kanji"], used_words, preferred_words
                        ),
                    )
                    tags = set(candidate["priority"])
                    picked = {
                        "word": candidate["word"],
                        "reading": candidate["reading"],
                        "meaning_en": candidate["meaning_en"],
                        "advanced": candidate["word"] not in N5_VOCAB_SEED
                        and candidate["word"] not in elementary_words
                        and not (
                            card["kanji"] in N5_CORE_KANJI
                            and is_strong_common(candidate.get("reading_priority", set()))
                        ),
                        "word_highlights": candidate["word_highlights"],
                        "reading_highlights": candidate["reading_highlights"],
                    }
                    source = "jmdict"
                if "word_highlights" not in picked:
                    add_verified_highlights(
                        picked,
                        card["kanji"],
                        display,
                        alignments,
                        allow_verified_variant=source in {"manual", "reference"},
                    )
                picked.update({"kind": kind, "reading_kana": display})
                examples.append(picked)
                used_words.add(picked["word"])
                audit.append({"kanji": card["kanji"], "source": source, **picked})
        card["reading_examples"] = examples
    return missing, audit


def update_ui(html: str) -> str:
    font_face = (
        "@font-face{font-family:'Noto Sans JP';"
        "src:url('assets/NotoSansJP-Variable.ttf') format('truetype');"
        "font-style:normal;font-weight:100 900;font-display:block}"
    )
    if font_face not in html:
        html = html.replace("<style>", "<style>" + font_face, 1)
    old_big_kanji = ".flashcard .big-kanji{font:145px/1.5 'Yu Mincho','Noto Serif CJK JP',serif}"
    new_big_kanji = ".flashcard .big-kanji{font:400 145px/1.5 'Noto Sans JP',sans-serif}"
    if old_big_kanji in html:
        html = html.replace(old_big_kanji, new_big_kanji, 1)
    elif new_big_kanji not in html:
        raise SystemExit("Main kanji font rule not found")
    old_library_kanji = ".tile .character{font:48px/1.6 'Yu Mincho',serif;display:block;text-align:center}"
    new_library_kanji = ".tile .character{font:400 48px/1.6 'Noto Sans JP',sans-serif;display:block;text-align:center}"
    if old_library_kanji in html:
        html = html.replace(old_library_kanji, new_library_kanji, 1)
    elif new_library_kanji not in html:
        raise SystemExit("Library kanji font rule not found")

    old = re.compile(
        r"(?:function highlightRanges\(value,ranges\)|function readingExample\(x\)|function readingBlock\(label,readings,kind(?:,examples)?\))\{.*?\nfunction startSession",
        re.S,
    )
    replacement = r'''function highlightRanges(value,ranges){if(!Array.isArray(ranges)||!ranges.length)return esc(value);let out='',cursor=0;for(const range of ranges){if(!Array.isArray(range)||range.length!==2)continue;const start=Number(range[0]),end=Number(range[1]);if(!Number.isInteger(start)||!Number.isInteger(end)||start<cursor||end<=start||end>value.length)continue;out+=esc(value.slice(cursor,start))+`<span class="reading-focus">${esc(value.slice(start,end))}</span>`;cursor=end;}return out+esc(value.slice(cursor));}
function readingExample(x){return `<div class="reading-example"><span class="reading-example-main"><span class="reading-example-word" lang="ja">${highlightRanges(x.word,x.word_highlights)}</span><span class="reading-example-kana" lang="ja">（${highlightRanges(x.reading,x.reading_highlights)}）</span></span><span class="reading-example-meaning" lang="en">${esc(x.meaning_en)}</span>${x.advanced?'<span class="reading-level">Advanced</span>':''}${x.usage_note?`<span class="reading-usage-note">${esc(x.usage_note)}</span>`:''}</div>`;}
function readingBlock(label,readings,kind,examples){return `<section class="reading-block ${kind}" aria-label="${label}"><div class="reading-title">${label}</div>${readings.length?`<div class="reading-list">${readings.map(r=>{const matches=examples.filter(x=>x.kind===kind&&x.reading_kana===r.kana);return `<div class="reading-item"><div class="reading-item-head"><span class="reading-kana" lang="ja">${esc(r.kana)}</span>${data.settings.romaji?`<span class="reading-romaji">${esc(r.romaji)}</span>`:''}</div><div class="reading-linked-examples">${matches.map(readingExample).join('')}</div></div>`}).join('')}</div>`:'<span class="reading-empty">Nessuna lettura essenziale selezionata</span>'}</section>`;}
function answer(c){const examples=c.reading_examples||[];const referenceCovered=examples.some(x=>x.word===c.reference_word&&x.reading===c.reference_word_reading_kana);return `<h2 class="answer-meaning" lang="en">${esc(c.meaning_en)}</h2><div class="reading-sections">${readingBlock("KUN'YOMI",c.kun_readings||[],'kun',examples)}${readingBlock("ON'YOMI",c.on_readings||[],'on',examples)}</div>${referenceCovered?'':`<div class="word-line"><span class="reference-word-label">Parola di riferimento</span><span lang="ja">${esc(c.reference_word)}</span> · <span lang="ja">${esc(c.reference_word_reading_kana)}</span>${data.settings.romaji?` · ${esc(c.reference_word_romaji)}`:''}<br><span lang="en">${esc(c.reference_word_meaning_en)}</span></div>`}<div class="example"><p class="jp" lang="ja">${esc(c.example_ja)}</p><p class="kana" lang="ja">${esc(c.example_kana)}</p><p class="en" lang="en">${esc(c.example_en)}</p></div>${c.notes_it?`<details><summary>Note</summary><p>${esc(c.notes_it)}</p></details>`:''}`;}
function startSession'''
    html, count = old.subn(replacement, html, count=1)
    if count != 1:
        raise SystemExit(f"Reading renderer not found: {count}")

    css = (
        ".reading-list{display:grid;gap:8px}.reading-item{min-width:0;text-align:left;padding:10px 11px}"
        ".reading-item-head{display:flex;align-items:baseline;gap:9px}.reading-romaji{margin-left:0}"
        ".reading-linked-examples{margin-top:7px;border-top:1px solid var(--line);padding-top:5px}"
        ".reading-example{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:3px 10px;align-items:baseline;padding:5px 0;border-bottom:1px solid #e2e8f0;font-size:12px}"
        ".reading-example:last-child{border-bottom:0}.reading-example-main{white-space:nowrap}"
        ".reading-example-word{font-size:16px}.reading-example-kana{font-size:12px;color:var(--muted)}.reading-focus{color:var(--orange);font-weight:700}"
        ".reading-example-meaning{color:var(--ink);min-width:0}.reading-level{grid-column:2;justify-self:start;font-size:9px;letter-spacing:.5px;color:#8d5038;background:#f5e9e3;border-radius:10px;padding:2px 6px}"
        ".reading-usage-note{grid-column:1/-1;color:var(--muted);font-size:10px}"
    )
    html = html.replace(
        ".reading-example{display:grid;grid-template-columns:minmax(0,auto) 1fr auto;gap:3px 8px;align-items:baseline;padding:5px 0;border-bottom:1px solid #e2e8f0;font-size:12px}",
        ".reading-example{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:3px 10px;align-items:baseline;padding:5px 0;border-bottom:1px solid #e2e8f0;font-size:12px}",
    )
    html = html.replace(
        ".reading-example-meaning{color:var(--ink)}.reading-level{font-size:9px;letter-spacing:.5px;color:#8d5038;background:#f5e9e3;border-radius:10px;padding:2px 6px}",
        ".reading-example-meaning{color:var(--ink);min-width:0}.reading-level{grid-column:2;justify-self:start;font-size:9px;letter-spacing:.5px;color:#8d5038;background:#f5e9e3;border-radius:10px;padding:2px 6px}",
    )
    if ".reading-linked-examples{" not in html:
        html = html.replace("@media(min-width:1500px)", css + "@media(min-width:1500px)", 1)
    elif ".reading-focus{" not in html:
        html = html.replace(
            ".reading-example-word{font-size:16px}.reading-example-kana{font-size:12px;color:var(--muted)}",
            ".reading-example-word{font-size:16px}.reading-example-kana{font-size:12px;color:var(--muted)}.reading-focus{color:var(--orange);font-weight:700}",
            1,
        )
    return html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("jmdict", type=Path)
    parser.add_argument("furigana", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()

    html = args.html.read_text(encoding="utf-8")
    match = LIBRARY_RE.search(html)
    if not match:
        raise SystemExit("Embedded library not found")
    cards = json.loads(match.group(2))
    lexical = load_jmdict(args.jmdict)
    candidates, alignments = load_furigana_candidates(
        args.furigana, {c["kanji"] for c in cards}, lexical
    )
    missing, audit = choose_examples(cards, lexical, candidates, alignments)
    if args.audit:
        args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "cards": len(cards),
        "displayed_readings": sum(len(c.get("kun_readings", [])) + len(c.get("on_readings", [])) for c in cards),
        "examples": sum(len(c.get("reading_examples", [])) for c in cards),
        "advanced": sum(x["advanced"] for x in audit),
        "highlighted": sum(bool(x.get("word_highlights")) for x in audit),
        "missing": missing,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if missing:
        raise SystemExit("Some displayed readings still lack a verified example")
    if not args.write:
        return

    library_json = json.dumps(cards, ensure_ascii=False, separators=(", ", ": "))
    html = html[:match.start(2)] + library_json + html[match.end(2):]
    html = update_ui(html)
    args.html.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
