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
