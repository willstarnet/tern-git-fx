"""git clone: a sheep gets copied.

loop: the sheep stands calmly while a little scanner drone sweeps its beam up and down over it.
success: the sheep steps aside, the drone projects a cyan hologram sheep that fills in, flashes and
  becomes a real second sheep; sparkles and a check.
fail: the hologram comes out jittery and garbled, the copy shakes apart and fizzles into smoke; cross.
"""

from __future__ import annotations

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame


# A fluffy white sheep facing right, gray face and legs; unoutlined, Frame.outline() adds the ink.
SHEEP = [
    "...ww.ww.ww.......",
    "..wwwwwwwwwwww....",
    ".wwwwwwwwwwwwwww..",
    "wwwwwwwwwwwwwGGGG.",
    "wwwwwwwwwwwwGGGkGG",
    "wwwwwwwwwwwwwGGGGG",
    "wwwwwwwwwwwwwwGGs.",
    "wwwwwwwwwwwwww....",
    "wwwwwwwwwwwwww....",
    ".wwwwwwwwwwwww....",
    "..gggggggggggg....",
    "..GG.ss..GG.ss....",
    "..GG.ss..GG.ss....",
    "..GG.ss..GG.ss....",
    "..GG.ss..GG.ss....",
]
SW, SH = len(SHEEP[0]), len(SHEEP)
FLOOR_Y = 28
SHEEP_Y = FLOOR_Y - SH
MID_X = 7  # sheep x while alone, centered
LEFT_X, CLONE_X = 1, 13  # after stepping aside; the copy stands just behind and to the right

LAMP = [
    ".GGGGGG.",
    "GggggggG",
    ".bbbbbb.",
]
LAMP_Y = 5
LENS_Y = LAMP_Y + 2
BEAM = "b"
GLITCH = [{"w": "l", "g": "e"}, {}, {"w": "o", "g": "r", "G": "P"}, {"w": "c", "g": "b"}]


def floor(f: Frame) -> None:
    f.rect(2, FLOOR_Y, 29, FLOOR_Y, "e")


def lamp(f: Frame, x: int, light: str = "l") -> tuple[int, int]:
    """Scanner drone with its top-left at (x, LAMP_Y); returns the lens span."""
    f.sprite(LAMP, x, LAMP_Y)
    f.put(x + 3, LAMP_Y - 1, light)
    f.put(x + 4, LAMP_Y - 1, light)
    return x + 1, x + len(LAMP[0]) - 2


def lamp_over(sheep_x: int) -> int:
    return sheep_x + 5


def sheep(
    f: Frame,
    x: int,
    y: int = SHEEP_Y,
    shifts: tuple[int, int, int] = (0, 0, 0),
    palettes: tuple[dict[str, str], ...] | None = None,
) -> None:
    """The sheep; shifts/palettes apply per band (back/head, belly, legs) for the glitch."""
    for j, row in enumerate(SHEEP):
        band = 0 if j < 6 else (1 if j < 11 else 2)
        f.sprite([row], x + shifts[band], y + j, recolor=palettes[band] if palettes else None)


def in_front(f: Frame, x: int) -> None:
    """The original sheep drawn with its own outline over whatever is behind it."""
    g = Frame()
    sheep(g, x)
    g.outline()
    f.blit(g)


def beam(f: Frame, lens: tuple[int, int], x0: int, x1: int, y: int, broken: bool = False) -> None:
    """Fan from the lens down to a scan line at row y spanning x0..x1 (drawn after the outline)."""
    a, b = lens
    f.line(a, LENS_Y + 1, x0, y, BEAM)
    if not broken:
        f.line(b, LENS_Y + 1, x1, y, BEAM)
        f.line(x0, y, x1, y, BEAM)
    else:
        f.line(x0, y, (x0 + x1) // 2 - 2, y, BEAM)
        f.line((x0 + x1) // 2 + 2, y, x1, y, "r")


def hologram(f: Frame, x: int, fill_from: int, shifts: tuple[int, int, int] = (0, 0, 0), hot: bool = False) -> None:
    """Cyan see-through copy: edges in blue, interior filled in cyan from row `fill_from` down.

    Drawn after the outline and only on empty pixels, so it sits behind the original.
    """
    mask = {(i, j) for j, row in enumerate(SHEEP) for i, ch in enumerate(row) if ch != "."}
    for i, j in mask:
        band = 0 if j < 6 else (1 if j < 11 else 2)
        px, py = x + i + shifts[band], SHEEP_Y + j
        if f.get(px, py) != ".":
            continue
        edge = any(n not in mask for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)))
        if edge:
            f.put(px, py, "r" if hot and band == 1 else "b")
        elif SHEEP_Y + j >= fill_from:
            f.put(px, py, "c")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base() -> Frame:
    f = Frame()
    floor(f)
    return f


def loop() -> Anim:
    frames = []
    for i, y in enumerate((14, 17, 20, 23, 26, 23, 20, 17)):
        f = base()
        sheep(f, MID_X)
        lens = lamp(f, lamp_over(MID_X), "l" if i < 4 else "e")
        f.outline()
        beam(f, lens, MID_X - 1, MID_X + SW, y)
        frames.append(f)
    return Anim(frames, [110] * 8)


def success() -> Anim:
    frames, durations = [], []
    # the scan finishes
    f = base()
    sheep(f, MID_X)
    lens = lamp(f, lamp_over(MID_X))
    f.outline()
    beam(f, lens, MID_X - 1, MID_X + SW, FLOOR_Y - 1)
    frames.append(f)
    durations.append(120)
    # the sheep steps aside as the drone glides over
    f = base()
    sheep(f, (MID_X + LEFT_X) // 2, SHEEP_Y - 1)
    lamp(f, (lamp_over(MID_X) + lamp_over(CLONE_X)) // 2)
    frames.append(finish(f))
    durations.append(110)
    # a hologram is projected and fills in from the bottom up
    for scan_y in (FLOOR_Y - 1, SHEEP_Y + 7, SHEEP_Y):
        f = base()
        sheep(f, LEFT_X)
        lens = lamp(f, lamp_over(CLONE_X))
        f.outline()
        hologram(f, CLONE_X, scan_y)
        beam(f, lens, CLONE_X - 1, CLONE_X + SW, scan_y)
        frames.append(f)
        durations.append(130)
    # flash: it turns solid white, then real; the drone floats off
    f = base()
    sheep(f, CLONE_X, palettes=({"G": "w", "s": "w", "g": "w", "k": "w"},) * 3)
    lamp(f, 6)
    in_front(f, LEFT_X)
    sparkle(f, 19, 8, 1)
    frames.append(finish(f))
    durations.append(90)
    for step in range(5):
        f = base()
        sheep(f, CLONE_X, SHEEP_Y - (1 if step == 0 else 0))
        lamp(f, 3)
        in_front(f, LEFT_X)
        sparkle(f, 19, 7, step + 2)
        sparkle(f, 13, 10, step)
        if step >= 1:
            check_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(110 if step < 4 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    # scan, step aside
    f = base()
    sheep(f, MID_X)
    lens = lamp(f, lamp_over(MID_X))
    f.outline()
    beam(f, lens, MID_X - 1, MID_X + SW, FLOOR_Y - 1)
    frames.append(f)
    durations.append(120)
    f = base()
    sheep(f, (MID_X + LEFT_X) // 2, SHEEP_Y - 1)
    lamp(f, (lamp_over(MID_X) + lamp_over(CLONE_X)) // 2, "y")
    frames.append(finish(f))
    durations.append(110)
    # the projection stutters: jittery, misaligned hologram
    for scan_y, shifts in ((SHEEP_Y + 9, (2, -1, 1)), (SHEEP_Y + 2, (-2, 2, 0))):
        f = base()
        sheep(f, LEFT_X)
        lens = lamp(f, lamp_over(CLONE_X), "r")
        f.outline()
        hologram(f, CLONE_X, scan_y, shifts, hot=True)
        beam(f, lens, CLONE_X - 1, CLONE_X + SW, scan_y, broken=True)
        frames.append(f)
        durations.append(130)
    # out comes a garbled copy that shakes apart
    for shifts, pals in (((2, -2, 1), (GLITCH[0], GLITCH[1], GLITCH[2])), ((-2, 3, -1), (GLITCH[2], GLITCH[3], GLITCH[0]))):
        f = base()
        sheep(f, CLONE_X, shifts=shifts, palettes=pals)
        lamp(f, lamp_over(CLONE_X), "r")
        in_front(f, LEFT_X)
        frames.append(finish(f))
        durations.append(110)
    f = base()
    for j in range(0, SH, 3):
        f.sprite([SHEEP[j]], CLONE_X + (3 if j % 2 else -3), SHEEP_Y + j, recolor=GLITCH[j % len(GLITCH)])
    smoke(f, CLONE_X + SW // 2 + 2, FLOOR_Y - 5, 1)
    lamp(f, lamp_over(CLONE_X) - 3, "r")
    in_front(f, LEFT_X)
    frames.append(finish(f))
    durations.append(100)
    # smoke, cross
    for step in range(4):
        f = base()
        smoke(f, CLONE_X + SW // 2 + 2, FLOOR_Y - 5, 2 + min(step, 1))
        lamp(f, 3, "r")
        in_front(f, LEFT_X)
        if step >= 1:
            x_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(130 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
