"""Index-color frames and drawing primitives for the tern-git-fx pixel art.

A Frame is a fixed grid of palette characters (see palette.py); "." is transparent. Coordinates
are integer pixels, (0, 0) top-left, and every shape is clipped to the frame. All primitives are
deterministic: no randomness here (scenes seed their own `random.Random(name)` if they need it).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from PIL import Image

from .palette import CLEAR, HEX, OUTLINE, rgba

SIZE = 32


class Frame:
    def __init__(self, width: int = SIZE, height: int = SIZE) -> None:
        self.width = width
        self.height = height
        self.px: list[list[str]] = [[CLEAR] * width for _ in range(height)]

    # -- pixels ---------------------------------------------------------------------------------

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> str:
        return self.px[y][x] if self.inside(x, y) else CLEAR

    def put(self, x: int, y: int, c: str) -> None:
        if c != CLEAR and c not in HEX:
            raise ValueError(f"unknown palette key {c!r}")
        x, y = int(round(x)), int(round(y))
        if self.inside(x, y):
            self.px[y][x] = c

    def erase(self, x: int, y: int) -> None:
        if self.inside(x, y):
            self.px[y][x] = CLEAR

    def copy(self) -> "Frame":
        f = Frame(self.width, self.height)
        f.px = [row[:] for row in self.px]
        return f

    # -- shapes ---------------------------------------------------------------------------------

    def rect(self, x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        """Filled rectangle, corners inclusive."""
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.put(x, y, c)

    def box(self, x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        """1 px rectangle border, corners inclusive."""
        self.line(x0, y0, x1, y0, c)
        self.line(x0, y1, x1, y1, c)
        self.line(x0, y0, x0, y1, c)
        self.line(x1, y0, x1, y1, c)

    def line(self, x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        """Bresenham line, endpoints inclusive."""
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, x0: int, y0: int, x1: int, y1: int, c: str, fill: bool = True) -> None:
        """Ellipse inscribed in the inclusive box; sampled at pixel centers."""
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (abs(x1 - x0) + 1) / 2, (abs(y1 - y0) + 1) / 2
        inside = set()
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                if ((x + 0.5 - cx - 0.5) / rx) ** 2 + ((y + 0.5 - cy - 0.5) / ry) ** 2 <= 1.0:
                    inside.add((x, y))
        for x, y in inside:
            if fill:
                self.put(x, y, c)
            elif any(n not in inside for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                self.put(x, y, c)

    def circle(self, cx: int, cy: int, r: int, c: str, fill: bool = True) -> None:
        self.ellipse(cx - r, cy - r, cx + r, cy + r, c, fill)

    def poly(self, points: Sequence[tuple[int, int]], c: str) -> None:
        """Filled polygon (even-odd, sampled at pixel centers) plus its edges."""
        n = len(points)
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs: list[float] = []
            for i in range(n):
                (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.put(x, y, c)
        for i in range(n):
            (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
            self.line(ax, ay, bx, by, c)

    # -- sprites --------------------------------------------------------------------------------

    def sprite(self, rows: Sequence[str], x: int, y: int, flip: bool = False, recolor: dict[str, str] | None = None) -> None:
        """Draws ASCII rows (palette keys, "." transparent) with the top-left at (x, y)."""
        for j, row in enumerate(rows):
            line = row[::-1] if flip else row
            for i, ch in enumerate(line):
                if ch == CLEAR or ch == " ":
                    continue
                self.put(x + i, y + j, (recolor or {}).get(ch, ch))

    def blit(self, other: "Frame", x: int = 0, y: int = 0) -> None:
        for j in range(other.height):
            for i in range(other.width):
                ch = other.px[j][i]
                if ch != CLEAR:
                    self.put(x + i, y + j, ch)

    def outline(self, c: str = OUTLINE, diagonal: bool = False) -> None:
        """Adds a 1 px outline on transparent pixels that touch an opaque one."""
        offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonal:
            offsets += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        add = []
        for y in range(self.height):
            for x in range(self.width):
                if self.px[y][x] != CLEAR:
                    continue
                if any(self.get(x + dx, y + dy) not in (CLEAR, c) for dx, dy in offsets):
                    add.append((x, y))
        for x, y in add:
            self.px[y][x] = c

    def shift(self, dx: int, dy: int) -> "Frame":
        """A copy moved by (dx, dy); pixels leaving the frame are dropped."""
        f = Frame(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                if self.px[y][x] != CLEAR:
                    f.put(x + dx, y + dy, self.px[y][x])
        return f

    # -- output ---------------------------------------------------------------------------------

    def opaque_count(self) -> int:
        return sum(1 for row in self.px for ch in row if ch != CLEAR)

    def image(self) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        img.putdata([rgba(ch) for row in self.px for ch in row])
        return img


def sprite_size(rows: Sequence[str]) -> tuple[int, int]:
    return (max(len(r) for r in rows), len(rows))


def rotate(rows: Sequence[str], turns: int = 1) -> list[str]:
    """ASCII sprite rotated clockwise by `turns` quarter turns (rows padded to equal width)."""
    w, _ = sprite_size(rows)
    out = [r.ljust(w, CLEAR) for r in rows]
    for _ in range(turns % 4):
        out = ["".join(out[len(out) - 1 - j][i] for j in range(len(out))) for i in range(len(out[0]))]
    return out


@dataclass
class Anim:
    """One animation: frames and how long each shows. Loops repeat; outros end on the last frame."""

    frames: list[Frame]
    durations_ms: list[int]

    def __post_init__(self) -> None:
        if len(self.frames) != len(self.durations_ms):
            raise ValueError(f"{len(self.frames)} frames but {len(self.durations_ms)} durations")


def anim(frames: Iterable[Frame], durations_ms: int | Sequence[int]) -> Anim:
    """Builds an Anim; a single duration applies to every frame."""
    fs = list(frames)
    ds = [int(durations_ms)] * len(fs) if isinstance(durations_ms, int) else [int(d) for d in durations_ms]
    return Anim(fs, ds)
