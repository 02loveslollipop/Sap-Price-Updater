# Changelog

All notable changes to this project are documented in this file.
Releases are created automatically by CI on every push to `main` (tagged `v<run_number>`).

## 2026-09-11 — Maintenance release

### Fixed
- **Windows clipboard paste**: carriage-return characters (`\r`) no longer leak into the last column's values when pasting data copied from Excel with Windows line endings (`\r\n`).
- **Cost files without a `COSTO PROD` sheet**: the app no longer crashes with `Worksheet named 'COSTO PROD' not found` when processing. The sheet detected while browsing (first sheet as fallback) is now reused during processing.
- **`load_cost_file` with `sheet_name=None`**: previously returned a dict of all sheets instead of a DataFrame; it now reads the first sheet.
- **Infinite values**: `normalize_article_code` no longer raises `OverflowError` on infinite float values; they pass through as strings.
- **Trailing zero rows**: clipboard rows containing `0.000`-style zeros are now removed consistently with other zero variants (empty rows are filtered with a single shared rule).
- **Cost column auto-selection**: now also runs when the cost file is read from the fallback sheet; the "Configure Columns" button state is refreshed correctly after a failed read.
- **Language selector**: shows language names (`English` / `Español`) instead of raw codes (`en` / `es`), and the "Language" label now updates when switching languages.

### Changed
- Added `requirements.txt` (runtime) and `requirements-dev.txt` (development/build); CI and build scripts install from them.
- Added `xlrd` as a dependency so `.xls` files — already offered by the file dialog — can actually be opened.
- CI: bumped GitHub Actions (`checkout` v7, `setup-python` v7, `upload-artifact` v7, `download-artifact` v8, `gh-release` v3); tests now run on Python 3.11 and 3.13; builds use Python 3.13.
- CI: the release job now grants `contents: write` to the built-in `GITHUB_TOKEN` — `action-gh-release` v3 no longer reads the token from the `GITHUB_TOKEN` env var, which made releases fail with 403; the `RELEASE_TOKEN` secret is no longer needed.
- Verified compatibility with pandas 3.x (tests pass on pandas 2.1 and 3.0).

### Tests
- 67 unit tests (up from 60), including regression tests for all the fixes above and a headless GUI smoke test path (browse fallback → process → clipboard copy → language switch).
