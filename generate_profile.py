#!/usr/bin/env python3
"""
Builds animated dark_mode.svg and light_mode.svg: a two-window terminal card.
  left window   ./portrait.sh  your ASCII portrait; it types itself in, then every row is
                retyped in place as code symbols and language logos, and the loop repeats
  right window  ./stats.sh     GitHub numbers as cards, with a languages bar

Inputs: portrait.txt + portrait_tone.txt (make_portrait.py), layers/*.txt (make_layers.py).
Usage:  python generate_profile.py        (no dependencies)
"""
import xml.dom.minidom
from pathlib import Path

# ───────────────────────── CONFIG ─────────────────────────
USER = "garvit"
NAME = "Garvit Sharma"
LOCATION = "Ghaziabad, India"
BUILDING = "Vasuki, AI interviewer"

CARDS = [                       # (label, value, sub-text)  - edit freely
    ("repos", "43", "on github"),
    ("followers", "5", "following 2"),
    ("contributions", "19", "in the last year"),
    ("commits", "109", "recorded by github"),
    ("stars", "1", "top repo: ai-interview"),
    ("patents filed", "2", "Vasuki · Pavitra Step"),
]
LANGS = [("TypeScript", 45, "ts"), ("Python", 20, "py"), ("Other", 35, "ot")]

FRAMES = [("code", "// code"), ("python", "// python"), ("typescript", "// typescript"),
          ("javascript", "// javascript"), ("flutter", "// flutter / dart"),
          ("firebase", "// firebase"), ("arduino", "// arduino"), ("espressif", "// esp32")]
SLOT = 4.5         # seconds each frame stays (typing + hold)
STAGGER = 0.03     # seconds between one row starting to type and the next
TYPE_TIME = 0.30   # seconds one row takes to type
# ──────────────────────────────────────────────────────────

W, H = 1080, 562
CW, CH, FS = 3.1, 6.2, 5.6                   # portrait cell width / height / font size
HERE = Path(__file__).parent
PORTRAIT = (HERE / "portrait.txt").read_text(encoding="utf-8").splitlines()
TONE = (HERE / "portrait_tone.txt").read_text(encoding="utf-8").splitlines()
N_FRAMES = len(FRAMES) + 1
LOOP_DUR = SLOT * N_FRAMES

THEMES = {
    "dark": dict(page="#0b0f14", panel="#0d1117", edge="#21262d", bar="#10151c", fg="#c9d1d9", dim="#7d8590",
                 bright="#f0f6fc", card="#141a22", cardedge="#242c36", skin="#e0a66c", green="#3fb950",
                 ts="#3178c6", py="#f7df1e", ot="#484f58",
                 frames=dict(code="#3fb950", python="#5ba3d9", typescript="#3b8fe0", javascript="#f7df1e",
                             flutter="#54c5f8", firebase="#ffca28", arduino="#00b8c4", espressif="#ef5350")),
    "light": dict(page="#eaeef2", panel="#ffffff", edge="#d0d7de", bar="#f6f8fa", fg="#24292f", dim="#6e7781",
                  bright="#1f2328", card="#f6f8fa", cardedge="#d8dee4", skin="#9a5b22", green="#1a7f37",
                  ts="#3178c6", py="#bf8700", ot="#afb8c1",
                  frames=dict(code="#1a7f37", python="#3776ab", typescript="#3178c6", javascript="#b59a00",
                              flutter="#02569b", firebase="#dd2c00", arduino="#00878f", espressif="#e7352c")),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row_keyframes():
    """Shared keyframes: type a row left to right, hold, vanish. Per-row delays reuse them."""
    tp = TYPE_TIME / LOOP_DUR * 100
    hp = SLOT / LOOP_DUR * 100
    return (f"@keyframes row {{ "
            f"0% {{ clip-path: inset(0 100% 0 0); opacity: 0; }} "
            f"0.001% {{ clip-path: inset(0 100% 0 0); opacity: 1; animation-timing-function: steps(24, end); }} "
            f"{tp:.3f}% {{ clip-path: inset(0 0 0 0); opacity: 1; }} "
            f"{hp - 0.01:.3f}% {{ clip-path: inset(0 0 0 0); opacity: 1; }} "
            f"{hp:.3f}%, 100% {{ clip-path: inset(0 0 0 0); opacity: 0; }} }}")


def tinted_row(row, tone):
    """Run-length groups so skin cells get the warm colour and the rest the default."""
    tone = tone.ljust(len(row))
    parts, cur, buf = [], None, ""
    for ch, t in zip(row, tone):
        k = "s" if t == "s" else "d" if t == "d" else cur or "d"
        if k != cur and buf:
            parts.append((cur, buf))
            buf = ""
        cur = k
        buf += ch
    if buf:
        parts.append((cur, buf))
    return "".join(f'<tspan class="s">{esc(b)}</tspan>' if k == "s" else f'<tspan>{esc(b)}</tspan>'
                   for k, b in parts)


def build(name):
    t = THEMES[name]
    out = []
    add = out.append
    frame_css = "\n  ".join(f".f-{k} text {{ fill: {v}; }}" for k, v in t["frames"].items())

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{USER}@github terminal card with ASCII portrait and GitHub stats">')
    add(f"""<style>
  text {{ font-family: Consolas, Menlo, "DejaVu Sans Mono", "Liberation Mono", monospace; fill: {t['fg']}; white-space: pre; }}
  .art {{ font-size: {FS}px; }}
  .art .s {{ fill: {t['skin']}; }}
  .ttl {{ font-size: 9px; fill: {t['dim']}; }}
  .lab {{ font-size: 12px; fill: {t['dim']}; }}
  .num {{ font-size: 32px; font-weight: 700; fill: {t['bright']}; }}
  .sub {{ font-size: 11px; fill: {t['dim']}; }}
  .pr {{ font-size: 9px; fill: {t['dim']}; }}
  .pr b {{ fill: {t['bright']}; font-weight: 700; }}
  .lbl {{ font-size: 10px; fill: {t['dim']}; }}
  {frame_css}
  .row {{ animation: row {LOOP_DUR:.1f}s linear infinite both; }}
  .a {{ opacity: 0; animation: slide .55s ease-out forwards; }}
  .grow {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow .9s ease-out forwards; }}
  .cur {{ fill: {t['fg']}; animation: blink 1s steps(1) infinite; }}
  {row_keyframes()}
  @keyframes slide {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  @keyframes blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .row {{ animation: none; opacity: 0; clip-path: none; }}
    .f-portrait .row {{ opacity: 1; }}
    .a {{ animation: none; opacity: 1; }}
    .grow {{ animation: none; transform: none; }}
    .cur {{ animation: none; }}
  }}
</style>""")
    add(f'<rect width="{W}" height="{H}" fill="{t["page"]}"/>')

    def window(x, title):
        add(f'<rect x="{x}" y="18" width="494" height="520" rx="8" fill="{t["panel"]}" stroke="{t["edge"]}"/>')
        add(f'<path d="M{x} 42 V26 a8 8 0 0 1 8 -8 H{x + 486} a8 8 0 0 1 8 8 V42 Z" fill="{t["bar"]}"/>')
        add(f'<line x1="{x}" y1="42" x2="{x + 494}" y2="42" stroke="{t["edge"]}"/>')
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
            add(f'<circle cx="{x + 14 + i * 14}" cy="30" r="3.6" fill="{c}"/>')
        add(f'<text class="ttl" x="{x + 247}" y="33" text-anchor="middle">{esc(title)}</text>')
        add(f'<line x1="{x}" y1="512" x2="{x + 494}" y2="512" stroke="{t["edge"]}"/>')

    window(30, f"{USER}@github: ~$ ./portrait.sh")
    window(556, f"{USER}@github: ~$ ./stats.sh")
    add(f'<text class="pr" x="42" y="529" xml:space="preserve">{USER}@github:~$ whoami  <tspan class="pr" font-weight="700" style="fill:{t["bright"]}">{esc(NAME)}</tspan></text>')
    add(f'<text class="pr" x="568" y="529" xml:space="preserve">{USER}@github:~$ </text>'
        f'<rect class="cur" x="{568 + 9 * 5.4 + len(USER) * 5.4 + 6 * 5.4 + 2:.0f}" y="521" width="5" height="9"/>')

    # ── portrait frames: every row types in at its own moment, in place ──
    X0, Y0 = 30 + (494 - 150 * CW) / 2, 50

    def frame(k, cls, rows, caption=None, tones=None):
        add(f'<g class="{cls}">')
        for i, row in enumerate(rows):
            if not row.strip():
                continue
            delay = k * SLOT + i * STAGGER
            body = tinted_row(row, tones[i]) if tones and i < len(tones) else esc(row)
            add(f'<text class="art row" x="{X0:.1f}" y="{Y0 + FS + i * CH:.1f}" textLength="{len(row) * CW:.1f}" '
                f'lengthAdjust="spacing" style="animation-delay:{delay:.2f}s" xml:space="preserve">{body}</text>')
        if caption:
            delay = k * SLOT + len(rows) * STAGGER
            add(f'<text class="lbl row" x="42" y="506" style="animation-delay:{delay:.2f}s">{esc(caption)}</text>')
        add('</g>')

    frame(0, "f-portrait", PORTRAIT, tones=TONE)
    for k, (fname, caption) in enumerate(FRAMES, start=1):
        rows = (HERE / "layers" / f"{fname}.txt").read_text(encoding="utf-8").splitlines()
        frame(k, f"f-{fname}", rows, caption)

    # ── stats cards ──
    cx = [568, 568 + 240.5]
    cw, chh, gap = 229.5, 92, 10
    d = 0.6
    for i, (label, value, sub) in enumerate(CARDS):
        x, y = cx[i % 2], 54 + (i // 2) * (chh + gap)
        add(f'<g class="a" style="animation-delay:{d + i * 0.12:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{cw}" height="{chh}" rx="6" fill="{t["card"]}" stroke="{t["cardedge"]}"/>'
            f'<text class="lab" x="{x + 14}" y="{y + 24}">$ {esc(label)}</text>'
            f'<text class="num" x="{x + 14}" y="{y + 60}"{" style=\"fill:" + t["green"] + "\"" if i == 2 else ""}>{esc(value)}</text>'
            f'<text class="sub" x="{x + 14}" y="{y + 80}">{esc(sub)}</text></g>')

    # languages card
    ly = 54 + 3 * (chh + gap)
    lw = 2 * cw + 10
    add(f'<g class="a" style="animation-delay:{d + 0.8:.2f}s">'
        f'<rect x="568" y="{ly}" width="{lw}" height="94" rx="6" fill="{t["card"]}" stroke="{t["cardedge"]}"/>'
        f'<text class="lab" x="582" y="{ly + 24}">$ languages</text></g>')
    bx, bw, by = 582, lw - 28, ly + 36
    xcur = bx
    for j, (lname, pct, key) in enumerate(LANGS):
        seg = bw * pct / 100
        add(f'<rect class="grow" x="{xcur:.1f}" y="{by}" width="{seg - 2:.1f}" height="10" rx="3" fill="{t[key]}" '
            f'style="animation-delay:{1.5 + j * 0.25:.2f}s"/>')
        xcur += seg
    lx = bx
    for j, (lname, pct, key) in enumerate(LANGS):
        add(f'<g class="a" style="animation-delay:{1.9 + j * 0.15:.2f}s"><circle cx="{lx + 4}" cy="{by + 30}" r="4" fill="{t[key]}"/>'
            f'<text class="sub" x="{lx + 14}" y="{by + 34}">{esc(lname)} {pct}%</text></g>')
        lx += 14 + (len(lname) + 5) * 6.6 + 18

    # info card
    iy = ly + 104
    add(f'<g class="a" style="animation-delay:{d + 1.0:.2f}s">'
        f'<rect x="568" y="{iy}" width="{lw}" height="44" rx="6" fill="{t["card"]}" stroke="{t["cardedge"]}"/>'
        f'<text class="sub" x="582" y="{iy + 26}" xml:space="preserve">location  <tspan style="fill:{t["bright"]}">{esc(LOCATION)}</tspan>   building  <tspan style="fill:{t["bright"]}">{esc(BUILDING)}</tspan></text></g>')
    add('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    for name in ("dark", "light"):
        svg = build(name)
        xml.dom.minidom.parseString(svg)       # fail loudly on malformed SVG
        (HERE / f"{name}_mode.svg").write_text(svg, encoding="utf-8")
        print(f"wrote {name}_mode.svg ({len(svg) / 1024:.1f} KB)")
