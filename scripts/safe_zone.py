"""Instagram Reels safe zone on a 1080x1920 canvas.

Clear area: x 63 to 1014, y 267 to 1535. Below y 1151 the right edge is x 851
(the like, comment and share column). Keep text a further 16px inside.

CLI: python3 safe_zone.py overlay OUT.png   draws a 50% purple overlay of the unsafe area
"""
import sys

W, H = 1080, 1920
LEFT, RIGHT, TOP, BOTTOM = 63, 1014, 267, 1535
LOW_Y, LOW_RIGHT = 1151, 851
MARGIN = 16


def check(box):
    """box: dict with x0, x1, y0, y1 in 1080x1920 pixels. Returns a list of problems, empty when safe."""
    problems = []
    if box["x0"] < LEFT + MARGIN or box["x1"] > RIGHT - MARGIN:
        problems.append("outside the left or right edge")
    if box["y0"] < TOP + MARGIN:
        problems.append("above the top edge")
    if box["y1"] > BOTTOM - MARGIN:
        problems.append("below the bottom edge")
    if box["y1"] > LOW_Y and box["x1"] > LOW_RIGHT - MARGIN:
        problems.append("under the like, comment and share buttons")
    return problems


def overlay(path):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    unsafe = (128, 64, 200, 128)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, TOP], fill=unsafe)
    draw.rectangle([0, BOTTOM, W, H], fill=unsafe)
    draw.rectangle([0, TOP, LEFT, BOTTOM], fill=unsafe)
    draw.rectangle([RIGHT, TOP, W, LOW_Y], fill=unsafe)
    draw.rectangle([LOW_RIGHT, LOW_Y, W, BOTTOM], fill=unsafe)
    img.save(path)
    return path


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "overlay":
        print(overlay(sys.argv[2]))
    else:
        sys.exit(__doc__)
