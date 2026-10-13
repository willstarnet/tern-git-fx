"""git blame: a magnifying glass over a page of code.

loop: the glass sweeps around the page, magnifying the lines under it.
success: it settles on one line, which lights up yellow; an exclamation pops up and a check.
fail: it hunts left and right, comes to rest over blank paper, a question mark pops up; cross.
"""

from __future__ import annotations

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim

PAGE = (4, 4, 19, 27)  # x0, y0, x1, y1
FOLD = 4
# Code lines: (y, x, [(length, color), ...]).
LINES = [
    (8, 6, [(3, "P"), (5, "B")]),
    (11, 8, [(4, "B"), (3, "o")]),
    (14, 8, [(2, "P"), (6, "e")]),
    (17, 10, [(3, "B"), (4, "E")]),
    (20, 6, [(4, "o")]),
    (23, 6, [(2, "P")]),
]
CULPRIT = 2  # the line blame lands on

BANG = [
    "yy",
    "yy",
    "yy",
    "yy",
    "..",
    "yy",
]
QUESTION = [
    ".cccc.",
    "cc..cc",
    "....cc",
    "...cc.",
    "..cc..",
    "......",
    "..cc..",
]


def page(highlight: bool = False) -> Frame:
    x0, y0, x1, y1 = PAGE
    f = Frame()
    f.rect(x0, y0, x1, y1, "w")
    # dog-eared corner
    for i in range(FOLD):
        for j in range(FOLD - i):
            f.erase(x1 - i, y0 + j)
    for i in range(FOLD):
        f.line(x1 - FOLD + 1, y0 + i, x1 - FOLD + 1 + i, y0 + i, "g")
    for n, (y, x, tokens) in enumerate(LINES):
        if highlight and n == CULPRIT:
            f.rect(x0 + 1, y - 1, x1 - 1, y + 1, "y")
        for length, c in tokens:
            f.rect(x, y, x + length - 1, y, c)
            x += length + 1
    return f


def glass(f: Frame, under: Frame, cx: int, cy: int, sag: int = 0) -> None:
    """Lens at (cx, cy) showing `under` at 2x; the handle points down-right (sag tips it down)."""
    r = 5
    # handle first so the ring sits over its end
    hx, hy = cx + 4, cy + 4
    ex, ey = hx + 4 - sag, hy + 4
    f.line(hx, hy, ex, ey, "n")
    f.line(hx + 1, hy, ex + 1, ey, "n")
    f.line(hx, hy + 1, ex, ey + 1, "N")
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 > (r + 0.5) ** 2:
                continue
            if d2 > (r - 0.5) ** 2:
                f.put(x, y, "o")
                continue
            c = under.get(cx + (x - cx) // 2, cy + (y - cy) // 2)
            f.put(x, y, "c" if c in (".", "w", "g") else c)
    # glint
    f.put(cx - 2, cy - 3, "w")
    f.put(cx - 3, cy - 2, "w")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def scene(cx: int, cy: int, highlight: bool = False, sag: int = 0) -> Frame:
    under = page(highlight)
    f = under.copy()
    glass(f, under, cx, cy, sag)
    return f


SWEEP = [(8, 9), (12, 8), (16, 10), (17, 14), (15, 18), (11, 19), (8, 17), (7, 13)]


def loop() -> Anim:
    return anim([finish(scene(x, y)) for x, y in SWEEP], 130)


def success() -> Anim:
    frames, durations = [], []
    y = LINES[CULPRIT][0]
    # sweep in, slow down, stop on the culprit line
    for x, yy, d in ((8, 9, 90), (12, 11, 90), (14, y, 110), (13, y, 160)):
        frames.append(finish(scene(x, yy)))
        durations.append(d)
    # it lights up, exclamation
    for i in range(2):
        f = scene(13, y, highlight=True)
        if i:
            f.sprite(BANG, 22, y - 3)
        frames.append(finish(f))
        durations.append(120)
    for step in range(3):
        f = scene(13, y, highlight=True)
        f.sprite(BANG, 22, y - 2)
        sparkle(f, 2, 10, step)
        sparkle(f, 25, y + 8, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    # hunting back and forth, faster
    for x, y, d in ((8, 11, 120), (16, 11, 110), (8, 17, 100), (16, 17, 90), (13, 21, 160)):
        frames.append(finish(scene(x, y)))
        durations.append(d)
    # over blank paper: nothing; a question mark, the glass sags
    for i in range(2):
        f = scene(15, 21, sag=i)
        f.sprite(QUESTION, 23, 13 - i)
        frames.append(finish(f))
        durations.append(150)
    for step in range(3):
        f = scene(15, 21, sag=2)
        f.sprite(QUESTION, 23, 13)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(120 if step < 2 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
