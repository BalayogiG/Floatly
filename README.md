# Floatly

A tiny charm that hangs from the top of your screen on a rope and gently
swings — a small delight, right on your Linux desktop.

[Watch the demo video](docs/swing-demo.mp4)

It sways on its own like a wind chime (a damped pendulum with the occasional
random "air current"), reacts to a click with a little push, and can be
dragged left/right along the top edge. Everywhere except the rope and charm
itself is click-through, so it never gets in the way of whatever's under it.

## Requirements

- Linux with an X11 or XWayland-capable desktop (the widget runs as an
  XWayland client even under a Wayland compositor — see
  [`python-widget/README.md`](python-widget/README.md#why-qt_qpa_platformxcb)
  for why)
- [`uv`](https://docs.astral.sh/uv/) for the widget
- Rust/`cargo` for the optional COSMIC panel applet

## Quick start

```sh
cd python-widget
./run.sh
```

That's the whole widget: it installs its own dependencies into a local
`.venv` on first run and hangs the charm from the top of your primary
screen.

## Project layout

This repo has two parts that work together:

| Part | What it is | Docs |
| --- | --- | --- |
| [`python-widget/`](python-widget) | The hanging charm itself — a transparent, always-on-top PySide6 window | [`python-widget/README.md`](python-widget/README.md) |
| [`applet/`](applet) | A COSMIC panel icon (Rust + `libcosmic`) that opens the widget's Settings dialog | [`applet/README.md`](applet/README.md) |

The applet is optional: it's just a convenient panel launcher for the
widget's Settings dialog on the COSMIC desktop. A panel applet can't draw a
rope reaching down onto the desktop itself (it's confined to a small bar
icon), which is why the two are separate processes, talking to each other
through `~/.config/floatly/config.json`.

If you're not on COSMIC, the widget still works completely standalone — run
its Settings dialog directly with `uv run floatly-settings` from
`python-widget/`, no applet needed.

## Configuring

Settings (rope position, rope length, charm image, click-through) are edited
live via:

```sh
cd python-widget
uv run floatly-settings
```

Changes are written to `~/.config/floatly/config.json`, which the running
widget watches and picks up instantly. See
[`python-widget/README.md`](python-widget/README.md#settings) for details.

## License

Not yet licensed — all rights reserved for now.
