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
