//! Pendulum physics and drawing for the single hanging charm.

use std::f32::consts::PI;

use cosmic::iced::widget::canvas::{self, Event, Frame, Geometry, Path};
use cosmic::iced::{mouse, Color, Point, Rectangle};
use cosmic::{Renderer, Theme};

use crate::window::Message;

const GRAVITY: f32 = 1400.0;
const DAMPING: f32 = 0.55;
const GUST_CHANCE: f32 = 0.01;
const GUST_STRENGTH: f32 = 0.9;

/// The swinging state of the charm. Lives in `Window` and survives redraws;
/// only the numbers needed to render/step the pendulum are kept here.
#[derive(Debug, Clone, Copy)]
pub struct Pendulum {
    pub angle: f32,
    pub angular_velocity: f32,
    string_length_hint: f32,
}

impl Default for Pendulum {
    fn default() -> Self {
        Self {
            angle: 0.18,
            angular_velocity: 0.0,
            string_length_hint: 22.0,
        }
    }
}

impl Pendulum {
    pub fn step(&mut self, dt: f32, seed: &mut u32) {
        let length = self.string_length_hint;
        let accel = -(GRAVITY / length) * self.angle.sin() - DAMPING * self.angular_velocity;
        self.angular_velocity += accel * dt;
        self.angle += self.angular_velocity * dt;

        // cheap xorshift so we don't need a `rand` dependency for one ambient gust
        *seed ^= *seed << 13;
        *seed ^= *seed >> 17;
        *seed ^= *seed << 5;
        let r = (*seed as f32) / (u32::MAX as f32);
        if r < GUST_CHANCE {
            let dir = if r < GUST_CHANCE / 2.0 { -1.0 } else { 1.0 };
            self.angular_velocity += dir * GUST_STRENGTH * 0.4;
        }
    }

    pub fn nudge(&mut self, seed: &mut u32) {
        *seed ^= *seed << 13;
        *seed ^= *seed >> 17;
        *seed ^= *seed << 5;
        let dir = if seed.wrapping_shr(16) % 2 == 0 { -1.0 } else { 1.0 };
        self.angular_velocity += dir * 3.2;
    }
}

/// A `canvas::Program` that draws the charm at its current swing angle.
/// Constructed fresh on every `view()` call from the app's `Pendulum` state.
pub struct CharmCanvas {
    pub angle: f32,
    pub accent: Color,
}

impl canvas::Program<Message, Theme, Renderer> for CharmCanvas {
    type State = ();

    fn update(
        &self,
        _state: &mut Self::State,
        event: &Event,
        _bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> Option<canvas::Action<Message>> {
        if !cursor.is_over(_bounds) {
            return None;
        }
        if let Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) = event {
            return Some(canvas::Action::publish(Message::OpenSettings).and_capture());
        }
        None
    }

    fn draw(
        &self,
        _state: &Self::State,
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        _cursor: mouse::Cursor,
    ) -> Vec<Geometry> {
        let mut frame = Frame::new(renderer, bounds.size());

        let w = bounds.width;
        let h = bounds.height;
        let anchor = Point::new(w / 2.0, 2.0);
        let string_length = (h - anchor.y - 4.0).max(4.0);
        let bob = Point::new(
            anchor.x + string_length * self.angle.sin(),
            anchor.y + string_length * self.angle.cos(),
        );

        let string_path = Path::line(anchor, bob);
        frame.stroke(
            &string_path,
            canvas::Stroke::default()
                .with_width(1.0)
                .with_color(Color::from_rgba(0.6, 0.6, 0.65, 0.55)),
        );

        let radius = (w.min(h) * 0.24).max(3.0);
        let star = star_path(bob, radius, self.angle * 0.4);
        frame.fill(&star, self.accent);
        frame.stroke(
            &star,
            canvas::Stroke::default()
                .with_width(radius * 0.14)
                .with_color(Color {
                    a: 0.35,
                    ..Color::WHITE
                }),
        );

        vec![frame.into_geometry()]
    }

    fn mouse_interaction(
        &self,
        _state: &Self::State,
        bounds: Rectangle,
        cursor: mouse::Cursor,
    ) -> mouse::Interaction {
        if cursor.is_over(bounds) {
            mouse::Interaction::Pointer
        } else {
            mouse::Interaction::default()
        }
    }
}

fn star_path(center: Point, r: f32, rotation: f32) -> Path {
    Path::new(|builder| {
        let mut points = Vec::with_capacity(10);
        for i in 0..10 {
            let angle = PI / 2.0 + (i as f32) * PI / 5.0 + rotation;
            let radius = if i % 2 == 0 { r } else { r * 0.42 };
            points.push(Point::new(
                center.x + radius * angle.cos(),
                center.y - radius * angle.sin(),
            ));
        }
        builder.move_to(points[0]);
        for p in &points[1..] {
            builder.line_to(*p);
        }
        builder.close();
    })
}
