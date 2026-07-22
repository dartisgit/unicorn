//! Main panel: scrollable commit log, one row per commit, styled like a
//! compact `git log --oneline` with colorized hash / author / summary
//! columns via a `Table` widget (rather than `List`) so the columns
//! align cleanly regardless of content length.

use ratatui::layout::{Constraint, Rect};
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, Cell, Row, Table};
use ratatui::Frame;

use crate::app::{App, Focus};
use crate::ui::Theme;

pub fn draw(frame: &mut Frame, area: Rect, app: &mut App, theme: &Theme) {
    let focused = app.focus == Focus::CommitLog;

    let rows: Vec<Row> = app
        .commits
        .iter()
        .map(|c| {
            let when = format_relative_time(c.author_time_unix);
            Row::new(vec![
                Cell::from(c.short_id.clone()).style(
                    ratatui::style::Style::default().fg(theme.accent_secondary),
                ),
                Cell::from(c.summary.clone()),
                Cell::from(c.author_name.clone())
                    .style(ratatui::style::Style::default().fg(theme.text_muted)),
                Cell::from(when).style(ratatui::style::Style::default().fg(theme.text_muted)),
            ])
        })
        .collect();

    let widths = [
        Constraint::Length(9),
        Constraint::Min(20),
        Constraint::Length(18),
        Constraint::Length(12),
    ];

    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(theme.border_style(focused))
        .title(Line::from(" Commit Log ").style(theme.title_style()));

    let header = Row::new(vec!["Hash", "Summary", "Author", "When"])
        .style(
            ratatui::style::Style::default()
                .fg(theme.text_muted)
                .add_modifier(ratatui::style::Modifier::BOLD),
        )
        .bottom_margin(0);

    let table = Table::new(rows, widths)
        .header(header)
        .block(block)
        .row_highlight_style(theme.selection_style())
        .highlight_symbol("▶ ");

    frame.render_stateful_widget(table, area, &mut app.commit_state);
}

/// Minimal, dependency-light relative-time formatter ("3d ago", "2h ago",
/// "just now") for the log's "When" column. Uses `chrono` only for the
/// current-time lookup; the actual bucketing is plain arithmetic.
fn format_relative_time(author_time_unix: i64) -> String {
    let now = chrono::Utc::now().timestamp();
    let delta = (now - author_time_unix).max(0);

    const MINUTE: i64 = 60;
    const HOUR: i64 = 60 * MINUTE;
    const DAY: i64 = 24 * HOUR;
    const WEEK: i64 = 7 * DAY;

    if delta < MINUTE {
        "just now".to_string()
    } else if delta < HOUR {
        format!("{}m ago", delta / MINUTE)
    } else if delta < DAY {
        format!("{}h ago", delta / HOUR)
    } else if delta < WEEK {
        format!("{}d ago", delta / DAY)
    } else {
        format!("{}w ago", delta / WEEK)
    }
}
