"""git add: a file going into the staging box.

loop: a page with a green plus bobs above an open cardboard box.
success: the page drops in, the box bumps, the flaps fold shut; sparkles and a check.
fail: the page clips the rim, bounces off and lands on its side outside the box; a cross.
"""

from __future__ import annotations

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim, rotate

PAGE = [
    "wwwwwG..",
    "wwwwwgG.",
    "wwwwwggG",
    "wwwwwwww",
    "wwweewww",
    "wwweewww",
    "weeeeeew",
    "weeeeeew",
    "wwweewww",
    "wwweewww",
    "gggggggg",
]
PW, PH = len(PAGE[0]), len(PAGE)
GROUND_Y = 28
BX0, BX1 = 11, 24  # box
MID = (BX0 + BX1) // 2
RIM = 18  # top of the front face is RIM + 1
PX = 14  # page left edge when centered over the box
HOVER = 5  # page top while hovering


def ground(f: Frame) -> None:
    f.rect(1, GROUND_Y, 29, GROUND_Y, "G")


def page(f: Frame, x: int, y: int, turns: int = 0) -> None:
    f.sprite(rotate(PAGE, turns) if turns else PAGE, x, y)


def flap_cells(state: str) -> list[tuple[int, int, int]]:
    """Rows (y, x0, x1) of the left flap; the right flap mirrors it."""
    if state == "out":
        return [(RIM - k, BX0 - k, BX0 + 3 - k) for k in range(6)]
    if state == "up":
        return [(RIM - k, BX0, BX0 + 2) for k in range(7)]
    if state == "in":
        return [(RIM - k, BX0 + k, BX0 + 2 + k) for k in range(5)]
    return [(RIM - 1, BX0, MID), (RIM, BX0, MID)]  # shut


def flaps(f: Frame, state: str, dy: int = 0) -> None:
    for y, x0, x1 in flap_cells(state):
        for a, b in ((x0, x1), (BX0 + BX1 - x1, BX0 + BX1 - x0)):
            f.rect(a, y + dy, b, y + dy, "t")
    if state == "shut":
        f.rect(BX0, RIM - 1 + dy, BX1, RIM - 1 + dy, "y")
        f.rect(MID, RIM - 1 + dy, MID + 1, RIM + dy, "n")
    else:
        for y, x0, x1 in flap_cells(state):
            f.put(x0, y + dy, "n")
            f.put(BX0 + BX1 - x0, y + dy, "n")


def box_back(f: Frame, dy: int = 0) -> None:
    f.rect(BX0 + 1, RIM - 1 + dy, BX1 - 1, RIM + dy, "N")


def box_front(f: Frame, dy: int = 0) -> None:
    top, bottom = RIM + 1 + dy, GROUND_Y - 1
    f.rect(BX0, top, BX1, bottom, "t")
    f.rect(BX0, top, BX1, top, "y")
    f.rect(BX1, top + 1, BX1, bottom, "n")
    f.rect(BX0, bottom, BX1, bottom, "n")
    # hand hole
    f.rect(MID - 1, top + 3, MID + 2, top + 3, "N")


def scene(page_at: tuple[int, int] | None = None, state: str = "out", dy: int = 0, turns: int = 0,
          page_front: bool = False) -> Frame:
    """Ground, box (back, page inside it, front, flaps); `page_front` draws the page over the box."""
    f = Frame()
    ground(f)
    box_back(f, dy)
    if page_at and not page_front:
        page(f, *page_at, turns)
    box_front(f, dy)
    flaps(f, state, dy)
    if page_at and page_front:
        page(f, *page_at, turns)
    return f


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def loop() -> Anim:
    frames = []
    for bob in (0, -1, -2, -1):
        f = scene((PX, HOVER + bob), page_front=True)
        frames.append(finish(f))
    return anim(frames, 170)


def success() -> Anim:
    frames, durations = [], []
    # anticipation, then the drop
    for y, d in ((HOVER - 2, 110), (HOVER + 5, 60), (HOVER + 10, 60)):
        frames.append(finish(scene((PX, y), page_front=y + PH <= RIM)))
        durations.append(d)
    inside = RIM - 1
    # lands inside: the box bumps
    frames.append(finish(scene((PX, inside), dy=1)))
    durations.append(90)
    # flaps fold shut
    for state, d in (("up", 80), ("in", 80), ("shut", 100)):
        frames.append(finish(scene((PX, inside), state)))
        durations.append(d)
    # sparkle, badge
    for step in range(3):
        f = scene((PX, inside), "shut")
        sparkle(f, BX0 - 3, RIM - 6, step + 1)
        sparkle(f, BX1 - 2, RIM - 5, step + 3)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    # the page drifts left as it falls and clips the left flap
    for (x, y), d in (((PX, HOVER - 2), 110), ((PX - 2, HOVER + 3), 70), ((PX - 3, HOVER + 6), 60)):
        frames.append(finish(scene((x, y), page_front=True)))
        durations.append(d)
    # knocked away, tumbling
    for (x, y), turns, d in (((5, 1), 1, 80), ((1, 8), 2, 80), ((1, 16), 3, 80)):
        frames.append(finish(scene((x, y), turns=turns, page_front=True)))
        durations.append(d)
    # lands on its side outside the box, with a small bounce
    lying_y = GROUND_Y - PW
    for bounce, d in ((0, 70), (2, 70)):
        frames.append(finish(scene((1, lying_y - bounce), turns=3, page_front=True)))
        durations.append(d)
    for step in range(4):
        f = scene((1, lying_y), turns=3, page_front=True)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
