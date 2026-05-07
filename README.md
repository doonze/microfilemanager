# Micro File Manager (MFM)

[![Live demo](https://img.shields.io/badge/Live-Demo-brightgreen.svg?style=flat-square)](https://github.com/doonze/microfilemanager)
[![GitHub Release](https://img.shields.io/github/release/doonze/microfilemanager.svg?style=flat-square)](https://github.com/doonze/microfilemanager/releases)
[![GitHub License](https://img.shields.io/github/license/doonze/microfilemanager.svg?style=flat-square)](https://github.com/doonze/microfilemanager/blob/master/LICENSE)

> Micro File Manager is a fork of [TinyFileManager](https://github.com/prasathmani/tinyfilemanager) — a versatile, lightweight, single-file PHP web file manager. Drop one PHP file onto any server and instantly get a full-featured file management UI in your browser. MFM builds on TFM's solid foundation with a focus on upgrade-safe configuration, bug fixes, and usability improvements.

<sub>**Caution!** _Avoid utilizing this script as a standard file manager in public spaces. It is imperative to remove this script from the server after completing any tasks._</sub>

## ✨ MFM Enhancements over TinyFileManager

These are the improvements MFM adds on top of the upstream TFM codebase:

| Enhancement | Description |
|---|---|
| **Optional external config system** | All settings configurable via `config.php` — no need to touch the main file. You can still keep configs in the main file just like TFM if you prefer.<br>➕ `config.php` survives version upgrades — drop in a new `microfilemanager.php` and your settings are untouched.<br>➖ Requires copying both files when deploying — `microfilemanager.php` + `config.php`. |
| **Smart config merging** | `$auth_users`, `$readonly_users`, and `$directories_users` are merged from `config.php`, not replaced. Main file wins on conflict. |
| **Server local timezone** | File timestamps display in the server's local timezone. Removed TFM's hardcoded UTC override. Timezone is also configurable via `$default_timezone` in `config.php` if you'd prefer a specific zone over the server default. |
| **Conflict resolution** | Upload, copy, and move operations now show an **Overwrite / Rename / Cancel** dialog on name collision. TFM previously failed silently or threw an error with no recovery options. |
| **Upload conflict queue** | When uploading multiple files with simultaneous name collisions, conflicts are queued and resolved one at a time, preventing concurrent conflict dialogs from stomping each other and locking the UI. |
| **ACE editor config** | Editor theme and font size configurable via `config.php` (`$ace_theme`, `$ace_font_size`). TFM has these hard-coded; MFM exposes them as user-configurable settings. |
| **Dark-mode file viewer** | TFM's file viewer was hard-coded to a light-mode syntax theme regardless of UI theme. MFM's viewer auto-switches the Highlight.js theme to match the UI. Configurable separately for light and dark via `config.php`. |
| **Write-permission awareness** | TFM used `@fwrite` — errors were silently swallowed with zero feedback. MFM removes the suppressor and properly checks `is_writable()`, `fopen()`, and `fwrite()` at each step. Read-only files show a **Read Only** badge; the Save button is disabled; Ctrl+S is unbound. Save errors surface as specific messages (e.g., *"File is not writable. Check permissions/ownership."*) rather than TFM's generic "try again". HTTP 403 is returned server-side before any write is attempted. |
| **Permission denied on move** | When a move operation fails, MFM checks whether the source directory, destination directory, or destination file is the culprit and appends **(Permission denied)** to the error. TFM returned a generic move-failed message with no indication of why. |
| **Full config coverage** | Every configurable setting in the main file is documented and overridable in `config.php`. See `config.example.php`. |

## Demo

*(Coming soon)*

[![Micro File Manager](screenshot.gif)](screenshot.gif)

## Requirements

- PHP 5.5.0 or higher.
- Fileinfo, iconv, zip, tar and mbstring extensions are strongly recommended.

## How to use

Copy `microfilemanager.php` to your webspace — that's all :)

You can rename the file to anything you want (`files.php`, `index.php`, etc.).

### Configuration

MFM uses an external `config.php` for all settings. Copy `config.example.php` to `config.php`
in the same directory as `microfilemanager.php` and edit it to set your users and preferences.

```bash
cp config.example.php config.php
```

Set your users in `config.php`:

```php
$auth_users = array(
    'admin' => '$2y$10$...', // generate hash below
);
```

:warning: **Never commit `config.php` to a public repository** — it contains your credentials.

To generate a password hash:
```bash
php -r "echo password_hash('yourpassword', PASSWORD_DEFAULT);"
```

Or use the online tool: [https://tinyfilemanager.github.io/docs/pwd.html](https://tinyfilemanager.github.io/docs/pwd.html)

To enable/disable authentication set `$use_auth` to true or false in `config.php`.

### :loudspeaker: Features

- :cd: **Open Source:** Lightweight, minimalist, and extremely simple to set up.
- :iphone: **Mobile Friendly:** Optimized for touch devices and mobile viewing.
- :information_source: **Core Features:** Easily create, delete, modify, view, download, copy, and move files.
- :arrow_double_up: **Advanced Upload Options:** Ajax-powered uploads with drag-and-drop support, URL imports, and multi-file uploads with extension filtering.
- :file_folder: **Folder & File Management:** Create and organize folders and files effortlessly.
- :gift: **Compression Tools:** Compress and extract files in `zip` and `tar` formats.
- :sunglasses: **User Permissions:** User-specific root folder mapping and session-based access control.
- :floppy_disk: **Direct URLs:** Easily copy direct URLs for files.
- :pencil2: **Code Editor:** Includes ACE editor with syntax highlighting for 150+ languages and 35+ themes.
- :page_facing_up: **Document Preview:** Google/Microsoft document viewer for PDF/DOC/XLS/PPT, supporting previews up to 25 MB.
- :zap: **Security Features:** Backup capabilities, IP blacklisting, and whitelisting.
- :mag_right: **Search Functionality:** Use `datatable.js` for fast file search and filtering.
- :file_folder: **Customizable Listings:** Exclude specific folders and files from directory views.
- :globe_with_meridians: **Multi-language Support:** Translations available in 35+ languages with `translation.json`.
- :wrench: **External Config:** All settings manageable via `config.php` without touching the main file.
- :bangbang: **And Much More!**

## [Deploy by Docker](https://github.com/doonze/microfilemanager/wiki/Deploy-by-Docker)

Build and run with Docker Compose:

```bash
docker compose up -d
```

Or run directly:

```bash
docker build . -t doonze/microfilemanager:master
docker run -d -v /absolute/path:/var/www/html/data -p 80:80 --restart=always --name microfilemanager doonze/microfilemanager:master
```

Mount your `config.php` into the container to persist settings:

```yaml
volumes:
  - ./config.php:/var/www/html/config.php
```

Set your server timezone via the `TZ` environment variable in `docker-compose.yml`,
or leave it as UTC and control it via `$default_timezone` in `config.php`.

## License, Credit

- Available under the [GNU license](https://github.com/doonze/microfilemanager/blob/master/LICENSE)
- Forked from [TinyFileManager](https://github.com/prasathmani/tinyfilemanager) by prasathmani — original concept and development
- Original concept by github.com/alexantr/filemanager
- CDN Used — _jQuery, Bootstrap, Font Awesome, Highlight js, ace js, DropZone js, and DataTable js_
- To report a bug or request a feature, please file an [issue](https://github.com/doonze/microfilemanager/issues)
