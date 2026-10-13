"""git stash: a squirrel burying an acorn.

loop: the squirrel digs at a hole, paws scrabbling, dirt flicking onto a pile, tail bobbing.
success: it holds the acorn up, drops it in the hole, pats the dirt down and sits up proud; check.
fail: the acorn slips from its paws and bounces away out of frame; the squirrel stares after it; cross.
"""

from __future__ import annotations

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim

# Unoutlined fur; Frame.outline() adds the ink. The tail is drawn over the body with its own ink
# seam (except at the base, rows >= TAIL_BASE, where it grows out of the rump).
TAIL = [
    "..ooooo..",
    ".ooooooo.",
    "oootttooo",
    "oot...ooo",
    "ot...oooo",
    "....ooooo",
    "...ooooo.",
    "...oooo..",
    "..ooooo..",
    "..oooo...",
    "..oooo...",
    "..oooo...",
    "..ooooo..",
    "...ooooo.",
    "...oooooo",
]
TAIL_BASE = 12

# Sitting up, facing right; feet on the last row.
SIT = [
    "..........o......",
    ".........ooo.....",
    "........oooooo...",
    ".......oooookoo..",
    ".......oooooooon.",
    ".......ootttttt..",
    "........otttt....",
    ".......ootttt....",
    "......ooootooo...",
    "oooo.ooooottt....",
    "oooooooooootttt..",
    ".oooooooootttt...",
    "..oooooooottttt..",
    "...ooooooootttt..",
    "...oooooooooooo..",
    "...nnnnnnn.nnnn..",
]
SIT_TAIL = (-3, -4)  # tail origin relative to the SIT origin

# SIT with the head hung low, eye shut and arms dropped.
SLUMP = [
    ".................",
    "..........o......",
    ".........ooo.....",
    "........oooooo...",
    ".......ooookkoo..",
    ".......oooooooo..",
    ".......ootttttn..",
    "........otttt....",
    "......oooottt....",
] + SIT[9:]

# Hunched over the hole, facing right; front paws are drawn separately.
HUNCH = [
    "..oooo..............",
    ".ooooooo............",
    "oooooooooo..........",
    "ooooooooooo...o.....",
    "oooooooooooo.ooo....",
    ".oooooooooooooooo...",
    ".ooooooooooooookoo..",
    "..ooooooootttoooooon",
    "...ooooo.....ttttt..",
    "...nnnnn............",
]
HUNCH_TAIL = (-2, -9)

ACORN = [
    "...k...",
    "..kNk..",
    ".knnnk.",
    "knnnnnk",
    "ktyttok",
    ".ktttk.",
    "..kok..",
]

BANG = [
    "y",
    "y",
    "y",
    ".",
    "y",
]

GROUND_Y = 27
HOLE = (21, 26)  # x range of the hole
SIT_X = 6  # SIT origin x; its feet land on GROUND_Y - 1
HUNCH_X = 5


def ground(f: Frame, hole: bool = True) -> None:
    f.rect(1, GROUND_Y, 30, GROUND_Y, "e")
    f.rect(1, GROUND_Y + 1, 30, GROUND_Y + 2, "n")
    if hole:
        f.ellipse(HOLE[0], GROUND_Y - 1, HOLE[1], GROUND_Y + 1, "k")


def pile(f: Frame) -> None:
    """The dug-out dirt right of the hole."""
    f.ellipse(27, GROUND_Y - 3, 30, GROUND_Y + 1, "n")
    f.put(28, GROUND_Y - 2, "t")


def filled(f: Frame, h: int) -> None:
    """Dirt patted over the hole, h px above the ground."""
    f.ellipse(HOLE[0], GROUND_Y - h, HOLE[1], GROUND_Y + 1, "n")


def tail(f: Frame, x: int, y: int) -> None:
    """The tail with a seam where it lies over the body (ink vanishes on dark themes, so it's brown)."""
    t = Frame()
    t.sprite(TAIL, x, y)
    t.outline()
    for j in range(t.height):
        for i in range(t.width):
            c = t.px[j][i]
            if c == "." or (c == "k" and (j >= y + TAIL_BASE or f.get(i, j) == ".")):
                continue
            f.put(i, j, "N" if c == "k" else c)


def sitting(f: Frame, bob: int = 0, rows: list[str] = SIT) -> None:
    y = GROUND_Y - len(rows)
    f.sprite(rows, SIT_X, y)
    tail(f, SIT_X + SIT_TAIL[0], y + SIT_TAIL[1] - bob)


def hunched(f: Frame, paws: int, bob: int = 0) -> None:
    """paws 0: down in the hole, 1: pulled back, 2: raised, 3: patting flat."""
    y = GROUND_Y - len(HUNCH)
    x = HUNCH_X
    f.sprite(HUNCH, x, y)
    px, py = x + 16, y + 8
    if paws == 0:
        f.put(px, py, "o")
        f.rect(px + 1, py, px + 1, py + 2, "t")
    elif paws == 1:
        f.rect(px - 1, py, px - 1, py + 1, "o")
        f.put(px, py + 1, "t")
    elif paws == 2:
        f.rect(px + 1, py - 1, px + 2, py - 1, "o")
        f.rect(px + 3, py - 2, px + 3, py - 1, "t")
    else:
        f.put(px, py, "o")
        f.rect(px + 1, py + 1, px + 3, py + 1, "t")
    tail(f, x + HUNCH_TAIL[0], y + HUNCH_TAIL[1] - bob)


def acorn(f: Frame, x: int, y: int) -> None:
    f.sprite(ACORN, x, y)


def clod(f: Frame, x: int, y: int) -> None:
    f.rect(x, y, x + 1, y + 1, "n")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base(hole: bool = True) -> Frame:
    f = Frame()
    ground(f, hole)
    pile(f)
    return f


# A clod's flight from the hole onto the pile, one point per loop frame.
ARC = [(24, 21), (25, 17), (26, 15), (28, 16), (29, 19), (28, 22)]


def loop() -> Anim:
    frames = []
    for i in range(6):
        f = base()
        hunched(f, i % 2, bob=(0, 0, 1, 1, 1, 0)[i])
        for k in (0, 3):
            if (i + k) % 6 < 5:
                clod(f, *ARC[(i + k) % 6])
        frames.append(finish(f))
    return anim(frames, 120)


HELD = (SIT_X + 9, 15)


def success() -> Anim:
    frames, durations = [], []
    # sit up, acorn held, then raised
    for dy in (0, -2):
        f = base()
        sitting(f)
        acorn(f, HELD[0], HELD[1] + dy)
        frames.append(finish(f))
        durations.append(180 if dy else 160)
    # drop into the hole
    for x, y in ((HOLE[0] - 3, 16), (HOLE[0] - 1, 20), (HOLE[0] - 1, 23)):
        f = base()
        sitting(f)
        acorn(f, x, y)
        ground(f)  # the hole and soil cover the part of the acorn that's in
        frames.append(finish(f))
        durations.append(90)
    # pat the dirt down over it
    for i, h in enumerate((3, 3, 2, 2)):
        f = base(hole=False)
        filled(f, h)
        hunched(f, 2 if i % 2 == 0 else 3)
        frames.append(finish(f))
        durations.append(110)
    # sit up proud, check
    for step in range(3):
        f = base(hole=False)
        filled(f, 1)
        sitting(f, bob=step % 2)
        sparkle(f, 24, 21, step)
        sparkle(f, 17, 5, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    for dy in (0, -2):
        f = base()
        sitting(f)
        acorn(f, HELD[0], HELD[1] + dy)
        frames.append(finish(f))
        durations.append(160)
    # fumble: it pops up and away, bounces off the pile and out of frame
    for x, y in ((18, 6), (21, 8), (24, 13), (26, 18), (28, 12), (31, 15), (34, 22)):
        f = base()
        sitting(f)
        f.sprite(BANG, SIT_X + 10, GROUND_Y - len(SIT) - 7)
        acorn(f, x, y)
        frames.append(finish(f))
        durations.append(80)
    # a beat staring after it, then it slumps; cross
    f = base()
    sitting(f)
    frames.append(finish(f))
    durations.append(220)
    for step in range(3):
        f = base()
        sitting(f, bob=-1, rows=SLUMP)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(120 if step < 2 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
