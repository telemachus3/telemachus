Added

- **Changelog fragments** (`changelog.d/`, `tools/changelog.py`). Branches drop
  one file per change instead of editing `CHANGELOG.md`, and the release folds
  them in. Two branches never touch the same path, so concurrent appends cannot
  interfere.

  The motivation is not the merge conflict, which git reports and a human
  resolves in seconds. It is the quieter failure observed on this repository:
  two branches each appended their own `### Fixed` and `### Added` under
  `[Unreleased]`, both merges succeeded, nothing was reported, and the section
  ended up with five subheadings for three categories. `release.yml` reads this
  file by regex and falls back silently, so a malformed section surfaces in
  published release notes rather than in CI.
