# mfm-elevate — Server Installation Guide

One-time setup on the Debian server. Do this once; MFM will auto-detect
the daemon on every page load going forward.

---

## 1. Install dependency

```bash
sudo apt install python3-pam
```

---

## 2. Install the daemon

```bash
sudo mkdir -p /opt/mfm-elevate
sudo cp mfm-elevate.py /opt/mfm-elevate/mfm-elevate.py
sudo chmod 750 /opt/mfm-elevate/mfm-elevate.py
sudo chown root:root /opt/mfm-elevate/mfm-elevate.py
```

---

## 3. Set up logging

```bash
sudo touch /var/log/mfm-elevate.log
sudo chown root:root /var/log/mfm-elevate.log
sudo chmod 640 /var/log/mfm-elevate.log
```

---

## 4. Install and enable the systemd service

```bash
sudo cp mfm-elevate.service /etc/systemd/system/mfm-elevate.service
sudo systemctl daemon-reload
sudo systemctl enable mfm-elevate
sudo systemctl start mfm-elevate
```

---

## 5. Verify it's running

```bash
sudo systemctl status mfm-elevate
sudo tail /var/log/mfm-elevate.log
```

You should see:
```
mfm-elevate started — listening on /run/mfm-elevate/mfm-elevate.sock
```

Check socket ownership (www-data must be able to connect):
```bash
ls -la /run/mfm-elevate/
# Expected: srw-rw---- 1 root www-data ... mfm-elevate.sock
```

---

## 6. Verify PHP can reach the socket

Open MFM in a browser. Open the browser console (F12) and check:
```javascript
window.mfmElevateAvailable  // should be: true
```

If it's `false`, check:
- `sudo systemctl status mfm-elevate` — is the service running?
- `ls -la /run/mfm-elevate/` — does the socket exist with right perms?
- `/var/log/mfm-elevate.log` — any errors?

---

## 7. Test elevation in MFM

Navigate to a file that `www-data` cannot write (e.g. `/etc/hostname`).
You should see:
- The editor opens in **read-only mode**
- A yellow **⚡ Elevate** button appears next to the disabled Save button

Click Elevate, enter your Linux username + password. If access is granted,
the editor unlocks and the Save button becomes **Save (Elevated)**.

---

## Updating the daemon

```bash
sudo cp mfm-elevate.py /opt/mfm-elevate/mfm-elevate.py
sudo systemctl restart mfm-elevate
```

---

## Blocked paths (never writable via elevation)

These are hardcoded in `mfm-elevate.py` and cannot be overridden:

- `/etc/sudoers` and `/etc/sudoers.d/`
- `/etc/shadow`, `/etc/gshadow`
- `/etc/passwd`, `/etc/group`
- `/etc/ssh/`
- `/root/`
- `/proc/`, `/sys/`

To add more, edit `BLOCKED_PATHS` in `mfm-elevate.py` and restart the service.

---

## Removing the daemon

```bash
sudo systemctl stop mfm-elevate
sudo systemctl disable mfm-elevate
sudo rm /etc/systemd/system/mfm-elevate.service
sudo rm -rf /opt/mfm-elevate
sudo rm /var/log/mfm-elevate.log
sudo systemctl daemon-reload
```

MFM will fall back to normal read-only behaviour immediately — no MFM
changes needed.
