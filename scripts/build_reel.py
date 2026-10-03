"""Build reels as editable Palmier Pro projects from a spec file, and optionally export them.

  python3 build_reel.py specs.json --root OUTPUT_FOLDER               build every reel
  python3 build_reel.py specs.json --root OUTPUT_FOLDER --only reel01 build some
  python3 build_reel.py specs.json --root OUTPUT_FOLDER --export      export every built project to finals/

Paths in the spec (source, images) are relative to --root. See examples/reel-specs.example.json.
Palmier Pro must be open. Projects are created in Palmier's default folder, then closed, moved into
--root and reopened there so Palmier knows the new location.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palmier_mcp import call  # noqa: E402
from safe_zone import overlay  # noqa: E402

DEFAULT_SHADOW = {"enabled": True, "color": "#000000", "opacity": 0.9, "blur": 11, "offset": {"x": 0, "y": 2}}


def timeline():
    return call("get_timeline", {})


def camera_keyframes(move, amount, frames):
    """Scale and position keyframes for a full-canvas clip. Position is the clip's top-left corner, 0 to 1."""
    z = 1 + amount
    mid = -(z - 1) / 2
    last = frames - 1
    hold = [[0, z, z, "linear"], [last, z, z, "linear"]]
    if move == "pan-right":
        return hold, [[0, 0.0, mid, "linear"], [last, -(z - 1), mid, "linear"]]
    if move == "pan-left":
        return hold, [[0, -(z - 1), mid, "linear"], [last, 0.0, mid, "linear"]]
    if move == "drift-up":
        return hold, [[0, mid, -(z - 1), "linear"], [last, mid, 0.0, "linear"]]
    if move == "push-in":
        return [[0, 1.0, 1.0, "linear"], [last, z, z, "linear"]], [[0, 0.0, 0.0, "linear"], [last, mid, mid, "linear"]]
    if move == "pull-out":
        return [[0, z, z, "linear"], [last, 1.0, 1.0, "linear"]], [[0, mid, mid, "linear"], [last, 0.0, 0.0, "linear"]]
    return None, None


def capture(project_path, frame, name):
    before = set(glob.glob(f"{project_path}/media/frame-*.png"))
    call("capture_frame", {"timelineFrame": frame, "name": name})
    time.sleep(1)
    new = sorted(set(glob.glob(f"{project_path}/media/frame-*.png")) - before, key=os.path.getmtime)
    return new[-1] if new else None


def newest_track(before):
    ids = [t["trackId"] for t in timeline()["tracks"] if t["trackId"] not in before]
    return ids[0] if ids else None


def build(spec, root, checks_dir, overlay_png):
    from PIL import Image
    frames = spec["frames"]
    created = call("manage_project", {"action": "create", "name": spec["name"], "fps": spec.get("fps", 30), "aspectRatio": "9:16", "quality": "1080p"})
    path = created["path"]
    media = call("import_media", {"source": {"path": os.path.join(root, spec["source"])}, "folder": "Footage"})
    added = call("add_clips", {"entries": [{"mediaRef": media["mediaRef"], "startFrame": 0, "includeAudio": False}]})
    footage_id = added["clips"][0]["id"]
    call("set_project_settings", {"width": 1080, "height": 1920})

    cam = spec.get("camera") or {}
    scale_kf, pos_kf = camera_keyframes(cam.get("move", "none"), cam.get("amount", 0.08), frames)
    if scale_kf:
        call("set_keyframes", {"clipId": footage_id, "property": "scale", "keyframes": scale_kf})
        call("set_keyframes", {"clipId": footage_id, "property": "position", "keyframes": pos_kf})
    if spec.get("grade"):
        call("apply_color", dict(clipIds=[footage_id], **spec["grade"]))

    names = {}
    for i, text in enumerate(spec.get("texts", [])):
        before = {t["trackId"] for t in timeline()["tracks"]}
        style = dict(text.get("style", {}))
        style.setdefault("color", "#FFFFFF")
        style.setdefault("shadow", DEFAULT_SHADOW)
        call("add_texts", {"entries": [{"startFrame": text.get("start", 0), "endFrame": frames, "content": text["content"],
                                        "style": style, "transform": {"x": text.get("x", 0.5), "y": text["y"]}}]})
        names[newest_track(before)] = text.get("track", f"Text{i + 1}")
    for i, img in enumerate(spec.get("images", [])):
        before = {t["trackId"] for t in timeline()["tracks"]}
        m = call("import_media", {"source": {"path": os.path.join(root, img["file"])}, "folder": "Images"})
        a = call("add_clips", {"entries": [{"mediaRef": m["mediaRef"], "startFrame": 0, "endFrame": frames}]})
        w = img.get("w", img.get("size", 140))  # px on the 1080x1920 canvas; size alone means a square
        h = img.get("h", img.get("size", 140))
        call("set_clip_properties", {"clipIds": [a["clips"][0]["id"]], "transform": {
            "centerX": img["x"], "centerY": img["y"], "width": w / 1080, "height": h / 1920}})
        names[newest_track(before)] = img.get("track", f"Image{i + 1}")

    tl = timeline()
    footage_track = [t["trackId"] for t in tl["tracks"] if any(c["id"] == footage_id for c in t["clips"])][0]
    names[footage_track] = "Footage"
    call("manage_tracks", {"set": [{"trackId": k, "name": v} for k, v in names.items() if k]})
    videos = [t for t in tl["tracks"] if t["type"] == "video"]
    if videos[-1]["trackId"] != footage_track:
        call("manage_tracks", {"reorder": [{"trackId": footage_track, "to": len(videos) - 1}]})

    tl = timeline()
    report = {"reel": spec["id"], "totalFrames": tl["totalFrames"], "expected": frames, "canvas": f"{tl['width']}x{tl['height']}",
              "tracks": [t.get("name") for t in tl["tracks"]], "checks": []}
    ov = Image.open(overlay_png).convert("RGBA")
    for fr in spec.get("check_frames") or [frames // 2]:
        f = capture(path, fr, f"check-{fr}")
        if not f:
            continue
        im = Image.open(f).convert("RGBA")
        out_plain = os.path.join(checks_dir, f"{spec['id']}-f{fr}.png")
        out_safe = os.path.join(checks_dir, f"{spec['id']}-f{fr}-safe.png")
        im.convert("RGB").save(out_plain)
        Image.alpha_composite(im, ov.resize(im.size)).convert("RGB").save(out_safe)
        report["checks"] += [out_plain, out_safe]

    call("manage_project", {"action": "close", "path": path})
    dest = os.path.join(root, os.path.basename(path))
    if os.path.exists(dest):
        raise RuntimeError(f"{dest} already exists; rename the reel or move the old project first")
    shutil.move(path, dest)
    call("manage_project", {"action": "open", "path": dest})
    call("manage_project", {"action": "close", "path": dest})
    report["project"] = dest
    return report


def export(spec, root):
    projects = glob.glob(os.path.join(root, f"{spec['name']}.palmier"))
    if not projects:
        return {"reel": spec["id"], "error": "project not found; build it first"}
    project = projects[0]
    os.makedirs(os.path.join(root, "finals"), exist_ok=True)
    out = os.path.join(root, "finals", f"{spec['id']}-v1.mp4")
    if os.path.exists(out):
        return {"reel": spec["id"], "export": out, "status": "exists; delete or bump the version to re-export"}
    call("manage_project", {"action": "open", "path": project})
    job = call("export_project", {"mode": "video", "codec": "H.264", "resolution": "Match Timeline", "outputPath": out, "overwrite": False})
    status = None
    for _ in range(300):
        listing = call("manage_exports", {"action": "list"})
        jobs = listing.get("exports") or listing.get("jobs") or []
        match = [j for j in jobs if j.get("jobId") == job.get("jobId")]
        if match and match[0].get("status") in ("completed", "failed", "cancelled"):
            status = match[0]["status"]
            break
        time.sleep(2)
    call("manage_project", {"action": "close", "path": project})
    got = None
    if os.path.exists(out):
        got = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                           "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out]).decode().strip())
    return {"reel": spec["id"], "export": out, "status": status, "frames": got, "expected": spec["frames"],
            "ok": got == spec["frames"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs")
    ap.add_argument("--root", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    reels = json.load(open(a.specs))["reels"]
    checks = os.path.join(root, "checks")
    os.makedirs(checks, exist_ok=True)
    overlay_png = overlay(os.path.join(checks, "safe-zone-overlay.png"))
    for spec in reels:
        if a.only and spec["id"] not in a.only:
            continue
        try:
            result = export(spec, root) if a.export else build(spec, root, checks, overlay_png)
        except Exception as err:
            result = {"reel": spec["id"], "error": str(err)[:400]}
        print(json.dumps(result))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
