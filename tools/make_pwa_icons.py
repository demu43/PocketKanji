#!/usr/bin/env python3
"""Generate dependency-free PocketKanji PNG icons."""

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def make_icon(size):
    navy = (25, 59, 101)
    cream = (247, 245, 239)
    pixels = [[navy for _ in range(size)] for _ in range(size)]

    margin = round(size * 0.05)
    radius = round(size * 0.16)
    for y in range(margin, size - margin):
        for x in range(margin, size - margin):
            dx = max(margin + radius - x, 0, x - (size - margin - radius - 1))
            dy = max(margin + radius - y, 0, y - (size - margin - radius - 1))
            if dx * dx + dy * dy <= radius * radius:
                pixels[y][x] = cream

    glyph_scale = 0.8

    def bar(x1, y1, x2, y2, thickness=0.035):
        # Shrink the glyph around the centre to leave more room inside the frame.
        x1, y1, x2, y2 = (0.5 + (c - 0.5) * glyph_scale for c in (x1, y1, x2, y2))
        t = max(2, round(size * thickness * glyph_scale))
        for y in range(round(size * y1), round(size * y2) + t):
            for x in range(round(size * x1), round(size * x2) + t):
                if 0 <= x < size and 0 <= y < size:
                    pixels[y][x] = navy

    # A clean geometric rendering inspired by 字, readable at home-screen size.
    bar(.31, .31, .69, .31)
    bar(.28, .36, .28, .48)
    bar(.28, .45, .72, .45)
    bar(.72, .36, .72, .48)
    bar(.38, .53, .65, .53)
    bar(.50, .53, .50, .72)
    bar(.35, .68, .65, .68)

    raw = b"".join(b"\x00" + bytes(channel for pixel in row for channel in (*pixel, 255)) for row in pixels)
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")


for icon_size in (180, 192, 512):
    (ROOT / "assets" / f"icon-{icon_size}.png").write_bytes(make_icon(icon_size))
