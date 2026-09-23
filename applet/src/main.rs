use window::Window;

mod charm;
mod window;

fn main() -> cosmic::iced::Result {
    let env = env_logger::Env::default().filter_or("FLOATLY_LOG", "warn");
    env_logger::init_from_env(env);
    cosmic::applet::run::<Window>(())
}
