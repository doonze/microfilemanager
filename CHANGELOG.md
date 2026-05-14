# Changelog

All notable changes to Micro File Manager are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

> **Convention:** The moment a version is committed, it is locked. All new work goes
> into the next version's section immediately. We are always working on the next version.

---

## [3.2] - Unreleased

### Added
- Version number now displayed on the login page title (`Micro File Manager 3.2`)

---

## [3.1] - 2026-05-13

### Added
- **Browse Files button** on the upload page — prominent button above the drag-and-drop
  zone that triggers the OS file picker directly. Works around the browser security
  restriction that prevents programmatic file picker opens without a real user gesture.
- **Batch conflict resolution** — all files in a drop finish uploading before any
  conflict dialog appears (previously a dialog would interrupt mid-upload). When 2+
  conflicts are queued, a **"Do this for all remaining conflicts"** checkbox appears:
  - *Overwrite All* — silently overwrites all remaining conflicting files
  - *Cancel All* — silently deletes all remaining `.part` files
  - *Auto-name All* — server auto-numbers remaining files (`file (1).jpg`, etc.)
    without prompting for individual names
- **`autonumber` upload_resolve action** (PHP) — generates a unique incremented
  filename server-side (`basename (1).ext`, `(2)`, etc.) used by Auto-name All.

### Fixed
- `$ is not defined` crash on the upload page — the global jQuery `ajaxError` handler
  now guards itself with `typeof $ !== 'undefined'`. The upload page loads jQuery after
  the `window.csrf` script block, so the handler was crashing on that page.

### Removed
- Auto-open file picker on upload page load — browsers block `input[type=file].click()`
  from non-user-gesture call stacks (setTimeout, Dropzone init callback, etc.).
  Replaced by the Browse Files button above.

---

## [3.0] - 2026-05-12

Initial MFM release — fork of TinyFileManager V2.6.

### Added
- **External config system** — all settings overridable via `config.php` without
  touching the main file. Config survives version upgrades.
- **Smart config merging** — `$auth_users`, `$readonly_users`, `$directories_users`
  merged from `config.php`; main file wins on conflict.
- **Full config coverage** — every configurable setting documented and exposed in
  `config.example.php`.
- **Conflict resolution** — upload, copy, and move operations show an
  Overwrite / Rename / Cancel dialog on name collision. TFM failed silently.
- **Upload conflict queue** — multiple simultaneous name collisions are serialized
  with a queue depth badge; no more concurrent dialogs stomping each other.
- **Configurable session timeout** — `$session_timeout` (default 4 hours).
  Applied via `ini_set` + `session_set_cookie_params` before `session_start`.
- **Server local timezone** — timestamps display in server timezone; removed TFM's
  hardcoded UTC override. Configurable via `$default_timezone`.
- **ACE editor config** — `$ace_theme` and `$ace_font_size` configurable via
  `config.php`. TFM had these hard-coded.
- **Dark-mode file viewer** — Highlight.js theme auto-switches with UI theme.
  Configurable separately for light/dark via `config.php`.
- **Write-permission awareness** — `is_writable()` checked before save; read-only
  files show badge and disabled Save button; specific error messages on failure.
- **Permission denied on move** — identifies whether source dir, destination dir,
  or destination file caused the failure.
- **Copy/Move button on file view page** — between Advanced Editor and Back.
  Hidden in FM_READONLY mode.
- **Copy/Move destination guard** — buttons disabled until a destination folder is
  selected; prevents copy-to-source-directory error.

### Changed
- Rebranded from TinyFileManager to **Micro File Manager (MFM)** — new author
  card, versioning, all UI/meta references updated. Fork attribution preserved.
- Login screen — H3K SVG logo replaced with bold `APP_TITLE` text.
- Upload dropzone message — updated to "Drop files here or click to choose"
  (original only mentioned dropping, no hint it was clickable).
ble).
