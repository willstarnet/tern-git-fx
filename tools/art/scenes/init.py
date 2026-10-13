"""git init: a seed planted in a flower pot.

loop: a watering can, tipped over the pot, sways gently while droplets fall into the soil.
success: the can lifts away, a sprout pushes up and unfurls two leaves; sparkles and a check.
fail: the sprout comes up, wilts and droops brown, then the pot cracks and a shard drops; a cross.
"""

from __future__ import annotations

import math

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim

CX = 16
SOIL_Y = 19  # top row of the soil mound
RIM_Y = 21  # two rim rows
BODY_Y = 23  # pot body rows down to the saucer
SAUCER_Y = 29

# Watering can, in local coordinates around its body centre (x right, y down, unrotated).
CAN_BODY = [(-4, -3), (4, -3), (4, 3), (-4, 3)]
CAN_HANDLE = [(-3, -3), (-2, -5), (1, -5), (2, -3)]
CAN_SPOUT = [(3, 1), (9, -4)]
CAN_ROSE = (10, -5)
CAN_X, CAN_Y = 7, 7

LEAF = [  # left leaf; its base sits against the stem at the bottom right
    "ll....",
    "llll..",
    ".lllle",
    "..eeee",
]

# Drooping sprout, stem base at column 1 of the last row.
WILT_NOD = [
    "..ee..",
    ".e..yy",
    ".e..yt",
    ".e....",
    ".e....",
    ".e....",
]
WILT_DEAD = [
    "..tt..",
    ".t..t.",
    ".t..tt",
    ".t..nt",
    ".t....",
    ".t....",
]

SHARD = [
    "oo.",
    "otn",
    ".n.",
]


def pot(f: Frame, cracked: bool = False) -> None:
    # soil mound
    f.rect(CX - 5, SOIL_Y + 1, CX + 5, SOIL_Y + 1, "n")
    f.rect(CX - 3, SOIL_Y, CX + 3, SOIL_Y, "n")
    f.put(CX - 3, SOIL_Y + 1, "N")
    f.put(CX + 3, SOIL_Y, "N")
    # rim
    f.rect(CX - 7, RIM_Y, CX + 7, RIM_Y, "t")
    f.rect(CX - 7, RIM_Y + 1, CX + 7, RIM_Y + 1, "o")
    f.put(CX + 7, RIM_Y + 1, "n")
    # tapering body with a highlight on the left and shade on the right
    for j, y in enumerate(range(BODY_Y, SAUCER_Y)):
        inset = 1 + j // 2
        x0, x1 = CX - 7 + inset, CX + 7 - inset
        f.rect(x0, y, x1, y, "o")
        f.put(x0 + 1, y, "t")
        f.rect(x1 - 1, y, x1, y, "n")
    # saucer
    f.rect(CX - 6, SAUCER_Y, CX + 6, SAUCER_Y, "n")
    if cracked:
        crack = [(CX + 1, RIM_Y), (CX + 1, RIM_Y + 1), (CX, RIM_Y + 2), (CX, RIM_Y + 3), (CX + 1, RIM_Y + 4),
                 (CX + 2, RIM_Y + 5), (CX + 1, RIM_Y + 6), (CX + 1, RIM_Y + 7)]
        for x, y in crack:
            f.put(x, y, "N")
        # a chunk of the rim is gone
        for x in range(CX + 4, CX + 8):
            f.erase(x, RIM_Y)
        for x in range(CX + 5, CX + 8):
            f.erase(x, RIM_Y + 1)
        f.erase(CX + 5, BODY_Y)


def watering_can(f: Frame, cx: int, cy: int, deg: float) -> tuple[int, int]:
    """Draws the can rotated clockwise by `deg`; returns the rose (spout head) position."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)

    def tr(p: tuple[float, float]) -> tuple[int, int]:
        x, y = p
        return (round(cx + x * ca - y * sa), round(cy + x * sa + y * ca))

    pts = [tr(p) for p in CAN_HANDLE]
    for p, q in zip(pts, pts[1:]):
        f.line(*p, *q, "B")
    (sx0, sy0), (sx1, sy1) = tr(CAN_SPOUT[0]), tr(CAN_SPOUT[1])
    f.line(sx0, sy0, sx1, sy1, "B")
    f.line(sx0 + 1, sy0, sx1 + 1, sy1, "B")
    f.poly([tr(p) for p in CAN_BODY], "b")
    # highlight band and a darker foot
    f.line(*tr((-2, -2)), *tr((-2, 2)), "c")
    f.line(*tr((-4, 3)), *tr((4, 3)), "B")
    rx, ry = tr(CAN_ROSE)
    f.circle(rx, ry, 1, "g")
    f.put(rx, ry, "w")
    return rx, ry


def droplet(f: Frame, x: int, y: int) -> None:
    f.put(x, y, "c")
    f.put(x, y + 1, "b")


def sprout(f: Frame, stage: int, wilt: int = 0) -> None:
    """stage 0: the seed cracks the soil; 1: a hooked shoot; 2: folded leaves; 3: leaves fling
    open; 4: settled. `wilt` 1 nods the head, 2 is the dead brown droop."""
    top = SOIL_Y - 1
    if wilt:
        f.sprite(WILT_NOD if wilt == 1 else WILT_DEAD, CX - 1, top - 5)
        return
    if stage == 0:
        f.rect(CX - 1, top, CX, top, "t")
        f.put(CX, top - 1, "l")
        return
    if stage == 1:
        f.line(CX, top, CX, top - 2, "e")
        f.rect(CX, top - 3, CX + 1, top - 3, "l")
        return
    height = {2: 5, 3: 8, 4: 7}[stage]
    tip = top - height + 1
    f.line(CX, top, CX, tip, "e")
    if stage == 2:
        # two leaves still folded up against each other
        f.rect(CX - 1, tip - 3, CX - 1, tip - 1, "l")
        f.rect(CX + 1, tip - 3, CX + 1, tip - 1, "l")
        f.put(CX, tip - 1, "e")
        return
    # the open leaves flank a little centre bud, kept low and clear of the badge corner
    f.sprite(LEAF, CX - 6, tip)
    f.sprite(LEAF, CX + 1, tip, flip=True)
    f.put(CX, tip, "l")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base(cracked: bool = False) -> Frame:
    f = Frame()
    pot(f, cracked)
    return f


def loop() -> Anim:
    frames = []
    n = 6
    for i in range(n):
        f = base()
        deg = 52 + 4 * math.sin(2 * math.pi * i / n)
        rx, ry = watering_can(f, CAN_X, CAN_Y, deg)
        # a trickle of two droplets falling 2 px per frame, 3 px apart
        for k in range(2):
            y = ry + 2 + (i * 2 + k * 3) % 6
            if y + 1 < SOIL_Y:
                droplet(f, rx, y)
        frames.append(finish(f))
    return anim(frames, 120)


def lift_can(f: Frame, step: int) -> None:
    """The can tips back (step 0) and slides away to the left (step 1)."""
    if step == 0:
        watering_can(f, CAN_X, CAN_Y, 30)
    else:
        watering_can(f, CAN_X - 7, CAN_Y - 1, 0)


def success() -> Anim:
    frames, durations = [], []
    # last drop lands, the can tips back and leaves
    for step in range(2):
        f = base()
        lift_can(f, step)
        if step == 0:
            droplet(f, CX + 1, SOIL_Y - 3)
        frames.append(finish(f))
        durations.append(120)
    # the sprout pushes up and unfurls
    for stage, ms in ((0, 180), (1, 140), (2, 140), (3, 100)):
        f = base()
        sprout(f, stage)
        frames.append(finish(f))
        durations.append(ms)
    # settled, sparkles, check
    for step in range(4):
        f = base()
        sprout(f, 4)
        sparkle(f, CX - 9, 7, step)
        sparkle(f, CX + 9, 15, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(100 if step < 3 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    f = base()
    lift_can(f, 1)
    frames.append(finish(f))
    durations.append(120)
    # comes up, then gives up
    for stage, wilt, ms in ((0, 0, 160), (1, 0, 130), (2, 0, 240), (2, 1, 200), (2, 2, 220)):
        f = base()
        sprout(f, stage, wilt)
        frames.append(finish(f))
        durations.append(ms)
    # the pot cracks, a shard drops off with a puff, then the cross
    for step in range(4):
        f = base(cracked=True)
        sprout(f, 2, 2)
        # the shard drops off the rim, lands and rocks to rest
        if step == 0:
            f.sprite(SHARD, CX + 7, RIM_Y + 3)
        else:
            f.sprite(SHARD, CX + 9, SAUCER_Y - 2 - (1 if step == 1 else 0))
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(120 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
