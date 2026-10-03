"""Measure the on-screen text in a reel frame: lines, line height, pitch, block bounds, safe-zone verdict.

Works on reels with white or near-white text. Frames are rescaled to 1080x1920 first, so numbers
are comparable across reels of any resolution. Bright screens and lamps can register as extra
lines; always confirm by looking at the frame.

CLI: python3 measure_text.py REEL.mp4 1.0 5.0     (seconds to sample)
     python3 measure_text.py FRAME.png              (a still)
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_zone import check  # noqa: E402


def frame(path, t=None, w=1080, h=1920):
    if path.lower().endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(path).convert("RGB").resize((w, h))
        return np.asarray(img).astype(int)
    tmp = os.path.join(tempfile.gettempdir(), "measure_text_frame.png")
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t or 0), "-i", path, "-vframes", "1", "-vf", vf, tmp], check=True)
    return np.asarray(Image.open(tmp).convert("RGB")).astype(int)


def lines(a):
    lo, hi = a.min(2), a.max(2)
    mask = (lo > 200) & ((hi - lo) < 40)
    transitions = np.abs(np.diff(mask.astype(int), axis=1)).sum(1)
    rows = transitions >= 10
    bands, start = [], None
    for y, on in enumerate(list(rows) + [False]):
        if on and start is None:
            start = y
        if not on and start is not None:
            if y - start >= 8:
                bands.append((start, y))
            start = None
    out = []
    for y0, y1 in bands:
        cols = np.where(np.abs(np.diff(mask[y0:y1].astype(int), axis=1)).sum(0) > 0)[0]
        if len(cols) >= 4:
            out.append({"y0": int(y0), "y1": int(y1), "h": int(y1 - y0), "x0": int(cols[0]), "x1": int(cols[-1])})
    return out


def report(a, label):
    found = lines(a)
    if not found:
        print(f"{label}: no text found")
        return
    box = {"x0": min(l["x0"] for l in found), "x1": max(l["x1"] for l in found), "y0": found[0]["y0"], "y1": found[-1]["y1"]}
    heights = sorted(l["h"] for l in found)
    pitch = float(np.median(np.diff([l["y0"] for l in found]))) if len(found) > 1 else 0
    centre = (box["y0"] + box["y1"]) / 2
    verdict = check(box) or ["inside the safe zone"]
    print(f"{label}: {len(found)} lines, line height median {heights[len(heights) // 2]}px, pitch {pitch:.0f}px, "
          f"block x {box['x0']} to {box['x1']}, y {box['y0']} to {box['y1']}, centre {centre / 1920:.2f} of height; "
          f"{'; '.join(verdict)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    times = [float(x) for x in sys.argv[2:]] or [None]
    for t in times:
        report(frame(src, t), f"t={t}s" if t is not None else os.path.basename(src))
