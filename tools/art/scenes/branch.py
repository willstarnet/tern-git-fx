"""git branch: a small tree on a tuft of grass.

loop: the crown sways and rustles gently in a breeze.
success: a new branch grows out sideways from the trunk and a leafy bud pops at its tip; check.
fail: the new branch grows, sags, cracks at the joint and drops to the grass with a puff; cross.
"""

from __future__ import annotations

import math

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame, anim

TX = 11  # trunk centre column
GROUND_Y = 27
JOINT = (TX + 2, 20)  # where the new branch leaves the trunk
BRANCH_LEN = 11
BRANCH_DEG = -22  # up and to the right

# Crown blobs: (cx, cy, r, colour), drawn in order.
CROWN = [
    (TX, 10, 6, "e"),
    (TX - 5, 12, 4, "e"),
    (TX + 5, 13, 4, "e"),
    (TX, 6, 4, "e"),
    (TX - 4, 7, 3, "e"),
    (TX + 4, 7, 3, "e"),
]
SHADE = [(TX - 5, 14, 2), (TX + 4, 15, 2), (TX, 15, 2)]
HIGHLIGHT = [(TX - 2, 4, 1), (TX - 6, 10, 1), (TX + 3, 8, 1)]


def ground(f: Frame) -> None:
    f.rect(3, GROUND_Y, 28, GROUND_Y, "e")
    f.rect(4, GROUND_Y + 1, 27, GROUND_Y + 1, "n")
    for x in (5, 9, 17, 22, 26):
        f.put(x, GROUND_Y - 1, "e")
    for x in (7, 15, 20, 24):
        f.put(x, GROUND_Y, "l")


def trunk(f: Frame) -> None:
    f.rect(TX - 1, 14, TX + 1, GROUND_Y - 1, "n")
    f.line(TX - 1, 14, TX - 1, GROUND_Y - 1, "t")
    f.line(TX + 1, 16, TX + 1, GROUND_Y - 1, "N")
    # root flare
    f.put(TX - 2, GROUND_Y - 1, "n")
    f.put(TX + 2, GROUND_Y - 1, "N")


def crown(sway: int = 0, rustle: int = 0) -> Frame:
    """The leaves on their own layer; the top sways by `sway` px, the bottom stays put."""
    c = Frame()
    for x, y, r, col in CROWN:
        c.circle(x, y, r, col)
    for x, y, r in SHADE:
        c.circle(x, y, r, "E")
    for i, (x, y, r) in enumerate(HIGHLIGHT):
        dx = (1 if (i + rustle) % 2 else 0) if rustle else 0
        c.circle(x + dx, y, r, "l")
    # a couple of leaf tufts on the rim that flutter between two spots
    for i, (x0, y0, x1, y1) in enumerate(((TX - 9, 9, TX - 9, 11), (TX + 9, 11, TX + 9, 13), (TX - 2, 1, TX + 1, 1))):
        if (i + rustle) % 2:
            c.put(x0, y0, "e")
        else:
            c.put(x1, y1, "e")
    out = Frame()
    for y in range(c.height):
        dx = round(sway * max(0.0, (14 - y) / 12))
        for x in range(c.width):
            ch = c.px[y][x]
            if ch != ".":
                out.put(x + dx, y, ch)
    return out


def branch(f: Frame, length: float, deg: float = BRANCH_DEG, origin: tuple[int, int] = JOINT) -> tuple[int, int]:
    """A 2 px thick limb from `origin`, tapering to 1 px; returns its tip."""
    a = math.radians(deg)
    ox, oy = origin
    tx, ty = round(ox + length * math.cos(a)), round(oy + length * math.sin(a))
    if length <= 0:
        return ox, oy
    mx, my = round(ox + length * 0.6 * math.cos(a)), round(oy + length * 0.6 * math.sin(a))
    f.line(ox, oy + 1, mx, my + 1, "N")
    f.line(ox, oy, tx, ty, "n")
    f.line(ox, oy, mx, my, "t")
    return tx, ty


def bud(f: Frame, x: int, y: int, size: int) -> None:
    """size 1: a small bud, 2: leaves burst (overshoot), 3: settled tuft."""
    if size == 1:
        f.rect(x, y - 1, x + 1, y, "l")
        return
    r = 4 if size == 2 else 3
    f.circle(x + 1, y - 1, r, "e")
    f.circle(x, y - 2, r - 2, "l")
    f.put(x + 2, y + r - 2, "E")
    f.put(x + 3, y + r - 3, "E")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base(sway: int = 0, rustle: int = 0) -> Frame:
    f = Frame()
    ground(f)
    trunk(f)
    f.blit(crown(sway, rustle))
    return f


def loop() -> Anim:
    frames = []
    for i, sway in enumerate((0, 1, 2, 1, 0, -1, -2, -1)):
        frames.append(finish(base(sway, i // 2 % 2 + 1)))
    return anim(frames, 150)


def success() -> Anim:
    frames, durations = [], []
    # the limb pushes out of the trunk
    for length, ms in ((2, 120), (5, 110), (8, 110), (BRANCH_LEN, 120)):
        f = base()
        branch(f, length)
        frames.append(finish(f))
        durations.append(ms)
    # bud, burst, settle
    for size, ms in ((1, 140), (2, 100), (3, 100)):
        f = base()
        tx, ty = branch(f, BRANCH_LEN)
        bud(f, tx, ty, size)
        frames.append(finish(f))
        durations.append(ms)
    for step in range(4):
        f = base(sway=(0, 1, 0, 0)[step])
        tx, ty = branch(f, BRANCH_LEN)
        bud(f, tx, ty, 3)
        sparkle(f, tx + 4, ty + 5, step)
        sparkle(f, 3, 2, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(100 if step < 3 else 400)
    return Anim(frames, durations)


def crack(f: Frame) -> None:
    jx, jy = JOINT
    f.put(jx + 1, jy - 1, "w")
    f.put(jx + 2, jy, "w")
    f.put(jx + 1, jy + 1, "w")


def fallen(f: Frame) -> None:
    """The snapped limb lying in the grass: splintered end left, wilted bud right."""
    x0, x1 = JOINT[0] + 2, JOINT[0] + 1 + BRANCH_LEN
    y = GROUND_Y - 3
    f.rect(x0, y, x1, y, "t")
    f.rect(x0, y + 1, x1, y + 1, "n")
    f.rect(x0 + 1, y + 2, x1 - 1, y + 2, "N")
    f.put(x0 - 1, y, "w")
    f.put(x0 - 1, y + 2, "w")
    f.put(x0 + 6, y - 1, "n")
    f.rect(x1 + 1, y, x1 + 2, y + 1, "y")


def fail() -> Anim:
    frames, durations = [], []
    for length, ms in ((3, 120), (7, 110), (BRANCH_LEN, 140)):
        f = base()
        tx, ty = branch(f, length)
        if length == BRANCH_LEN:
            bud(f, tx, ty, 1)
        frames.append(finish(f))
        durations.append(ms)
    # it sags under its own weight and cracks
    for deg, cracked, ms in ((0, False, 160), (14, True, 140), (30, True, 120)):
        f = base()
        tx, ty = branch(f, BRANCH_LEN, deg)
        bud(f, tx, ty, 1)
        if cracked:
            crack(f)
        frames.append(finish(f))
        durations.append(ms)
    # snaps off and drops to the grass
    jx, jy = JOINT
    f = base()
    tx, ty = branch(f, BRANCH_LEN - 1, 18, (jx + 2, jy + 3))
    bud(f, tx, ty, 1)
    frames.append(finish(f))
    durations.append(90)
    # lands in the grass kicking up dust; the stub stays on the trunk; the cross
    for step in range(4):
        f = base()
        f.put(jx, jy, "n")
        f.put(jx, jy + 1, "N")
        if step < 2:
            smoke(f, jx + 1, GROUND_Y - 2, step)
            smoke(f, jx + BRANCH_LEN + 3, GROUND_Y - 2, step)
        fallen(f)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(120 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
