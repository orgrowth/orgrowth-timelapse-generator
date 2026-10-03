# Timelapse reel generator

A skill that turns a folder of your own timelapses or b-roll into short vertical reels with your text on screen. It watches the footage, picks the best moments, cuts them, and builds every reel as an editable [Palmier Pro](https://www.palmier.io) project, kept inside the Instagram safe zone, then exports.

You write every word. The skill asks for your text and any reference reels you like the look of, then handles the editing.

## What it does

1. Asks for your footage folder, your text, any reference reel links, how many reels, and where to save.
2. Studies the references for layout only: text size, position, line count, timing, camera movement.
3. Watches your footage and proposes which clip and moment goes with each piece of text.
4. Cuts each moment to an exact length.
5. Builds each reel in Palmier Pro with every text block, image and the footage on its own track, plus a subtle camera move.
6. Checks legibility, the safe zone and the camera moves on real frames.
7. Exports finished files to `finals/`.

It can also make several versions of the same text that differ in length, camera move, font, size, position, grade and footage, for posting as separate tests.

## Requirements

- macOS with [Palmier Pro](https://www.palmier.io) installed and open (free)
- `ffmpeg` and `yt-dlp`: `brew install ffmpeg yt-dlp`
- Python 3 with numpy and Pillow: `pip3 install numpy pillow`

## Install

```bash
git clone https://github.com/orgrowth/orgrowth-timelapse-generator ~/.claude/skills/orgrowth-timelapse-generator
```

Then start a new Claude Code session and say "turn my timelapses into reels", or type `/orgrowth-timelapse-generator`.

## What is in here

| Path | What it is |
| :- | :- |
| `SKILL.md` | The step-by-step workflow the skill follows |
| `scripts/palmier_mcp.py` | Talks to Palmier Pro on its local port |
| `scripts/pick_window.py` | Scores each clip for its steadiest stretch and writes frame strips |
| `scripts/cut_source.py` | Cuts an exact-length, silent source clip |
| `scripts/build_reel.py` | Builds and exports Palmier projects from a spec file |
| `scripts/measure_text.py` | Measures text size and position on reference or rendered frames |
| `scripts/safe_zone.py` | Instagram safe zone numbers and overlay |
| `scripts/check_edges.py` | Checks camera moves never expose empty canvas |
| `scripts/make_icon_tile.py` | Turns a logo into a rounded square tile |
| `references/palmier-traps.md` | Palmier behaviours that fail quietly |
| `examples/reel-specs.example.json` | Every spec field, with placeholder text |

## Licence

MIT
