use std::time::{Duration, SystemTime, UNIX_EPOCH};

use cosmic::app::{Core, Task};
use cosmic::iced::widget::canvas;
use cosmic::iced::{window::Id, Length, Subscription};
use cosmic::Element;

use crate::charm::{CharmCanvas, Pendulum};

const ID: &str = "io.github.balayogi.Floatly";
const TICK: Duration = Duration::from_millis(33);

pub struct Window {
    core: Core,
    pendulum: Pendulum,
    seed: u32,
}

impl Default for Window {
    fn default() -> Self {
        // seed the tiny PRNG from the clock so gusts differ run to run
        let seed = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.subsec_nanos())
            .unwrap_or(0xC0FF_EE)
            .max(1);

        Self {
            core: Core::default(),
            pendulum: Pendulum::default(),
            seed,
        }
    }
}

#[derive(Clone, Debug)]
pub enum Message {
    Tick,
    OpenSettings,
    Surface(cosmic::surface::Action<Message>),
}

impl cosmic::Application for Window {
    type Executor = cosmic::SingleThreadExecutor;
    type Flags = ();
    type Message = Message;
    const APP_ID: &'static str = ID;

    fn core(&self) -> &Core {
        &self.core
    }

    fn core_mut(&mut self) -> &mut Core {
        &mut self.core
    }

    fn init(core: Core, _flags: Self::Flags) -> (Self, Task<Message>) {
        let window = Window {
            core,
            ..Default::default()
        };
        (window, Task::none())
    }

    fn subscription(&self) -> Subscription<Message> {
        cosmic::iced::time::every(TICK).map(|_| Message::Tick)
    }

    fn update(&mut self, message: Message) -> Task<Message> {
        match message {
            Message::Tick => {
                self.pendulum.step(TICK.as_secs_f32(), &mut self.seed);
            }
            Message::OpenSettings => {
                self.pendulum.nudge(&mut self.seed);
                // cosmic-panel spawns applets with a minimal PATH that doesn't include
                // ~/.local/bin, so this can't rely on PATH lookup
                let settings_bin = std::env::var_os("HOME")
                    .map(std::path::PathBuf::from)
                    .map(|home| home.join(".local/bin/floatly-settings"));
                match settings_bin {
                    Some(path) => {
                        if let Err(err) = std::process::Command::new(path).spawn() {
                            log::warn!("failed to launch floatly-settings: {err}");
                        }
                    }
                    None => log::warn!("$HOME not set; can't locate floatly-settings"),
                }
            }
            Message::Surface(a) => {
                return cosmic::task::message(cosmic::Action::Surface(a));
            }
        }
        Task::none()
    }

    fn view(&self) -> Element<'_, Message> {
        let (w, h) = self.core.applet.suggested_size(true);
        let (pad_w, pad_h) = self.core.applet.suggested_padding(true);

        let accent = self.core.applet.theme().map_or(
            cosmic::iced::Color::from_rgb(0.98, 0.65, 0.75),
            |theme| theme.cosmic().accent_color().into(),
        );

        let charm = canvas(CharmCanvas {
            angle: self.pendulum.angle,
            accent,
        })
        .width(Length::Fixed(f32::from(w)))
        .height(Length::Fixed(f32::from(h)));

        let padded: Element<'_, Message> = cosmic::widget::container(charm)
            .padding([f32::from(pad_h), f32::from(pad_w)])
            .into();

        Element::from(self.core.applet.applet_tooltip::<Message>(
            padded,
            "Floatly — click to open settings",
            false,
            Message::Surface,
            None,
        ))
    }

    fn view_window(&self, _id: Id) -> Element<'_, Message> {
        "".into()
    }

    fn style(&self) -> Option<cosmic::iced::theme::Style> {
        Some(cosmic::applet::style())
    }
}
