# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-13

### Added

- Pixel-art animations for `git commit`, `push`, `pull`, `fetch`, `add`, `restore`, `init`,
  `clone`, `branch`, `checkout` (and `switch`), `stash`, `blame` and `reset`: a loop while the
  command runs and a success or failure ending by exit status.
- Recognizes git global options, wrapper programs, command lists (the last git command wins),
  the oh-my-zsh git aliases, `g` for `git` and common git config aliases.
- `config.json`: corner, offset, scale, loop delay, hold time, per-command switches and extra
  aliases. "Open git animations config" creates it.
- "Toggle git animations" (`ctrl+alt+cmd+g`), shared by every window.

[Unreleased]: https://github.com/willstarnet/tern-git-fx/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/willstarnet/tern-git-fx/releases/tag/v0.1.0
