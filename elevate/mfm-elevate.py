#!/usr/bin/env python3
"""
mfm-elevate — MicroFileManager privilege-elevation daemon
==========================================================
Listens on a Unix socket and handles four actions:

    ping        → health check / daemon detection
    check       → authenticate user via PAM, verify read/write access to target file
                  (sudo group member OR file owner with appropriate bit)
    read        → re-authenticate, then return file content as root
    write       → re-authenticate, then write file content as root

Security rules (all enforced server-side, not in PHP):
  - Root is NEVER accepted as a username.
  - User MUST either be in the sudo group OR own the file with write permission.
  - Paths in BLOCKED_PATHS (and their children) are always refused.
  - File content is capped at MAX_CONTENT_BYTES.
  - Passwords are never written to the log.

Requires: python3-pam  (apt install python3-pam)
Run as:   root  (systemd service — see mfm-elevate.service)
"""

import grp
import json
import logging
import os
import pwd
import shutil
import socket
import stat
import sys
import tempfile
import threading

import pam

# ── Configuration ─────────────────────────────────────────────────────────────

SOCKET_PATH    = "/run/mfm-elevate/mfm-elevate.sock"
SOCKET_GROUP   = "www-data"       # Group that owns the socket (must match web server)
SOCKET_MODE    = 0o660            # rw-rw---- : root + SOCKET_GROUP only
SUDO_GROUP     = "sudo"           # Group whose members are authorised to elevate
LOG_FILE       = "/var/log/mfm-elevate.log"
MAX_CONTENT_BYTES = 10 * 1024 * 1024   # 10 MB hard cap on file content

# Paths (and everything beneath them) that the daemon will NEVER write to,
# regardless of who is authenticated.  Keeps sudoers internals opaque.
BLOCKED_PATHS = [
    "/etc/sudoers",
    "/etc/sudoers.d",
    "/etc/shadow",
    "/etc/gshadow",
    "/etc/passwd",       # can't change users via MFM
    "/etc/group",        # same
    "/etc/ssh",          # SSH host keys / authorized_keys
    "/root",             # root's home
    "/proc",
    "/sys",
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("mfm-elevate")


# ── Helpers ───────────────────────────────────────────────────────────────────

def user_in_sudo_group(username: str) -> bool:
    """Return True if *username* is a member of the sudo group."""
    try:
        entry = grp.getgrnam(SUDO_GROUP)
        return username in entry.gr_mem
    except KeyError:
        log.warning("sudo group '%s' not found on this system", SUDO_GROUP)
        return False


def user_can_write(username: str, filepath: str) -> tuple:
    """
    Return (allowed: bool, reason: str) where reason is one of:
      'sudo'  — user is in the sudo group (can write anything)
      'owner' — user owns the file and has the owner-write bit set
      ''      — neither; access denied

    PAM authentication must be verified BEFORE calling this.
    """
    if user_in_sudo_group(username):
        return True, "sudo"

    try:
        uid = pwd.getpwnam(username).pw_uid
        st  = os.stat(filepath)
        if st.st_uid == uid and (st.st_mode & stat.S_IWUSR):
            return True, "owner"
    except (KeyError, OSError):
        pass

    return False, ""


def user_can_read(username: str, filepath: str) -> tuple:
    """
    Return (allowed: bool, reason: str) where reason is one of:
      'sudo'  — user is in the sudo group (can read anything)
      'owner' — user owns the file and has the owner-read bit set
      ''      — neither; access denied

    PAM authentication must be verified BEFORE calling this.
    """
    if user_in_sudo_group(username):
        return True, "sudo"

    try:
        uid = pwd.getpwnam(username).pw_uid
        st  = os.stat(filepath)
        if st.st_uid == uid and (st.st_mode & stat.S_IRUSR):
            return True, "owner"
    except (KeyError, OSError):
        pass

    return False, ""


def path_is_blocked(filepath: str) -> bool:
    """
    Return True if *filepath* (after resolving) falls inside any BLOCKED_PATHS
    entry or IS that entry.
    """
    try:
        # Resolve symlinks so a symlink to /etc/sudoers is also caught.
        resolved = os.path.realpath(filepath)
    except Exception:
        return True   # can't resolve → block it

    for blocked in BLOCKED_PATHS:
        blocked_real = os.path.realpath(blocked)
        if resolved == blocked_real or resolved.startswith(blocked_real + os.sep):
            return True
    return False


def authenticate(username: str, password: str) -> bool:
    """Authenticate *username* / *password* against PAM."""
    p = pam.pam()
    return p.authenticate(username, password, service="login")


def atomic_write(filepath: str, content: str) -> None:
    """
    Write *content* to *filepath* atomically (temp file + rename).
    Preserves the original file's mode and ownership where possible.
    Raises OSError / IOError on failure.
    """
    dirpath = os.path.dirname(os.path.abspath(filepath))

    # Capture existing stat before we touch anything
    try:
        orig_stat = os.stat(filepath)
        has_orig  = True
    except FileNotFoundError:
        has_orig  = False

    fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix=".mfm-elevate-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)

        # Restore permissions / ownership from the original file
        if has_orig:
            os.chmod(tmp_path, stat.S_IMODE(orig_stat.st_mode))
            try:
                os.chown(tmp_path, orig_stat.st_uid, orig_stat.st_gid)
            except PermissionError:
                pass   # already running as root — this shouldn't happen, but be safe

        os.replace(tmp_path, filepath)   # atomic on POSIX
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── Request handlers ──────────────────────────────────────────────────────────

def handle_ping(_req: dict) -> dict:
    """Simple liveness probe — PHP calls this on page load."""
    return {"ok": True, "version": "1.0"}


def handle_check(req: dict) -> dict:
    """
    Validate credentials and confirm the user may write the target file.

    Checks (in order):
      1. Required fields present
      2. username is not root
      3. filepath is not in BLOCKED_PATHS
      4. PAM authentication succeeds
      5. User is in the sudo group
      6. Target file exists and is not a directory
    """
    username = req.get("username", "").strip()
    password = req.get("password", "")
    filepath = req.get("filepath", "").strip()

    if not username or not password or not filepath:
        return {"ok": False, "error": "Missing required fields."}

    if username == "root":
        return {"ok": False, "error": "root cannot be used for elevation."}

    if path_is_blocked(filepath):
        return {"ok": False, "error": "That path is restricted and cannot be elevated."}

    if not authenticate(username, password):
        log.warning("check: PAM auth FAILED for user '%s' on '%s'", username, filepath)
        return {"ok": False, "error": "Authentication failed. Check username and password."}

    allowed, reason = user_can_write(username, filepath)
    if not allowed:
        log.warning("check: user '%s' denied for '%s' (not sudo, not owner)", username, filepath)
        return {"ok": False, "error": "Access denied: user does not have sudo privileges and does not own this file."}

    # File must exist (we're elevating to edit an existing file, not create one)
    if not os.path.exists(filepath):
        return {"ok": False, "error": "File not found."}

    if os.path.isdir(filepath):
        return {"ok": False, "error": "Path is a directory, not a file."}

    log.info("check: OK — user '%s' authorised for '%s' (via %s)", username, filepath, reason)
    return {"ok": True}


def handle_write(req: dict) -> dict:
    """
    Re-authenticate and write file content as root.

    Re-authentication is mandatory on every write — the check result is never
    trusted in isolation (prevents CSRF / replay via the PHP layer).
    """
    username = req.get("username", "").strip()
    password = req.get("password", "")
    filepath = req.get("filepath", "").strip()
    content  = req.get("content", "")

    if not username or not password or not filepath:
        return {"ok": False, "error": "Missing required fields."}

    if username == "root":
        return {"ok": False, "error": "root cannot be used for elevation."}

    if path_is_blocked(filepath):
        return {"ok": False, "error": "That path is restricted and cannot be elevated."}

    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        return {"ok": False, "error": "File content exceeds the 10 MB limit."}

    if not authenticate(username, password):
        log.warning("write: PAM auth FAILED for user '%s' on '%s'", username, filepath)
        return {"ok": False, "error": "Authentication failed."}

    allowed, reason = user_can_write(username, filepath)
    if not allowed:
        log.warning("write: user '%s' denied for '%s' (not sudo, not owner)", username, filepath)
        return {"ok": False, "error": "Access denied: user does not have sudo privileges and does not own this file."}

    if not os.path.isfile(filepath):
        return {"ok": False, "error": "File not found or is not a regular file."}

    try:
        atomic_write(filepath, content)
        log.info("write: OK — '%s' wrote '%s' (via %s)", username, filepath, reason)
        return {"ok": True}
    except Exception as exc:
        log.error("write: FAILED '%s' → '%s': %s", username, filepath, exc)
        return {"ok": False, "error": f"Write failed: {exc}"}


def handle_read(req: dict) -> dict:
    """
    Authenticate and return file content as root.

    Security mirrors handle_write: re-authenticates on every call,
    checks sudo group membership, respects BLOCKED_PATHS and MAX_CONTENT_BYTES.
    """
    username = req.get("username", "").strip()
    password = req.get("password", "")
    filepath = req.get("filepath", "").strip()

    if not username or not password or not filepath:
        return {"ok": False, "error": "Missing required fields."}

    if username == "root":
        return {"ok": False, "error": "root cannot be used for elevation."}

    if path_is_blocked(filepath):
        return {"ok": False, "error": "That path is restricted and cannot be elevated."}

    if not authenticate(username, password):
        log.warning("read: PAM auth FAILED for user '%s' on '%s'", username, filepath)
        return {"ok": False, "error": "Authentication failed. Check username and password."}

    allowed, reason = user_can_read(username, filepath)
    if not allowed:
        log.warning("read: user '%s' denied for '%s' (not sudo, not owner)", username, filepath)
        return {"ok": False, "error": "Access denied: user does not have sudo privileges and does not own this file."}

    if not os.path.isfile(filepath):
        return {"ok": False, "error": "File not found or is not a regular file."}

    try:
        size = os.path.getsize(filepath)
        if size > MAX_CONTENT_BYTES:
            return {"ok": False, "error": f"File exceeds the {MAX_CONTENT_BYTES // (1024*1024)} MB read limit."}
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        log.info("read: OK — user '%s' read '%s' (via %s)", username, filepath, reason)
        return {"ok": True, "content": content}
    except Exception as exc:
        log.error("read: FAILED '%s' → '%s': %s", username, filepath, exc)
        return {"ok": False, "error": f"Read failed: {exc}"}


HANDLERS = {
    "ping":  handle_ping,
    "check": handle_check,
    "read":  handle_read,
    "write": handle_write,
}


# ── Connection loop ───────────────────────────────────────────────────────────

def handle_connection(conn: socket.socket) -> None:
    """Read one JSON request, dispatch it, send one JSON response, close."""
    try:
        raw = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                break
            raw += chunk
            if len(raw) > MAX_CONTENT_BYTES + 8192:
                conn.sendall(json.dumps(
                    {"ok": False, "error": "Request too large."}
                ).encode())
                return

        if not raw:
            return

        try:
            req = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            conn.sendall(json.dumps(
                {"ok": False, "error": "Invalid JSON request."}
            ).encode())
            return

        action = req.get("action", "")
        handler = HANDLERS.get(action)
        if handler is None:
            response = {"ok": False, "error": f"Unknown action: {action!r}"}
        else:
            response = handler(req)

        conn.sendall(json.dumps(response).encode("utf-8"))

    except Exception as exc:
        log.error("Unhandled error in connection handler: %s", exc)
        try:
            conn.sendall(json.dumps(
                {"ok": False, "error": "Internal daemon error."}
            ).encode())
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if os.geteuid() != 0:
        sys.exit("mfm-elevate must run as root.")

    # Ensure socket directory exists with tight permissions
    sock_dir = os.path.dirname(SOCKET_PATH)
    os.makedirs(sock_dir, mode=0o750, exist_ok=True)

    # Remove stale socket from a previous run
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCKET_PATH)

    # Set socket ownership + permissions so only www-data can connect
    try:
        gid = grp.getgrnam(SOCKET_GROUP).gr_gid
        os.chown(SOCKET_PATH, 0, gid)
        os.chmod(SOCKET_PATH, SOCKET_MODE)
    except KeyError:
        log.warning(
            "Group '%s' not found — socket left world-readable. "
            "Set SOCKET_GROUP correctly in mfm-elevate.py.", SOCKET_GROUP
        )
        os.chmod(SOCKET_PATH, 0o666)

    srv.listen(10)
    log.info("mfm-elevate started — listening on %s", SOCKET_PATH)

    while True:
        try:
            conn, _ = srv.accept()
            t = threading.Thread(target=handle_connection, args=(conn,), daemon=True)
            t.start()
        except KeyboardInterrupt:
            log.info("mfm-elevate shutting down.")
            break
        except Exception as exc:
            log.error("Accept error: %s", exc)

    srv.close()
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)


if __name__ == "__main__":
    main()
