#!/usr/bin/env python3
"""Manta AirLab | Fabio Giuliodori — Explore https://duilio.cc.

Release helper for Airfoil Tools.

Usage:
  python release_tool/release_tool.py
  python release_tool/release_tool.py build
  python release_tool/release_tool.py clean
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def do_build(root: Path) -> None:
    req_file = root / "release_tool" / "requirements-build.txt"
    spec_file = root / "release_tool" / "airfoil-tools.spec"

    if not req_file.exists():
        raise FileNotFoundError(f"Missing requirements file: {req_file}")
    if not spec_file.exists():
        raise FileNotFoundError(f"Missing PyInstaller spec file: {spec_file}")

    run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], cwd=root)
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_file)], cwd=root)

    out_file = root / "dist" / "airfoil-tools.exe"
    if out_file.exists():
        print(f"Build completed: {out_file}")
    else:
        print("Build completed. Check dist/ for generated artifacts.")


def do_clean(root: Path) -> None:
    targets = [
        root / "build",
        root / "dist",
        root / "airfoil-tools.spec",
        root / "__pycache__",
        root / "release_tool" / "__pycache__",
    ]

    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
            print(f"Removed directory: {target}")
        elif target.is_file():
            target.unlink()
            print(f"Removed file: {target}")

    print("Clean completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and clean Airfoil Tools release artifacts")
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=["build", "clean"],
        help="Action to execute (default: build)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    if args.command == "build":
        do_build(root)
    elif args.command == "clean":
        do_clean(root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
