#!/usr/bin/env bash
# Every check CI runs: formatting, lint, types, unit tests, and that the committed sprites match
# a fresh build. Prints a summary; exits 1 if anything failed. Run scripts/setup.sh first.
set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools/bin:$PATH"

sources=(window.luau fx tests)
failed=()

run() {
  local label="$1"; shift
  echo "--- $label"
  "$@" || failed+=("$label")
}

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "check: $1 not found; run scripts/setup.sh" >&2; exit 2; }
}
need stylua; need selene; need luau-lsp; need lune; need uv
[ -f types/tern.d.luau ] || { echo "check: types/tern.d.luau missing; run scripts/setup.sh" >&2; exit 2; }

typecheck() {
  # luau-lsp's definition parser lacks the `userdata` type the SDK file uses.
  { echo "type userdata = any"; cat types/tern.d.luau; } > .tools/tern.d.luau
  luau-lsp analyze --platform=standard --definitions=@tern=.tools/tern.d.luau \
    window.luau $(find fx -name '*.luau' | sort)
}

sprites() {
  uv run tools/build_sprites.py >/dev/null || return 1
  if ! git diff --quiet -- assets/sprites docs/images/sprites-preview.png; then
    echo "rebuilding changed committed sprites:"
    git diff --stat -- assets/sprites docs/images/sprites-preview.png
    return 1
  fi
}

run format stylua --check "${sources[@]}"
run lint selene --display-style=quiet "${sources[@]}"
run types typecheck
run tests lune run tests/run.luau
run sprites sprites

echo
if [ "${#failed[@]}" -gt 0 ]; then
  echo "check: FAILED: ${failed[*]}"
  exit 1
fi
echo "check: all passed"
