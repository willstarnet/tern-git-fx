"""git commit: an instant camera taking a snapshot.

loop: the camera waits on the ground, record light blinking, a glint sweeping across the lens.
success: shutter press, flash burst, a photo slides out of the top and develops; a check pops in.
fail: shutter press, the flash only sputters, smoke rises from it and the lens cracks; a cross.
"""

from __future__ import annotations

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame, anim

GROUND_Y = 28
X0, X1 = 6, 25  # camera body
TOP = 14  # body top row (the photo slot)
LENS = (16, 21)
FLASH = (8, 18)  # center of the flash window
SLOT_X0, SLOT_X1 = 11, 20

# The developed photo: white instant-film frame, a sunny hill.
PHOTO = [
    "wwwwwwwwww",
    "wbbbbbbyyw",
    "wbbbbbbyyw",
    "wbbbbbbbbw",
    "wbbblllbbw",
    "wblleeellw",
    "weeeeeeeew",
    "wwwwwwwwww",
    "wwwwwwwwww",
    "wwwwwwwwww",
    "gggggggggg",
]
PW, PH = len(PHOTO[0]), len(PHOTO)
# Film before it develops: the picture area is still gray.
BLANK = {"b": "G", "y": "G", "l": "G", "e": "G"}
HALF = {"b": "g", "y": "w", "l": "g", "e": "G"}


def ground(f: Frame) -> None:
    f.rect(X0 - 2, GROUND_Y, X1 + 2, GROUND_Y, "G")


def camera(f: Frame, pressed: bool = False, light: str = "r", flash: str = "w", glint: int = 0,
           cracked: bool = False, dy: int = 0) -> None:
    top = TOP + dy
    # shutter button and viewfinder hump
    f.rect(20, top - 2 + (1 if pressed else 0), 23, top - 1, "y")
    # body: silver band over a red shell
    f.rect(X0, top, X1, GROUND_Y - 1 + dy, "r")
    f.rect(X0, top, X1, top + 2, "g")
    f.rect(X0, top, X1, top, "w")
    f.rect(SLOT_X0, top, SLOT_X1, top, "s")
    f.rect(X0, GROUND_Y - 1 + dy, X1, GROUND_Y - 1 + dy, "P")
    f.rect(X1, top + 3, X1, GROUND_Y - 1 + dy, "P")
    f.rect(X0, top + 3, X0, GROUND_Y - 2 + dy, "o")
    # record light on the band
    f.rect(22, top + 1, 23, top + 1, light)
    # flash window and viewfinder
    fx, fy = FLASH[0], FLASH[1] + dy
    f.rect(fx - 1, fy - 1, fx + 2, fy + 1, "g")
    f.rect(fx, fy, fx + 1, fy, flash)
    f.rect(21, top + 4, 23, top + 5, "D")
    f.put(21, top + 4, "b")
    # lens: barrel, glass, glint
    lx, ly = LENS[0], LENS[1] + dy
    f.circle(lx, ly, 5, "g")
    f.circle(lx, ly, 4, "w")
    f.circle(lx, ly, 3, "D")
    f.circle(lx, ly, 1, "B")
    f.put(lx, ly, "E")
    if cracked:
        for a, b in (((-3, -2), (-1, -1)), ((-1, -1), (0, 1)), ((0, 1), (3, 2)), ((0, 1), (-1, 3)), ((-1, -1), (0, -3))):
            f.line(lx + a[0], ly + a[1], lx + b[0], ly + b[1], "w")
    else:
        gx = (-3, -2, -1, 0, 1, 2)[glint % 6]
        if glint % 6 < 5:
            f.line(lx + gx, ly + 1, lx + gx + 2, ly - 1, "c")
        f.put(lx - 2, ly - 2, "w")


def photo(f: Frame, out: int, recolor: dict[str, str] | None = None) -> None:
    """The print pushed `out` rows above the slot; drawn before the camera so the body hides the rest."""
    f.sprite(PHOTO, SLOT_X0, TOP - out, recolor=recolor)


def burst(f: Frame, size: int) -> None:
    """Flash burst around the flash window; size 1..3."""
    cx, cy = FLASH[0] + 1, FLASH[1]
    rays = ((-1, -1), (0, -1), (1, -1), (-1, 0), (-1, 1))
    reach = (0, 3, 6, 8)[size]
    for dx, dy in rays:
        for d in range(2, reach + 1):
            c = "w" if d <= reach // 2 + 1 else "y"
            f.put(cx + dx * d, cy + dy * d, c)
    f.circle(cx, cy, 1 + size // 2, "w")
    if size >= 2:
        f.put(cx - reach - 1, cy - reach - 1, "y")


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base() -> Frame:
    f = Frame()
    ground(f)
    return f


def loop() -> Anim:
    frames = []
    for i in range(6):
        f = base()
        camera(f, light="r" if i < 3 else "G", glint=i)
        frames.append(finish(f))
    return anim(frames, 150)


def success() -> Anim:
    frames, durations = [], []
    # press the shutter
    for pressed, d in ((False, 120), (True, 90)):
        f = base()
        camera(f, pressed=pressed)
        frames.append(finish(f))
        durations.append(d)
    # flash
    for size, d in ((3, 70), (2, 80), (1, 70)):
        f = base()
        camera(f, pressed=size > 1, flash="y")
        burst(f, size)
        frames.append(finish(f))
        durations.append(d)
    # the print slides out of the top, still blank
    for out in (3, 6, 9):
        f = base()
        photo(f, out, BLANK)
        camera(f)
        frames.append(finish(f))
        durations.append(90)
    # ... clears the slot, develops, and the badge pops in
    for step, (recolor, d) in enumerate(((BLANK, 110), (HALF, 120), (None, 110), (None, 400))):
        f = base()
        photo(f, PH + 1 + (1 if step == 0 else 0), recolor)
        camera(f)
        if step >= 2:
            sparkle(f, SLOT_X0 - 3, 4, step)
            sparkle(f, 4, 11, step + 2)
        if step >= 1:
            check_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(d)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    # press the shutter
    for pressed, d in ((False, 120), (True, 90)):
        f = base()
        camera(f, pressed=pressed)
        frames.append(finish(f))
        durations.append(d)
    # the flash sputters: a weak orange spark, nothing, a spark, dead
    for flash, spark, d in (("o", 2, 90), ("s", 0, 110), ("o", 1, 70), ("s", 0, 120)):
        f = base()
        camera(f, pressed=True, flash=flash, light="G")
        if spark:
            sparkle(f, FLASH[0] + 1, FLASH[1] - 4, spark, "o")
        frames.append(finish(f))
        durations.append(d)
    # a jolt, the lens cracks, smoke from the flash
    f = base()
    camera(f, flash="s", light="G", cracked=True, dy=1)
    smoke(f, FLASH[0], FLASH[1] - 3, 0)
    frames.append(finish(f))
    durations.append(90)
    for step in range(4):
        f = base()
        smoke(f, FLASH[0] - (step % 2), FLASH[1] - 4, 1 + min(step, 2))
        camera(f, flash="s", light="G", cracked=True)
        x_badge(f, step=step)
        frames.append(finish(f))
        durations.append(110 if step < 3 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
