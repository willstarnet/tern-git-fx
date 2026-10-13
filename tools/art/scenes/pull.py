"""git pull: a supply crate parachuting down from the remote.

loop: the crate sways gently under its striped canopy, high above the ground.
success: it touches down in a puff of dust, the canopy sags and drapes beside it, a check pops in.
fail: the canopy rips apart, the crate drops and bursts open on the ground, dust and a cross.
"""

from __future__ import annotations

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame, anim

# Unoutlined body; Frame.outline() adds the ink.
CRATE = [
    "nnnnnnnnn",
    "nttttttNn",
    "ntttttNtn",
    "nttttNttn",
    "ntttNtttn",
    "nttNttttn",
    "ntNtttttn",
    "nnnnnnnnn",
]
CW, CH = 9, len(CRATE)
GROUND_Y = 28
CX = 16
LAND_TOP = GROUND_Y - CH  # crate top row when resting on the ground
HIGH_TOP = 15  # crate top row while drifting in the loop
LINES = 8  # rows of shroud line between the canopy hem and the crate

# Canopy rows as (first, last) column; gores alternate red/white every 3 columns.
CANOPY = [(5, 9), (3, 11), (1, 13), (0, 14), (0, 14)]
CANOPY_W = 15
ROPE = "t"


def ground(f: Frame) -> None:
    f.rect(4, GROUND_Y, 27, GROUND_Y, "e")
    f.rect(5, GROUND_Y + 1, 26, GROUND_Y + 1, "n")
    for x in (6, 25):
        f.put(x, GROUND_Y - 1, "l")


def gore(i: int, last_row: bool) -> str:
    red = (i // 3) % 2 == 0
    if last_row:
        return "r" if red else "g"
    return "r" if red else "w"


def canopy(f: Frame, cx: int, top: int) -> tuple[int, int, int]:
    """Full canopy centered on cx; returns (left, right, hem_y) for the shroud lines."""
    x0 = cx - CANOPY_W // 2
    for j, (a, b) in enumerate(CANOPY):
        for i in range(a, b + 1):
            f.put(x0 + i, top + j, gore(i, j == len(CANOPY) - 1))
    return x0, x0 + CANOPY_W - 1, top + len(CANOPY) - 1


def torn_canopy(f: Frame, cx: int, top: int, spread: int) -> None:
    """The canopy split down the middle, halves pulled apart by `spread` px."""
    x0 = cx - CANOPY_W // 2
    for j, (a, b) in enumerate(CANOPY):
        for i in range(a, b + 1):
            if i == 7 or (i in (6, 8) and j < 2):
                continue  # the jagged rip
            dx = -spread if i < 7 else spread
            f.put(x0 + i + dx, top + j + (spread if j > 2 else 0), gore(i, j == len(CANOPY) - 1))


def rag(f: Frame, x: int, y: int, flip: bool) -> None:
    """A loose scrap of canopy fluttering away."""
    f.sprite(["rrw..", ".rwww", "..ww."], x, y, flip=flip)


def crate(f: Frame, top: int, cx: int = CX) -> tuple[int, int, int]:
    """Crate with its top row at `top`; returns (left, right, top)."""
    x = cx - CW // 2
    f.sprite(CRATE, x, top)
    return x, x + CW - 1, top


def ropes(f: Frame, chute: tuple[int, int, int], box: tuple[int, int, int]) -> None:
    """Shroud lines, drawn after the outline so they stay 1 px."""
    left, right, hem = chute
    bl, br, btop = box
    mid = (left + right) // 2
    f.line(left, hem + 1, bl, btop - 1, ROPE)
    f.line(mid, hem + 1, (bl + br) // 2, btop - 1, ROPE)
    f.line(right, hem + 1, br, btop - 1, ROPE)


def drifting(f: Frame, crate_top: int, chute_dx: int = 0, crate_dx: int = 0) -> Frame:
    """Canopy plus crate in the air, outlined, with lines."""
    chute = canopy(f, CX + chute_dx, crate_top - LINES - len(CANOPY))
    box = crate(f, crate_top, CX + crate_dx)
    f.outline()
    ropes(f, chute, box)
    return f


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base() -> Frame:
    f = Frame()
    ground(f)
    return f


def loop() -> Anim:
    frames = []
    for sway in (0, 1, 1, 0, -1, -1):
        f = base()
        frames.append(drifting(f, HIGH_TOP, sway, -sway))
    return anim(frames, 160)


# Canopy folds once the crate is down: a sagging dome, then a crumpled pile behind the crate.
SAG = [(3, 11), (1, 13), (0, 14), (0, 15)]
PILE = [
    "....rw.....",
    "...rrww....",
    "..rrrwwr.w.",
    ".rrrwwwrrww",
    ".rrwwwrrrww",
    "rrrwwwrrwww",
    "rrrgggrrggg",
]

# The crate after the crash: smashed in from the top right, braces snapped.
WRECK = [
    "n........",
    "ntn......",
    "nttn..n..",
    "ntttNtnn.",
    "nttNttttn",
    "nnnnnnnnn",
]


def sagging(f: Frame, left: int, top: int) -> tuple[int, int, int]:
    for j, (a, b) in enumerate(SAG):
        for i in range(a, b + 1):
            f.put(left + i, top + j + (1 if j == len(SAG) - 1 and i % 3 == 1 else 0), gore(i, j == len(SAG) - 1))
    return left, left + SAG[-1][1], top + len(SAG)


def pile(f: Frame) -> None:
    f.sprite(PILE, CX + 2, GROUND_Y - len(PILE))


def dust(f: Frame, phase: int) -> None:
    smoke(f, CX - 7 - phase, GROUND_Y - 1, phase)
    smoke(f, CX + 7 + phase, GROUND_Y - 1, phase)


def success() -> Anim:
    frames, durations = [], []
    # the last stretch of the descent
    for top in (HIGH_TOP, HIGH_TOP + 2, HIGH_TOP + 4):
        f = base()
        frames.append(drifting(f, top))
        durations.append(130)
    # touchdown: dust kicks out from under the crate
    f = base()
    dust(f, 0)
    frames.append(drifting(f, LAND_TOP))
    durations.append(110)
    # the canopy sags and drifts right...
    f = base()
    dust(f, 1)
    chute = sagging(f, CX - 5, LAND_TOP - 7)
    box = crate(f, LAND_TOP)
    f.outline()
    ropes(f, chute, box)
    frames.append(f)
    durations.append(130)
    # ...and crumples beside the crate
    for step in range(5):
        f = base()
        pile(f)
        crate(f, LAND_TOP)
        if step >= 1:
            sparkle(f, CX - 9, LAND_TOP - 4, step)
            sparkle(f, CX + 1, LAND_TOP - 8, step + 2)
            check_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(130 if step == 0 else (100 if step < 4 else 400))
    return Anim(frames, durations)


def wreck(f: Frame, flying: bool) -> None:
    """The burst crate. flying: lid, a wall and fruit still in the air; else everything has landed."""
    left = CX - CW // 2
    f.sprite(WRECK, left, GROUND_Y - len(WRECK))
    if flying:
        f.line(CX - 5, 13, CX + 1, 10, "t")
        f.line(CX - 5, 14, CX + 1, 11, "n")
        f.line(CX + 7, 22, CX + 10, 18, "t")
        f.line(CX + 7, 23, CX + 10, 19, "n")
        for x, y, c in ((CX - 3, 18, "r"), (CX + 3, 17, "o"), (CX - 8, 20, "y")):
            f.circle(x, y, 1, c)
    else:
        # lid flat on the ground at left with fruit on it, a wall leaning on the right
        f.rect(4, GROUND_Y - 2, 9, GROUND_Y - 2, "t")
        f.rect(4, GROUND_Y - 1, 9, GROUND_Y - 1, "n")
        f.line(CX + 6, GROUND_Y - 1, CX + 9, GROUND_Y - 6, "t")
        f.line(CX + 7, GROUND_Y - 1, CX + 10, GROUND_Y - 6, "n")
        for x, y, c in ((7, GROUND_Y - 4, "o"), (CX + 1, GROUND_Y - 4, "r"), (CX + 12, GROUND_Y - 2, "y")):
            f.circle(x, y, 1, c)


def fail() -> Anim:
    frames, durations = [], []
    canopy_top = HIGH_TOP - LINES - len(CANOPY)
    left = CX - CANOPY_W // 2
    # drifting along, then the canopy splits
    f = base()
    frames.append(drifting(f, HIGH_TOP, 1, -1))
    durations.append(150)
    f = base()
    torn_canopy(f, CX, canopy_top, 1)
    box = crate(f, HIGH_TOP)
    f.put(CX - 1, canopy_top - 2, "w")
    f.put(CX + 2, canopy_top - 3, "r")
    f.outline()
    ropes(f, (left - 1, left + CANOPY_W, canopy_top + len(CANOPY)), box)
    frames.append(f)
    durations.append(170)
    # halves tear away, the crate starts to drop
    f = base()
    torn_canopy(f, CX, canopy_top - 2, 3)
    crate(f, HIGH_TOP + 1)
    frames.append(finish(f))
    durations.append(110)
    # free fall with speed lines, rags flutter off
    for i, top in enumerate((HIGH_TOP + 3, LAND_TOP)):
        f = base()
        rag(f, CX - 12 - i * 3, 3 - i * 4, False)
        rag(f, CX + 3 + i * 3, -1 - i * 4, True)
        crate(f, top)
        f.outline()
        for x in (CX - 2, CX + 2):
            f.line(x, top - 7 + abs(x - CX), x, top - 3, "g")
        frames.append(f)
        durations.append(80)
    # crash: the crate bursts, pieces fly
    f = base()
    dust(f, 1)
    wreck(f, flying=True)
    frames.append(finish(f))
    durations.append(120)
    # wreckage settles, cross
    for step in range(5):
        f = base()
        if step == 0:
            dust(f, 2)
        wreck(f, flying=False)
        if step >= 1:
            x_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(130 if step == 0 else (110 if step < 4 else 400))
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
