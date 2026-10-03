"""Make a 512px rounded app-icon tile from a logo, for the "icon + icon" reels.

Use the brand's own logo file (its site's apple-touch-icon or favicon is usually the cleanest source).
If the logo is already a full square app icon, pass --full to just round its corners.

CLI: python3 make_icon_tile.py LOGO.png OUT.png --bg "#FFFFFF" --scale 0.7
     python3 make_icon_tile.py APP_ICON.png OUT.png --full
"""
import argparse

from PIL import Image, ImageDraw

SIZE = 512


def rounded_mask(size=SIZE, radius=0.225):
    big = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(big).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=int(size * radius * 4), fill=255)
    return big.resize((size, size), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logo")
    ap.add_argument("out")
    ap.add_argument("--bg", default="#FFFFFF")
    ap.add_argument("--scale", type=float, default=0.7, help="logo size as a fraction of the tile")
    ap.add_argument("--full", action="store_true", help="the input is already a square icon; only round it")
    a = ap.parse_args()
    logo = Image.open(a.logo)
    if getattr(logo, "info", {}).get("sizes"):
        logo.size = max(logo.info["sizes"])
    logo = logo.convert("RGBA")
    if a.full:
        tile = logo.resize((SIZE, SIZE), Image.LANCZOS)
    else:
        if logo.getbbox():
            logo = logo.crop(logo.getbbox())
        target = int(SIZE * a.scale)
        ratio = min(target / logo.width, target / logo.height)
        logo = logo.resize((max(1, int(logo.width * ratio)), max(1, int(logo.height * ratio))), Image.LANCZOS)
        tile = Image.new("RGBA", (SIZE, SIZE), a.bg)
        tile.alpha_composite(logo, ((SIZE - logo.width) // 2, (SIZE - logo.height) // 2))
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(tile, (0, 0), rounded_mask())
    out.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
