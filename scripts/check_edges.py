"""Check a built reel's first and last frames for exposed canvas (a camera move that went too far).

Empty canvas is pure black with no noise along an edge. Very dark footage can also be pure black,
so a flag means "look at this frame", not "this is broken".

CLI: python3 check_edges.py PROJECT.palmier
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palmier_mcp import call  # noqa: E402


def capture(project, frame):
    before = set(os.listdir(os.path.join(project, "media")))
    call("capture_frame", {"timelineFrame": frame, "name": f"edge-{frame}"})
    time.sleep(1)
    new = [f for f in os.listdir(os.path.join(project, "media")) if f not in before and f.startswith("frame-")]
    return os.path.join(project, "media", sorted(new)[-1]) if new else None


def edge_black(png):
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    bands = {"left": a[:, :3], "right": a[:, -3:], "top": a[:3, :], "bottom": a[-3:, :]}
    return {k: round(float((v.max(axis=2) == 0).mean()), 3) for k, v in bands.items()}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    project = os.path.abspath(sys.argv[1])
    call("manage_project", {"action": "open", "path": project})
    total = call("get_timeline", {})["totalFrames"]
    result = {}
    for label, frame in (("first", 0), ("last", total - 1)):
        png = capture(project, frame)
        result[label] = edge_black(png) if png else "capture failed"
    call("manage_project", {"action": "close", "path": project})
    flagged = any(isinstance(v, dict) and max(v.values()) > 0.5 for v in result.values())
    print(json.dumps({"project": os.path.basename(project), "edges": result,
                      "verdict": "look at the first and last frames" if flagged else "no exposed canvas"}))


if __name__ == "__main__":
    main()
