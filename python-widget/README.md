# Floatly

A tiny always-on-top charm that hangs from the very top edge of your screen
on a rope, and gently swings, like a single wind chime for your desktop.

## Run

```sh
./run.sh
```

This installs dependencies into a local `.venv` (via `uv`) on first run and
launches the charm centered along the top of your primary screen.

It sways on its own (a lightly damped pendulum with the occasional random
"air current"). Click it to give it a push. Drag it left/right to reposition
it horizontally — the rope always stays anchored to the top of the screen.

Only the rope and charm itself are clickable — everywhere else in that
column is click-through, so it never blocks whatever's underneath. This
uses the X11 Shape extension's *input* shape (see `src/floatly/xshape.py`)
rather than Qt's own window masking, which clips visible pixels too and
would turn the transparent background solid black.

## Settings

Open Settings with:

```sh
uv run floatly-settings
```

(On COSMIC, the companion panel applet in `../applet` does this for you —
click its icon in the panel.)

The dialog has sliders for:

- **Horizontal position** — where along the top edge the rope hangs
- **Rope length**

plus a **Charm image** picker (any image file, or revert to the default
drawn star), a checkbox to disable interaction entirely (the rope stops
reacting to clicks too, beyond the click-through it already has by
default), and a **Quit Floatly** button.

Settings apply live: dragging a slider immediately moves the charm, even
though Settings runs as its own process — it writes
`~/.config/floatly/config.json` on every change, and the running widget
watches that file and picks up edits instantly. Dragging the charm directly
also updates and saves its horizontal position.

## Install as an app-menu entry / autostart

```sh
cp floatly.desktop ~/.local/share/applications/
# to also launch at login:
cp floatly.desktop ~/.config/autostart/
```

## Why `QT_QPA_PLATFORM=xcb`

Floatly runs the Qt app through XWayland instead of native Wayland. Plain
Wayland compositors (including COSMIC) don't let a client position its own
window or reliably stay pinned above other windows — that's intentionally
disallowed by the protocol. Running as an X11 client via XWayland (the same
trick tools like `conky` and `plank` use) gets that control back.
