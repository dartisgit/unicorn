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
            let reference = reference?;
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
