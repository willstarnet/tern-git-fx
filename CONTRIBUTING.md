# Contributing

Thanks for helping with tern-git-fx. Small, tested pull requests are the easiest to review.
Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems
privately as [SECURITY.md](SECURITY.md) describes, never in a public issue; questions go where
[SUPPORT.md](SUPPORT.md) says.

## Setup

You need [Tern](https://docs.stencil.so/tern/) 0.8.3 or later to run the plugin, and
[uv](https://docs.astral.sh/uv/) for the sprite build (`brew install uv`). Everything else is
pinned and installed into `.tools/` (gitignored) by one script, on macOS arm64 and Linux x86_64:

```sh
bash scripts/setup.sh   # lune, stylua, selene, luau-lsp; types/tern.d.luau
bash scripts/check.sh   # what CI runs
```

`setup.sh` writes the Tern API types with `tern plugin types` when Tern is installed, else
downloads the published SDK's. Re-run it after upgrading Tern.

## Checks

`scripts/check.sh` runs, in order, and exits 1 if any fail:

| Step | Command |
|---|---|
| format | `stylua --check window.luau fx tests` (fix with `stylua window.luau fx tests`) |
| lint | `selene window.luau fx tests` |
| types | `luau-lsp analyze` of `window.luau` and `fx/` against the Tern types |
| tests | `lune run tests/run.luau` (add a filter argument to run matching cases only) |
| sprites | `uv run tools/build_sprites.py --check`: fails if a committed sheet's pixels, the manifest or the preview are out of date |

## Code layout

- `window.luau` is the only file that touches the `tern` global: Tern events, palette commands,
  config file, toggle.
- `fx/` is pure and takes its I/O as injected functions, so it runs under Lune without Tern.
  `classify` reads command lines, `config` validates `config.json`, `player` is the per-pane
  state machine, `css` writes the overlay sheet, `sprites` loads and validates the sheets.
- `tools/art/` draws the sprites in code; [docs/sprites.md](docs/sprites.md) covers the scene
  format and the build.

## Tests

- Specs live in `tests/unit/<module>_spec.luau` and use `tests/lib/test.luau`
  (`describe`, `it`, `expect(x).toBe/toEqual/toContain/...`).
- Write the failing spec first. A bug fix starts with a spec that reproduces the bug.
- Assert what a user or Tern would observe: the command a line maps to, the sheet installed,
  the warning shown. Timers in `player_spec` are driven by a fake clock; keep them that way.
- Window behavior (the overlay in a real pane, palette commands, toasts) has no automated test.
  Check it in a sandboxed Tern and say how in the pull request.

## Trying changes in Tern

Never point a development build at your real Tern. `scripts/sandbox.sh` moves the CLI's config,
daemon and logs into `$SB` and refuses to continue otherwise:

```sh
export SB=/tmp/gitfx-dev
source scripts/sandbox.sh
mkdir -p "$SB/pkg" && cp -R plugin.toml window.luau fx assets "$SB/pkg/"
tern plugin link "$SB/pkg"
tern --control "$SB/win.sock" ~/some/repo &    # a sandboxed window
tern ctl --control "$SB/win.sock" run '"git status"'
```

Link a copy, not the checkout: Tern reloads a linked plugin whenever a file in its folder
changes, and builds and logs write there. Copy again to pick up an edit. Plugin log lines land in
`$SB/logs`. Quit the window with `tern ctl --control "$SB/win.sock" quit`; the idle daemon exits
by itself.

## Sprites

Art changes are code changes: edit `tools/art/scenes/<command>.py`, run
`uv run tools/build_sprites.py <command>` and look at `build/preview/<command>.png` on both
backgrounds, then run the full `uv run tools/build_sprites.py` and commit the scene, the sheets,
`manifest.json` and `docs/images/sprites-preview.png` together. Contributed art must be your
own work, drawn in code, and is licensed MIT like the rest of the repository.

## Guarantees reviewers hold the line on

- The command line is reduced to a command name inside the event handler and never stored,
  logged or sent.
- No network, no processes, no clipboard, no writes to Tern's settings, nothing typed into or
  read from a terminal.
- The overlay is `pointer-events: none` and never changes terminal content, focus or layout.
- Every value interpolated into CSS is validated (`fx/css.luau`).

## Pull requests

1. For anything bigger than a bug fix, open an issue first so the approach can be agreed on.
2. Branch from `main`; one change per pull request.
3. Use [Conventional Commits](https://www.conventionalcommits.org/): `feat: ...`, `fix: ...`,
   `docs: ...`, `test: ...`, `build: ...`, `chore: ...`, optionally scoped (`fix(classify): ...`).
4. Add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for anything a user would
   notice, and update the README when config keys, commands or aliases change.
5. `bash scripts/check.sh` passes and CI is green on macOS and Linux.
