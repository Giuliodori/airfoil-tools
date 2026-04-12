"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Setup module for Manta AirLab.
Creates local asset directories, installs missing Python packages, and
downloads external runtime assets such as the airfoil database and XFOIL.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DATABASE_DIR = REPO_ROOT / "database"
XFOIL_DIR = REPO_ROOT / "xfoil"

AIRFOIL_DB_PATH = DATABASE_DIR / "airfoil.db"
AIRFOIL_DB_URL = "https://github.com/Giuliodori/airfoil-db-maker/releases/latest/download/airfoil.db"

XFOIL_EXE_PATH = XFOIL_DIR / "xfoil.exe"
XFOIL_ZIP_URL = "https://web.mit.edu/drela/Public/web/xfoil/XFOIL6.99.zip"


def ensure_local_directories():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    XFOIL_DIR.mkdir(parents=True, exist_ok=True)


def _prompt_yes_no(title: str, message: str, assume_yes: bool = False):
    if assume_yes:
        return True
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno(title, message)
        finally:
            root.destroy()
    except Exception:
        resp = input(f"{message} [y/N]: ")
        return resp.strip().lower().startswith("y")


def _show_error(title: str, message: str):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showerror(title, message)
        finally:
            root.destroy()
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def run_pip_install(packages):
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    try:
        completed = subprocess.run(cmd, check=False)
    except Exception:
        return False
    return completed.returncode == 0


def ensure_python_packages(packages, *, context="", assume_yes=False, show_errors=True):
    packages = [pkg for pkg in packages if pkg]
    if not packages:
        return True

    pkg_list = ", ".join(packages)
    message = f"Missing dependencies: {pkg_list}.\nInstall now?"
    if context:
        message = f"{message}\n\n{context}"

    if not _prompt_yes_no("Install dependencies", message, assume_yes=assume_yes):
        return False

    if run_pip_install(packages):
        return True

    if show_errors:
        _show_error(
            "Install failed",
            "Unable to install required packages automatically. Please install them manually and retry.",
        )
    return False


def _download_to_path(url: str, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, open(destination, "wb") as output:
        output.write(response.read())


def _prune_xfoil_directory(keep_exe: Path):
    keep_exe = keep_exe.resolve()
    for path in XFOIL_DIR.rglob("*"):
        if path.is_dir():
            continue
        if path.resolve() == keep_exe:
            continue
        path.unlink()

    for path in sorted(XFOIL_DIR.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass


def ensure_airfoil_db(*, assume_yes=False, refresh_if_exists=False):
    ensure_local_directories()
    db_exists = AIRFOIL_DB_PATH.exists()
    if db_exists and not refresh_if_exists:
        return AIRFOIL_DB_PATH

    if db_exists:
        message = (
            "Local airfoil database found.\n"
            "Download and replace it with the latest release?\n\n"
            f"Target:\n{AIRFOIL_DB_PATH}"
        )
        title = "Update airfoil database"
    else:
        message = (
            "The local airfoil database is missing.\n"
            f"Download it now to:\n{AIRFOIL_DB_PATH}"
        )
        title = "Install airfoil database"

    if not _prompt_yes_no(title, message, assume_yes=assume_yes):
        return None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".airfoil.db.tmp", dir=str(DATABASE_DIR)
        ) as tmp:
            tmp_path = Path(tmp.name)
        try:
            _download_to_path(AIRFOIL_DB_URL, tmp_path)
            tmp_path.replace(AIRFOIL_DB_PATH)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
    except Exception as exc:
        _show_error("Download failed", f"Unable to download airfoil.db.\n\n{exc}")
        return None
    return AIRFOIL_DB_PATH


def ensure_xfoil(*, assume_yes=False):
    ensure_local_directories()
    if XFOIL_EXE_PATH.exists():
        _prune_xfoil_directory(XFOIL_EXE_PATH)
        return XFOIL_EXE_PATH

    message = (
        "XFOIL is missing.\n"
        f"Download and extract it now to:\n{XFOIL_DIR}"
    )
    if not _prompt_yes_no("Install XFOIL", message, assume_yes=assume_yes):
        return None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "xfoil.zip"
            _download_to_path(XFOIL_ZIP_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(XFOIL_DIR)
    except Exception as exc:
        _show_error("Download failed", f"Unable to download or extract XFOIL.\n\n{exc}")
        return None

    for candidate in XFOIL_DIR.rglob("xfoil.exe"):
        target = XFOIL_EXE_PATH
        if candidate.resolve() != target.resolve():
            target.write_bytes(candidate.read_bytes())
        _prune_xfoil_directory(target)
        return target

    _show_error("Install failed", f"XFOIL was downloaded but xfoil.exe was not found under:\n{XFOIL_DIR}")
    return None


def ensure_runtime_assets(
    *,
    include_airfoil_db=True,
    include_xfoil=True,
    assume_yes=False,
    refresh_airfoil_db=False,
):
    ensure_local_directories()
    results = {}
    if include_airfoil_db:
        results["airfoil_db"] = ensure_airfoil_db(
            assume_yes=assume_yes,
            refresh_if_exists=refresh_airfoil_db,
        )
    if include_xfoil:
        results["xfoil"] = ensure_xfoil(assume_yes=assume_yes)
    return results
