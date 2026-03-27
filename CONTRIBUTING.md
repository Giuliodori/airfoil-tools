# Contributing

## Application Entry Point

The main application entry point is `airfoil_tools.py`.
On Windows, use `airfoil-tools.bat`.

## Release Build

To package the executable with PyInstaller, use:

```bash
python release_tool/release_tool.py build
```

To clean generated artifacts:

```bash
python release_tool/release_tool.py clean
```

More details are available in `release_tool/README.md`.

## Licensing of Contributions

By contributing to this repository, you agree that your contributions may be used under both:

- GPL-3.0-only
- a commercial license

This ensures the project can continue to be dual-licensed.
