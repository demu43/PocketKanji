#!/usr/bin/env python3
"""Add conservative, whole-sentence kanji/kana alignments to PocketKanji cards."""

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "PocketKanji.html"
LIB = re.compile(r'(<script id="library-data" type="application/json">)(.*?)(</script>)', re.S)
KANJI = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')


def hira(value):
    return ''.join(chr(ord(c) - 96) if 'ァ' <= c <= 'ヶ' else c for c in value)


def variants(value):
    value = hira(value.replace('.', ''))
    out = {value}
    pairs = {'か':'が','き':'ぎ','く':'ぐ','け':'げ','こ':'ご','さ':'ざ','し':'じ','す':'ず','せ':'ぜ','そ':'ぞ','た':'だ','ち':'ぢ','つ':'づ','て':'で','と':'ど','は':'ば','ひ':'び','ふ':'ぶ','へ':'べ','ほ':'ぼ'}
    if value and value[0] in pairs:
        out.add(pairs[value[0]] + value[1:])
    return {x for x in out if x}


def build_readings(cards):
    readings = {}
    for card in cards:
        values = set()
        for item in card.get('kun_readings', []) + card.get('on_readings', []):
            values |= variants(item['kana'])
        for ex in card.get('reading_examples', []):
            for start, end in ex.get('reading_highlights', []):
                values |= variants(ex['reading'][start:end])
        readings[card['kanji']] = sorted(values, key=lambda x: (-len(x), x))
    return readings


def align(sentence, kana, readings, target):
    @lru_cache(None)
    def walk(i, j):
        if i == len(sentence):
            return ((),) if j == len(kana) else ()
        ch = sentence[i]
        results = []
        if KANJI.fullmatch(ch):
            for reading in readings.get(ch, ()):
                if kana.startswith(reading, j):
                    for rest in walk(i + 1, j + len(reading)):
                        results.append(((i, j, j + len(reading)),) + rest)
        else:
            normalized = hira(ch)
            if j < len(kana) and hira(kana[j]) == normalized:
                results.extend(walk(i + 1, j + 1))
            elif ch.isspace() or ch in '。、！？!?・「」『』（）()':
                results.extend(walk(i + 1, j))
        return tuple(results[:200])

    solutions = walk(0, 0)
    if not solutions:
        return None
    target_maps = []
    for solution in solutions:
        spans = tuple((start, end) for index, start, end in solution if sentence[index] == target)
        target_maps.append(spans)
    if not target_maps or not target_maps[0] or any(item != target_maps[0] for item in target_maps[1:]):
        return None
    word_spans = [[i, i + 1] for i, ch in enumerate(sentence) if ch == target]
    return word_spans, [list(span) for span in target_maps[0]]


def main():
    html = HTML.read_text(encoding='utf-8')
    match = LIB.search(html)
    cards = json.loads(match.group(2))
    readings = build_readings(cards)
    count = 0
    for card in cards:
        card.pop('sentence_word_highlights', None)
        card.pop('sentence_reading_highlights', None)
        result = align(card['example_ja'], card['example_kana'], readings, card['kanji'])
        if result:
            card['sentence_word_highlights'], card['sentence_reading_highlights'] = result
            count += 1
    payload = json.dumps(cards, ensure_ascii=False, separators=(',', ':'))
    HTML.write_text(html[:match.start(2)] + payload + html[match.end(2):], encoding='utf-8')
    print(f'sentence highlights: {count}/{len(cards)}')


if __name__ == '__main__':
    main()
