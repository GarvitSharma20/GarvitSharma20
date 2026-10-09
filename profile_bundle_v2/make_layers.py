#!/usr/bin/env python3
"""
One-time build step for the morph frames. Reads portrait.txt and icons/*.svg, writes:
  layers/code.txt        your portrait redrawn with code symbols ({ } < > / ; ...)
  layers/<language>.txt  each language logo drawn out of code symbols
Needs:  pip install pillow cairosvg numpy
"""
import io
import re
from pathlib import Path
import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
CELL_W, CELL_H = 10, 20                    # raster pixels per character cell (1:2, like the SVG's cells)
LOGOS = ["python", "typescript", "javascript", "flutter", "firebase", "arduino", "espressif"]
PALETTE = list("./\\|<>()[]{}=+-*#&$%@;:,!?~^")
DENSE = list("{}<>/;()[]=#&")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def coverage(ch, font):
    im = Image.new("L", (60, 80), 0)
    ImageDraw.Draw(im).text((10, 10), ch, font=font, fill=255)
    return float(np.asarray(im, dtype=float).mean() / 255)


def pick(seq, r, c):
    return seq[(r * 31 + c * 17 + r * c) % len(seq)]


def code_portrait(rows, cols, font):
    pal = [(coverage(ch, font), ch) for ch in PALETTE]
    cache, out = {}, []
    for r, row in enumerate(rows):
        line = []
        for c, ch in enumerate(row.ljust(cols)):
            if ch == " ":
                line.append(" ")
                continue
            if ch not in cache:
                cv = coverage(ch, font)
                cache[ch] = [p[1] for p in sorted(pal, key=lambda p: abs(p[0] - cv))[:3]]
            line.append(pick(cache[ch], r, c))
        out.append("".join(line).rstrip())
    return out


def logo_ascii(svg_path, cols, rows):
    d = re.search(r'<path d="([^"]+)"', Path(svg_path).read_text(encoding="utf-8")).group(1)
    W, H = cols * CELL_W, rows * CELL_H
    size = int(min(W, H) * 0.86)
    png = cairosvg.svg2png(bytestring=(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">'
        f'<path d="{d}"/></svg>').encode())
    alpha = Image.open(io.BytesIO(png)).convert("RGBA").split()[3]
    canvas = Image.new("L", (W, H), 0)
    canvas.paste(alpha, ((W - size) // 2, (H - size) // 2))
    cov = np.asarray(canvas.resize((cols, rows), Image.BOX), dtype=float) / 255
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            v = cov[r, c]
            if v >= 0.55:
                line.append(pick(DENSE, r, c))
            elif v >= 0.28:
                line.append(pick(list("+*:;="), r, c))
            elif v >= 0.10:
                line.append(".")
            else:
                line.append(" ")
        out.append("".join(line).rstrip())
    return out


if __name__ == "__main__":
    (HERE / "layers").mkdir(exist_ok=True)
    rows = (HERE / "portrait.txt").read_text(encoding="utf-8").splitlines()
    cols, nrows = max(len(r) for r in rows), len(rows)
    cols = max(cols, 150)
    font = ImageFont.truetype(FONT, 40)
    (HERE / "layers/code.txt").write_text("\n".join(code_portrait(rows, cols, font)) + "\n", encoding="utf-8")
    for name in LOGOS:
        art = logo_ascii(HERE / "icons" / f"{name}.svg", cols, nrows)
        (HERE / f"layers/{name}.txt").write_text("\n".join(art) + "\n", encoding="utf-8")
    print(f"grid {cols}x{nrows}: wrote layers/code.txt +", ", ".join(LOGOS))
