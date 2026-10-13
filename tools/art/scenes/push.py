"""git push: a rocket on a launch pad.

loop: the rocket rumbles on the pad, engine idling.
success: full burn, lift-off, gone; the pad smokes and a check pops in.
fail: the engine sputters out, the rocket tips over, smoke and a cross.
"""

from __future__ import annotations

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame, anim, rotate

# Unoutlined body; Frame.outline() adds the ink.
ROCKET = [
    "...r...",
    "..rrr..",
    "..rrr..",
    ".wwwgw.",
    ".wbbwg.",
    ".wbcwg.",
    ".wbbwg.",
    ".wwwwg.",
    ".wwwwg.",
    "rwwwwgr",
    "rrwwgrr",
    "r.sss.r",
]
RW, RH = 7, len(ROCKET)
PAD_Y = 27
CX = 16


def pad(f: Frame) -> None:
    f.rect(8, PAD_Y, 24, PAD_Y + 1, "G")
    f.rect(9, PAD_Y + 2, 23, PAD_Y + 2, "s")
    f.line(10, PAD_Y, 10, PAD_Y + 2, "s")
    f.line(22, PAD_Y, 22, PAD_Y + 2, "s")
    # gantry
    f.rect(5, 12, 6, PAD_Y - 1, "G")
    for y in range(13, PAD_Y, 3):
        f.put(7, y, "g")


def rocket(f: Frame, x: int, bottom: int, tilt: int = 0) -> None:
    """Rocket with its nozzle row at `bottom`; tilt shears it sideways by 1 px per 4 rows."""
    top = bottom - RH + 1
    for j, row in enumerate(ROCKET):
        dx = (tilt * (RH - 1 - j)) // 4
        f.sprite([row], x - RW // 2 + dx, top + j)


def flame(f: Frame, x: int, y: int, size: int, flicker: int) -> None:
    """Exhaust below (x, y); size 0..3."""
    if size <= 0:
        return
    length = [0, 2, 4, 7][min(size, 3)] + (flicker % 2)
    for j in range(length):
        half = 1 if j < length - 1 else 0
        if size >= 2 and j < length // 2:
            half = 2
        c = "w" if j == 0 else ("y" if j < length * 0.6 else "o")
        f.rect(x - half, y + j, x + half, y + j, c)
    f.put(x, y + length, "r")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base() -> Frame:
    f = Frame()
    pad(f)
    return f


def loop() -> Anim:
    frames = []
    for i in range(6):
        f = base()
        jitter = (0, 1, 0, -1, 0, 1)[i]
        bottom = PAD_Y - 2
        flame(f, CX, bottom + 1, 1, i)
        rocket(f, CX + jitter, bottom)
        smoke(f, CX - 6 + (i % 2), PAD_Y - 1, i % 2)
        smoke(f, CX + 6 - (i % 2), PAD_Y - 1, (i + 1) % 2)
        frames.append(finish(f))
    return anim(frames, 110)


def success() -> Anim:
    frames, durations = [], []
    # ignition: two frames of full burn on the pad
    for i in range(2):
        f = base()
        flame(f, CX, PAD_Y - 1, 2, i)
        rocket(f, CX + (i % 2), PAD_Y - 2)
        smoke(f, CX - 7, PAD_Y - 1, 1 + i)
        smoke(f, CX + 7, PAD_Y - 1, 2 + i)
        frames.append(finish(f))
        durations.append(110)
    # lift-off, accelerating
    for i, rise in enumerate((2, 5, 10, 17, 27, 40)):
        f = base()
        bottom = PAD_Y - 2 - rise
        smoke(f, CX - 5, PAD_Y - 1, 3)
        smoke(f, CX + 5, PAD_Y - 1, 3)
        if rise < 30:
            smoke(f, CX, PAD_Y - 2, 2)
        flame(f, CX, bottom + 1, 3, i)
        rocket(f, CX, bottom)
        frames.append(finish(f))
        durations.append(90)
    # the pad, a contrail and the badge
    for step in range(4):
        f = base()
        f.line(CX, 0, CX, 10 - step * 3, "g")
        smoke(f, CX - 5, PAD_Y - 1, 3 - min(step, 1))
        smoke(f, CX + 5, PAD_Y - 1, 3 - min(step, 1))
        sparkle(f, CX - 7, 6, step)
        sparkle(f, CX + 3, 3, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(100 if step < 3 else 400)
    return Anim(frames, durations)


def lying(f: Frame, bounce: int = 0) -> None:
    """The rocket on its side on the pad, nose right."""
    rows = rotate(ROCKET, 1)
    f.sprite(rows, CX - RH // 2, PAD_Y - RW - bounce)


def fail() -> Anim:
    frames, durations = [], []
    # sputter: flame flickers and dies
    for i, size in enumerate((2, 1, 2, 0, 1, 0)):
        f = base()
        flame(f, CX, PAD_Y - 1, size, i)
        rocket(f, CX + (1 if i % 2 else 0), PAD_Y - 2)
        frames.append(finish(f))
        durations.append(110)
    # lean, lean further, fall flat (with a small bounce)
    for tilt in (1, 3):
        f = base()
        rocket(f, CX, PAD_Y - 2, tilt)
        frames.append(finish(f))
        durations.append(130)
    for bounce in (2, 0):
        f = base()
        lying(f, bounce)
        frames.append(finish(f))
        durations.append(90)
    # smoking, cross
    for step in range(4):
        f = base()
        smoke(f, CX - RH // 2 - 2, PAD_Y - 6, 1 + (step % 3))
        lying(f)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
