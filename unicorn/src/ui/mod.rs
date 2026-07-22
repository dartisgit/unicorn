//! Top-level UI composition: splits the frame into panels and delegates
//! rendering of each one to a dedicated module. Keeping one function
//! (`draw`) as the single entry point means the overall layout is easy
//! to see and change in one place, even as individual panels grow.

mod branches;
mod commit_log;
mod statusbar;
mod theme;

use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::Frame;

use crate::app::App;

pub use theme::Theme;

/// Renders one frame of the whole UI. Called every loop iteration from
/// `App::run` inside `terminal.draw(...)`.
pub fn draw(frame: &mut Frame, app: &mut App) {
    let theme = Theme::default();

    // Vertical split: main content area on top, one-line status bar
    // pinned to the bottom.
    let [main_area, status_area] = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(0), Constraint::Length(1)])
        .areas(frame.area());

    // Horizontal split of the main area: a narrower branches panel on
    // the left, commit log taking the remaining space on the right.
    let [branches_area, commit_area] = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(28), Constraint::Percentage(72)])
        .areas(main_area);

    branches::draw(frame, branches_area, app, &theme);
    commit_log::draw(frame, commit_area, app, &theme);
    statusbar::draw(frame, status_area, app, &theme);
}
