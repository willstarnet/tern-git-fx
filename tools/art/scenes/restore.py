"""git restore: a crumpled page wound back to how it was.

loop: a rewind arrow circles a crumpled ball of paper, counterclockwise.
success: the arrow whips round, the page springs open and smooths out clean; sparkles and a check.
fail: the arrow stalls, shudders and greys out; the page starts to open, tears in two and the
halves flop to the ground; a cross.
"""

from __future__ import annotations

import math

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim

GROUND_Y = 30
CX, CY = 16, 15  # orbit center
R_IN, R_OUT = 7.6, 9.6  # orbit ring

# A balled-up sheet: white facets, crease strokes, a shaded underside.
CRUMPLED = [
    "...www.ww..",
    "..wwwgwwww.",
    ".wwwgwwwgww",
    "wggwgwwggww",
    "wwwggggwwgw",
    "wwwwwwgggww",
    ".wwwwgwwwgw",
    "wwwwgwwwggw",
    ".wggwwwggg.",
    "...ggggg...",
]

# The clean page: dog-ear, lines of text.
PAGE = [
    "wwwwwwwwG..",
    "wwwwwwwwgG.",
    "wwwwwwwwggG",
    "wwwwwwwwwww",
    "wBBBBBwwwww",
    "wwwwwwwwwww",
    "wBBBBBBBBww",
    "wwwwwwwwwww",
    "wBBBBBBBwww",
    "wwwwwwwwwww",
    "wBBBBBBBBww",
    "wwwwwwwwwww",
    "wBBBBwwwwww",
    "wwwwwwwwwww",
    "ggggggggggg",
]
PW, PH = len(PAGE[0]), len(PAGE)
PAGE_X, PAGE_Y = CX - PW // 2, CY - PH // 2
LANDED = GROUND_Y - 1 - (PAGE_Y + PH - 1)  # drop that puts the page's bottom row on the ground


def ground(f: Frame) -> None:
    f.rect(CX - 8, GROUND_Y, CX + 8, GROUND_Y, "G")


def crumpled(f: Frame, dy: int = 0) -> None:
    w, h = len(CRUMPLED[0]), len(CRUMPLED)
    f.sprite(CRUMPLED, CX - w // 2, CY - h // 2 + dy)


def page_frame(semi: bool = False, dy: int = 0) -> Frame:
    """The page on its own frame; `semi` leaves it ragged and creased, halfway restored."""
    f = Frame()
    f.sprite(PAGE, PAGE_X, PAGE_Y + dy)
    if semi:
        x0, y0, x1, y1 = PAGE_X, PAGE_Y + dy, PAGE_X + PW - 1, PAGE_Y + PH - 1 + dy
        for x, y in ((x0, y0 + 5), (x0, y0 + 6), (x1, y0 + 9), (x0 + 3, y1), (x0 + 4, y1), (x1 - 2, y1)):
            f.erase(x, y)
        f.line(x0 + 1, y0 + 3, x1 - 2, y0 + 9, "g")
        f.line(x0 + 2, y1 - 2, x1 - 1, y0 + 6, "g")
    return f


def ring(f: Frame, head: float, span: float, colors: tuple[str, str, str] = ("b", "c", "B")) -> None:
    """Arc arrow on the orbit, moving counterclockwise with its head at angle `head` (degrees, 0 = right,
    90 = up). Colors: outer band, inner band, arrowhead tip shade."""
    outer, inner, tip = colors
    for y in range(CY - 12, CY + 13):
        for x in range(CX - 12, CX + 13):
            dx, dy = x + 0.5 - (CX + 0.5), (CY + 0.5) - (y + 0.5)
            d = math.hypot(dx, dy)
            if not R_IN <= d <= R_OUT:
                continue
            a = math.degrees(math.atan2(dy, dx))
            back = (head - a) % 360
            if back <= span:
                f.put(x, y, inner if d < (R_IN + R_OUT) / 2 else outer)
    # arrowhead: a triangle pointing along the counterclockwise tangent
    t = math.radians(head)
    rm = (R_IN + R_OUT) / 2
    px, py = CX + rm * math.cos(t), CY - rm * math.sin(t)
    tx, ty = -math.sin(t), -math.cos(t)  # screen-space CCW tangent
    nx, ny = math.cos(t), -math.sin(t)  # outward normal
    base = [(px + nx * 3, py + ny * 3), (px - nx * 3, py - ny * 3)]
    tipp = (px + tx * 4, py + ty * 4)
    f.poly([(round(a), round(b)) for a, b in (base[0], tipp, base[1])], outer)
    f.put(round(px + tx * 1), round(py + ty * 1), tip)


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base() -> Frame:
    f = Frame()
    ground(f)
    return f


def loop() -> Anim:
    frames = []
    for i in range(8):
        f = base()
        ring(f, 90 + i * 45, 150)
        crumpled(f)
        frames.append(finish(f))
    return anim(frames, 120)


def success() -> Anim:
    frames, durations = [], []
    # the arrow whips round, faster and longer
    for i, (head, span) in enumerate(((90, 150), (180, 200), (300, 260), (60, 300))):
        f = base()
        ring(f, head, span)
        crumpled(f, dy=-(i % 2))
        frames.append(finish(f))
        durations.append(80 if i < 2 else 60)
    # the page springs open, then smooths out clean
    f = base()
    ring(f, 200, 120, ("c", "w", "b"))
    f.blit(page_frame(semi=True))
    frames.append(finish(f))
    durations.append(90)
    f = base()
    f.blit(page_frame())
    for x, y, p in ((PAGE_X - 3, PAGE_Y + 2, 2), (PAGE_X + PW + 2, PAGE_Y + 9, 2), (PAGE_X - 2, PAGE_Y + 12, 1)):
        sparkle(f, x, y, p, "c")
    frames.append(finish(f))
    durations.append(110)
    # it settles onto the ground: sparkle, badge
    f = base()
    f.blit(page_frame(dy=LANDED // 2))
    frames.append(finish(f))
    durations.append(70)
    for step in range(3):
        f = base()
        f.blit(page_frame(dy=LANDED))
        sparkle(f, PAGE_X - 3, PAGE_Y + LANDED + 3, step + 3)
        sparkle(f, PAGE_X + PW + 2, PAGE_Y + LANDED + 9, step + 1)
        check_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def halves(page: Frame, sep: int, tilt: int, drop: int) -> Frame:
    """Tears `page` down a jagged line; halves pull `sep` px apart, lean out by `tilt` and sink by `drop`."""
    out = Frame()
    bottom = PAGE_Y + PH - 1
    for y in range(page.height):
        zig = CX + (0, 1, 1, 0, -1, -1)[y % 6]
        for x in range(page.width):
            c = page.get(x, y)
            if c == ".":
                continue
            lean = (tilt * (bottom - y)) // PH
            if x < zig:
                out.put(x - sep - lean, y + drop, c)
            elif x > zig:
                out.put(x + sep + lean, y + drop, c)
    return out


def fail() -> Anim:
    frames, durations = [], []
    # the arrow slows, stalls and shudders back and forth
    for head, d in ((90, 120), (135, 180), (160, 240), (150, 110), (160, 110)):
        f = base()
        ring(f, head, 150)
        crumpled(f)
        frames.append(finish(f))
        durations.append(d)
    # it greys out; the page tries to open
    f = base()
    ring(f, 155, 150, ("g", "G", "s"))
    f.blit(page_frame(semi=True))
    frames.append(finish(f))
    durations.append(140)
    # rip: a gap opens, the halves part, lean out and flop to the ground
    semi = page_frame(semi=True)
    for sep, tilt, drop, d in ((0, 0, 0, 100), (1, 0, 1, 70), (2, 2, 4, 70), (3, 4, LANDED, 90)):
        f = base()
        f.blit(halves(semi, sep, tilt, drop))
        frames.append(finish(f))
        durations.append(d)
    for step in range(3):
        f = base()
        f.blit(halves(semi, 3, 4, LANDED))
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 2 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
