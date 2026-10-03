"""Break a text block into balanced lines: every line close to the same rendered width, so the block reads
as one even shape instead of a long line with a stub hanging under it.

Widths are measured with the real font file at the size Palmier renders it (fontSize x 1.78 px on a
1080x1920 reel). Only the line breaks are chosen here; the words are never changed.

  python3 balance_text.py "the user's text" --font HelveticaNeue-Bold --size 24
  python3 balance_text.py "first line" --font Futura-Medium --size 22 --match "a short second beat"

Paragraphs (separated by a blank line) are balanced separately. --lines forces a line count per
paragraph; otherwise the fewest lines that fit the safe width are used, and two lines when one line
would run past 80 percent of that width. --match prints the font size at which a second, separate
line (for example a reveal that appears later) is as wide as the widest line of the first block.
"""
import argparse
import glob
import itertools
import os

from PIL import ImageFont

PX_PER_POINT = 1920 / 1080
SAFE_WIDTH = 860  # px: Palmier wraps text boxes at about 80 percent of a 1080 canvas
FONT_DIRS = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts",
             os.path.expanduser("~/Library/Fonts")]
_cache = {}
# A line should not end on a word that leads into the next one.
WEAK_ENDS = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "from", "with", "by", "and", "or", "but", "my",
             "your", "his", "her", "their", "our", "its", "is", "was", "got", "get", "gets", "just", "who", "that",
             "than", "as", "into", "what", "when", "if", "so", "it's", "i", "i'm", "we", "we're", "you", "he", "she"}


def font_file(name):
    """Find (path, index) for a PostScript font name such as HelveticaNeue-CondensedBold."""
    if name in _cache:
        return _cache[name]
    want = name.replace("-", "").replace(" ", "").lower()
    for d in FONT_DIRS:
        for path in glob.glob(os.path.join(d, "*.tt[cf]")) + glob.glob(os.path.join(d, "*.otf")):
            for index in range(40):
                try:
                    f = ImageFont.truetype(path, 20, index=index)
                except OSError:
                    break
                family, style = f.getname()
                got = (family + style).replace(" ", "").lower()
                if got in (want, want + "regular") or (style == "Regular" and family.replace(" ", "").lower() == want):
                    _cache[name] = (path, index)
                    return _cache[name]
    raise SystemExit(f"font not found: {name}")


def width(text, name, size):
    path, index = font_file(name)
    return ImageFont.truetype(path, round(size * PX_PER_POINT), index=index).getlength(text)


def break_cost(line):
    """Penalty for ending a line here: inside a phrase costs, after punctuation is free."""
    last = line.split()[-1].lower()
    if last[-1] in ".,:;!?":
        return 0.0
    if last.strip("\"'") in WEAK_ENDS:
        return 0.35
    if last.lstrip("+$").replace(",", "").replace(".", "").isdigit():
        return 0.45  # a number split from what it counts
    return 0.08


def balance_paragraph(words, name, size, lines=None):
    """Best split of words into lines: no one-word line, every line inside the safe width, breaks between
    phrases, and widths as even as possible."""
    def splits(k):
        for cuts in itertools.combinations(range(1, len(words)), k - 1):
            edges = (0,) + cuts + (len(words),)
            yield [" ".join(words[a:b]) for a, b in zip(edges, edges[1:])]

    one = " ".join(words)
    if lines is None and width(one, name, size) <= 0.8 * SAFE_WIDTH:
        return [one]
    best = None
    for k in ([lines] if lines else range(2, min(5, len(words)) + 1)):
        for parts in splits(k):
            if k > 1 and any(len(p.split()) < 2 for p in parts):
                continue
            ws = [width(p, name, size) for p in parts]
            if max(ws) > SAFE_WIDTH:
                continue
            score = (max(ws) - min(ws)) / max(ws) + sum(break_cost(p) for p in parts[:-1])
            if best is None or score < best[0] - 1e-9:
                best = (score, parts, ws)
        if best and not lines:
            break
    if best is None:
        raise SystemExit(f"cannot fit within {SAFE_WIDTH}px at size {size}: {one!r}; lower the size")
    return best[1]


def balance(text, name, size, lines=None):
    paragraphs = [p.split() for p in text.replace("\r", "").split("\n\n")]
    return "\n\n".join("\n".join(balance_paragraph(p, name, size, lines)) for p in paragraphs if p)


def report(text, name, size):
    ws = [width(l, name, size) for l in text.split("\n") if l.strip()]
    return {"widths_px": [round(w) for w in ws], "evenness": round(min(ws) / max(ws), 2)}


def match_size(line, block, name, size, lo=0.8, hi=1.6):
    """Font size at which `line` is as wide as the widest line of `block` (clamped to lo..hi of size)."""
    target = max(width(l, name, size) for l in block.split("\n") if l.strip())
    k = target / width(line, name, size)
    return round(size * max(lo, min(hi, k)), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--font", required=True)
    ap.add_argument("--size", type=float, required=True, help="Palmier fontSize")
    ap.add_argument("--lines", type=int)
    ap.add_argument("--match")
    a = ap.parse_args()
    out = balance(a.text, a.font, a.size, a.lines)
    print(out)
    print(report(out, a.font, a.size))
    if a.match:
        print({"match_size": match_size(a.match, out, a.font, a.size)})


if __name__ == "__main__":
    main()
