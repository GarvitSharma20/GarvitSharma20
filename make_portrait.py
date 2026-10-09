#!/usr/bin/env python3
"""
Turns avatar.png into portrait.txt (characters) and portrait_tone.txt (which cells are skin vs dark).
Usage: python make_portrait.py [avatar.png]     Needs: pip install pillow numpy
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "avatar.png"
COLS, ROWS = 150, 73                      # grid; char cell is 1:2 so the picture keeps its shape
PANEL_ASPECT = 473 / 459                  # portrait panel width / height in the SVG
RAMP = " .'`:;-~+=*xX#%@"                # light -> dense, few shapes so the picture stays readable


def main():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    a = np.asarray(img, dtype=float)
    yy, xx = np.mgrid[0:h, 0:w]
    r_from_c = np.hypot(xx - w / 2, yy - h / 2)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    cream = (r > 215) & (g > 210) & (b > 185) & ((r - b) < 60)          # the pale circle background
    inside = r_from_c < 0.412 * w                                         # drop the outer ring and dark surround
    subject = inside & ~cream

    lum = np.asarray(img.convert("L").filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2)), dtype=float)
    ink = 1 - lum / 255                                                   # darker = denser characters
    lo, hi = np.percentile(ink[subject], [2, 98])
    ink = np.clip((ink - lo) / (hi - lo), 0, 1)
    # skin is mid-tone, so stretch it on its own: eyes, nose and lips need to stand out from the cheeks
    skin_mask = subject & (r > 110) & ((r - b) > 35)
    if skin_mask.sum() > 100:
        slo, shi = np.percentile(ink[skin_mask], [3, 97])
        stretched = np.clip((ink - slo) / (shi - slo), 0, 1) * 0.72 + 0.12
        ink = np.where(skin_mask, stretched, ink)
    ink = (ink ** 0.9) * subject

    ys, xs = np.where(subject)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    ch = (ys.max() - ys.min()) * 1.04
    cw = ch * PANEL_ASPECT
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))

    def grid(arr):
        im = Image.fromarray((arr * 255).astype(np.uint8)) if arr.dtype != np.uint8 else Image.fromarray(arr)
        return np.asarray(im.crop(box).resize((COLS, ROWS), Image.BOX), dtype=float) / 255

    ink_g = grid(ink)
    mask_g = grid(subject.astype(float))
    skin_px = subject & (r > 110) & ((r - b) > 35)
    skin_g = grid(skin_px.astype(float))

    chars = RAMP
    rows, tones = [], []
    for j in range(ROWS):
        row, tone = [], []
        for i in range(COLS):
            v = ink_g[j, i]
            if mask_g[j, i] < 0.18 or v < 0.05:
                row.append(" "); tone.append(" "); continue
            k = int(min(v, 0.999) * (len(chars) - 1)) + 1
            row.append(chars[k])
            tone.append("s" if skin_g[j, i] / max(mask_g[j, i], 1e-6) > 0.5 else "d")
        rows.append("".join(row).rstrip())
        tones.append("".join(tone).rstrip())
    (HERE / "portrait.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (HERE / "portrait_tone.txt").write_text("\n".join(tones) + "\n", encoding="utf-8")
    print(f"portrait {COLS}x{ROWS}; crop box {box}")


if __name__ == "__main__":
    main()
