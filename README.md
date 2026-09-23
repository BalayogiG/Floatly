# Floatly

A tiny charm that hangs from the top of your screen on a rope and gently
swings — a small delight, right on your Linux desktop.

Two parts work together:

## `python-widget/` — the hanging charm itself

A transparent, always-on-top PySide6 window that hangs a single charm from
the true top edge of the screen. Drag it to reposition horizontally, click
it for a little push. See `python-widget/README.md`.

## `applet/` — COSMIC panel control icon

A native COSMIC panel applet (Rust + `libcosmic`): a small swinging charm
icon in the panel that, when clicked, opens the **Settings** dialog for the
widget above — horizontal position, rope length, and charm image, all with
live sliders. A panel applet can't draw a rope reaching down onto the
desktop (it's confined to a small bar icon), which is why the two are
separate processes talking through `~/.config/floatly/config.json`. See
`applet/README.md`.

If you're not on COSMIC, the widget still works standalone — run its
Settings dialog directly with `uv run floatly-settings` from
`python-widget/`, no applet needed.
