# shellcheck shell=bash
# Source this to point the `tern` CLI, daemon and windows at a throwaway config instead of
# yours:   SB=/tmp/gitfx-dev source scripts/sandbox.sh
# A shell inside a Tern pane inherits variables naming your real daemon and pane, so they are
# cleared too. Refuses (returns 1) if Tern's plugin directory is not inside the sandbox.

export SB="${SB:-/tmp/tern-git-fx-sandbox}"
mkdir -p "$SB/config" "$SB/logs" || return 1
export TERN_CONFIG_DIR="$SB/config"
export TERN_DAEMON_SOCKET="$SB/daemon.sock"
export STENCIL_LOG_DIR="$SB/logs"
export STENCIL_LOG="warn,tern::plugin=debug"
for v in TERN_PANE TERN_PANE_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET TERN_BLOB_DIR \
  TERN_COMPLETE TERN_LENSES TERN_IDENTITY; do
  unset "$v"
done

case "$(tern plugin dir 2>/dev/null)" in
  "$SB"/* | /private"$SB"/*) echo "sandbox: $SB" ;;
  *) echo "sandbox: refusing, Tern's plugin dir is outside $SB" >&2; return 1 ;;
esac
