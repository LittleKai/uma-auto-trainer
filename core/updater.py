"""
Auto-update module for Uma Musume Auto Train.
Checks GitHub Releases for new versions, downloads and applies updates.
"""

import os
import sys
import json
import tempfile
import zipfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

from version import APP_VERSION, GITHUB_REPO

# Files that should NOT be overwritten during update (user settings)
PROTECTED_FILES = [
    "bot_settings.json",
    "config.json",
    "region_settings.json",
]

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _compare_versions(v1, v2):
    """Compare two semver strings. Returns 1 if v1>v2, -1 if v1<v2, 0 if equal."""
    def parse(v):
        return [int(x) for x in v.lstrip("v").split(".")]

    parts1 = parse(v1)
    parts2 = parse(v2)

    # Pad shorter list with zeros
    max_len = max(len(parts1), len(parts2))
    parts1.extend([0] * (max_len - len(parts1)))
    parts2.extend([0] * (max_len - len(parts2)))

    for a, b in zip(parts1, parts2):
        if a > b:
            return 1
        if a < b:
            return -1
    return 0


def check_for_update():
    """
    Check GitHub Releases for a newer version.

    Returns:
        dict with keys: has_update, latest_version, release_notes, download_url, html_url
        or dict with has_update=False on error/no update
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "UmaAutoTrain-Updater"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_version = data.get("tag_name", "").lstrip("v")
        if not latest_version:
            return {"has_update": False}

        if _compare_versions(latest_version, APP_VERSION) <= 0:
            return {"has_update": False, "latest_version": latest_version}

        # Find zip asset
        download_url = None
        for asset in data.get("assets", []):
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            return {"has_update": False}

        return {
            "has_update": True,
            "latest_version": latest_version,
            "release_notes": data.get("body", ""),
            "download_url": download_url,
            "html_url": data.get("html_url", ""),
        }

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, KeyError):
        return {"has_update": False}


def download_update(url, progress_callback=None):
    """
    Download update zip to a temp directory.

    Args:
        url: Download URL for the zip file
        progress_callback: callable(downloaded_bytes, total_bytes) for progress updates

    Returns:
        Path to downloaded zip file, or None on failure
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UmaAutoTrain-Updater"}
        )
        resp = urllib.request.urlopen(req, timeout=60)

        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 8192

        temp_dir = tempfile.mkdtemp(prefix="uma_update_")
        zip_path = os.path.join(temp_dir, "update.zip")

        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded, total_size)

        resp.close()
        return zip_path

    except Exception:
        return None


def apply_update(zip_path):
    """
    Extract update zip and create a batch script to replace files after app exits.

    The batch script will:
    1. Wait for current process to exit
    2. Copy new files, skipping protected user settings
    3. Restart the application
    4. Clean up temp files

    Args:
        zip_path: Path to the downloaded update zip

    Returns:
        True if batch script was launched successfully, False otherwise
    """
    try:
        # Determine app directory
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
            exe_name = os.path.basename(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            exe_name = None

        # Extract zip to temp directory
        extract_dir = os.path.join(os.path.dirname(zip_path), "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # Find the actual content directory (zip may contain a top-level folder)
        items = os.listdir(extract_dir)
        if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
            source_dir = os.path.join(extract_dir, items[0])
        else:
            source_dir = extract_dir

        # Build skip list for xcopy exclusion
        temp_dir = os.path.dirname(zip_path)
        exclude_file = os.path.join(temp_dir, "exclude.txt")
        with open(exclude_file, "w") as f:
            for pf in PROTECTED_FILES:
                f.write(pf + "\n")

        # Create batch script
        pid = os.getpid()
        batch_path = os.path.join(temp_dir, "uma_update.bat")

        # Build restart command
        if exe_name:
            restart_cmd = f'start "" "{os.path.join(app_dir, exe_name)}"'
        else:
            restart_cmd = f'start "" "{sys.executable}" "{os.path.join(app_dir, "main.py")}"'

        # Protected files copy-back: save them before overwrite, restore after
        protect_cmds_save = []
        protect_cmds_restore = []
        protect_backup_dir = os.path.join(temp_dir, "protect_backup")
        for pf in PROTECTED_FILES:
            src = os.path.join(app_dir, pf)
            dst = os.path.join(protect_backup_dir, pf)
            protect_cmds_save.append(f'if exist "{src}" (copy /Y "{src}" "{dst}" >nul 2>&1)')
            protect_cmds_restore.append(f'if exist "{dst}" (copy /Y "{dst}" "{src}" >nul 2>&1)')

        save_block = "\n".join(protect_cmds_save)
        restore_block = "\n".join(protect_cmds_restore)

        batch_content = f"""@echo off
chcp 65001 >nul 2>&1

REM Wait for the application to exit
:wait_loop
tasklist /FI "PID eq {pid}" 2>nul | find /I "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

REM Small extra delay for file handles to release
timeout /t 2 /nobreak >nul

REM Create backup dir for protected files
mkdir "{protect_backup_dir}" >nul 2>&1

REM Save protected files
{save_block}

REM Copy new files (overwrite all)
xcopy "{source_dir}\\*" "{app_dir}\\" /E /Y /I /Q >nul 2>&1

REM Restore protected files
{restore_block}

REM Restart application
{restart_cmd}

REM Cleanup temp files
timeout /t 3 /nobreak >nul
rmdir /S /Q "{temp_dir}" >nul 2>&1

REM Self-delete
(goto) 2>nul & del "%~f0"
"""

        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)

        # Launch batch script detached
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            ["cmd.exe", "/c", batch_path],
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            close_fds=True,
        )

        return True

    except Exception:
        return False
