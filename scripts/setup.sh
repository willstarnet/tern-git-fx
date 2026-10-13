#!/usr/bin/env bash
# Installs the pinned dev tools into .tools/bin and writes types/tern.d.luau.
# Safe to re-run: a tool already at its pinned version is skipped.
set -euo pipefail
cd "$(dirname "$0")/.."

LUNE=0.11.0
STYLUA=2.6.0
SELENE=0.32.0
LUAU_LSP=1.70.1

platform="$(uname -s)/$(uname -m)"
case "$platform" in
  Darwin/arm64)
    lune_asset="lune-$LUNE-macos-aarch64.zip"; stylua_asset="stylua-macos-aarch64.zip"
    selene_asset="selene-$SELENE-macos.zip"; lsp_asset="luau-lsp-macos.zip" ;;
  Linux/x86_64)
    lune_asset="lune-$LUNE-linux-x86_64.zip"; stylua_asset="stylua-linux-x86_64.zip"
    selene_asset="selene-$SELENE-linux.zip"; lsp_asset="luau-lsp-linux-x86_64.zip" ;;
  *) echo "setup: no pinned tool builds for $platform" >&2; exit 1 ;;
esac

bin=.tools/bin
mkdir -p "$bin"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# install NAME VERSION URL: unzip URL and put its NAME binary in .tools/bin.
install_tool() {
  local name="$1" version="$2" url="$3"
  if [ "$(cat "$bin/.$name.version" 2>/dev/null)" = "$version" ] && [ -x "$bin/$name" ]; then
    return
  fi
  curl -fsSL "$url" -o "$work/$name.zip"
  unzip -q -o "$work/$name.zip" -d "$work/$name"
  install -m 0755 "$work/$name/$name" "$bin/$name"
  echo "$version" > "$bin/.$name.version"
  echo "setup: $name $version"
}

install_tool lune "$LUNE" "https://github.com/lune-org/lune/releases/download/v$LUNE/$lune_asset"
install_tool stylua "$STYLUA" "https://github.com/JohnnyMorganz/StyLua/releases/download/v$STYLUA/$stylua_asset"
install_tool selene "$SELENE" "https://github.com/Kampfkarren/selene/releases/download/$SELENE/$selene_asset"
install_tool luau-lsp "$LUAU_LSP" "https://github.com/JohnnyMorganz/luau-lsp/releases/download/$LUAU_LSP/$lsp_asset"

# Tern's plugin API types: from the installed Tern when there is one (matches what you run),
# else the published SDK.
mkdir -p types
if command -v tern >/dev/null 2>&1 && tern plugin types types >/dev/null 2>&1; then
  echo "setup: types/tern.d.luau from $(tern --version)"
else
  curl -fsSL "https://raw.githubusercontent.com/stencil-hq/tern-sdk/${TERN_SDK_REF:-main}/plugins/tern.d.luau" \
    -o types/tern.d.luau
  echo "setup: types/tern.d.luau from stencil-hq/tern-sdk@${TERN_SDK_REF:-main}"
fi
