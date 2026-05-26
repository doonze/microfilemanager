#!/usr/bin/env python3
"""
MFM Offline Asset Downloader
─────────────────────────────────────────────────────────────────────────────
Downloads all external CDN dependencies to mfm-assets/ so MFM can serve
them locally when the CDN is unreachable (enterprise/offline environments).

Run this from the directory containing microfilemanager.php:
    python download_assets.py

Re-run whenever you bump a library version in microfilemanager.php.
The VERSIONS dict below must stay in sync with the $external array in PHP.
─────────────────────────────────────────────────────────────────────────────
"""

import os
import re
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# ── Versions (keep in sync with $external in microfilemanager.php) ───────────
VERSIONS = {
    "bootstrap":   "5.3.3",
    "dropzone":    "5.9.3",
    "fontawesome": "4.7.0",
    "highlightjs": "11.9.0",
    "ace":         "1.32.2",
}

CDNJS      = "https://cdnjs.cloudflare.com/ajax/libs"
ASSETS_DIR = Path("mfm-assets")

# ── Highlight.js themes ───────────────────────────────────────────────────────
# Add any theme name from https://cdnjs.com/libraries/highlight.js
HLJS_THEMES = [
    # Dark
    "atom-one-dark", "monokai", "dracula", "nord", "a11y-dark", "github-dark",
    # Light
    "github", "atom-one-light", "vs", "xcode", "a11y-light", "default",
]

# ── ACE editor modes ──────────────────────────────────────────────────────────
# Covers all modes used by the $_ace_mode_map in microfilemanager.php
ACE_MODES = [
    "javascript", "jsx", "typescript", "tsx", "coffee", "graphqlschema",
    "html", "twig", "coldfusion", "xml",
    "json", "yaml", "toml", "ini",
    "apache_conf", "sh", "powershell", "batchfile",
    "php", "python", "ruby", "golang", "swift", "java", "c_cpp", "csharp",
    "razor", "perl", "markdown", "text", "css", "scss", "sass", "less",
    "log", "sql",
]

# ── ACE editor themes ─────────────────────────────────────────────────────────
ACE_THEMES = [
    # Dark — chaos is mandatory per project requirements
    "chaos", "monokai", "dracula", "tomorrow_night", "cobalt",
    "merbivore", "twilight", "vibrant_ink", "nord_dark", "solarized_dark",
    # Light
    "github", "dawn", "chrome", "tomorrow", "xcode",
    "textmate", "solarized_light", "tomorrow_morning",
]

# ── Static file manifest ──────────────────────────────────────────────────────
# (url, local_dest)  — optionally (url, local_dest, transform)
BASE_FILES = [
    # Bootstrap
    (f"{CDNJS}/bootstrap/{VERSIONS['bootstrap']}/css/bootstrap.min.css",
     "bootstrap/bootstrap.min.css"),
    (f"{CDNJS}/bootstrap/{VERSIONS['bootstrap']}/js/bootstrap.bundle.min.js",
     "bootstrap/bootstrap.bundle.min.js"),

    # Dropzone
    (f"{CDNJS}/dropzone/{VERSIONS['dropzone']}/min/dropzone.min.css",
     "dropzone/dropzone.min.css"),
    (f"{CDNJS}/dropzone/{VERSIONS['dropzone']}/min/dropzone.min.js",
     "dropzone/dropzone.min.js"),

    # Font Awesome CSS — font URLs are rewritten after download (see rewrite_fa_css)
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/css/font-awesome.min.css",
     "fontawesome/css/font-awesome.min.css", "rewrite_fa"),

    # Font Awesome font files
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/fontawesome-webfont.woff2",
     "fontawesome/fonts/fontawesome-webfont.woff2"),
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/fontawesome-webfont.woff",
     "fontawesome/fonts/fontawesome-webfont.woff"),
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/fontawesome-webfont.ttf",
     "fontawesome/fonts/fontawesome-webfont.ttf"),
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/fontawesome-webfont.eot",
     "fontawesome/fonts/fontawesome-webfont.eot"),
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/fontawesome-webfont.svg",
     "fontawesome/fonts/fontawesome-webfont.svg"),
    (f"{CDNJS}/font-awesome/{VERSIONS['fontawesome']}/fonts/FontAwesome.otf",
     "fontawesome/fonts/FontAwesome.otf"),

    # Highlight.js core
    (f"{CDNJS}/highlight.js/{VERSIONS['highlightjs']}/highlight.min.js",
     "highlightjs/highlight.min.js"),

    # ACE core
    (f"{CDNJS}/ace/{VERSIONS['ace']}/ace.js",
     "ace/ace.js"),
]


def build_file_list():
    """Expand dynamic entries (themes, modes) into the full download list."""
    files = list(BASE_FILES)

    for theme in HLJS_THEMES:
        v = VERSIONS["highlightjs"]
        files.append((
            f"{CDNJS}/highlight.js/{v}/styles/{theme}.min.css",
            f"highlightjs/styles/{theme}.min.css",
        ))

    for mode in ACE_MODES:
        v = VERSIONS["ace"]
        files.append((
            f"{CDNJS}/ace/{v}/mode-{mode}.js",
            f"ace/mode-{mode}.js",
        ))

    for theme in ACE_THEMES:
        v = VERSIONS["ace"]
        files.append((
            f"{CDNJS}/ace/{v}/theme-{theme}.js",
            f"ace/theme-{theme}.js",
        ))

    return files


def rewrite_fa_css(content: bytes) -> bytes:
    """
    Rewrite Font Awesome font URLs so they resolve through the ?mfm_asset= endpoint.

    The original CSS has relative paths like:
        url('../fonts/fontawesome-webfont.woff2?v=4.7.0')
    When served via ?mfm_asset=, relative paths break. Rewrite to:
        url('?mfm_asset=fontawesome/fonts/fontawesome-webfont.woff2')
    """
    text = content.decode("utf-8")
    text = re.sub(
        r"url\s*\(\s*['\"]?\.\./fonts/"
        r"(fontawesome-webfont\.[a-zA-Z0-9]+|FontAwesome\.otf)"
        r"[^'\")\s]*['\"]?\s*\)",
        lambda m: f"url('?mfm_asset=fontawesome/fonts/{m.group(1)}')",
        text,
    )
    return text.encode("utf-8")


def download_file(url: str, dest: str, transform: str | None = None) -> int | None:
    """
    Download one file. Returns byte count on success, None if 404 (skip), raises on error.
    Retries up to 3 times on transient failures.
    """
    dest_path = ASSETS_DIR / dest
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "mfm-asset-downloader/1.0"}

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()

            if transform == "rewrite_fa":
                content = rewrite_fa_css(content)

            dest_path.write_bytes(content)
            return len(content)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                   # Not available for this version — skip
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise
        except Exception:
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise

    return None


def main():
    print("MFM Offline Asset Downloader")
    print("=" * 50)
    print(f"Output dir : {ASSETS_DIR.resolve()}")
    print(f"Versions   : {json.dumps(VERSIONS)}")
    print()

    ASSETS_DIR.mkdir(exist_ok=True)

    files    = build_file_list()
    ok       = 0
    skipped  = 0
    failed   = 0
    failures = []

    for entry in files:
        url, dest = entry[0], entry[1]
        transform = entry[2] if len(entry) > 2 else None

        label = dest.ljust(52)
        print(f"  {label}", end="", flush=True)

        try:
            size = download_file(url, dest, transform)
            if size is None:
                print("SKIP (404)")
                skipped += 1
            else:
                print(f"OK  ({size:,} B)")
                ok += 1
        except Exception as exc:
            print(f"FAIL — {exc}")
            failed += 1
            failures.append((dest, str(exc)))

    # Write manifest so PHP can read version info if needed
    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "versions":  VERSIONS,
        "counts":    {"ok": ok, "skipped": skipped, "failed": failed},
    }
    (ASSETS_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print()
    print("=" * 50)
    print(f"  Downloaded : {ok}")
    print(f"  Skipped    : {skipped}  (404 — not available for this version)")
    print(f"  Failed     : {failed}")
    print(f"  Manifest   : {ASSETS_DIR}/manifest.json")

    if failures:
        print("\nFailed files:")
        for dest, err in failures:
            print(f"  {dest}: {err}")
        print("\nRe-run to retry — transient network issues are common.")
        sys.exit(1)

    print("\nAll done! MFM will use these files when the CDN is unreachable. 🐾")


if __name__ == "__main__":
    main()
