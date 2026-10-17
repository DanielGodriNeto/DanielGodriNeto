"""One-off generator: terminal-style thumbnails for the README's Selected work cards (assets/work/*.png).
The other two cards use real screenshots (cs2 dashboard demo, Godri-Culling terrain).

Needs Pillow. Swap any PNG for a real screenshot at the same name when you have one.
Usage: python make_work_thumbs.py assets/work
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

BOLD, REG = r"C:\Windows\Fonts\consolab.ttf", r"C:\Windows\Fonts\consola.ttf"
W, H = 800, 400
WORK = [
    ("local-ai-agent", "push-to-talk voice agent", ["Python", "Whisper", "ONNX"], (61, 220, 151)),
    ("Asteroids-Scratch", "arcade + roguelite build mode", ["Scratch 3", "game design"], (240, 120, 120)),
]


def thumb(name, line, chips, accent, out):
    img = Image.new("RGB", (W, H), (15, 20, 25))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 44], fill=(22, 29, 36))
    for i, c in enumerate([(240, 120, 120), (224, 164, 88), (61, 220, 151)]):
        d.ellipse([20 + i * 26, 15, 34 + i * 26, 29], fill=c)
    d.text((W - 24, 14), "~/work", font=ImageFont.truetype(REG, 16), fill=(125, 138, 150), anchor="ra")
    d.text((48, 110), "$ cat README", font=ImageFont.truetype(REG, 22), fill=(125, 138, 150))
    size = 52 if len(name) < 18 else 44
    d.text((48, 160), name, font=ImageFont.truetype(BOLD, size), fill=accent)
    d.text((48, 235), line, font=ImageFont.truetype(REG, 26), fill=(232, 238, 242))
    x, f = 48, ImageFont.truetype(REG, 20)
    for c in chips:
        w = d.textlength(c, font=f) + 28
        d.rounded_rectangle([x, 310, x + w, 346], radius=6, outline=(43, 54, 64), width=2)
        d.text((x + 14, 318), c, font=f, fill=(127, 182, 212))
        x += w + 12
    img.save(out, optimize=True)


if __name__ == "__main__":
    for name, line, chips, accent in WORK:
        thumb(name, line, chips, accent, os.path.join(sys.argv[1], name + ".png"))
