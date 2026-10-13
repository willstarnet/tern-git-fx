"""git checkout: a shopping cart (as in, heading to the checkout).

loop: the cart rolls along on the spot: wheels turning, the floor streaming past, speed lines.
success: the cart brakes and rocks to a stop, a receipt prints up out of the basket; check.
fail: a traffic cone slides into view, the cart slams into it, the front wheel snaps off, the cart
drops onto its nose and the shopping spills across the floor; cross.
"""

from __future__ import annotations

from typing import Callable

from ..effects import check_badge, sparkle, x_badge
from ..raster import Anim, Frame, anim

GROUND_Y = 28  # floor row
CART_X = 6  # left edge of the basket
RIM_Y = GROUND_Y - 15  # top of the basket when the cart stands still

Contents = Callable[[Frame, int, int], None]


def floor(f: Frame, scroll: int = 0) -> None:
    """Dashed floor line, drawn after the outline; `scroll` moves the dashes left."""
    for x in range(32):
        if (x + scroll) % 8 < 5:
            f.put(x, GROUND_Y, "G")


def baguette(f: Frame, x0: int, top: int) -> None:
    f.line(x0 + 4, top + 2, x0 + 6, top - 4, "t")
    f.line(x0 + 5, top + 2, x0 + 7, top - 4, "t")
    f.put(x0 + 6, top - 2, "n")


def bottle(f: Frame, x: int, y: int) -> None:
    """Upright bottle, cap at (x + 1, y)."""
    f.put(x + 1, y, "w")
    f.put(x + 1, y + 1, "e")
    f.rect(x, y + 2, x + 2, y + 6, "e")
    f.put(x, y + 3, "l")


def cereal(f: Frame, x: int, y: int, w: int = 4, h: int = 5) -> None:
    f.rect(x, y, x + w - 1, y + h - 1, "y")
    f.rect(x + 1, y + 1, x + w - 2, y + 2, "r")


def groceries(f: Frame, x0: int, top: int) -> None:
    """Groceries poking out of the basket whose rim is at row `top`."""
    baguette(f, x0, top)
    bottle(f, x0 + 9, top - 5)
    cereal(f, x0 + 12, top - 2, w=3)


def wheel(f: Frame, cx: int, cy: int, phase: int) -> None:
    f.circle(cx, cy, 2, "s")
    f.put(cx, cy, "g")
    dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[phase % 4]
    f.put(cx + dx, cy + dy, "g")


def cart(
    f: Frame,
    x0: int = CART_X,
    bob: int = 0,
    phase: int = 0,
    contents: Contents | None = groceries,
    jump: int = 0,
    front_wheel: bool = True,
    tilt: float = 0.0,
    pivot: int | None = None,
) -> None:
    """The cart with its basket's left edge at x0 and wheels on the floor.

    `bob` lifts the body, `jump` lifts the contents (drawn behind the basket by `contents(f, x0,
    rim_y)`). `tilt` pitches the body by shearing columns: each drops `tilt` px per px right of
    the `pivot` column (forward when positive). By default a forward pitch rocks on the front
    wheel and a backward one on the back wheel, so neither sinks into the floor."""
    gy = GROUND_Y
    top = gy - 15 - bob
    body = Frame()
    if contents:
        contents(body, x0, top - jump)
    # chassis and legs
    body.line(x0 + 4, gy - 6 - bob, x0 + 17, gy - 6 - bob, "g")
    body.line(x0 + 5, gy - 6 - bob, x0 + 5, gy - 5, "g")
    if front_wheel:
        body.line(x0 + 15, gy - 6 - bob, x0 + 15, gy - 5, "g")
    # basket, tapering to the bottom, with a bright rim and wire ribs
    for j in range(8):
        inset = (j * 2 + 3) // 7
        body.line(x0 + 2 + inset, top + j, x0 + 19 - inset, top + j, "b")
    body.line(x0 + 2, top, x0 + 19, top, "c")
    for k in range(3):
        body.line(x0 + 7 + k * 4, top + 2, x0 + 7 + k * 4, top + 6, "B")
    body.line(x0 + 4, top + 7, x0 + 17, top + 7, "B")
    # handle
    body.line(x0 + 1, top, x0 - 1, top - 3, "g")
    body.rect(x0 - 3, top - 4, x0 - 1, top - 4, "r")

    if pivot is None:
        pivot = x0 + 15 if tilt > 0 else x0 + 5
    px = pivot

    def drop(x: int) -> int:
        return round((x - px) * tilt)

    for y in range(body.height):
        for x in range(body.width):
            ch = body.px[y][x]
            if ch != ".":
                f.put(x, y + drop(x), ch)
    wheel(f, x0 + 5, gy - 3 + drop(x0 + 5), phase)
    if front_wheel:
        wheel(f, x0 + 15, gy - 3 + drop(x0 + 15), phase)


def speed_lines(f: Frame, i: int) -> None:
    for y, length in ((10, 3), (16, 4), (21, 3)):
        off = (i + y) % 2
        f.line(off, y, length + off - 1, y, "w")


def finish(f: Frame, scroll: int | None = None) -> Frame:
    f.outline()
    if scroll is not None:
        floor(f, scroll)
    return f


def loop() -> Anim:
    frames = []
    for i in range(4):
        f = Frame()
        speed_lines(f, i)
        cart(f, bob=i % 2, phase=i)
        frames.append(finish(f, i * 2))
    return anim(frames, 100)


def with_receipt(height: int) -> Contents:
    """The groceries plus a paper strip `height` px tall rising out of the basket behind them."""

    def draw(f: Frame, x0: int, top: int) -> None:
        rx0, rx1 = x0 + 9, x0 + 13
        y0 = top - height + 1
        f.rect(rx0, y0, rx1, top + 1, "w")
        for y in range(y0 + 2, top - 3, 2):
            f.line(rx0 + 1, y, rx1 - (1 if (y // 2) % 2 else 2), y, "g")
        for x in range(rx0, rx1 + 1, 2):
            f.erase(x, y0)
        groceries(f, x0, top)

    return draw


def success() -> Anim:
    frames, durations = [], []
    # braking: the floor slows, the cart pitches onto its front wheel and settles back
    for i, (scroll, tilt, jump, phase, ms) in enumerate(
        ((2, 0.0, 0, 1, 90), (3, 0.15, 1, 2, 140), (3, 0.0, 0, 2, 120))
    ):
        f = Frame()
        if i == 0:
            speed_lines(f, 1)
        cart(f, phase=phase, tilt=tilt, jump=jump)
        frames.append(finish(f, scroll))
        durations.append(ms)
    # the receipt prints up out of the basket
    for height, ms in ((7, 100), (11, 100), (14, 140)):
        f = Frame()
        cart(f, phase=2, contents=with_receipt(height))
        frames.append(finish(f, 3))
        durations.append(ms)
    for step in range(4):
        f = Frame()
        cart(f, phase=2, contents=with_receipt(14))
        sparkle(f, CART_X + 6, RIM_Y - 10, step)
        sparkle(f, CART_X + 22, RIM_Y + 1, step + 2)
        check_badge(f, step=step)
        frames.append(finish(f, 3))
        durations.append(100 if step < 3 else 400)
    return Anim(frames, durations)


def cone(f: Frame, x: int, y: int = GROUND_Y - 1, flying: bool = False) -> None:
    """A traffic cone with its base centred at (x, y); flying tumbles it on its side, tip right."""
    if not flying:
        f.rect(x - 3, y, x + 3, y, "o")
        f.poly([(x - 2, y - 1), (x + 2, y - 1), (x, y - 7)], "o")
        f.rect(x - 1, y - 4, x + 1, y - 3, "w")
    else:
        f.rect(x - 3, y - 3, x - 3, y + 3, "o")
        f.poly([(x - 2, y - 2), (x - 2, y + 2), (x + 4, y)], "o")
        f.rect(x, y - 1, x + 1, y + 1, "w")


BROKEN_X = CART_X - 2  # the cart recoils off the cone
BROKEN_TILT = 0.42  # enough to put the front of the chassis on the floor


def spill(f: Frame, t: int) -> None:
    """The bottle and the cereal box flying out (t 0, 1) and landed (t >= 2)."""
    gy = GROUND_Y - 1
    if t == 0:
        bottle(f, 20, 4)
        cereal(f, 24, 8)
    elif t == 1:
        # bottle tumbling on its side, box falling
        f.rect(23, 13, 27, 15, "e")
        f.put(28, 14, "w")
        f.put(25, 13, "l")
        cereal(f, 27, 17)
    else:
        # bottle lying in front of the cart's nose, box upright beside it
        f.rect(22, gy - 2, 25, gy, "e")
        f.put(23, gy - 2, "l")
        f.put(26, gy - 1, "w")
        cereal(f, 27, gy - 4)


def fail() -> Anim:
    frames, durations = [], []
    # rolling along; a cone slides in from the right
    for i, cx in enumerate((35, 31, 28)):
        f = Frame()
        cone(f, cx)
        cart(f, bob=i % 2, phase=i)
        frames.append(finish(f, i * 2))
        durations.append(100)
    # impact: the cart jolts back, the groceries jump, the cone goes flying
    f = Frame()
    cart(f, x0=CART_X - 1, phase=3, jump=2, tilt=0.1)
    cone(f, 29, GROUND_Y - 9, flying=True)
    for x, y in ((26, 16), (27, 19), (26, 22)):
        f.put(x, y, "y")
    frames.append(finish(f, 6))
    durations.append(130)
    # the front wheel snaps off and rolls away; the cart drops onto its nose, spilling the shopping
    for tilt, t, wx, ms in ((0.2, 0, 24, 100), (BROKEN_TILT, 1, 29, 120), (BROKEN_TILT, 2, 35, 140)):
        f = Frame()
        wheel(f, wx, GROUND_Y - 3, t + 1)
        cart(f, x0=BROKEN_X, contents=baguette, front_wheel=False, tilt=tilt, pivot=BROKEN_X + 5)
        spill(f, t)
        frames.append(finish(f, 6))
        durations.append(ms)
    for step in range(4):
        f = Frame()
        cart(f, x0=BROKEN_X, contents=baguette, front_wheel=False, tilt=BROKEN_TILT, pivot=BROKEN_X + 5)
        spill(f, 2)
        x_badge(f, step=step)
        frames.append(finish(f, 6))
        durations.append(110 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
