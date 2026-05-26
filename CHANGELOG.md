# Changelog

All notable changes to Micro File Manager are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

> **Convention:** The moment a version is committed, it is locked. All new work goes
> into the next version's section immediately. We are always working on the next version.

---

## [3.4] - Unreleased

### Added
- **Image/audio/video hover preview via `?raw=` endpoint** — new PHP handler serves
  media files directly from the filesystem through PHP, bypassing Apache DocumentRoot
  restrictions. Output buffers flushed before `readfile()` to prevent buffered HTML
  corrupting binary data. Allowlist extended to include mkv/avi/m4v/wmv/flv/m4a/opus.
- **Elevation on view page** — unreadable files show Permission denied banner with
  ⚡ Elevate to View button. After credentials verified, content loads into `<pre>`.
  Modal does NOT auto-open on page load — user sees file info first and decides.
- **Permissions/Owner row on view page** — file info table now shows octal permissions
  and `owner:group` using `posix_getpwuid` / `posix_getgrgid`.
- **ACE editor safe init + lazy-init** — ACE wrapped in IIFE with `getElementById`
  guard; if `#editor` not in DOM, warns and returns gracefully instead of throwing
  uncaught exception that killed `renderThemeMode()` and all toolbar wiring.
  `_unlockEditor` lazy-inits ACE using `window.mfmAceMode` / `window.mfmAceTheme`
  if editor is still null when elevation supplies content.

### Fixed
- **Elevation modal double-click removed** — verifying credentials now immediately
  fires edit/view action on success. The redundant "Begin Editing/Viewing" button is
  gone. Verify button shows "Loading…" as feedback while action fires. Null ref crash
  (setting `disabled` on removed button element) also fixed.
- **Redirect loop on home for root-path users** — `FM_ROOT_PATH=''` + `FM_PATH=''`
  produced `$path=''`, `is_dir('')=false` → infinite redirect. Restored `$root_path='/'`
  fallback; cosmetic double-slash fixed in `fm_get_display_path()` with `preg_replace`.
- **Edit block missing `$file = $_GET['edit']`** — edit handler used leftover `$file`
  from `foreach` directory scan. For unreadable dirs, scan returns `[]`, `$file` was
  undefined → `is_file` check failed → redirect before editor rendered. Matched view
  block pattern: `$file = $_GET['edit']; fm_clean_path(); str_replace()`.
- **`$ext` out of scope in `fm_show_footer()`** — lazy-init ACE code used
  `<?php echo $ext ?>` inside footer function where `$ext` is undefined → PHP notice
  injected into JS string → SyntaxError killed entire script block →
  `mfmShowElevateModal` undefined on every page. Fixed with `window.mfmAceMode`
  injected from edit page scope where `$ext` IS defined.
- **Elevation handlers ignored `?view=` param** — `elevate_check`, `elevate_read`,
  and `elevate_write` only checked `$_GET['edit']`; view page uses `$_GET['view']`
  → "File not found" on verify. All three now use `$_GET['edit'] ?? $_GET['view']`.
- **Unreadable files on edit page crashed ACE** — `$is_text=false` for unreadable
  files meant no `#editor` div rendered, ACE `ace.edit('editor')` threw uncaught
  exception. Added extension-based detection to set `$is_text=true` for unreadable
  files matching known text extensions.
- **Elevate button hidden for unreadable-only files** — button condition was
  `!$file_writable` only; now `!$file_writable || !$file_readable`.
- **Label mismatches** — `for="js-3-1"` → `for="js-3-0"` (theme select);
  `for="staticEmail2"` removed (no matching element, Bootstrap boilerplate).
- **MKV and other video formats missing from `?raw=` allowlist** — added mkv/avi/
  m4v/wmv/flv/m4a/opus/weba.
- **Root-owned files showing `?:root` in file listing and view page** — upstream
  TinyFileManager had an explicit `if ($owner_id != 0)` guard in both directory listing
  blocks that intentionally skipped `posix_getpwuid()` for uid 0, leaving the default
  `array('name' => '?')` in place. Group had no equivalent skip so gid 0 correctly
  resolved to `root` via `posix_getgrgid()`. Fixed all three locations (2× listing
  blocks + view page): uid/gid 0 now explicitly maps to `'root'` before any posix call.
  restrictions. Required when `FM_ROOT_PATH` is outside the web root (e.g. set to `/`).
  Allowlist: gif/jpg/jpeg/png/bmp/ico/svg/webp/avif/mp3/ogg/wav/flac/mp4/webm/ogv/mov.
  Session-gated (requires valid login). Output buffers flushed before `readfile()` to
  prevent buffered HTML from corrupting binary data. `Content-Length` set cleanly.
- **Privilege elevation extended to unreadable files** — files that `www-data` cannot
  read (e.g. `root:root 640`) now auto-open the elevation modal on the edit page with
  a clear "not readable" warning. After authentication, content is fetched via a new
  `elevate_read` AJAX endpoint + daemon `read` action. Editor unlocks with file content
  loaded. Elevation daemon (`mfm-elevate.py`) updated: new `user_can_read()` helper,
  new `handle_read()` action, HANDLERS dict updated to `ping/check/read/write`.
- **GitHub Pages site** — `docs/index.html` landing page + `docs/pwd.html` client-side
  bcrypt password generator. `.nojekyll` added.
- **Favicon** — `favicon.svg` (dark navy + blue folder + amber lightning bolt) and
  `favicon.ico` (16+32 dual-size). SVG-first with ICO fallback in both head sections.
  User `$favicon_path` config still takes priority.

### Fixed
- **`FM_ROOT_PATH` double-slash when root set to `/` or `''`** — previous session added
  a restore line that forced `FM_ROOT_PATH` back to `/` after rtrim, breaking all path
  construction (`//var/www/...`). Removed restore line; `is_dir` check now uses
  `$root_path ?: '/'` as fallback only for validation.
- **`fm_get_mime_type()` PHP warning on unreadable files** — added `is_readable()` guard;
  returns `'--'` instead of triggering `finfo_file()` permission denied warning.
- **View/edit page PHP warnings on unreadable files** — `file_get_contents()` now guarded
  behind `$file_readable` flag on both view and edit pages.
- **Elevation modal auto-shows for unreadable files** — `window.mfmFileReadable` injected
  into page JS; DOMContentLoaded triggers modal automatically when file is unreadable.
- **Orphaned lines from `mfmBeginElevatedEdit` rewrite** — old function's closing
  `modal.hide()` + `toast()` + `}` left behind, causing JS SyntaxError that broke all
  JavaScript site-wide.
- **Missing `if` condition on backup AJAX handler** — eaten during `elevate_read`
  insertion, causing PHP parse error and 500 on every page load.
- **ACE editor mode selector `$modeEl` reference error** — leftover jQuery variable from
  vanilla JS conversion; converted to `modeEl.innerHTML`.
- **`aria-hidden` console warning on modals** — removed static `aria-hidden="true"`
  attribute from upload conflict, create item, elevate, and search modals.
- **Upload conflict modal focus warning** — added `document.activeElement.blur()` before
  `modal.hide()` in `resolveConflict()` and `bulkResolve()` to release focus before hide.

### Changed
- **View page image/audio/video** now served via `?raw=` instead of direct `FM_ROOT_URL`
  links — works correctly regardless of where `FM_ROOT_PATH` points on the filesystem.
- **`$elevate_available`** now true when file is unwritable OR unreadable (was only
  unwritable). Elevation now covers the full read+write case for restricted files.

### Removed
- **jQuery** — see v3.4 entries above
- **DataTables** — see v3.4 entries above
- **`previewImage` jQuery plugin** — see v3.4 entries above

- **Removed jQuery dependency entirely** — all `$.ajax()` calls replaced with a central
  `mfmFetch()` helper using native `fetch()`. All `$()` DOM selectors replaced with
  `document.getElementById` / `querySelector`. Bootstrap modal calls converted to
  `bootstrap.Modal.getOrCreateInstance()`. One less CDN request per page load.
- **Removed DataTables entirely** — replaced with ~60 lines of vanilla JS sort + filter.
  Supports smart value parsing (file sizes, numbers, text), per-column sort direction
  toggle, Unicode sort arrows via CSS `::after`, and live row filtering. Zero CDN
  dependency. Column sort CSS updated from base64 PNG sprites to clean pseudo-elements.
- **Replaced `previewImage` jQuery plugin with vanilla JS** — 30-line jQuery plugin
  factory removed. Replaced with a 20-line vanilla JS overlay that uses `closest()`,
  `dataset`, and `fixed` positioning. Cursor-following behavior preserved.
- **Converted ACE editor toolbar/select wiring to vanilla JS** — `$(function(){})`,
  `$(this).attr()`, and `.on('change')` jQuery patterns replaced with `addEventListener`
  and `getAttribute()`.
- **Global jQuery ajaxError handler removed** — 401 session-expired handling now built
  into `mfmFetch()` and fires on every request automatically.

### Removed
- **Dead `savedata` form-POST save path (JS + PHP)** — The JS else-branch that built and
  submitted a `<form>` with a `savedata` textarea was permanently unreachable (guarded by
  `if (true)`). Its corresponding PHP handler had no CSRF token check. Both removed.
- **`if (true)` wrapper** in the normal editor save path — pointless conditional stripped;
  the AJAX save call is now direct.
- **Dead cURL upload branch** — `$use_curl` was hardcoded to `false`, making the entire
  `curl_init` / `curl_exec` block (~20 lines) permanently unreachable. Removed; only the
  `stream_context_create()` / `copy()` path remains.

### Fixed
- **Duplicate `show_hidden` check** in the settings AJAX handler — identical `if` block
  was copy-pasted directly below itself with no effect. Second occurrence removed.
- **Duplicate `show_new_pwd()` function** — defined twice inside `fm_show_footer()`. The
  first (orphaned) definition removed; the second is the canonical one.
- **Obsolete `safe_mode` check** in `fm_get_size()` — `ini_get('safe_mode')` always
  returns falsy on PHP 7.0+. Removed from exec availability check.

---

## [3.3] - 2026-05-20

### Added
- **Privilege Elevation (Elevate feature)** — allows editing files that `www-data` cannot
  write (e.g. root-owned system files) without granting `www-data` any sudo permissions.
  Requires the companion `mfm-elevate` Python daemon running on the server (see
  `elevate/INSTALL.md`). Full feature set:
  - **Auto-detection** — MFM pings the daemon socket on every editor page load. If the
    daemon is not running, everything behaves exactly as before — no Elevate button appears.
  - **⚡ Elevate button** — appears alongside the disabled Save button on read-only files,
    but only when the daemon is detected. Opens a credential modal.
  - **Two-factor gate** — to elevate you must know BOTH the MFM password AND a Linux system
    username/password that authenticates via PAM and has sudo group membership.
  - **Pre-flight access check** — credentials and sudo membership are verified BEFORE
    the editor unlocks, so you can't spend time editing a file you can't actually save.
  - **Editor locked until elevated** — textarea and ACE editor are set to read-only
    when a file is not writable. Elevation unlocks the editor and enables Ctrl+S.
  - **Save (Elevated)** — after elevation succeeds, the Save button becomes a red
    "Save (Elevated)" button. Re-authenticates with the daemon on every save.
  - **root blocked** — the daemon refuses `root` as a username unconditionally.
  - **Blocked paths** — `/etc/sudoers`, `/etc/sudoers.d/`, `/etc/shadow`, `/etc/gshadow`
    and others are blocked from both viewing and editing in MFM, independent of the daemon.
    Configured via `$elevate_view_blocked` in `config.php`. Daemon enforces its own list too.
  - **Atomic writes** — daemon uses temp-file + rename for safe privileged writes.
  - **Credentials in memory only** — never persisted to localStorage or cookies.
    Cleared on page navigation.
  - **Daemon files** in new `elevate/` directory: `mfm-elevate.py`, `mfm-elevate.service`,
    `INSTALL.md`.

### Fixed
- **`/` as root path now works** — `rtrim($root_path, '\\/')` stripped the sole `/` to
  an empty string, causing a false "Root path not found" error for any user whose root
  was set to the filesystem root. Empty result is now restored to `'/'`.

---

## [3.2] - 2026-05-19

### Added
- **Version number on login page** — title now shows `Micro File Manager 3.2`.
  Auto-updates with every version bump.
- **Brute-force login protection** — failed login attempts are tracked per IP (hashed,
  never stored raw) in the system temp directory. After `$login_max_attempts` (default 5)
  consecutive failures the IP is locked out for `$login_lockout_minutes` (default 15).
  Lockout expires automatically; counter clears on successful login. Both values are
  overridable in `config.php`. Uses `$_SERVER['REMOTE_ADDR']` only (not spoofable proxy
  headers).
- **Security headers** — sent on every response: `X-Frame-Options: SAMEORIGIN` (anti-
  clickjacking), `X-Content-Type-Options: nosniff` (anti-MIME-sniff), `Referrer-Policy:
  strict-origin-when-cross-origin`, `X-XSS-Protection: 1; mode=block`. `X-Powered-By`
  header stripped to avoid leaking PHP version.
- **Session fixation prevention** — `session_regenerate_id(true)` called on every
  successful login so a pre-auth session ID can never be promoted to an authenticated one.

### Fixed
- **Session timeout ignored by Debian system cron** — Debian's `sessionclean` cron/timer
  reads `session.gc_maxlifetime` directly from `php.ini` (typically 1440 s / 24 min) and
  deletes session files on its own schedule, completely ignoring `ini_set()` at runtime.
  Fixed with two layers: (1) application-level `fm_last_activity` idle tracking so sessions
  expire correctly regardless of server GC; (2) MFM sessions stored in `./mfm_sessions/`
  next to the PHP file — a directory the system cleanup never touches — so
  `$session_timeout` is fully respected. Directory created automatically with mode `0700`.
  An `.htaccess` (`Require all denied`) is auto-dropped inside to block direct HTTP access
  on Apache. `mfm_sessions/` added to `.gitignore`.
- **Expired session not detected while idle** — the 401 redirect only fired when the user
  performed an action (editor save, file op, etc.). Added a 2-minute JS heartbeat
  (`session_ping` AJAX type) that detects expiry while idle and immediately reloads to
  the login page. Heartbeat skips hidden tabs and fires once on tab-return. Only active
  when `FM_USE_AUTH` is enabled.
- **Settings save intermittent first-try failure** — `FM_Config::save()` previously
  rewrote the target file in-place using `fopen("w")`, creating a race condition where
  any concurrent request holding the file open caused a silent write failure while the
  AJAX handler still echoed `true`. Four-part fix: (1) atomic write via `config.php.tmp`
  → `rename()`; (2) `save()` returns `true`/`false` — AJAX handler returns proper JSON,
  JS shows an alert on failure instead of silently reloading; (3) standalone mode
  bootstraps a new `config.php` instead of rewriting the running PHP file (which
  invalidated OPcache); (4) `opcache_invalidate()` called after write so the reloaded
  page reflects new settings immediately. The "sometimes the save action may not work
  on the first try" notice removed from the settings page.
- **Upload conflict resolution fails silently on symlinked directories** — `upload_resolve`
  used `realpath()` which followed symlinks outside `FM_ROOT_PATH`, silently blocking all
  conflict resolution on symlinked dirs. Dual-check fix: accept if unresolved path starts
  with `FM_ROOT_PATH` OR `realpath()` check passes. No traversal risk introduced.
- **Screenshot updated** — replaced legacy TinyFileManager screenshot with MFM-specific
  6-frame walkthrough GIF (1901×954, 3 s per frame).

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
