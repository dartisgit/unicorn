//! Central application state and the top-level event/draw loop.
//!
//! `App` owns:
//!   - the opened repository (`git::Repository`)
//!   - derived UI-facing data (branch list, commit log) computed once at
//!     startup — a real app would refresh these on a timer or on file-
//!     system change notification, but for a scaffold, "load once" keeps
//!     the example legible.
//!   - `ratatui` selection state (`ListState`) for each focusable panel

use std::time::Duration;

use ratatui::widgets::ListState;
use ratatui::DefaultTerminal;

use crate::event::{self, AppEvent};
use crate::git::{self, CommitSummary};
use crate::ui;

/// Which panel currently has keyboard focus. `Tab` cycles through these.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Focus {
    Branches,
    CommitLog,
}

pub struct App {
    pub repo: git::Repository,
    pub branches: Vec<String>,
    pub commits: Vec<CommitSummary>,
    pub focus: Focus,
    pub branch_state: ListState,
    pub commit_state: ListState,
    pub should_quit: bool,
}

impl App {
    pub fn new(repo: git::Repository) -> anyhow::Result<Self> {
        let branches = repo.branch_names()?;
        let commits = repo.commit_log(200)?;

        let mut branch_state = ListState::default();
        if !branches.is_empty() {
            branch_state.select(Some(0));
        }
        let mut commit_state = ListState::default();
        if !commits.is_empty() {
            commit_state.select(Some(0));
        }

        Ok(Self {
            repo,
            branches,
            commits,
            focus: Focus::CommitLog,
            branch_state,
            commit_state,
            should_quit: false,
        })
    }

    /// Runs the main draw/input loop until the user quits or an error
    /// bubbles up. Takes `&mut DefaultTerminal` because that's what
    /// `ratatui::run`'s closure hands us.
    ///
    /// Returns `anyhow::Result` (not `color_eyre::Result`) so every `?`
    /// in this file and the modules it calls into converts uniformly —
    /// mixing `anyhow::Error` and `color_eyre`'s `eyre::Report` across a
    /// `?` boundary does not compile without an explicit conversion,
    /// since they're unrelated types. `main.rs` does that one
    /// conversion at the single point where this crosses into
    /// `color_eyre::Result`.
    pub fn run(&mut self, terminal: &mut DefaultTerminal) -> anyhow::Result<()> {
        // ~30fps poll timeout: fast enough to feel responsive, slow enough
        // not to busy-loop and burn CPU while idle.
        let tick_rate = Duration::from_millis(33);

        while !self.should_quit {
            terminal.draw(|frame| ui::draw(frame, self))?;

            match event::next(tick_rate)? {
                AppEvent::Quit => self.should_quit = true,
                AppEvent::MoveUp => self.move_selection(-1),
                AppEvent::MoveDown => self.move_selection(1),
                AppEvent::FocusNext => self.cycle_focus(),
                AppEvent::Select => { /* reserved for future drill-down */ }
                AppEvent::Tick => {}
            }
        }

        Ok(())
    }

    fn cycle_focus(&mut self) {
        self.focus = match self.focus {
            Focus::Branches => Focus::CommitLog,
            Focus::CommitLog => Focus::Branches,
        };
    }

    fn move_selection(&mut self, delta: i32) {
        match self.focus {
            Focus::Branches => {
                Self::move_list(&mut self.branch_state, self.branches.len(), delta)
            }
            Focus::CommitLog => {
                Self::move_list(&mut self.commit_state, self.commits.len(), delta)
            }
        }
    }

    /// Shared bounds-checked selection-move logic for any `ListState` +
    /// item count, wrapping at both ends so `k`/`j` (or arrows) never
    /// gets "stuck" at the top or bottom.
    fn move_list(state: &mut ListState, len: usize, delta: i32) {
        if len == 0 {
            return;
        }
        let current = state.selected().unwrap_or(0) as i32;
        let next = (current + delta).rem_euclid(len as i32);
        state.select(Some(next as usize));
    }
}
