# Floatly (COSMIC panel applet)

A small swinging charm icon that lives in the COSMIC panel. It's the control
point for the actual charm-on-a-rope that hangs from the top of your desktop
(that part is the separate `../python-widget` process — a panel applet can't
draw a rope reaching down onto the desktop, only a small icon in the bar).
Click the panel icon to open **Settings**, where you set the rope's
horizontal position, its length, and the charm image.

## Install

```sh
./install.sh
```

This builds a release binary, installs it to `~/.local/bin/floatly-applet`,
drops a `.desktop` entry at
`~/.local/share/applications/io.github.balayogi.Floatly.desktop` with
`X-CosmicApplet=true` so COSMIC Settings recognizes it as an applet, and
installs a `~/.local/bin/floatly-settings` launcher script the panel icon
uses to open the Settings dialog (see `../python-widget`).

Then add the applet to a panel: **Settings → Desktop → Panel → (pick a
panel) → Configure applets → Floatly**. Separately, start the actual hanging
charm with `../python-widget/run.sh` (or set it to autostart — see that
README).

If you'd rather skip the Settings UI, you can add `"io.github.balayogi.Floatly"`
directly to the applet list in
`~/.config/cosmic/com.system76.CosmicPanel.Panel/v1/plugins_wings` (or
`plugins_center`), then run `pkill -x cosmic-panel` to have it respawn and
pick up the change. Back up that file first — it's hand-edited RON with no
schema validation.

## Uninstall

Remove it from the panel via Settings, then:

```sh
rm ~/.local/bin/floatly-applet ~/.local/bin/floatly-settings
rm ~/.local/share/applications/io.github.balayogi.Floatly.desktop
```

## Development

```sh
cargo build          # debug build
cargo run             # runs it as a normal window, not embedded in a panel —
                       # useful for quick iteration, though sizing/theme come
                       # from panel context so it looks best actually panelled
```

The physics and drawing live in `src/charm.rs` (a damped pendulum + a
5-point star drawn on an `iced` `Canvas`); `src/window.rs` wires it up as a
`cosmic::Application` using the `applet` feature of `libcosmic`, and its
click handler spawns `$HOME/.local/bin/floatly-settings` (an absolute path,
since cosmic-panel spawns applets with a PATH that excludes `~/.local/bin`).
