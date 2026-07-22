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
