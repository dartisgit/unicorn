//! Translates raw crossterm input into the small set of semantic events
//! `App` actually cares about. Keeping this translation in one place
//! means `app.rs` never has to match on crossterm's `KeyCode` directly,
//! which makes it trivial to rebind keys later without touching app logic.

use crossterm::event::{self, Event as CtEvent, KeyCode, KeyEventKind};
use std::time::Duration;

/// Semantic input events the app reacts to. Deliberately small: add
/// variants here as the app grows new interactive features.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AppEvent {
    Quit,
    MoveUp,
    MoveDown,
    FocusNext,
    Select,
    Tick,
}

/// Block for up to `timeout` waiting for a terminal event, translate it,
/// and return it. Returns `AppEvent::Tick` if nothing arrived in time —
/// this is what makes the event loop double as a frame-rate limiter
/// without needing a separate timer thread.
pub fn next(timeout: Duration) -> std::io::Result<AppEvent> {
    if event::poll(timeout)? {
        if let CtEvent::Key(key) = event::read()? {
            // On some platforms/terminals crossterm reports both Press
            // and Release; only act on Press to avoid double-firing.
            if key.kind != KeyEventKind::Press {
                return Ok(AppEvent::Tick);
            }
            let mapped = match key.code {
                KeyCode::Char('q') | KeyCode::Esc => AppEvent::Quit,
                KeyCode::Up | KeyCode::Char('k') => AppEvent::MoveUp,
                KeyCode::Down | KeyCode::Char('j') => AppEvent::MoveDown,
                KeyCode::Tab => AppEvent::FocusNext,
                KeyCode::Enter => AppEvent::Select,
                _ => AppEvent::Tick,
            };
            return Ok(mapped);
        }
    }
    Ok(AppEvent::Tick)
}
