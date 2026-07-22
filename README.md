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
