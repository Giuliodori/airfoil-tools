# release_tool

Python helper to create and clean release artifacts for **Airfoil Tools**.

## Prerequisites

- Python 3.10+
- Internet access for first dependency install

## Build executable (Windows)

From repository root:

```bash
python release_tool/release_tool.py build
```

What it does:
1. Installs build dependencies from `release_tool/requirements-build.txt`
2. Runs PyInstaller with `release_tool/airfoil-tools.spec`
3. Produces executable in `dist/` (typically `dist/airfoil-tools.exe`)

## Clean artifacts

From repository root:

```bash
python release_tool/release_tool.py clean
```

This removes generated build folders/files such as `build/`, `dist/`, and local `__pycache__` folders.

## Notes

- The spec file includes the entire `images/` directory, required by GUI icon/logo assets.
- If antivirus flags a fresh executable, rebuild and sign in your standard release pipeline.
