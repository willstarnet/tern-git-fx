# Sprites

Every animation is drawn by Python code in `tools/art/scenes/<command>.py`; nothing is
hand-painted. `tools/build_sprites.py` turns the scenes into the bundled sheets, so the art can be
changed, reviewed and rebuilt like any other source. The pixels are deterministic for the pinned
Pillow; `--check` (run by `check.sh`) fails if a committed sheet's pixels, the manifest or the
preview are out of date. PNG bytes differ between platforms' zlib builds, so files are compared
and rewritten by decoded pixels only.

```sh
uv run tools/build_sprites.py              # every command: sheets, manifest.json, docs preview
uv run tools/build_sprites.py push commit  # only these: sheets and build/preview (no manifest)
uv run tools/build_sprites.py --check      # exit 1 if a committed output is out of date
```

Review aids (gitignored): `build/preview/<command>.png`, a 4x contact sheet (rows: loop,
success, fail, each on a light then a dark background) and `build/preview/<command>-<phase>.gif`.

## Phases

| phase | plays | limits |
|---|---|---|
| `loop` | while the command runs, repeating | 2-12 frames, 60-1000 ms each, 300-2400 ms total; last frame flows into the first |
| `success` | once on exit status 0; the last frame is held for `hold_ms` | 4-20 frames, 40-1500 ms each, 500-2600 ms total; ends with `check_badge` |
| `fail` | once on any other status, held the same way | same limits; ends with `x_badge` |

The build and the Luau loader (`fx/sprites.luau`) enforce the same limits; the loader also
checks each PNG's size against its frame count.

## Scene modules

Each module exports `build() -> {"loop": Anim, "success": Anim, "fail": Anim}`. Frames are
32x32 index-color canvases (`tools/art/raster.py`) drawn with the shared palette
(`tools/art/palette.py`, Sweetie 16 plus three browns; one character per color so sprites can be
written as ASCII rows). `tools/art/effects.py` holds the shared vocabulary: the check and cross
badges (top-right corner, popped in over the last frames), sparkles and smoke.

Conventions:

- One subject, roughly centered, standing on a ground line near y=27-30; the top-right corner
  stays clear while a badge shows.
- Bright fills with an ink outline (`Frame.outline()`, called last) so the sprite reads on light
  and dark themes.
- Deterministic: seed any jitter with `random.Random("<command>")`.
- Loops are gentle: they can run for minutes (an editor open for `git commit`, a pager for
  `git blame`).

`tools/art/scenes/push.py` is the reference scene.

## Manifest

`assets/sprites/manifest.json`, written by the full build:

```json
{
  "schema": 1,
  "frame_w": 32,
  "frame_h": 32,
  "commands": {
    "push": {
      "loop": { "sheet": "push-loop.png", "durations_ms": [110, 110, 110, 110, 110, 110] },
      "success": { "sheet": "push-success.png", "durations_ms": [...] },
      "fail": { "sheet": "push-fail.png", "durations_ms": [...] }
    }
  }
}
```

Each sheet is a horizontal strip of `frame_w` x `frame_h` frames.
