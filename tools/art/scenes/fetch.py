"""git fetch: a dog playing fetch.

loop: the dog runs in place, legs cycling, ears and tail bouncing, grass scrolling past.
success: a ball drops in, the dog leaps and catches it, then sits proudly with it, tail wagging; check.
fail: the ball sails over the leaping dog; it skids, sits empty-mouthed looking back, '?' and a cross.
"""

from __future__ import annotations

from ..effects import check_badge, smoke, sparkle, x_badge
from ..raster import Anim, Frame

# Unoutlined parts, facing right; Frame.outline() adds the ink.
HEAD = [
    "..tttt....",
    ".tttttt...",
    "..ttkttttk",
    "...tttttww",
    "....twwww.",
    ".....ww...",
]
EAR = ["nn", "nnn", "nnn", ".n"]  # hangs from the back of the head
BODY = [
    "...nnnttttt...",
    ".ttnnnttttttt.",
    "ttttttttttttww",
    "ttttttttttttww",
    ".tttttttttwww.",
    "..tttttttww...",
]
QUESTION = [
    ".www.",
    "ww.ww",
    "...ww",
    "..ww.",
    "..w..",
    ".....",
    "..w..",
]
GROUND_Y = 27
BX, BY = 7, 16  # body top-left when standing
HIP_BACK, HIP_FRONT = 9, 17
# Run cycle: (front foot dx, back foot dx, lift, body dy) per frame.
GAIT = [(3, -3, 0, 0), (0, 0, 1, -1), (-2, 2, 0, 0), (0, 0, 1, -1)]


def ground(f: Frame, scroll: int = 0) -> None:
    f.rect(2, GROUND_Y, 29, GROUND_Y, "e")
    f.rect(3, GROUND_Y + 1, 28, GROUND_Y + 1, "n")
    for x in range(-scroll % 8 + 3, 29, 8):
        f.put(x, GROUND_Y - 1, "l")


def head(f: Frame, x: int, y: int, ear_up: bool = False, flip: bool = False) -> tuple[int, int]:
    """Head with its top-left at (x, y); returns the mouth point (front of the jaw)."""
    f.sprite(HEAD, x, y, flip=flip)
    ex = x + 7 if flip else x + 1
    f.sprite(EAR, ex, y + 1 - (1 if ear_up else 0), flip=flip)
    return (x if flip else x + len(HEAD[0]) - 1), y + 4


def leg(f: Frame, hip_x: int, hip_y: int, foot_x: int, foot_y: int, c: str) -> None:
    f.line(hip_x, hip_y, foot_x, foot_y, c)
    f.line(hip_x + 1, hip_y, foot_x + 1, foot_y, c)
    f.put(foot_x + 2, foot_y, "w")
    f.put(foot_x + 1, foot_y, "w")


def tail(f: Frame, x: int, y: int, up: int) -> None:
    """Tail from the rump at (x, y); up 0..2 raises the tip."""
    tip = [(x - 3, y - 1), (x - 3, y - 3), (x - 2, y - 5)][up]
    f.line(x, y, tip[0], tip[1], "t")
    f.line(x, y + 1, tip[0], tip[1] + 1, "t")
    f.put(tip[0], tip[1], "w")


def standing(f: Frame, step: int, dy: int = 0, mouth: str = "tongue", flip_head: bool = False) -> tuple[int, int]:
    """The dog on its feet. step indexes GAIT (-1: standing still); returns the mouth point."""
    front, back, lift, bob = GAIT[step] if step >= 0 else (0, 0, 0, 0)
    by = BY + bob + dy
    hip_y = by + len(BODY) - 1
    foot_y = hip_y + 5 - lift - bob  # legs stretch a little on the bounce
    far_front, far_back, _, _ = GAIT[(step + 2) % 4] if step >= 0 else (1, 1, 0, 0)
    # far legs first, in shade
    leg(f, HIP_FRONT + 2, hip_y, HIP_FRONT + 2 + far_front, foot_y, "n")
    leg(f, HIP_BACK + 2, hip_y, HIP_BACK + 2 + far_back, foot_y, "n")
    tail(f, BX + 1, by + 1, (step % 2 + 1) if step >= 0 else 2)
    f.sprite(BODY, BX, by)
    leg(f, HIP_FRONT, hip_y, HIP_FRONT + front, foot_y, "t")
    leg(f, HIP_BACK, hip_y, HIP_BACK + back, foot_y, "t")
    f.rect(BX + 11, by, BX + 12, by, "r")  # collar
    hx, hy = BX + 10 + (0 if not flip_head else -2), by - 5
    mx, my = head(f, hx, hy, ear_up=bob < 0, flip=flip_head)
    if mouth == "tongue":
        f.put(mx - 3, my + 1, "r")
        f.put(mx - 3, my + 2, "r")
    return mx, my


def ball(f: Frame, x: int, y: int) -> None:
    """Tennis ball, 4x4 with its top-left at (x, y)."""
    f.ellipse(x, y, x + 3, y + 3, "l")
    f.put(x + 1, y + 1, "w")


def sitting(f: Frame, wag: int, flip_head: bool = False, droop: bool = False) -> tuple[int, int]:
    """Haunches down, chest up, head high; wag 0..2 sweeps the tail. Returns the mouth point."""
    tip = [(3, 25), (3, 22), (4, 20)][wag]
    f.line(8, 24, tip[0], tip[1], "t")
    f.line(8, 25, tip[0], tip[1] + 1, "t")
    f.put(tip[0], tip[1], "w")
    f.rect(14, 19, 15, GROUND_Y - 1, "n")  # far front leg
    f.poly([(11, 12), (17, 11), (19, 17), (18, 26), (9, 26), (7, 21), (8, 17)], "t")  # torso
    f.ellipse(6, 18, 14, GROUND_Y - 1, "t")  # haunch
    f.ellipse(16, 13, 19, 22, "w")  # chest
    f.rect(8, 17, 10, 18, "n")  # back patch
    f.rect(8, GROUND_Y - 2, 13, GROUND_Y - 1, "t")  # back paw
    f.rect(12, GROUND_Y - 1, 13, GROUND_Y - 1, "w")
    f.rect(17, 19, 18, GROUND_Y - 1, "t")  # near front leg
    f.rect(18, GROUND_Y - 1, 19, GROUND_Y - 1, "w")
    f.rect(12, 12, 16, 12, "r")  # collar
    hx, hy = (8, 6) if flip_head else (11, 6)
    return head(f, hx, hy + (1 if droop else 0), flip=flip_head)


def finish(f: Frame) -> Frame:
    f.outline()
    return f


def base(scroll: int = 0) -> Frame:
    f = Frame()
    ground(f, scroll)
    return f


def loop() -> Anim:
    frames = []
    for i in range(4):
        f = base(scroll=i * 2)
        standing(f, i)
        frames.append(finish(f))
    return Anim(frames, [120] * 4)


def success() -> Anim:
    frames, durations = [], []
    # running; a ball drops in from the top right
    for i, (bx, by) in enumerate(((29, 0), (27, 3))):
        f = base(scroll=i * 2)
        standing(f, i)
        ball(f, bx, by)
        frames.append(finish(f))
        durations.append(110)
    # leap and catch
    f = base(scroll=4)
    mx, my = standing(f, 0, dy=-4, mouth="none")
    ball(f, mx - 1, my - 3)
    frames.append(finish(f))
    durations.append(120)
    f = base(scroll=4)
    mx, my = standing(f, 0, dy=-2, mouth="none")
    ball(f, mx - 2, my - 1)
    frames.append(finish(f))
    durations.append(100)
    # sits down, ball in mouth, tail wagging
    for step in range(6):
        f = base(scroll=4)
        mx, my = sitting(f, wag=(step % 2) * 2)
        ball(f, mx - 2, my - 1)
        if step >= 2:
            sparkle(f, 5, 9, step)
            sparkle(f, 11, 3, step + 2)
            check_badge(f, step=step - 2)
        frames.append(finish(f))
        durations.append(130 if step < 5 else 400)
    return Anim(frames, durations)


def fail() -> Anim:
    frames, durations = [], []
    # running; the ball comes in high
    for i, (bx, by) in enumerate(((29, 0), (24, 1))):
        f = base(scroll=i * 2)
        standing(f, i)
        ball(f, bx, by)
        frames.append(finish(f))
        durations.append(110)
    # leaps, misses: the ball sails over and away
    f = base(scroll=4)
    standing(f, 0, dy=-4, mouth="none")
    ball(f, 15, 0)
    frames.append(finish(f))
    durations.append(120)
    f = base(scroll=4)
    standing(f, 0, dy=-2, mouth="none")
    ball(f, 5, 3)
    frames.append(finish(f))
    durations.append(100)
    # skid to a stop, look back
    f = base(scroll=4)
    standing(f, -1, mouth="none", flip_head=True)
    smoke(f, HIP_BACK - 2, GROUND_Y - 1, 1)
    ball(f, -2, 14)
    frames.append(finish(f))
    durations.append(160)
    # sits, empty-mouthed and puzzled
    for step in range(5):
        f = base(scroll=4)
        sitting(f, wag=0, flip_head=step < 2, droop=step >= 2)
        if step >= 1:
            f.sprite(QUESTION, 4, 2 if step == 1 else 3)
            x_badge(f, step=step - 1)
        frames.append(finish(f))
        durations.append(150 if step < 4 else 400)
    return Anim(frames, durations)


def build() -> dict[str, Anim]:
    return {"loop": loop(), "success": success(), "fail": fail()}
