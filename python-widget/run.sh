#!/usr/bin/env bash
# Launch Floatly. Forces the xcb (XWayland) Qt backend, since plain Wayland
# doesn't let apps position themselves or stay pinned above other windows.
set -euo pipefail
cd "$(dirname "$0")"
export QT_QPA_PLATFORM=xcb
exec uv run python -m floatly
