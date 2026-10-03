---
name: orgrowth-timelapse-generator
description: Use when someone wants short vertical reels made from their own timelapse or b-roll footage with text on screen; "turn my timelapses into reels", "put this text over my footage", "make reels from this folder", "make 10 variations of this reel", or /orgrowth-timelapse-generator. Watches the footage, picks the best moments, cuts them, and builds each reel as an editable Palmier Pro project with the user's own text, inside the Instagram safe zone, then exports. The user writes every word; this skill never writes or suggests copy.
---

# Timelapse reel generator

Turns a folder of timelapses or b-roll into short vertical reels: one shot of footage, the user's text on top, 8 to 10 seconds each. Every reel is delivered as a Palmier Pro project the user can still edit, plus an exported file.

**The user writes all of the text.** Never write, rewrite, suggest or improve copy. Lay out exactly what they give you, word for word. If a line is too long to fit, say so and ask them how they want to shorten it.

## Step 0: Ask before doing anything

Ask these in one message and wait for the answers:

1. **Footage:** the folder of clips to use.
2. **Text:** the exact text for each reel. For each one, ask which part is the main line and whether any line should appear partway through (for example, a last line that appears after 4 seconds).
3. **References:** "Do you have any reel links that show the look you want? Paste as many as you like." These set the layout (text size, position, number of lines, timing, camera movement), never the words.
4. **How many reels:** and whether each piece of text should become several variations.
5. **Images:** any logos or images to place on screen. They supply the files.
6. **Where to save:** an output folder. Default: `./timelapse-reels-YYYY-MM-DD/` with `source/`, `images/` and `finals/` inside it.

## Step 1: Set up Palmier Pro

The reels are built in Palmier Pro, a free video editor.

1. Check it is installed: `ls /Applications | grep -i palmier`. If not, tell the user to download it from https://www.palmier.io, install it, and open it.
2. Check it is running and reachable: `python3 scripts/palmier_mcp.py list` should print tool names such as `get_timeline`. If it fails, ask the user to open Palmier Pro and try again.
3. Check the other tools: `ffmpeg -version`, `yt-dlp --version`, and `python3 -c "import numpy, PIL"`. Tell the user the exact install command for anything missing (`brew install ffmpeg yt-dlp`, `pip3 install numpy pillow`).

`scripts/palmier_mcp.py` talks to Palmier over its local port directly, so this works whether or not Palmier is connected as an MCP server in the session. Read `references/palmier-traps.md` before the first Palmier call.

## Step 2: Study the references (if any)

Download each link:

```bash
yt-dlp --no-playlist --write-info-json -o "references/%(id)s.%(ext)s" <link>
```

Public reels usually download without a login. If one does not, ask the user to download it themselves or try `--cookies-from-browser chrome`.

For each reference, look at it before measuring anything:

- Pull 8 evenly spaced frames into a strip and view them all.
- Run `python3 scripts/measure_text.py REFERENCE.mp4 1.0 5.0` for the number of lines, line height, block position and a safe-zone check. Bright lamps and screens can register as extra lines, so confirm by eye.
- Note: does the text change during the reel? Does the camera move, and which way? How long is it? What colour and weight is the text, and does it have an outline, shadow or background?

Write a short layout summary for the user (sizes, positions, timing, movement) and ask them to confirm the look before building. Do not comment on the wording of the references.

## Step 3: Watch the footage and pick moments

```bash
python3 scripts/pick_window.py "/path/to/footage" --seconds 8.5 --out picks
```

This finds the steadiest stretch of each clip and writes a 10-frame strip per clip. Look at every strip. Then propose a pairing for each reel: which clip, which start time, and why (for example, "the text sits over the dark wall, so it stays readable"). Show the user the strips and the pairings and let them swap any before you cut.

Rules of thumb when pairing:

- Text needs a calm, even area behind it. Avoid bright windows and screens directly under the words.
- Pick stretches with steady motion and no one walking across the lens.
- Each reel gets its own clip or its own stretch of a clip.

## Step 4: Cut the sources

```bash
python3 scripts/cut_source.py CLIP.MP4 START_SECONDS FRAMES source/reel01.mp4
```

Defaults: 1296x2304 (1.2x the 1080x1920 canvas, so camera moves never upscale), 30fps, no audio, an exact frame count. 255 frames is 8.5 seconds.

## Step 5: Build each reel in Palmier

Describe every reel in a spec file; `examples/reel-specs.example.json` shows every field. Each text block, image and the footage gets its own named track, so the user can move or retype any of them later.

```bash
python3 scripts/build_reel.py specs.json --root OUTPUT_FOLDER
python3 scripts/build_reel.py specs.json --root OUTPUT_FOLDER --only reel01   # one at a time while dialling in a look
```

For each reel it creates the project, imports the source, locks the canvas to 1080x1920, adds the camera movement as keyframes, applies an optional light grade, adds each text block and image, captures check frames, then saves the project into the output folder.

Build one reel first, show the user the check frame, and adjust size, font and position with them before building the rest.

### Design rule: balanced, symmetrical blocks

Every centred text block should read as one even shape that feels complete: lines of near equal width, never a long line with a short stub hanging under it. A two-line block is the default for a sentence too long for one line, and both lines should be about the same width.

- **Choose the line breaks by measured width, not by character count.** Run `python3 scripts/balance_text.py "THE USER'S TEXT" --font FONT --size SIZE` for every multi-line block. It measures each line with the real font file and picks the breaks where the widths are most even. Aim for an evenness of 0.85 or better (shortest line divided by longest); below 0.8 looks lopsided.
- **Break between phrases, never inside one.** Never end a line on "a", "the", "of", "in", "your" and similar, and never split a number from the word it counts ("1,200 / subscribers"). The script penalises both.
- **One line is complete on its own.** If a sentence fits on one line inside the safe width, keep it on one line rather than splitting it into uneven halves.
- **A short second beat is sized to match.** When a short line appears after a longer one (a reveal, a punchline, a result), size it up so its width matches the line above: `--match "THE SHORT LINE"` prints that size. Cap it at about 1.6 times the hook size.
- **Paragraphs balance separately.** In a two-paragraph card, balance each paragraph on its own.
- **Only the line breaks and sizes change.** The words stay exactly as the user wrote them. If no break balances well, show the user the best two options and let them choose; never reword to make it fit.
- Lists and left-aligned diary-style text are ragged by nature; this rule is for centred hooks, headers, closers and reveals.

Images: turn a logo into a rounded square tile with `python3 scripts/make_icon_tile.py LOGO.png images/logo.png --bg "#FFFFFF" --scale 0.7` (or `--full` if it is already a square icon).

## Step 6: Check every reel

- **Read every check frame.** The text must be readable over the brightest part of the shot. If not, strengthen the shadow, add a thin outline, or move the text.
- **Safe zone.** On a 1080x1920 frame, keep text inside x 63 to 1014 and y 267 to 1535, and left of x 851 below y 1151 (Instagram's like, comment and share buttons), with a 16px margin. `python3 scripts/safe_zone.py overlay overlay.png` draws the unsafe area; lay it over a check frame to see it.
- **No single word alone on a line.** If a line wraps and leaves one word on its own, ask the user where to break it.
- **Balanced blocks.** Look at every centred block on the check frame: the lines should be close to the same width. If one looks lopsided, rerun `balance_text.py` and rebuild that reel.
- **Camera moves.** `python3 scripts/check_edges.py PROJECT.palmier` checks the first and last frames for exposed canvas.

## Step 7: Export

```bash
python3 scripts/build_reel.py specs.json --root OUTPUT_FOLDER --export
```

Writes `finals/<reel>-v1.mp4` for every project (H.264, silent) and checks each file's frame count. Tell the user to add music or sound in the app they post from. If they later change a project in Palmier, export it again as `v2`.

## Making several variations of one reel

If the user wants several versions of the same text (for example, to test them as separate posts), make every version differ from the others in each of these:

- length (8.0 to 10.5 seconds)
- camera movement and amount: pan left, pan right, push in, pull out, drift up, 5 to 14 percent
- font, text size and text position
- a light grade (exposure, contrast, colour temperature)
- the clip or stretch of footage

Same words, different everything else. The words stay exactly as the user wrote them.
