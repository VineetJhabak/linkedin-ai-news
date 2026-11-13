"""
generate_image.py — Draws one headline card (PNG) for the LinkedIn post.

Uses Pillow only: no API keys, no downloads, nothing that can go offline.
(LinkedIn does not accept SVG uploads, so the card is rendered as PNG.)
If drawing fails for any reason the post simply goes out as text only.
"""

import json
from datetime import datetime

W, H = 1200, 628
FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/dejavu/",
]


def font(size, bold=False):
    from PIL import ImageFont

    names = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    for d in FONT_DIRS:
        for n in names:
            try:
                return ImageFont.truetype(d + n, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def ascii_safe(text):
    """Fonts on the build machine cannot draw emoji, so keep basic characters only."""
    return "".join(c if 31 < ord(c) < 0x2500 else " " for c in text).strip()


def shorten(draw, text, fnt, max_width):
    if draw.textlength(text, font=fnt) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=fnt) > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def make_card(articles, fname="image_1.png"):
    from PIL import Image, ImageDraw

    top, bottom = (15, 12, 41), (48, 43, 99)
    accent, accent2 = (124, 58, 237), (167, 139, 250)

    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    d.rectangle([0, 0, W, 6], fill=accent)

    d.rounded_rectangle([60, 44, 210, 82], radius=19, fill=accent)
    d.text((135, 63), "AI NEWS", font=font(17, True), fill="white", anchor="mm")
    d.text((60, 100), "Top AI Stories", font=font(54, True), fill="white")
    d.text((60, 164), "From Around The World", font=font(54, True), fill=accent2)
    d.text((60, 236), datetime.now().strftime("%B %d, %Y"), font=font(21), fill=(170, 170, 200))

    y = 282
    title_font, meta_font, num_font = font(21), font(17), font(22, True)
    for i, a in enumerate(articles[:5], 1):
        d.rounded_rectangle([60, y, W - 60, y + 52], radius=8, fill=(40, 36, 84))
        d.text((80, y + 26), f"#{i}", font=num_font, fill=accent2, anchor="lm")
        country = ascii_safe(a.get("country_name", "Global"))
        d.text((128, y + 26), country, font=meta_font, fill=(160, 160, 195), anchor="lm")
        x = 128 + d.textlength(country, font=meta_font) + 16
        title = shorten(d, ascii_safe(a["title"]), title_font, W - 80 - x)
        d.text((x, y + 26), title, font=title_font, fill=(235, 235, 245), anchor="lm")
        y += 60

    d.text((60, 598), "#ArtificialIntelligence  #AINews  #MachineLearning  #Innovation", font=font(16), fill=(130, 130, 170), anchor="lm")
    img.save(fname, "PNG", optimize=True)
    return fname


if __name__ == "__main__":
    with open("news.json", encoding="utf-8") as f:
        articles = json.load(f)

    images = []
    try:
        images.append(make_card(articles))
        print(f"✅ Image ready: {images[0]}")
    except Exception as e:
        print(f"⚠️ Could not draw the image ({e}) — the post will be text only")

    with open("images.json", "w") as f:
        json.dump({"images": images, "generated_at": datetime.now().isoformat()}, f)
