"""Shared outcome effects, so every command ends with the same visual vocabulary.

- success: `check_badge` (green disc, white tick) and `sparkle`s;
- failure: `x_badge` (red disc, white cross) and `smoke` puffs.

Badges are 9x9 and meant for the top-right corner (x=22, y=1) of the last frames of an outro;
`badge_pop` gives the 3-step pop-in (small, overshoot, settled).
"""

from __future__ import annotations

from .raster import Frame

CHECK = [
    "..kkkkk..",
    ".keeeeek.",
    "keeeeewek",
    "keeeewwek",
    "kewewweek",
    "kewwweeek",
    "keeweeeek",
    ".keeeeek.",
    "..kkkkk..",
]

CROSS = [
    "..kkkkk..",
    ".krrrrrk.",
    "krwrrrwrk",
    "krrwrwrrk",
    "krrrwrrrk",
    "krrwrwrrk",
    "krwrrrwrk",
    ".krrrrrk.",
    "..kkkkk..",
]

SMALL_CHECK = [
    ".kkk.",
    "keeek",
    "kewek",
    "keeek",
    ".kkk.",
]

SMALL_CROSS = [
    ".kkk.",
    "krrrk",
    "krwrk",
    "krrrk",
    ".kkk.",
]

BADGE_X, BADGE_Y = 22, 1


def check_badge(f: Frame, x: int = BADGE_X, y: int = BADGE_Y, step: int = 2) -> None:
    """step 0: small, 1: overshoot (drawn 1 px up), 2+: settled."""
    if step <= 0:
        f.sprite(SMALL_CHECK, x + 2, y + 2)
    elif step == 1:
        f.sprite(CHECK, x, y - 1)
    else:
        f.sprite(CHECK, x, y)


def x_badge(f: Frame, x: int = BADGE_X, y: int = BADGE_Y, step: int = 2) -> None:
    if step <= 0:
        f.sprite(SMALL_CROSS, x + 2, y + 2)
    elif step == 1:
        f.sprite(CROSS, x, y - 1)
    else:
        f.sprite(CROSS, x, y)


def sparkle(f: Frame, x: int, y: int, phase: int, c: str = "y") -> None:
    """A 4-phase twinkle centered on (x, y): dot, plus, big plus, plus."""
    p = phase % 4
    f.put(x, y, "w" if p in (1, 2) else c)
    if p >= 1:
        for d in (1,) if p != 2 else (1, 2):
            f.put(x + d, y, c)
            f.put(x - d, y, c)
            f.put(x, y + d, c)
            f.put(x, y - d, c)


def smoke(f: Frame, x: int, y: int, phase: int) -> None:
    """A puff that grows and rises over phases 0-3, centered at (x, y) at phase 0."""
    p = max(0, min(phase, 3))
    r = 1 + p
    cy = y - p * 2
    f.circle(x, cy, r, "G")
    f.circle(x - 1, cy - 1, max(r - 1, 0), "g")
    if p >= 2:
        f.circle(x + r, cy + 1, max(r - 2, 1), "G")
