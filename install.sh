#!/usr/bin/env bash
#
# magnify installer - puts the `magnify` command on your PATH so you can
# run it from anywhere.
#
# Usage:
#   ./install.sh            install for the current user (~/.local, no sudo)
#   ./install.sh --user     same as above (explicit)
#   ./install.sh --system   install system-wide (needs sudo)
#   ./install.sh --uninstall  remove a previous install
#   ./install.sh --check    only report what is already installed
#
# magnify has zero runtime dependencies - Python 3.10+ standard library
# only. Nothing is downloaded except this project itself.
#
set -euo pipefail

PROJECT_NAME="magnify"
DIST_NAME="magnify-osint"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- pretty output ----------------------------------------------------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
  RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'; CYN=$'\033[36m'
else
  B=""; D=""; R=""; RED=""; GRN=""; YEL=""; CYN=""
fi
ok()   { printf '  %s✔%s %s\n' "$GRN" "$R" "$*"; }
warn() { printf '  %s!%s %s\n' "$YEL" "$R" "$*"; }
err()  { printf '  %s✖%s %s\n' "$RED" "$R" "$*" >&2; }
step() { printf '%s%s%s\n' "$B$CYN" "$*" "$R"; }

MODE="user"
ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --user)      MODE="user" ;;
    --system)    MODE="system" ;;
    --uninstall) ACTION="uninstall" ;;
    --check)     ACTION="check" ;;
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      err "unknown option: $arg (try --help)"
      exit 2 ;;
  esac
done

# ---- locate a usable python ------------------------------------------
find_python() {
  local cand
  for cand in python3 python3.13 python3.12 python3.11 python3.10 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
        command -v "$cand"
        return 0
      fi
    fi
  done
  return 1
}

echo
printf '%s\n' "${B}magnify installer${R}"
printf '%s\n' "${D}interactive OSINT orchestrator  |  authorized use only${R}"
echo

# ---- already installed? ----------------------------------------------
if command -v "$PROJECT_NAME" >/dev/null 2>&1; then
  EXISTING="$(command -v "$PROJECT_NAME")"
  EXISTING_VER="$("$PROJECT_NAME" --version 2>/dev/null | head -1 || true)"
  ok "already installed: $EXISTING ${EXISTING_VER:+($EXISTING_VER)}"
  if [ "$ACTION" = "install" ]; then
    warn "re-running will update it in place"
  fi
else
  if [ "$ACTION" = "check" ]; then
    warn "not currently on PATH"
  fi
fi

if [ "$ACTION" = "check" ]; then
  echo
  step "python interpreters found"
  if PY="$(find_python)"; then ok "$PY ($("$PY" --version 2>&1))"; else err "no Python 3.10+ found"; fi
  echo
  if command -v pipx >/dev/null 2>&1; then ok "pipx available: $(command -v pipx)"; else warn "pipx not installed (optional)"; fi
  echo
  exit 0
fi

# ---- uninstall --------------------------------------------------------
if [ "$ACTION" = "uninstall" ]; then
  step "removing magnify"
  removed=0
  if command -v pipx >/dev/null 2>&1 && pipx list --short 2>/dev/null | grep -q "$DIST_NAME"; then
    pipx uninstall "$DIST_NAME" && removed=1
  fi
  if PY="$(find_python)"; then
    "$PY" -m pip uninstall -y "$DIST_NAME" >/dev/null 2>&1 && removed=1 || true
  fi
  # drop any wrapper we wrote
  for w in "$HOME/.local/bin/$PROJECT_NAME" "/usr/local/bin/$PROJECT_NAME"; do
    if [ -f "$w" ] && grep -q "magnify installer wrapper" "$w" 2>/dev/null; then
      rm -f "$w" && ok "removed wrapper $w" && removed=1
    fi
  done
  # clean caches so a stale copy cannot re-appear
  rm -rf "$SRC_DIR/build" "$SRC_DIR"/*.egg-info 2>/dev/null || true
  [ "$removed" = 1 ] && ok "uninstalled" || warn "nothing to remove"
  echo
  exit 0
fi

# ---- pick an install strategy ----------------------------------------
PY="$(find_python)" || {
  err "Python 3.10 or newer is required and was not found."
  echo "  install it, then re-run:  ${B}./install.sh${R}" >&2
  exit 1
}

pip_usable() {
  "$PY" -m pip --version >/dev/null 2>&1
}

install_with_pipx() {
  step "installing with pipx (isolated, recommended)"
  pipx install --force "$SRC_DIR"
}

install_with_pip() {
  local pips=()
  if [ "$MODE" = "system" ]; then
    pips=(sudo "$PY" -m pip install --force-reinstall)
  else
    # Prefer a normal user install. If the distro blocks it (PEP 668
    # "externally managed environment"), retry with --user --break-system-packages.
    pips=("$PY" -m pip install --user --force-reinstall)
  fi
  step "installing with pip"
  if "${pips[@]}" "$SRC_DIR"; then
    return 0
  fi
  if [ "$MODE" = "user" ]; then
    warn "pip refused (externally managed env?) - retrying as user install"
    "$PY" -m pip install --user --break-system-packages --force-reinstall "$SRC_DIR" && return 0
  fi
  return 1
}

write_wrapper() {
  # Last-resort fallback: a tiny launcher on PATH that runs the source
  # tree directly. Used when pip/pipx are unavailable entirely.
  local bindir="$HOME/.local/bin"
  [ "$MODE" = "system" ] && bindir="/usr/local/bin"
  mkdir -p "$bindir" 2>/dev/null || sudo mkdir -p "$bindir"
  local target="$bindir/$PROJECT_NAME"
  step "writing launcher to $target"
  local sudo=""
  [ "$MODE" = "system" ] && sudo="sudo"
  $sudo tee "$target" >/dev/null <<EOF
#!/usr/bin/env bash
# magnify installer wrapper - runs from the source tree directly
exec "$PY" -m magnify "\$@"
EOF
  $sudo chmod +x "$target"
  ok "wrapper installed"
}

if command -v pipx >/dev/null 2>&1 && [ "$MODE" = "user" ]; then
  install_with_pipx
elif pip_usable; then
  install_with_pip
else
  warn "pip is not available for $PY"
  write_wrapper
fi

# ---- make sure the install dir is on PATH ----------------------------
BIN_DIR="$("$PY" -c 'import sysconfig; print(sysconfig.get_path("scripts", scheme="posix_user" if "'"$MODE"'"=="user" else "posix_prefix"))' 2>/dev/null || echo "$HOME/.local/bin")"
if ! printf '%s' ":$PATH:" | grep -q ":$BIN_DIR:"; then
  warn "$BIN_DIR is not on your PATH"
  echo "     add this to your shell rc (~/.bashrc or ~/.zshrc):"
  echo "       ${B}export PATH=\"$BIN_DIR:\$PATH\"${R}"
fi

# ---- verify -----------------------------------------------------------
echo
step "verifying"
hash -r 2>/dev/null || true
if command -v "$PROJECT_NAME" >/dev/null 2>&1; then
  ok "found at $(command -v "$PROJECT_NAME")"
  "$PROJECT_NAME" --version 2>/dev/null | head -1 | sed "s/^/     /" || true
  "$PROJECT_NAME" --status --no-color 2>/dev/null | sed -n '1,12p' || true
  echo
  ok "done - run ${B}magnify${R} from anywhere"
else
  warn "magnify was installed but is not on PATH yet"
  echo "     open a new shell, or run:  export PATH=\"$BIN_DIR:\$PATH\""
fi

cat <<EOF

${D}next steps:${R}
  ${B}magnify${R}                 start the interactive wizard
  ${B}magnify --status${R}        see which backends are connected
  ${B}magnify --help-backends${R} how to connect SearXNG / SerpAPI / an LLM

${D}authorized use only.${R}
EOF
