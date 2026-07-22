//! Bottom status bar: keybinding hints plus a live count of branches
//! and commits currently loaded, so the panel doubles as a lightweight
//! "is data actually loading?" sanity check while you're developing.

use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;
use ratatui::Frame;

use crate::app::App;
use crate::ui::Theme;

pub fn draw(frame: &mut Frame, area: Rect, app: &App, theme: &Theme) {
    let hint_style = Style::default().fg(theme.text_muted);
    let key_style = Style::default()
        .fg(theme.accent_primary)
        .add_modifier(Modifier::BOLD);

    let line = Line::from(vec![
        Span::styled(" ↑↓/jk ", key_style),
        Span::styled("move   ", hint_style),
        Span::styled("Tab ", key_style),
        Span::styled("switch panel   ", hint_style),
        Span::styled("q/Esc ", key_style),
        Span::styled("quit", hint_style),
        Span::raw("   —   "),
        Span::styled(
            format!("{} branches, {} commits loaded", app.branches.len(), app.commits.len()),
            hint_style,
        ),
    ]);

    frame.render_widget(Paragraph::new(line), area);
}
