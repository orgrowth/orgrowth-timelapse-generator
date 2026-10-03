"""Cut one exact-length source clip for a reel: fixed frame count, constant fps, no audio.

Cut at 1.2x the canvas (1296x2304 for a 1080x1920 reel) so camera moves never upscale.
Every frame of the source is kept (it is retimed to the target fps rather than dropped or duplicated),
which for 29.97fps footage at 30fps is a 0.1 percent speed change nobody will see.

CLI: python3 cut_source.py SRC.MP4 START_SECONDS FRAMES OUT.mp4 [--width 1296 --height 2304 --fps 30]
"""
import argparse
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("start", type=float)
    ap.add_argument("frames", type=int)
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1296)
    ap.add_argument("--height", type=int, default=2304)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    vf = f"setpts=N/({a.fps}*TB),scale={a.width}:{a.height}:flags=lanczos,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", a.src, "-an", "-vf", vf, "-r", str(a.fps),
                    "-frames:v", str(a.frames), "-c:v", "libx264", "-preset", "slow", "-crf", "13", "-movflags", "+faststart", a.out], check=True)
    got = subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                   "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", a.out]).decode().strip()
    if int(got) != a.frames:
        sys.exit(f"{a.out}: got {got} frames, wanted {a.frames}. The source likely ends before start + length; pick an earlier start or fewer frames.")
    print(f"{a.out}: {got} frames at {a.width}x{a.height}, {a.fps}fps")


if __name__ == "__main__":
    main()
