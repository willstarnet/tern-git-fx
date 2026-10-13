# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==12.3.0"]
# ///
"""Builds the bundled sprite sheets from tools/art/scenes/*.py.

    uv run tools/build_sprites.py               # every command: sheets, manifest, docs preview
    uv run tools/build_sprites.py push commit   # only these: sheets and build/preview (no manifest)
    uv run tools/build_sprites.py --check       # exit 1 if a committed output is out of date

Outputs (pixels are deterministic; PNG bytes vary with the platform's zlib, so files are only
rewritten, and --check only compares, by decoded pixels):
- assets/sprites/<command>-<phase>.png: one horizontal strip per animation;
- assets/sprites/manifest.json: frame size and per-animation sheet and frame durations;
- docs/images/sprites-preview.png: every animation's frames on a light and a dark background.
Review aids (gitignored): build/preview/<command>.png (4x contact sheet) and
build/preview/<command>-<phase>.gif.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from art.raster import SIZE, Anim  # noqa: E402

COMMANDS = [
    "commit",
    "push",
    "pull",
    "fetch",
    "add",
    "restore",
    "init",
    "clone",
    "branch",
    "checkout",
    "stash",
    "blame",
    "reset",
]
PHASES = ["loop", "success", "fail"]

# Limits the Luau loader also enforces (fx/sprites.luau).
LIMITS = {
    "loop": {"frames": (2, 12), "frame_ms": (60, 1000), "total_ms": (300, 2400)},
    "success": {"frames": (4, 20), "frame_ms": (40, 1500), "total_ms": (500, 2600)},
    "fail": {"frames": (4, 20), "frame_ms": (40, 1500), "total_ms": (500, 2600)},
}

LIGHT = (246, 244, 240, 255)
DARK = (30, 30, 40, 255)

SPRITES = ROOT / "assets" / "sprites"
PREVIEW = ROOT / "build" / "preview"


def validate(command: str, phase: str, a: Anim) -> list[str]:
    errors = []
    lim = LIMITS[phase]
    n = len(a.frames)
    if not lim["frames"][0] <= n <= lim["frames"][1]:
        errors.append(f"{command}/{phase}: {n} frames, want {lim['frames'][0]}-{lim['frames'][1]}")
    for i, (f, d) in enumerate(zip(a.frames, a.durations_ms)):
        if (f.width, f.height) != (SIZE, SIZE):
            errors.append(f"{command}/{phase} frame {i}: {f.width}x{f.height}, want {SIZE}x{SIZE}")
        if f.opaque_count() == 0:
            errors.append(f"{command}/{phase} frame {i}: empty")
        if not lim["frame_ms"][0] <= d <= lim["frame_ms"][1]:
            errors.append(f"{command}/{phase} frame {i}: {d} ms, want {lim['frame_ms'][0]}-{lim['frame_ms'][1]}")
    total = sum(a.durations_ms)
    if not lim["total_ms"][0] <= total <= lim["total_ms"][1]:
        errors.append(f"{command}/{phase}: {total} ms total, want {lim['total_ms'][0]}-{lim['total_ms'][1]}")
    return errors


def strip(a: Anim) -> Image.Image:
    img = Image.new("RGBA", (SIZE * len(a.frames), SIZE), (0, 0, 0, 0))
    for i, f in enumerate(a.frames):
        img.paste(f.image(), (i * SIZE, 0))
    return img


def on(bg: tuple[int, int, int, int], img: Image.Image) -> Image.Image:
    base = Image.new("RGBA", img.size, bg)
    base.alpha_composite(img)
    return base


def contact(anims: dict[str, Anim], scale: int) -> Image.Image:
    """Rows: phase x (light, dark); columns: frames. 2 px gutters."""
    cols = max(len(a.frames) for a in anims.values())
    cell = SIZE * scale + 2
    img = Image.new("RGBA", (cols * cell + 2, len(anims) * 2 * cell + 2), (128, 128, 128, 255))
    row = 0
    for phase in PHASES:
        a = anims[phase]
        for bg in (LIGHT, DARK):
            for i, f in enumerate(a.frames):
                tile = on(bg, f.image()).resize((SIZE * scale, SIZE * scale), Image.NEAREST)
                img.paste(tile, (2 + i * cell, 2 + row * cell))
            row += 1
    return img


def gif(a: Anim, path: Path, scale: int, bg: tuple[int, int, int, int]) -> None:
    frames = [on(bg, f.image()).resize((SIZE * scale, SIZE * scale), Image.NEAREST).convert("P") for f in a.frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=a.durations_ms, loop=0, disposal=2)


def load(command: str) -> dict[str, Anim]:
    module = importlib.import_module(f"art.scenes.{command}")
    anims = module.build()
    if sorted(anims) != sorted(PHASES):
        raise SystemExit(f"{command}: build() returned {sorted(anims)}, want {PHASES}")
    return anims


def preview_sheet(built: dict[str, dict[str, Anim]]) -> Image.Image:
    """docs preview: one row per command and phase, light then dark half, at 2x."""
    scale = 2
    cell = SIZE * scale
    cols = max(len(built[c][p].frames) for c in COMMANDS for p in PHASES)
    rows = len(COMMANDS) * len(PHASES)
    sheet = Image.new("RGBA", (cols * cell * 2 + 8, rows * cell), (0, 0, 0, 0))
    for r, (command, phase) in enumerate((c, p) for c in COMMANDS for p in PHASES):
        a = built[command][phase]
        for half, bg in enumerate((LIGHT, DARK)):
            band = Image.new("RGBA", (cols * cell, cell), bg)
            for i, f in enumerate(a.frames):
                band.alpha_composite(f.image().resize((cell, cell), Image.NEAREST), (i * cell, 0))
            sheet.paste(band, (half * (cols * cell + 8), r * cell))
    return sheet


def manifest_text(built: dict[str, dict[str, Anim]]) -> str:
    manifest = {
        "schema": 1,
        "frame_w": SIZE,
        "frame_h": SIZE,
        "commands": {
            command: {
                phase: {"sheet": f"{command}-{phase}.png", "durations_ms": built[command][phase].durations_ms}
                for phase in PHASES
            }
            for command in COMMANDS
        },
    }
    return json.dumps(manifest, indent=2) + "\n"


def stale(path: Path, want: Image.Image | str) -> bool:
    """Whether the committed file differs from `want`: pixels for images (PNG bytes vary with the
    platform's zlib), exact text otherwise."""
    if not path.exists():
        return True
    if isinstance(want, str):
        return path.read_text() != want
    with Image.open(path) as have:
        have_rgba = have.convert("RGBA")
        return have_rgba.size != want.size or have_rgba.tobytes() != want.convert("RGBA").tobytes()


def main(argv: list[str]) -> int:
    args = argv[1:]
    check = "--check" in args
    only = [a for a in args if a != "--check"]
    unknown = [c for c in only if c not in COMMANDS]
    if unknown:
        print(f"unknown commands: {unknown}", file=sys.stderr)
        return 2
    if check and only:
        print("--check always checks every command", file=sys.stderr)
        return 2
    commands = only or COMMANDS

    built: dict[str, dict[str, Anim]] = {}
    errors: list[str] = []
    for command in commands:
        anims = load(command)
        for phase in PHASES:
            errors += validate(command, phase, anims[phase])
        built[command] = anims
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    outputs: dict[Path, Image.Image | str] = {}
    for command, anims in built.items():
        for phase in PHASES:
            outputs[SPRITES / f"{command}-{phase}.png"] = strip(anims[phase])
    if not only:
        outputs[SPRITES / "manifest.json"] = manifest_text(built)
        outputs[ROOT / "docs" / "images" / "sprites-preview.png"] = preview_sheet(built)

    if check:
        changed = [str(p.relative_to(ROOT)) for p, want in outputs.items() if stale(p, want)]
        if changed:
            print("out of date (run uv run tools/build_sprites.py and commit):", file=sys.stderr)
            print("\n".join(f"  {c}" for c in changed), file=sys.stderr)
            return 1
        print(f"sprites up to date ({len(outputs)} files)")
        return 0

    PREVIEW.mkdir(parents=True, exist_ok=True)
    for path, want in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(want, str):
            path.write_text(want)
        elif stale(path, want):
            # Rewrite only real changes, so a rebuild on another platform leaves the files alone.
            want.save(path, optimize=False)
    for command, anims in built.items():
        for phase in PHASES:
            gif(anims[phase], PREVIEW / f"{command}-{phase}.gif", 6, DARK)
        contact(anims, 4).save(PREVIEW / f"{command}.png")
        print(f"built {command}: " + ", ".join(f"{p} {len(anims[p].frames)}f/{sum(anims[p].durations_ms)}ms" for p in PHASES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
