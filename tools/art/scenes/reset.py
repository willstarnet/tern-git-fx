"""git reset: an alarm clock rewinding.

loop: the hands spin backwards with a blur trailing the minute hand.
success: the hands slow down and snap to twelve; the clock hops and its bells ring; check.
fail: the clock rattles, a spring and gears burst out of it, hands go limp, smoke; cross.
"""

from __future__ import annotations

import math

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame, anim

CX, CY = 12, 18
R = 8  # rim radius; the face is R - 2
FEET_Y = 27

GEAR = [
    "..y.y..",
    ".yyyyy.",
    "yyyyyyy",
    ".yykyy.",
    "yyyyyyy",
    ".yyyyy.",
    "..y.y..",
]
SPRING = [
    "wwww.",
    "g..gg",
    ".wwww",
    "gg..g",
    "wwww.",
    "g..gg",
    ".wwww",
]


def point(angle: float, length: float, cx: int = CX, cy: int = CY) -> tuple[int, int]:
    """Clock angle in degrees (0 = twelve, clockwise) to a pixel."""
    a = math.radians(angle)
    return round(cx + length * math.sin(a)), round(cy - length * math.cos(a))


def clock(f: Frame, minute: float, hour: float, dx: int = 0, dy: int = 0, blur: int = 0, bells: int = 0) -> None:
    """The alarm clock; blur (degrees) smears a counter-clockwise minute hand, bells tilts them."""
    cx, cy = CX + dx, CY + dy
    # feet and bells behind the body
    f.line(cx - 5, cy + 6, cx - 6, FEET_Y + dy, "y")
    f.line(cx + 5, cy + 6, cx + 6, FEET_Y + dy, "y")
    for side in (-1, 1):
        bx, by = point(side * (45 + bells * side * 6), R + 1, cx, cy)
        f.circle(bx, by, 2, "y")
    f.line(cx, cy - R - 2, cx, cy - R, "y")
    f.circle(cx, cy, R, "r")
    f.circle(cx, cy, R - 2, "w")
    for a in (0, 90, 180, 270):
        f.put(*point(a, R - 3, cx, cy), "G")
    if blur:
        for y in range(cy - R, cy + R + 1):
            for x in range(cx - R, cx + R + 1):
                if not 1.5 <= math.hypot(x - cx, y - cy) <= R - 2.5:
                    continue
                diff = (math.degrees(math.atan2(x - cx, cy - y)) - minute) % 360
                if 0 < diff <= blur:
                    f.put(x, y, "b" if diff <= blur / 2 else "c")
    f.line(cx, cy, *point(minute, R - 3, cx, cy), "k")
    f.line(cx, cy, *point(hour, R - 5, cx, cy), "k")
    f.put(cx, cy, "r")


def burst(f: Frame, x: int, y: int, angles: tuple[int, ...], r0: int, r1: int, c: str = "y") -> None:
    for a in angles:
        f.line(*point(a, r0, x, y), *point(a, r1, x, y), c)


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def loop() -> Anim:
    frames = []
    for i in range(12):
        f = Frame()
        clock(f, minute=-60 * i, hour=-30 * i + 120, blur=50)
        frames.append(finish(f))
    return anim(frames, 80)


def success() -> Anim:
    frames, durations = [], []
    # spinning down, slowing
    for m, h, d, b in ((240, 210, 70, 50), (150, 150, 80, 50), (80, 100, 100, 40), (35, 50, 120, 25), (10, 15, 150, 10)):
        f = Frame()
        clock(f, m, h, blur=b)
        frames.append(finish(f))
        durations.append(d)
    # snap to twelve: ding
    lb, rb = point(-45, R + 1), point(45, R + 1)
    for i, (dy, bells) in enumerate(((-2, 1), (0, -1), (-1, 1))):
        f = Frame()
        clock(f, 0, 0, dy=dy, bells=bells)
        burst(f, lb[0], lb[1] + dy, (-90, -45, 0), 3, 5 + (i % 2), "w")
        burst(f, rb[0], rb[1] + dy, (90, 45), 3, 5 + (i % 2), "w")
        frames.append(finish(f))
        durations.append(90)
    for step in range(3):
        f = Frame()
        clock(f, 0, 0)
        sparkle(f, 2, 22, step)
        sparkle(f, 25, 20, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def spring(f: Frame, n: int, wobble: int = 0) -> None:
    """The first n coils of the spring, standing on the clock's top."""
    bottom = CY - R - 2
    for j, row in enumerate(SPRING[:n]):
        dx = wobble if j < n // 2 else 0
        f.sprite([row], CX - 2 + dx, bottom - n + 1 + j)


def gear(f: Frame, x: int, y: int) -> None:
    f.sprite(GEAR, x, y)


GROUNDED = 27 - len(GEAR) + 1


def fail() -> Anim:
    frames, durations = [], []
    # spinning backwards ever faster, rattling
    for i, (m, h) in enumerate(((0, 120), (-90, 60), (-200, 0), (-330, -90))):
        f = Frame()
        clock(f, m, h, dx=(0, 1, -1, 1)[i], blur=50 + i * 10)
        frames.append(finish(f))
        durations.append(110 - i * 10)
    # sproing: the spring shoots out, gears fly (one out of frame), the hands go limp
    left = [None, (3, 2), (-4, -2)]
    right = [None, (17, 3), (22, 7), (24, 14), (24, GROUNDED)]
    for i, rg in enumerate(right):
        f = Frame()
        if i >= 2:
            smoke(f, 4, 13, i - 2)
        clock(f, 190, 160, dx=(-1, 1, 0, 0, 0)[i])
        spring(f, (3, 6, 7, 7, 7)[i], wobble=(0, 0, 1, -1, 0)[i])
        if i == 0:
            burst(f, CX, CY - R - 3, (-80, -45, 45, 80), 4, 6, "w")
        if i < len(left) and left[i]:
            gear(f, *left[i])
        if rg:
            gear(f, *rg)
        frames.append(finish(f))
        durations.append(90)
    # wreck, smoke, cross
    for step in range(3):
        f = Frame()
        smoke(f, 4, 13, 2 + step % 2)
        clock(f, 190, 160)
        spring(f, len(SPRING))
        gear(f, 24, GROUNDED)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(120 if step < 2 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
