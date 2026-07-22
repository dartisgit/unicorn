//! Left panel: local branch list.
//!
//! Uses `List` + `ListState` (a `StatefulWidget`) so the currently
//! selected row is tracked across frames and rendered with a highlight,
//! rather than us hand-rolling selection highlighting ourselves.

use ratatui::layout::Rect;
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::app::{App, Focus};
use crate::ui::Theme;

pub fn draw(frame: &mut Frame, area: Rect, app: &mut App, theme: &Theme) {
    let focused = app.focus == Focus::Branches;

    let items: Vec<ListItem> = app
        .branches
        .iter()
        .map(|name| ListItem::new(Line::from(format!("🌿 {name}"))))
        .collect();

    // NOTE (ratatui 0.30): `Block::title()` takes `Into<Line>` directly —
    // there's no separate `Title` type to construct anymore.
    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(theme.border_style(focused))
        .title(Line::from(" Branches ").style(theme.title_style()));

    let list = List::new(items)
        .block(block)
        .highlight_style(theme.selection_style())
        // NOTE (ratatui 0.30): `highlight_symbol` takes `Into<Line>`,
        // so a plain `&str` still works via that conversion.
        .highlight_symbol("▶ ");

    frame.render_stateful_widget(list, area, &mut app.branch_state);
}
