"""One-off generator: shrinks the hand-made K2 ASCII art into a dark-theme version.

Reads the original (black ink on white, dense = dark), rebuilds its tone map, replaces the sky
and clouds with a quiet starfield, inverts it for a dark background (dense = bright snow) and
writes k2-ascii.txt and k2-ascii.png (the card embeds the PNG). Needs Pillow + numpy; the nightly card
only reads the PNG.
Usage: python make_k2_ascii.py montanha2_ascii.txt k2-ascii.txt k2-ascii.png
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

COLS, ROWS = 260, 195
FONT, SIZE = r"C:\Windows\Fonts\consolab.ttf", 10
# Sky outline (x, y) on a 1040x1560 view of the source: everything above this line is replaced.
SKY = [(1040, 0), (1040, 680), (940, 560), (820, 455), (700, 392), (600, 330), (530, 225), (515, 170),
       (440, 80), (395, 22), (370, 40), (330, 110), (290, 160), (220, 250), (130, 370), (60, 470),
       (0, 560), (0, 0)]


def load_tone(path):
    """Ink darkness (0 light .. 1 dark) of each character of the source, as a rows x cols grid."""
    from PIL import ImageFont
    font = ImageFont.truetype(FONT, SIZE)
    lines = open(path, encoding="utf-8").read().split(chr(10))
    width = max(map(len, lines))
    lines = [l.ljust(width) for l in lines]
    cw = round(font.getlength("M"))
    ink = {}
    for c in set("".join(lines)):
        im = Image.new("L", (cw, SIZE), 255)
        ImageDraw.Draw(im).text((0, 0), c, font=font, fill=0)
        ink[c] = 255 - np.asarray(im).mean()
    a = np.array([[ink[c] for c in l] for l in lines])
    return (a - a.min()) / (a.max() - a.min())


def density_ramp(levels=18):
    from PIL import ImageFont
    font = ImageFont.truetype(FONT, SIZE)
    cw = round(font.getlength("M"))
    chars = [chr(c) for c in range(32, 127)]

    def ink(c):
        im = Image.new("L", (cw, SIZE), 255)
        ImageDraw.Draw(im).text((0, 0), c, font=font, fill=0)
        return 255 - np.asarray(im).mean()

    dens = {c: ink(c) for c in chars}
    ordered = sorted(chars, key=lambda c: dens[c])
    ramp = [ordered[i] for i in np.linspace(0, len(ordered) - 1, levels).astype(int)]
    d = np.array([dens[c] for c in ramp])
    return ramp, (d - d.min()) / (d.max() - d.min())


def shrink(grid):
    img = Image.fromarray((grid * 255).astype(np.uint8))
    return np.asarray(img.resize((COLS, ROWS), Image.BOX), dtype=np.float32) / 255.0


def sky_mask(h, w):
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).polygon([(x * w / 1040, y * h / 1560) for x, y in SKY], fill=255)
    return shrink(np.asarray(img, dtype=np.float32) / 255.0) > 0.5


def to_ascii(tone):
    ramp, d = density_ramp()
    bright = 1 - shrink(tone)                                     # snow = bright = dense character
    lo, hi = np.percentile(bright, 4), np.percentile(bright, 97)
    g = np.clip((bright - lo) / (hi - lo), 0, 1)
    g = (1 / (1 + np.exp(-6 * (g - 0.5)))) ** 1.15                # S-curve, as in img2ascii.py
    idx = np.abs(g[..., None] - d[None, None, :]).argmin(-1)
    sky = sky_mask(*tone.shape)
    rng = np.random.default_rng(3)
    rows = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            if sky[r, c]:
                row.append("." if rng.random() < 0.012 else " ")
            else:
                row.append(ramp[idx[r, c]])
        rows.append("".join(row).rstrip())
    return chr(10).join(rows) + chr(10)


def to_png(art, out):
    """Draw the text on a dark background, denser characters in lighter shades."""
    from PIL import ImageFont
    font = ImageFont.truetype(FONT, SIZE)
    cw = round(font.getlength("M"))
    ramp, d = density_ramp()
    tones = [(58, 74, 88), (93, 116, 136), (159, 180, 195), (232, 238, 242)]
    shade = {c: tones[min(int(v * 4), 3)] for c, v in zip(ramp, d)}
    img = Image.new("RGB", (COLS * cw, ROWS * SIZE), (15, 20, 25))
    dr = ImageDraw.Draw(img)
    for y, line in enumerate(art.split(chr(10))[:ROWS]):
        for x, ch in enumerate(line):
            if ch != " ":
                dr.text((x * cw, y * SIZE), ch, font=font, fill=shade.get(ch, tones[0]))
    img.save(out, optimize=True)


if __name__ == "__main__":
    art = to_ascii(load_tone(sys.argv[1]))
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
        f.write(art)
    to_png(art, sys.argv[3])
