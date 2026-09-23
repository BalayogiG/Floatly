#!/usr/bin/env bash
# Build Floatly and install it as a COSMIC panel applet for the current user.
set -euo pipefail
cd "$(dirname "$0")"

APP_ID="io.github.balayogi.Floatly"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
PYTHON_WIDGET_DIR="$(cd "$(dirname "$0")/../python-widget" && pwd)"

echo "Building floatly-applet (release)..."
cargo build --release

mkdir -p "$BIN_DIR" "$APPS_DIR"
install -m755 target/release/floatly-applet "$BIN_DIR/floatly-applet"

# clicking the panel icon opens Settings by launching this; it must be on
# PATH for the *user's shell*, but cosmic-panel spawns applets with a
# minimal PATH, so the applet invokes it via $HOME/.local/bin directly
cat > "$BIN_DIR/floatly-settings" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$PYTHON_WIDGET_DIR"
export QT_QPA_PLATFORM=xcb
exec uv run floatly-settings "\$@"
EOF
chmod +x "$BIN_DIR/floatly-settings"

cat > "$APPS_DIR/$APP_ID.desktop" <<EOF
[Desktop Entry]
Name=Floatly
Comment=A tiny charm that hangs and swings in the panel
Type=Application
Exec=$BIN_DIR/floatly-applet
Terminal=false
Categories=COSMIC;
Keywords=COSMIC;Applet;Charm;Fun;
Icon=starred-symbolic
NoDisplay=true
X-CosmicApplet=true
X-CosmicShrinkable=true
EOF

command -v update-desktop-database >/dev/null && update-desktop-database "$APPS_DIR" || true

echo
echo "Installed. Now add it to a panel:"
echo "  Settings -> Desktop -> Panel -> (choose panel) -> Configure applets -> Floatly"
echo
echo "Or restart cosmic-panel after it's added via the config to pick it up immediately:"
echo "  pkill -x cosmic-panel"
echo
echo "The panel icon opens Settings; the actual hanging charm on your desktop is a"
echo "separate process. Start it with: ../python-widget/run.sh"
