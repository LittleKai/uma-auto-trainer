"""
Auto-update module for Uma Musume Auto Train.
Checks GitHub Releases for new versions, downloads and applies updates.
Also checks for event map file updates from the GitHub repository.
"""

import os
import sys
import json
import hashlib
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


# --- Event map update functions ---

# Directories and files to check for event map updates
EVENT_MAP_DIRS = [
    "assets/event_map/uma_musume",
    "assets/event_map/support_card/spd",
    "assets/event_map/support_card/sta",
    "assets/event_map/support_card/pow",
    "assets/event_map/support_card/gut",
    "assets/event_map/support_card/wit",
    "assets/event_map/support_card/frd",
]
EVENT_MAP_FILES = [
    "assets/event_map/common.json",
    "assets/event_map/other_sp_event.json",
]

GITHUB_CONTENTS_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"


def _compute_git_blob_sha(file_path):
    """Compute the git blob SHA1 for a local file (same algorithm GitHub uses)."""
    with open(file_path, "rb") as f:
        data = f.read()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _fetch_github_dir(dir_path):
    """Fetch file listing from a GitHub directory via the Contents API.

    Returns list of dicts with keys: name, path, sha, download_url
    or empty list on error.
    """
    url = GITHUB_CONTENTS_API + dir_path
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "UmaAutoTrain-Updater",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            items = json.loads(resp.read().decode("utf-8"))
        return [
            {
                "name": item["name"],
                "path": item["path"],
                "sha": item["sha"],
                "download_url": item["download_url"],
            }
            for item in items
            if item["type"] == "file" and item["name"].endswith(".json")
        ]
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, OSError, KeyError):
        return []


def _fetch_github_file_info(file_path):
    """Fetch info for a single file from GitHub Contents API.

    Returns dict with keys: name, path, sha, download_url
    or None on error.
    """
    url = GITHUB_CONTENTS_API + file_path
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "UmaAutoTrain-Updater",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            item = json.loads(resp.read().decode("utf-8"))
        if item.get("type") != "file":
            return None
        return {
            "name": item["name"],
            "path": item["path"],
            "sha": item["sha"],
            "download_url": item["download_url"],
        }
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, OSError, KeyError):
        return None


def _get_app_dir():
    """Get the application root directory."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_event_updates():
    """Check GitHub for new/updated event map files.

    Returns:
        dict with keys:
            has_updates (bool): True if there are files to update
            files_to_update (list): list of dicts with {path, download_url, status}
            error (str or None): error message if something went wrong
    """
    app_dir = _get_app_dir()
    files_to_update = []
    errors = []

    # Check directories
    for dir_path in EVENT_MAP_DIRS:
        remote_files = _fetch_github_dir(dir_path)
        if not remote_files and dir_path == EVENT_MAP_DIRS[0]:
            # If the first dir fails, likely a network issue
            errors.append(f"Could not fetch {dir_path}")
            continue

        for remote_file in remote_files:
            local_path = os.path.join(app_dir, remote_file["path"])

            if not os.path.exists(local_path):
                files_to_update.append({
                    "path": remote_file["path"],
                    "download_url": remote_file["download_url"],
                    "status": "New",
                })
            else:
                local_sha = _compute_git_blob_sha(local_path)
                if local_sha != remote_file["sha"]:
                    files_to_update.append({
                        "path": remote_file["path"],
                        "download_url": remote_file["download_url"],
                        "status": "Updated",
                    })

    # Check individual files
    for file_path in EVENT_MAP_FILES:
        remote_file = _fetch_github_file_info(file_path)
        if remote_file is None:
            continue

        local_path = os.path.join(app_dir, remote_file["path"])

        if not os.path.exists(local_path):
            files_to_update.append({
                "path": remote_file["path"],
                "download_url": remote_file["download_url"],
                "status": "New",
            })
        else:
            local_sha = _compute_git_blob_sha(local_path)
            if local_sha != remote_file["sha"]:
                files_to_update.append({
                    "path": remote_file["path"],
                    "download_url": remote_file["download_url"],
                    "status": "Updated",
                })

    error_msg = "; ".join(errors) if errors else None
    return {
        "has_updates": len(files_to_update) > 0,
        "files_to_update": files_to_update,
        "error": error_msg,
    }


def download_event_files(files_to_update, progress_callback=None):
    """Download event files from GitHub.

    Args:
        files_to_update: list of dicts with {path, download_url, status}
        progress_callback: callable(current_index, total_count, file_path)

    Returns:
        int: number of files updated successfully
    """
    app_dir = _get_app_dir()
    success_count = 0
    total = len(files_to_update)

    for i, file_info in enumerate(files_to_update):
        if progress_callback:
            progress_callback(i, total, file_info["path"])

        local_path = os.path.join(app_dir, file_info["path"])

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            req = urllib.request.Request(
                file_info["download_url"],
                headers={"User-Agent": "UmaAutoTrain-Updater"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()

            with open(local_path, "wb") as f:
                f.write(data)

            success_count += 1
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            continue

    if progress_callback:
        progress_callback(total, total, "")

    return success_count
