# MFM Code Map — microfilemanager.php

**File size:** ~280KB / 6,638 lines  
**Last mapped:** 2026-05-20 (v3.4 dev)  
**Previous size:** ~291KB / 6,786 lines — reduced by ~11KB / 148 lines total across cleanup passes

---

## 🚨 Known Issues (Fix Before Next Release)

| # | Severity | Location | Issue |
|---|----------|---------|-------|
| 1 | 🟡 Quality | `fm_show_nav_path()` | `$path2` assigned inline inside an HTML href attribute — confusing but not a bug |
| 2 | 🟡 Quality | `fm_show_footer()` JS ~line 6129 | `confirmDailog` is a persistent typo (should be `confirmDialog`) — consistent throughout HTML + JS so safe to leave |

### ✅ Fixed in v3.4 Cleanup Pass 2 (2026-05-20) — jQuery Removal

| # | Was | Now |
|---|-----|-----|
| 1 | jQuery 3.6.1 CDN dependency | Removed entirely |
| 2 | DataTables 1.13.1 (jQuery plugin) | DataTables 2.x standalone |
| 3 | `$.ajax()` — 7 call sites | `mfmFetch()` using native `fetch()` |
| 4 | `$()` DOM selectors throughout | `getElementById` / `querySelector` |
| 5 | `.modal('show'/.hide')` jQuery Bootstrap calls | `bootstrap.Modal.getOrCreateInstance()` |
| 6 | `previewImage` jQuery plugin (~30 lines) | 20-line vanilla JS overlay |
| 7 | `$(document).ready()` | `DOMContentLoaded` event listener |
| 8 | ACE toolbar + select wiring via jQuery | Vanilla `addEventListener` |
| 9 | Global jQuery `ajaxError` handler | Built into `mfmFetch()` |

### ✅ Fixed in v3.4 Cleanup Pass 1 (2026-05-20) — Dead Code

| # | Was | Fixed |
|---|-----|-------|
| 1 | 🔴 `$_POST['savedata']` — no CSRF token, dead code path | Removed entire handler |
| 2 | 🟠 JS `if (true)` wrapper + dead else branch | Removed, save path is now a clean direct AJAX call |
| 3 | 🟠 `$use_curl = false` + unreachable curl upload branch (~20 lines) | Removed, stream_context branch is now the only path |
| 4 | 🟡 `show_new_pwd()` defined twice in `fm_show_footer()` | Removed first (orphaned) definition |
| 5 | 🟡 Duplicate `show_hidden` check in settings AJAX handler | Removed copy-paste duplicate |
| 6 | 🟡 `ini_get('safe_mode')` in `fm_get_size()` — always true on PHP 7+ | Removed obsolete condition |

---

## 📐 File Structure

### BLOCK 1 — Bootstrap & Configuration (lines 1–245)
| Lines | Content |
|-------|---------|
| 1–3 | BOM + `<?php` + default `$CONFIG` JSON string |
| 4–16 | File docblock / fork attribution |
| 18–19 | `define('VERSION', ...)` |
| 21 | `define('APP_TITLE', ...)` |
| 27–236 | All configurable `$variables` — auth, paths, limits, IP rules, CDN, etc. |
| 237–245 | `define()` calls for upload limits + `FM_SESSION_ID` |

### BLOCK 2 — Runtime Initialization (lines 246–415)
| Lines | Content |
|-------|---------|
| 250–268 | `FM_Config` instantiation, load lang/theme/hidden/cols from config |
| 271–282 | `error_reporting` / `display_errors` toggle |
| 284–289 | FM_EMBED check (disable auth + sticky nav when embedded) |
| 291–358 | `set_time_limit`, charset, timezone, session setup |
| 292–335 | Session directory (`mfm_sessions/`), `.htaccess` drop, `session_start()` |
| 336–360 | Application-level session timeout (`fm_last_activity`) |
| 361–370 | Security headers (X-Frame-Options, nosniff, Referrer-Policy, XSS, X-Powered-By) |
| 373–413 | Rate-limiter helpers: `fm_rl_file()`, `fm_rl_get()`, `fm_rl_save()`, `fm_rl_record_failure()`, `fm_rl_clear()`, `fm_rl_is_locked()` |

### BLOCK 3 — Auth Gate (lines 416–644)
| Lines | Content |
|-------|---------|
| 416–420 | CSRF token generation (`$_SESSION['token']`) |
| 422–424 | Auto-disable auth if `$auth_users` is empty |
| 426–442 | `FM_ROOT_URL`, `FM_SELF_URL` construction |
| 444–449 | Logout handler |
| 451–494 | IP whitelist/blacklist check (`getClientIP()` defined inline here) |
| 496–584 | Login form + login POST handler (rate-limit → sleep(1) → verify → session fixation fix) |
| 585–644 | Post-auth path resolution: per-user dirs, `rtrim` `/` fix, `FM_ROOT_PATH` define |

### BLOCK 4 — Constants & Request Decode (lines 600–660)
| Lines | Content |
|-------|---------|
| 600–618 | All remaining `define()` calls (FM_SHOW_HIDDEN, FM_ROOT_PATH, FM_LANG, FM_READONLY, FM_IS_WIN, etc.) |
| 619–630 | JSON body decode for `application/json` AJAX requests |
| 631–644 | `define()` for FM_PATH, FM_USE_AUTH, FM_EDIT_FILE, etc. + `unset()` of used vars |

### BLOCK 5 — AJAX Dispatcher (lines 646–1016)
Entry gate at line 701: `if (session+auth OK && $_POST['ajax'] && $_POST['token'])` → `verifyToken()`.

| Lines | Type | Handler |
|-------|------|---------|
| 646 | comment | `ACTIONS` section banner |
| 657–699 | functions | Elevation helpers: `fm_elevate_send()`, `fm_elevate_available()`, `fm_path_is_blocked()` |
| 701–710 | gate | 401 JSON response if session expired during AJAX |
| 711–716 | ajax | `session_ping` — heartbeat alive check |
| 717–728 | ajax | `search` — recursive file search |
| 729–769 | ajax | `save` — write editor content to file (checks writable, atomic-ish) |
| 771–806 | ajax | `elevate_check` — PAM credential pre-flight via daemon |
| 807–850 | ajax | `elevate_write` — privileged write via daemon |
| 852–875 | ajax | `backup` — copy file with datestamp `.bak` suffix |
| 877–920 | ajax | `settings` — save config JSON (duplicate `show_hidden` check on line 901/905) |
| 921–925 | ajax | `pwdhash` — server-side bcrypt hash generation |
| 927–1015 | ajax | `upload` (URL) — fetch remote file. **`$use_curl = false` is hardcoded** — curl branch (lines 977–994) is dead code |
| 1016 | — | `exit()` — all AJAX paths terminate here |

### BLOCK 6 — Form/GET Action Handlers (lines 1018–1806)
| Lines | Action |
|-------|--------|
| 1018–1040 | `del` — single file/folder delete |
| 1041–1076 | `newfilename`+`newfile` — create file or folder |
| 1077–1184 | `copy`+`finish` — single copy/move (with overwrite dialog, permission error detail) |
| 1185–1255 | `file`+`copy_to`+`finish` — mass copy/move |
| 1256–1288 | `rename_from`+`rename_to` — rename |
| 1289–1325 | `dl` — single file download (calls `fm_download_file()`) |
| 1326–1422 | `upload_resolve` — conflict resolution (overwrite / rename / autonumber / cancel) |
| 1424–1573 | `$_FILES` — chunked upload handler (Dropzone, `.part` file assembly, conflict detection) |
| 1574–1610 | `group`+`delete` — mass delete |
| 1611–1675 | `group`+`zip`/`tar` — pack to archive |
| 1676–1746 | `unzip` — extract zip or tar |
| 1747–1806 | `chmod` — change file permissions (Linux only, `!FM_IS_WIN`) |

### BLOCK 7 — Page Rendering (lines 1807–3129)
Second `ACTIONS` comment banner at line 1807 (confusing — it's actually rendering, not actions).

| Lines | Page |
|-------|------|
| 1807–1820 | Current path + directory scan (builds `$folders[]` and `$files[]`) |
| 1852–2174 | **Upload page** — Dropzone form, URL upload form, conflict modal + conflict queue JS |
| 2178–2222 | **Bulk copy/move page** — folder tree picker |
| 2226–2282 | **Copy/move destination picker** — second folder tree variant |
| 2285–2375 | **Settings page** — toggle form, help sidebar with links |
| 2377–2432 | **Help page** — author card, links sidebar |
| 2436–2653 | **File view page** — image/video/audio/text/doc viewer |
| 2656–2795 | **File edit page** — normal textarea + ACE editor |
| 2691–2713 | ⚠️ `savedata` POST handler — **no CSRF token check** (dead code path) |
| 2798–2868 | **Chmod page** — permission bit checkboxes |
| 2872–3120 | **Main file listing** — DataTables table, folder/file rows, action buttons |
| 3120 | `fm_show_footer()` call — closes main page |

### BLOCK 8 — PHP Helper Functions (lines 3130–4434)
| Lines | Function | Purpose |
|-------|----------|---------|
| 3130 | `print_external($key)` | Print CDN link/script tag by key |
| 3148 | `verifyToken($token)` | CSRF token check |
| 3161 | `fm_rdelete($path)` | Recursive delete |
| 3192 | `fm_rchmod($path, $filemode, $dirmode)` | Recursive chmod |
| 3222 | `fm_is_valid_ext($filename)` | Check against allowed extension list |
| 3238 | `fm_rename($old, $new)` | Safe rename (checks ext + existence) |
| 3257 | `fm_rcopy($path, $dest, $upd, $force)` | Recursive copy |
| 3290 | `fm_mkdir($dir, $force)` | Safe mkdir |
| 3310 | `fm_copy($f1, $f2, $upd)` | Single file copy with timestamp check |
| 3331 | `fm_get_mime_type($file_path)` | finfo → mime_content_type → shell_exec fallback |
| 3354 | `fm_redirect($url, $code)` | HTTP redirect + exit |
| 3366 | `get_absolute_path($path)` | Resolve `..` and normalize separators |
| 3387 | `fm_clean_path($path, $trim)` | Sanitize path (strips `../`, normalizes) |
| 3404 | `fm_get_parent_path($path)` | Return parent directory |
| 3418 | `fm_get_display_path($file_path)` | Format path per `$path_display_mode` |
| 3448 | `fm_is_exclude_items($name, $path)` | Check against `$exclude_items` list |
| 3470 | `fm_get_translations($tr)` | Load language strings array |
| 3496 | `fm_get_size($file)` | Get file size (exec/COM/filesize). ⚠️ `safe_mode` check is PHP 5 vestige |
| 3543 | `fm_get_filesize($size)` | Human-readable size (B/KB/MB...) |
| 3557 | `fm_get_zif_info($path, $ext)` | List archive contents |
| 3603 | `fm_enc($text)` | `htmlspecialchars()` wrapper |
| 3613 | `fm_isvalid_filename($text)` | Reject dangerous filename characters |
| 3623 | `fm_set_msg($msg, $status)` | Store flash message in session |
| 3634 | `fm_is_utf8($string)` | UTF-8 check (used at line 2536) |
| 3644 | `fm_convert_win($filename)` | iconv Windows filename fix |
| 3656 | `fm_object_to_array($obj)` | Recursively cast object to array (used by FM_Config) |
| 3672 | `fm_get_file_icon_class($path)` | Map extension → Font Awesome class |
| 3877 | `fm_get_image_exts()` | Image extension list |
| 3886 | `fm_get_video_exts()` | Video extension list |
| 3895 | `fm_get_audio_exts()` | Audio extension list |
| 3904 | `fm_get_text_exts()` | Text/editable extension list |
| 4018 | `fm_get_text_mimes()` | Text MIME types |
| 4034 | `fm_get_text_names()` | Extensionless text file names (readme, license, etc.) |
| 4049 | `fm_get_onlineViewer_exts()` | Doc viewer supported extensions |
| 4059 | `fm_get_file_mimes($extension)` | Extension → MIME type map for downloads |
| 4114 | `scan($dir, $filter)` | Recursive regex file search |
| 4144 | `fm_download_file($fileLocation, $fileName, $chunkSize)` | Streaming file download with range support |

### BLOCK 9 — Classes (lines 4221–4513)
| Lines | Class | Purpose |
|-------|-------|---------|
| 4221 | `FM_Zipper` | ZipArchive wrapper (create, unzip, addFileOrDir, addDir) |
| 4329 | `FM_Zipper_Tar` | PharData/tar wrapper (create, unzip, addFileOrDir, addDir) |
| 4434 | `FM_Config` | Config JSON load/save. `save()` is atomic via tmp+rename, OPcache-aware |

### BLOCK 10 — Template Functions (lines 4516–5694)
| Lines | Function | Purpose |
|-------|----------|---------|
| 4516 | `fm_show_nav_path($path)` | Top navbar — breadcrumbs, search, upload, new item, user avatar dropdown |
| 4602 | `fm_show_message()` | Flash message display |
| 4615 | `fm_show_header_login()` | Full HTML head for login page (includes inline SVG background) |
| 4761 | `fm_show_footer_login()` | Login page closing tags |
| 4777 | `fm_show_header()` | Full HTML head for main app (Bootstrap, FontAwesome, inline CSS) |
| 5695 | `fm_show_footer()` | Closing tags + ALL JavaScript for the main app |

### BLOCK 11 — JavaScript (inside `fm_show_footer()`, lines 5695–6650+)
| Lines | Content |
|-------|---------|
| 5695–5750 | Bootstrap/jQuery/DataTables script tags |
| 5751–5790 | CSRF token injection (`window.csrf`), session heartbeat (2-min ping), global `ajaxError` handler |
| 5791–5822 | `edit_save()` — main save function, checks `mfmElevateState.active` |
| 5823–5874 | ⚠️ `if (true)` AJAX save block — `else` branch (lines 5854–5873) is **permanently dead** |
| 5876 | ⚠️ `show_new_pwd()` — **FIRST definition** (duplicate!) |
| 5880–5978 | Elevation JS: `mfmShowElevateModal()`, `mfmCheckElevate()`, `mfmBeginElevatedEdit()` |
| 5980 | ⚠️ `show_new_pwd()` — **SECOND definition** (the one that actually survives hoisting) |
| 5983–6020 | `save_settings()`, `new_password_hash()` |
| 6021–6075 | `upload_from_url()` |
| 6076–6100 | `search_template()`, `fm_search()` |
| 6129–6145 | `confirmDailog()` ⚠️ (typo — should be `confirmDialog`) |
| 6146–6175 | `previewImage` jQuery plugin (inline) |
| 6176–6260 | `$(document).ready()` — DataTable init, search filter, keyboard shortcuts, modal wires |
| 6260–6330 | Remaining DOM-ready event handlers (select-all, bulk actions, drag-drop, etc.) |

### BLOCK 12 — ACE Editor Init (lines 6300–6440, conditionally rendered)
Only output when `?edit=...&env=ace` is active.

| Lines | Content |
|-------|---------|
| 6300–6400 | PHP-side `$_ace_mode_map` array (extension → ACE mode) |
| 6400–6450 | ACE `editor` init, theme/mode set, Ctrl+S binding |
| 6450–6600 | `renderThemeMode()` — massive static JS object of all ACE themes and modes |

### BLOCK 13 — Translations (lines 6659–6786)
| Lines | Content |
|-------|---------|
| 6659 | `function lng($txt)` |
| 6660–6776 | `fm_get_translations($tr)` — single English translation array (only language present) |
| 6777–6786 | File end: `$i18n` lookup + `lng()` return |

---

## 🧹 Cleanup Candidates (No Functional Impact)

- **Line 958:** `$use_curl = false` + the dead `} else if ($use_curl) {` curl block (~25 lines). Remove both.
- **Lines 5854–5873:** Dead `else` branch in JS save path. Remove `if (true) {` wrapper and the entire else block.
- **Lines 2691–2713:** `$_POST['savedata']` PHP handler — dead code + no CSRF token. Remove it.
- **Line 5876 OR 5980:** One of the two `show_new_pwd()` definitions. Remove the first (5876).
- **Line 1807:** Second `ACTIONS` banner comment — rename to `// PAGE RENDERING` for clarity.
- **Line 4558:** `$path2 = $path ? $path : '.'` inline assignment — extract to a real variable above.
- **Line 901+905:** Duplicate `show_hidden` check in settings handler (lines 901–904 are a copy-paste of 897–900).
- **Line 3496:** `fm_get_size()` — remove `safe_mode` check, simplify to filesize() for 64-bit PHP (or at minimum remove the `!ini_get('safe_mode')` condition that's always true on PHP 7+).

---

## 🔒 Security Notes

| Issue | Status |
|-------|--------|
| CSRF on all form actions | ✅ `verifyToken()` used everywhere **except** `savedata` handler (line 2691) |
| Session fixation | ✅ `session_regenerate_id(true)` on login |
| Brute-force protection | ✅ Rate-limiter on login (IP-hashed file state) |
| Security headers | ✅ X-Frame-Options, nosniff, Referrer-Policy, XSS, no X-Powered-By |
| Path traversal | ✅ `fm_clean_path()` strips `../` before all file ops |
| Elevation blocklist | ✅ `/etc/sudoers`, `/etc/shadow`, etc. blocked at PHP layer AND daemon layer |
| `savedata` no-token | 🔴 **Must fix** — see issue #1 above |

---

*Generated by projects-puppy. Update this file whenever major structural changes are made.*
