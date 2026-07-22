#!/usr/bin/env python3
"""
scaffold_unicorn.py

Scaffolds "Unicorn" — a Soft Serve-style self-hosted git TUI server, built with:
  - Rust (2021 edition, standard workspace-free binary layout)
  - Ratatui 0.30.x for the terminal UI  (current as of mid-2026)
  - gitoxide (`gix` 0.84) for git operations, no libgit2/git2 dependency
  - crossterm as the terminal backend (via ratatui's re-export)

Verified against current upstream docs at generation time:
  - ratatui 0.30.0 modularized the crate into ratatui-core / ratatui-widgets /
    ratatui-crossterm, and introduced `ratatui::run()` / `ratatui::init()` /
    `ratatui::restore()` / `DefaultTerminal` as the recommended entry points,
    replacing the old manual enable_raw_mode()+Terminal::new(CrosstermBackend::new())
    boilerplate you'll see in older tutorials.
  - `Block::title()` now takes `Into<Line>` (the old `widgets::block::Title` type
    was removed), and `List::highlight_symbol()` now takes `Into<Line>` too.
    This scaffold's UI code already matches that shape.
  - gix 0.84 (crates.io latest) is used as the git backend. We deliberately avoid
    gix's `rev_walk()` builder in this scaffold and instead walk history by hand
    via `Commit::parents()`, because that surface is small, stable across gix
    0.7x-0.8x, and doesn't depend on getting a long fluent-builder chain exactly
    right. The generated code comments explain this so you can swap in
    `repo.rev_walk(...)` later if you want gix's more optimized traversal.

Usage:
    python3 scaffold_unicorn.py [target_dir]

    target_dir defaults to ./unicorn

After running:
    cd unicorn
    cargo run -- --path .        # opens the repo scaffold is run inside, or any repo
    cargo run -- --path /some/other/repo

Requires: Rust toolchain (rustc/cargo) installed separately. This script only
writes files — it does not invoke cargo or download crates, so it works even
without network access, and you control exactly when the build happens.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

# ---------------------------------------------------------------------------
# File contents
# ---------------------------------------------------------------------------

CARGO_TOML = dedent(
    """\
    [package]
    name = "unicorn"
    version = "0.1.0"
    edition = "2021"
    description = "Unicorn — a terminal UI for self-hosted git, powered by gitoxide."
    publish = false

    [[bin]]
    name = "unicorn"
    path = "src/main.rs"

    [dependencies]
    # --- TUI ---------------------------------------------------------------
    # Ratatui 0.30.x. The crate was modularized in 0.30 (ratatui-core /
    # ratatui-widgets / ratatui-crossterm live underneath it) but the `ratatui`
    # crate still re-exports everything an application needs, including the
    # `crossterm` backend, so this single dependency is enough for apps.
    ratatui = "0.30"
    # Re-exported by ratatui, but declared explicitly since we call crossterm
    # event/key APIs directly in the event loop.
    crossterm = "0.28"

    # --- Git -----------------------------------------------------------------
    # gitoxide's main library crate. `gix` is the entry point; it re-exports
    # the lower-level gix-* plumbing crates you need (gix-ref, gix-object, etc).
    gix = "0.84"

    # --- CLI / errors / misc -------------------------------------------------
    clap = { version = "4", features = ["derive"] }
    anyhow = "1"
    color-eyre = "0.6"
    chrono = { version = "0.4", default-features = false, features = ["clock", "std"] }
    directories = "5"
    unicode-width = "0.2"

    [profile.release]
    opt-level = 3
    lto = true
    codegen-units = 1
    panic = "abort"
    strip = true
    """
)

GITIGNORE = dedent(
    """\
    /target
    Cargo.lock
    *.swp
    .DS_Store
    """
)

README = dedent(
    """\
    # 🦄 Unicorn

    Unicorn is a terminal UI for browsing and administering self-hosted git
    repositories — a Soft Serve-style tool, built from scratch in Rust on top of:

    - **[Ratatui](https://ratatui.rs)** (0.30.x) for the terminal interface
    - **[gitoxide](https://github.com/GitoxideLabs/gitoxide)** (`gix` 0.84) for
      git operations — no `libgit2`/`git2` dependency, no shelling out to `git`
    - **[crossterm](https://github.com/crossterm-rs/crossterm)** as the terminal
      backend (via Ratatui's own re-export, so versions always match)

    This is proprietary scaffolding generated for internal use — fill in the
    `LICENSE` / distribution terms of your choice before shipping it anywhere.

    ## Layout

    ```
    unicorn/
    ├── Cargo.toml
    ├── README.md
    └── src/
        ├── main.rs           # entry point: CLI parsing, terminal setup/teardown
        ├── app.rs            # central App state + top-level event dispatch
        ├── event.rs          # crossterm → app event translation
        ├── git/
        │   ├── mod.rs        # git module root
        │   ├── repository.rs # thin wrapper around gix::Repository
        │   └── commit.rs     # commit-log data model + hand-rolled history walk
        └── ui/
            ├── mod.rs         # ui module root, top-level frame layout
            ├── theme.rs       # centralized color palette
            ├── branches.rs    # left panel: branch/ref list widget
            ├── commit_log.rs  # main panel: commit log table widget
            └── statusbar.rs   # footer: keybinding hints / status line
    ```

    ## Building

    ```bash
    cd unicorn
    cargo run -- --path .
    ```

    Point `--path` at any local git repository (bare or with a worktree).
    Omit it to use the current directory.

    ## Keybindings

    | Key         | Action                          |
    |-------------|----------------------------------|
    | `↑` / `k`   | Move selection up                |
    | `↓` / `j`   | Move selection down              |
    | `Tab`       | Switch focus: branches ↔ commits |
    | `Enter`     | (reserved) inspect selection      |
    | `q` / `Esc` | Quit                              |

    ## Why gitoxide instead of libgit2 (`git2`)?

    gitoxide is a from-scratch, memory-safe Rust implementation of git — no C
    bindings, no libgit2 dependency to vendor or link against, and it's
    generally faster for read-heavy operations like the ones a TUI does
    constantly (listing refs, walking commit history, reading trees). The
    tradeoff is that its API is younger and moves faster than `git2`'s, so if
    you upgrade the `gix` version later, re-check the parts of `src/git/`
    that touch its API surface directly.

    ## Extending this scaffold

    The obvious next steps, roughly in order of how most Soft Serve-alikes
    grow:

    1. **Diff view** — add a `git/diff.rs` using `gix::Repository::diff_tree_to_tree`
       and a `ui/diff.rs` panel.
    2. **SSH server** — Soft Serve's actual value-add is serving repos over
       SSH with per-key access control. That's a separate long-running async
       service (consider `russh` or `thrussh`) that would run alongside, or
       instead of, this TUI — the TUI here is the *admin/browsing* front end.
    3. **Repo list / multi-repo support** — right now Unicorn opens one repo
       at `--path`. A real server needs a landing screen listing all hosted
       repos before drilling into one.
    4. **Config file** — `directories` is already a dependency (unused so far)
       for locating a per-user config directory once you need one.
    """
)

# ---------------------------------------------------------------------------
# src/main.rs
# ---------------------------------------------------------------------------

MAIN_RS = dedent(
    """\
    //! Unicorn — entry point.
    //!
    //! Responsibilities kept deliberately narrow here:
    //!   1. Parse CLI args (just `--path`, for now).
    //!   2. Open the git repository via our `git` module (gitoxide-backed).
    //!   3. Hand off to `ratatui::run`, which owns terminal init/teardown
    //!      (including automatic restoration on panic) for the lifetime of
    //!      the closure we give it.
    //!
    //! `ratatui::run` is the Ratatui 0.30+ recommended entry point: it wraps
    //! `ratatui::init()` (raw mode + alternate screen) and `ratatui::restore()`
    //! (undoes that, even on panic) around your closure, so the terminal is
    //! never left in a broken state if `App::run` returns an error or panics.

    mod app;
    mod event;
    mod git;
    mod ui;

    use clap::Parser;

    /// Unicorn: a terminal UI for self-hosted git repositories.
    #[derive(Parser, Debug)]
    #[command(name = "unicorn", author, version, about, long_about = None)]
    struct Cli {
        /// Path to the git repository to browse. Defaults to the current directory.
        #[arg(short, long, default_value = ".")]
        path: std::path::PathBuf,
    }

    fn main() -> color_eyre::Result<()> {
        // color-eyre gives us prettier panic/error output than the default,
        // and composes cleanly with ratatui's own panic-hook restoration.
        color_eyre::install()?;

        // Everything below returns `anyhow::Result`, uniformly, so every `?`
        // inside `run()` (and every function it calls into, across the
        // `app` and `git` modules) converts cleanly. `anyhow::Error` and
        // color-eyre's `eyre::Report` are unrelated types with no automatic
        // conversion between them, so we do exactly one explicit
        // conversion here, at the single point where an anyhow error needs
        // to become a color-eyre one for pretty-printing.
        if let Err(err) = run() {
            return Err(color_eyre::eyre::eyre!("{err:?}"));
        }
        Ok(())
    }

    fn run() -> anyhow::Result<()> {
        let cli = Cli::parse();

        let repo = git::Repository::open(&cli.path)?;
        let mut app = app::App::new(repo)?;

        // `ratatui::run` performs init() -> closure -> restore(), including
        // restoration on panic. The closure receives a `&mut DefaultTerminal`,
        // and its return type is inferred from `app.run(terminal)`, which is
        // `anyhow::Result<()>`.
        ratatui::run(|terminal| app.run(terminal))?;

        Ok(())
    }
    """
)

# ---------------------------------------------------------------------------
# src/event.rs
# ---------------------------------------------------------------------------

EVENT_RS = dedent(
    """\
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
    """
)

# ---------------------------------------------------------------------------
# src/app.rs
# ---------------------------------------------------------------------------

APP_RS = dedent(
    """\
    //! Central application state and the top-level event/draw loop.
    //!
    //! `App` owns:
    //!   - the opened repository (`git::Repository`)
    //!   - derived UI-facing data (branch list, commit log) computed once at
    //!     startup — a real app would refresh these on a timer or on file-
    //!     system change notification, but for a scaffold, "load once" keeps
    //!     the example legible.
    //!   - `ratatui` selection state for each focusable panel: `ListState` for
    //!     the branches list, `TableState` for the commit log table

    use std::time::Duration;

    use ratatui::widgets::{ListState, TableState};
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
        /// `TableState`, not `ListState` — the commit log renders as a `Table`
        /// (see `ui/commit_log.rs`), and `Table` is a `StatefulWidget` whose
        /// associated `State` type is `TableState`. `ListState` and
        /// `TableState` happen to expose the same `select`/`selected` shape,
        /// but they are distinct types with no shared trait, so the field type
        /// has to match whichever widget actually renders with it.
        pub commit_state: TableState,
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
            let mut commit_state = TableState::default();
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
                    let next = Self::next_index(self.branch_state.selected(), self.branches.len(), delta);
                    self.branch_state.select(next);
                }
                Focus::CommitLog => {
                    let next = Self::next_index(self.commit_state.selected(), self.commits.len(), delta);
                    self.commit_state.select(next);
                }
            }
        }

        /// Bounds-checked, wrapping selection arithmetic shared by both panels.
        /// This is deliberately just index math with no `ListState`/`TableState`
        /// involved, since those two types expose the same `selected()`/
        /// `select(Some(_))` shape but aren't unified by any shared trait —
        /// factoring out the arithmetic (rather than the state mutation) is
        /// what actually gets reused between the two call sites above.
        /// Wraps at both ends so `k`/`j` (or arrows) never gets "stuck" at the
        /// top or bottom. Returns `None` if there's nothing to select.
        fn next_index(current: Option<usize>, len: usize, delta: i32) -> Option<usize> {
            if len == 0 {
                return None;
            }
            let current = current.unwrap_or(0) as i32;
            let next = (current + delta).rem_euclid(len as i32);
            Some(next as usize)
        }
    }
    """
)

# ---------------------------------------------------------------------------
# src/git/mod.rs
# ---------------------------------------------------------------------------

GIT_MOD_RS = dedent(
    """\
    //! Git backend module, built on gitoxide (`gix`) rather than `git2`/libgit2.
    //!
    //! Kept intentionally thin: `repository.rs` wraps the handful of
    //! `gix::Repository` calls the TUI needs, and `commit.rs` defines the
    //! plain-data types the UI layer renders. Nothing in `ui/` ever touches
    //! `gix` types directly — it only sees `CommitSummary` and `String`
    //! branch names — so the git backend could later be swapped without
    //! touching any rendering code.

    mod commit;
    mod repository;

    pub use commit::CommitSummary;
    pub use repository::Repository;
    """
)

# ---------------------------------------------------------------------------
# src/git/repository.rs
# ---------------------------------------------------------------------------

GIT_REPOSITORY_RS = dedent(
    """\
    //! Thin wrapper around `gix::Repository` exposing only what the TUI needs.
    //!
    //! API notes (gix 0.84, verified against current docs.rs):
    //!   - `gix::open(path)` opens a repository at an exact path (it does NOT
    //!     search upward through parent directories). We use plain `open`
    //!     rather than `gix::discover` because `--path` is meant to point
    //!     directly at the repo you want, mirroring how Soft Serve addresses
    //!     hosted repos individually rather than via "nearest .git upward".
    //!     Swap in `gix::discover(path)` if you'd rather have `unicorn`
    //!     walk up from an arbitrary subdirectory the way plain `git` does.
    //!   - `Repository::head_commit()` resolves HEAD and decodes the commit
    //!     it points at in a single call — no separate `Id`/`ObjectId`
    //!     handle to juggle ourselves.
    //!   - `Repository::references()` returns a platform; its
    //!     `.local_branches()` method gives an iterator over exactly
    //!     `refs/heads/*` references — confirmed directly from gix's own
    //!     doctest (`repo.references()?.local_branches()?...`), so we use
    //!     it directly rather than hand-filtering `.all()` by prefix.
    //!   - `Repository::find_commit(id)` decodes a single commit object.
    //!
    //! We deliberately do NOT use `Repository::rev_walk(...)`'s fluent
    //! builder here. It exists and is the more optimized way to walk commit
    //! history in gix, but its exact chained-method shape has moved between
    //! releases; the hand-rolled BFS in `commit.rs` (via `Commit::parents()`,
    //! a small and stable surface) is slightly less optimal but far less
    //! likely to break on your first `cargo build`. Once this compiles for
    //! you, swapping in `rev_walk` is a good follow-up — check
    //! `docs.rs/gix/latest/gix/struct.Repository.html#method.rev_walk` for
    //! the exact signature on whatever `gix` version you land on.

    use std::path::Path;

    use gix::bstr::ByteSlice;

    use super::commit::{walk_commit_log, CommitSummary};

    pub struct Repository {
        inner: gix::Repository,
    }

    impl Repository {
        /// Opens the repository at an exact path. Fails if `path` is not
        /// itself a git repository (bare or with a worktree) — see the
        /// module docs above if you want upward-searching behavior instead.
        pub fn open(path: &Path) -> anyhow::Result<Self> {
            let inner = gix::open(path)?;
            Ok(Self { inner })
        }

        /// Returns local branch names (`refs/heads/*`), shortened (i.e.
        /// `main` rather than `refs/heads/main`), sorted alphabetically so
        /// the branch panel has a stable, predictable order.
        ///
        /// `local_branches()` only ever yields references under
        /// `refs/heads/`, so stripping that exact prefix ourselves — rather
        /// than reaching for a `shorten()`-style helper whose return
        /// type's `Display`/`ToString` support isn't independently
        /// confirmed — keeps this call built entirely out of methods
        /// (`as_bstr()`, `strip_prefix()`, `to_str_lossy()`) verified
        /// directly against gix's own doctest examples and the `bstr`
        /// crate's documented API.
        pub fn branch_names(&self) -> anyhow::Result<Vec<String>> {
            let mut names = Vec::new();

            for reference in self.inner.references()?.local_branches()? {
                // `local_branches()`'s items are `Result<Reference,
                // Box<dyn Error + Send + Sync>>`. `?` can't convert a boxed
                // trait object into `anyhow::Error` on its own — `dyn Error`
                // isn't `Sized`, which is exactly the scenario anyhow's own
                // issue tracker documents (dtolnay/anyhow#66). The fix anyhow
                // shipped for it (#50) is to wrap explicitly with the
                // `anyhow!` macro, which is what `map_err` does here.
                let reference = reference.map_err(|e| anyhow::anyhow!(e))?;
                let full_name = reference.name().as_bstr();
                let short = full_name.strip_prefix(b"refs/heads/").unwrap_or(full_name);
                names.push(short.to_str_lossy().into_owned());
            }

            names.sort();
            Ok(names)
        }

        /// Returns up to `limit` commits reachable from HEAD, newest first.
        /// See `commit.rs` for the traversal itself.
        pub fn commit_log(&self, limit: usize) -> anyhow::Result<Vec<CommitSummary>> {
            // `head_commit()` resolves HEAD and decodes the commit object
            // it points at in one call, so there's no intermediate
            // `Id`/`ObjectId` handle to convert ourselves — one less thing
            // that can drift if the exact `Id` conversion methods change
            // between `gix` releases.
            let head_commit = self.inner.head_commit()?;
            walk_commit_log(&self.inner, head_commit, limit)
        }
    }
    """
)

# ---------------------------------------------------------------------------
# src/git/commit.rs
# ---------------------------------------------------------------------------

GIT_COMMIT_RS = dedent(
    """\
    //! Plain-data commit representation for the UI layer, plus the manual
    //! history walk that populates it.
    //!
    //! Why a hand-rolled walk instead of `gix::Repository::rev_walk(...)`:
    //! `Commit::parents()` (an iterator over parent `ObjectId`s) has been a
    //! stable, simple part of gix's `Commit` API across many releases, so a
    //! plain breadth-first walk built on it is very likely to compile
    //! unchanged even if you bump the `gix` version later. `rev_walk`'s
    //! fluent builder is more efficient (it can use the commit-graph file
    //! for acceleration) but its exact method-chaining shape is more prone
    //! to drift between releases — a reasonable thing to adopt once this
    //! scaffold is building green for you and you're ready to check the
    //! current signature.

    use std::collections::{HashSet, VecDeque};

    use gix::bstr::ByteSlice;
    use gix::ObjectId;

    /// Everything the commit-log panel needs to render one row. Deliberately
    /// flat and owned (no lifetimes tied to the `gix::Repository`) so it's
    /// trivial to store in `App` alongside the rest of the UI state.
    #[derive(Debug, Clone)]
    pub struct CommitSummary {
        pub id: ObjectId,
        pub short_id: String,
        pub summary: String,
        pub author_name: String,
        /// Seconds since Unix epoch, author time. Kept as a raw offset
        /// rather than a formatted string so `ui/commit_log.rs` can decide
        /// how to render it (relative "3 days ago" vs absolute).
        pub author_time_unix: i64,
    }

    /// Breadth-first walk of commit history starting at `start`, following
    /// `Commit::parents()`, collecting up to `limit` commits. BFS (rather
    /// than DFS) keeps commits roughly in recency order for typical
    /// mostly-linear histories without needing a full topological sort,
    /// which is the right tradeoff for a log view that just needs "newest
    /// first, good enough" ordering.
    pub fn walk_commit_log(
        repo: &gix::Repository,
        start: gix::Commit<'_>,
        limit: usize,
    ) -> anyhow::Result<Vec<CommitSummary>> {
        let mut out = Vec::with_capacity(limit.min(256));
        let mut seen: HashSet<ObjectId> = HashSet::new();
        let mut queue: VecDeque<ObjectId> = VecDeque::new();

        seen.insert(start.id);
        queue.push_back(start.id);

        while let Some(id) = queue.pop_front() {
            if out.len() >= limit {
                break;
            }

            let commit = repo.find_commit(id)?;
            out.push(summarize(&commit)?);

            for parent_id in commit.parent_ids() {
                let parent_id = parent_id.detach();
                if seen.insert(parent_id) {
                    queue.push_back(parent_id);
                }
            }
        }

        Ok(out)
    }

    fn summarize(commit: &gix::Commit<'_>) -> anyhow::Result<CommitSummary> {
        let id = commit.id;
        let short_id = id.to_hex_with_len(8).to_string();

        // `message_raw()` gives the full commit message as bytes; we only
        // want the summary (first line), matching `git log --oneline`.
        let message = commit.message_raw()?;
        let summary = message
            .lines()
            .next()
            .unwrap_or_default()
            .to_str_lossy()
            .into_owned();

        let author = commit.author()?;
        let author_name = author.name.to_str_lossy().into_owned();
        // `seconds` is seconds-since-epoch per gix's `gix_date::Time`.
        let author_time_unix = author.time()?.seconds;

        Ok(CommitSummary {
            id,
            short_id,
            summary,
            author_name,
            author_time_unix,
        })
    }
    """
)

# ---------------------------------------------------------------------------
# src/ui/mod.rs
# ---------------------------------------------------------------------------

UI_MOD_RS = dedent(
    """\
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
    """
)

# ---------------------------------------------------------------------------
# src/ui/theme.rs
# ---------------------------------------------------------------------------

UI_THEME_RS = dedent(
    """\
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
    """
)

# ---------------------------------------------------------------------------
# src/ui/branches.rs
# ---------------------------------------------------------------------------

UI_BRANCHES_RS = dedent(
    """\
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
    """
)

# ---------------------------------------------------------------------------
# src/ui/commit_log.rs
# ---------------------------------------------------------------------------

UI_COMMIT_LOG_RS = dedent(
    """\
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
    """
)

# ---------------------------------------------------------------------------
# src/ui/statusbar.rs
# ---------------------------------------------------------------------------

UI_STATUSBAR_RS = dedent(
    """\
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
    """
)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

FILES: dict[str, str] = {
    "Cargo.toml": CARGO_TOML,
    ".gitignore": GITIGNORE,
    "README.md": README,
    "src/main.rs": MAIN_RS,
    "src/event.rs": EVENT_RS,
    "src/app.rs": APP_RS,
    "src/git/mod.rs": GIT_MOD_RS,
    "src/git/repository.rs": GIT_REPOSITORY_RS,
    "src/git/commit.rs": GIT_COMMIT_RS,
    "src/ui/mod.rs": UI_MOD_RS,
    "src/ui/theme.rs": UI_THEME_RS,
    "src/ui/branches.rs": UI_BRANCHES_RS,
    "src/ui/commit_log.rs": UI_COMMIT_LOG_RS,
    "src/ui/statusbar.rs": UI_STATUSBAR_RS,
}


def scaffold(target_dir: Path) -> None:
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"error: {target_dir} already exists and is not empty.", file=sys.stderr)
        print("Choose a different target directory, or remove the existing one.", file=sys.stderr)
        sys.exit(1)

    for relative_path, contents in FILES.items():
        full_path = target_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(contents, encoding="utf-8")
        print(f"  wrote {full_path.relative_to(target_dir.parent) if target_dir.parent != Path('.') else full_path}")

    print()
    print(f"✅ Unicorn scaffolded at: {target_dir.resolve()}")
    print()
    print("Next steps:")
    print(f"  cd {target_dir}")
    print("  cargo run -- --path .        # or point --path at any other local git repo")
    print()
    print("Dependency versions pinned in Cargo.toml (current as of generation):")
    print('  ratatui   = "0.30"   (modularized crate; ratatui::run()/DefaultTerminal entry point)')
    print('  gix       = "0.84"   (gitoxide\'s main library crate)')
    print('  crossterm = "0.28"')
    print()
    print("cargo will resolve exact patch versions on first build — if a newer")
    print("0.30.x / 0.8x.x has shipped by the time you build, cargo will pick it")
    print("up automatically since these are caret (^) requirements by default.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "target_dir",
        nargs="?",
        default="unicorn",
        help="Directory to scaffold the project into (default: ./unicorn)",
    )
    args = parser.parse_args()

    scaffold(Path(args.target_dir))


if __name__ == "__main__":
    main()
