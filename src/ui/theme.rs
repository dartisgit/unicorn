//! Centralized color palette so the "beautiful, colorful, clean" look
//! is defined once and reused everywhere, rather than scattered as
//! magic `Color::Rgb(...)` calls throughout the panel modules. Tweak
//! this file to reskin the whole app.

use ratatui::style::{Color, Modifier, Style};

#[derive(Debug, Clone, Copy)]
pub struct Theme {
    pub background: Color,
    pub surface: Color,
    pub border_idle: Color,
    pub border_focused: Color,
    pub text_primary: Color,
    pub text_muted: Color,
    pub accent_primary: Color,
    pub accent_secondary: Color,
    pub selection_bg: Color,
}

impl Default for Theme {
    fn default() -> Self {
        // A cohesive violet/cyan pairing on a near-black background —
        // reads as "unicorn" without tipping into pastel-illegible.
        Self {
            background: Color::Rgb(13, 13, 20),
            surface: Color::Rgb(20, 20, 30),
            border_idle: Color::Rgb(70, 70, 90),
            border_focused: Color::Rgb(180, 120, 255),
            text_primary: Color::Rgb(230, 230, 240),
            text_muted: Color::Rgb(130, 130, 150),
            accent_primary: Color::Rgb(180, 120, 255), // violet
            accent_secondary: Color::Rgb(100, 220, 220), // cyan
            selection_bg: Color::Rgb(60, 40, 90),
        }
    }
}

impl Theme {
    pub fn border_style(&self, focused: bool) -> Style {
        Style::default().fg(if focused {
            self.border_focused
        } else {
            self.border_idle
        })
    }

    pub fn title_style(&self) -> Style {
        Style::default()
            .fg(self.accent_primary)
            .add_modifier(Modifier::BOLD)
    }

    pub fn selection_style(&self) -> Style {
        Style::default()
            .bg(self.selection_bg)
            .fg(self.text_primary)
            .add_modifier(Modifier::BOLD)
    }
}
