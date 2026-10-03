"""Score every clip in a footage folder for its steadiest window of N seconds and write a frame strip per clip.

The score favours steady, continuous motion (a person working) and penalises spikes (cuts, glitches,
someone walking through the lens). Always look at the strips before choosing.

CLI: python3 pick_window.py "/path/to/timelapses" --seconds 8.5 --out picks
"""
import argparse
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw

VIDEO = (".mp4", ".mov", ".m4v")


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def score(path, seconds):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=2,scale=54:96,format=gray", "-f", "rawvideo", "-"])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 96, 54).astype(float)
    if len(frames) < 3:
        return None
    diff = np.abs(np.diff(frames, axis=0)).mean((1, 2))
    width = int(seconds * 2)
    best = None
    for start in range(0, max(1, len(diff) - width + 1)):
        seg = diff[start:start + width]
        s = seg.mean() - 2 * max(0, seg.max() - 3 * np.median(diff))
        if best is None or s > best[0]:
            best = (s, start / 2)
    return {"start": best[1], "motion": float(diff.mean()), "brightness": float(frames.mean())}


def strip(path, out_png, label):
    d = duration(path)
    tiles = []
    for k in range(10):
        t = d * (k + 0.5) / 10
        tmp = out_png + f".{k}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", path, "-vframes", "1", "-vf", "scale=-2:256", tmp], check=True)
        img = Image.open(tmp).convert("RGB")
        ImageDraw.Draw(img).text((4, 4), f"{t:.1f}s", fill="yellow")
        tiles.append(img)
        os.remove(tmp)
    sheet = Image.new("RGB", (sum(i.width for i in tiles), 256 + 20), "#111")
    x = 0
    for img in tiles:
        sheet.paste(img, (x, 20))
        x += img.width
    ImageDraw.Draw(sheet).text((4, 2), label, fill="white")
    sheet.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--seconds", type=float, default=8.5)
    ap.add_argument("--out", default="picks")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for name in sorted(os.listdir(args.folder)):
        if not name.lower().endswith(VIDEO):
            continue
        path = os.path.join(args.folder, name)
        d = duration(path)
        if d < args.seconds:
            print(f"{name}: {d:.1f}s, shorter than {args.seconds}s, skipped")
            continue
        s = score(path, args.seconds)
        if not s:
            continue
        label = f"{name}  {d:.1f}s  best window starts {s['start']:.1f}s  brightness {s['brightness']:.0f}"
        strip(path, os.path.join(args.out, os.path.splitext(name)[0] + "-strip.png"), label)
        print(label)


if __name__ == "__main__":
    main()
