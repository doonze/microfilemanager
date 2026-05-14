<?php
// MicroFileManager — External Configuration Example
// ─────────────────────────────────────────────────────────────────────────────
// Copy this file to config.php (same directory as microfilemanager.php).
// Any variable set here overrides the defaults in microfilemanager.php.
//
// OVERRIDE RULES:
//   Scalar settings (theme, font size, paths, etc.)
//     → config.php wins. Last assignment takes effect.
//   $auth_users and $directories_users (associative arrays)
//     → MERGED. Main file wins on duplicate keys; config.php adds new entries.
//   $readonly_users (indexed array)
//     → MERGED. Both lists combined, duplicates removed.
//   $exclude_items, $ip_whitelist, $ip_blacklist (arrays without merge logic)
//     → config.php fully REPLACES the main file's list.


// ─── Users & Auth ────────────────────────────────────────────────────────────
// MERGED with any users in microfilemanager.php — main file wins on conflict.
// An empty array here is safe; it just adds no extra users.
// Generate a hash: php -r "echo password_hash('yourpassword', PASSWORD_DEFAULT);"
$auth_users = array(
    // 'admin'     => '$2y$10$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    // 'user2'     => '$2y$10$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    // 'guest'     => '$2y$10$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
);

// Session timeout in seconds — how long an idle session stays alive before
// the user is redirected to the login page.
// Default: 14400 (4 hours).
// $session_timeout = 14400;  // 4 hours
// $session_timeout = 3600;   // 1 hour
// $session_timeout = 86400;  // 24 hours

// ─── Brute-Force Protection ───────────────────────────────────────────────────
// How many consecutive failed logins from one IP trigger a lockout.
// Default: 5 attempts, 15 minute lockout.
// $login_max_attempts    = 3;   // lock after this many consecutive failures
// $login_lockout_minutes = 15;  // how long the lockout lasts (minutes)

// ─── Readonly Users ───────────────────────────────────────────────────────────
// MERGED with readonly_users in microfilemanager.php — duplicates removed.
// Users listed here can browse and view but not upload, edit, or delete.
$readonly_users = array(
    // 'guest',
    // 'viewer',
);

// ─── Per-User Root Paths ──────────────────────────────────────────────────────
// MERGED with directories_users in microfilemanager.php — main file wins on conflict.
// Sets the root directory each user sees when they log in.
// Paths are relative to $root_path unless absolute.
$directories_users = array(
    // 'admin'  => '/var/www',
    // 'user2'  => '/home/user2',
    // 'guest'  => '/var/www/public',
);

// ─── Timezone ─────────────────────────────────────────────────────────────────
// Leave commented out (or set to '') to use the server's own timezone as
// configured in php.ini / the OS. File modification times will then display
// in local server time automatically.
// Set explicitly only if you want to force a specific zone.
// Full list: https://www.php.net/manual/en/timezones.php
// $default_timezone = 'America/Chicago';  // CST/CDT
// $default_timezone = 'America/New_York'; // EST/EDT
// $default_timezone = 'Etc/UTC';          // Force UTC

// ─── Root path ───────────────────────────────────────────────────────────────
// The directory the file manager exposes.
// $root_path = '/var/www/html';
// $root_url  = 'https://example.com';

// Server hostname — auto-detected from $_SERVER['HTTP_HOST'] by default.
// Override only if MFM generates wrong URLs (e.g. behind a reverse proxy).
// $http_host = 'example.com';

// Favicon path — full URL or document-root-relative path to a .png
// $favicon_path = 'images/icons/favicon.png';

// ─── General UI ──────────────────────────────────────────────────────────────
// Stick the top nav bar to the top of the page while scrolling.
// $sticky_navbar = true;

// Date format for file modification timestamps.
// Doc: https://www.php.net/manual/en/function.date.php
// $datetime_format = 'm/d/Y g:i A';  // US 12-hour: 05/15/2025 3:45 PM
// $datetime_format = 'd/m/Y H:i';    // EU 24-hour: 15/05/2025 15:45
// $datetime_format = 'Y-m-d H:i';    // ISO:        2025-05-15 15:45

// How paths are shown when viewing file info.
// 'full'     => full absolute path
// 'relative' => relative to root_path
// 'host'     => as seen from the web host
// $path_display_mode = 'full';

// Global read-only mode — disables ALL write operations for ALL users,
// even when auth is on. Useful for a temporary lockdown.
// $global_readonly = false;

// ─── File Browser ─────────────────────────────────────────────────────────────
// Files and folders hidden from the listing.
// Supports wildcards: '*.php', 'secret-*', etc.
// NOTE: fully REPLACES the main file's list (no merge).
// $exclude_items = array('.config', '.cache', '.DS-Store', '.*');

// Online document viewer for Office files.
// 'google' => Google Docs Viewer  |  'microsoft' => Microsoft Web Apps  |  false => disabled
// $online_viewer = 'google';

// Allowed extensions for creating/renaming files. Empty = all allowed.
// $allowed_file_extensions = 'txt,html,css,js,php';

// ─── Upload ───────────────────────────────────────────────────────────────────
// Allowed extensions for uploads. Empty = all allowed.
// $allowed_upload_extensions = 'gif,png,jpg,mp4,zip,pdf';

// Maximum upload size in bytes. Also requires matching php.ini settings:
// memory_limit, upload_max_filesize, post_max_size
// $max_upload_size_bytes = 5000000000;  // ~5 GB

// Chunk size for chunked uploads in bytes.
// Decrease (e.g. 1000000 = 1MB) if your server returns 413 Entity Too Large.
// $upload_chunk_size_bytes = 2000000;  // ~2 MB

// ─── IP Filtering ─────────────────────────────────────────────────────────────
// 'OFF' => disabled (default)
// 'AND' => must be on whitelist AND not on blacklist
// 'OR'  => must be on whitelist OR not on blacklist
// $ip_ruleset = 'OFF';

// Silently block connections that fail IP rules (true), or show a notice (false).
// $ip_silent = true;

// NOTE: these fully REPLACE the main file's arrays (no merge).
// $ip_whitelist = array('127.0.0.1', '::1');
// $ip_blacklist = array('0.0.0.0', '::');

// ─── ACE Editor ──────────────────────────────────────────────────────────────
// Enable/disable the ACE code editor on editable files.
// $edit_files = true;

// Default editor theme.
// Leave empty string to use ACE's built-in default.
// Common dark themes:  'chaos', 'dracula', 'monokai', 'cobalt', 'tomorrow_night'
// Common light themes: 'github', 'chrome', 'eclipse', 'xcode'
// Full list: https://github.com/ajaxorg/ace/tree/master/src/theme
// $ace_theme = 'chaos';

// Default editor font size.
// Valid values: 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 24, 32
// $ace_font_size = 14;

// ─── Highlight.js (file viewer syntax theme) ─────────────────────────────────
// Enable/disable syntax highlighting on file view.
// $use_highlightjs = true;

// Syntax highlighting theme for view-only mode when UI is in light theme.
// See https://highlightjs.org/examples for all available styles.
// $highlightjs_style = 'vs';

// Syntax highlighting theme for view-only mode when UI is in dark theme.
// Good options: 'atom-one-dark', 'monokai-sublime', 'github-dark', 'ir-black'
// $highlightjs_style_dark = 'atom-one-dark';
