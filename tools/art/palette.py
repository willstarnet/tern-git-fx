"""The shared pixel palette: one character per color, so sprites can be drawn as ASCII rows.

Based on Sweetie 16 (by GrafxKid, lospec.com) plus three browns. Every scene uses only these
colors so the set reads as one family. "." is transparent.
"""

from __future__ import annotations

CLEAR = "."

HEX: dict[str, str] = {
    "k": "#1a1c2c",  # ink: outlines, darkest shadow
    "s": "#333c57",  # slate
    "G": "#566c86",  # gray
    "g": "#94b0c2",  # light gray
    "w": "#f4f4f4",  # white
    "P": "#5d275d",  # plum
    "r": "#b13e53",  # red
    "o": "#ef7d57",  # orange
    "y": "#ffcd75",  # yellow
    "l": "#a7f070",  # lime
    "e": "#38b764",  # green
    "E": "#257179",  # teal
    "D": "#29366f",  # navy
    "B": "#3b5dc9",  # blue
    "b": "#41a6f6",  # sky
    "c": "#73eff7",  # cyan
    "N": "#4e2f22",  # dark brown
    "n": "#8f563b",  # brown
    "t": "#d9a066",  # tan
}

OUTLINE = "k"


def rgba(key: str) -> tuple[int, int, int, int]:
    if key == CLEAR:
        return (0, 0, 0, 0)
    h = HEX[key]
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
