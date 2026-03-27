# Airfoil Tools

Airfoil Tools is a desktop GUI application to design and export NACA 4-digit airfoils, with optional curvature and live aerodynamic estimates.

![gui](images/gui.png)
![Manta](images/manta.jpg)

## Features

- NACA 4-digit geometry generation
- Flat and curved profile modes
- Geometric transforms (rotation, mirror X/Y)
- Live `.pts` preview
- Export to `.pts` and `.dxf`
- Quick aerodynamic estimates (Re, CL, CD, Lift, Drag, L/D)

## Requirements

- Python 3.10+
- Runtime libraries:
  - `numpy`
  - `matplotlib`
  - `ezdxf` (required for `.dxf` export)

Install dependencies (example):

```bash
python -m pip install numpy matplotlib ezdxf
```

## Run the application

### Option A — Python source

On Windows you can use the launcher:
- Double-click `airfoil-tools.bat`

Or from terminal:

```bash
python airfoil_tools.py
```

### Option B — Direct executable

If you build (or receive) the packaged executable, you can run it directly without starting from source Python.

Typical output path after build:
- `dist/airfoil-tools.exe`

## Quick workflow

1. Enter NACA code (example `2412`)
2. Set chord and points per side
3. Choose flat/curved mode and optional transforms
4. Validate live plot and aerodynamic KPIs
5. Export `.pts` or `.dxf`

## Guided examples

### Example 1 — Standard flat profile for CAD

- NACA: `2412`
- Mode: `Flat profile`
- Chord: `100` mm
- Points/side: `100`
- Export: `Save .dxf`

Use case: fast CAD import of a conventional wing section.

### Example 2 — Curved profile for duct/prop integration

- NACA: `0012`
- Mode: `Curved profile (radius)`
- Radius: `120` mm
- Curvature: `convex`
- Export: `Save .pts`

Use case: integrate an airfoil profile on curved supports or ring structures.

### Example 3 — Quick aerodynamic comparison

- Fluid: `air` or `water`
- Set velocity, aero chord, span, and alpha
- Compare CL/CD/Lift/Drag between two NACA codes

Use case: early design screening before external CFD/validation.

## Common use cases

- RC/UAV wing section prototyping
- Marine foil early sizing
- Quick `.pts` datasets for simulation pipelines
- Geometry handoff to CAD/CAM via DXF

## Build executable (PyInstaller)

This repository includes a dedicated release helper under `release_tool/`.

```bash
python release_tool/release_tool.py build
```

For full details, see:
- `release_tool/README.md`

To clean release artifacts:

```bash
python release_tool/release_tool.py clean
```

## Troubleshooting

- `ezdxf` missing during DXF export:
  - install with `python -m pip install ezdxf`
- GUI does not start:
  - verify Python + dependencies are installed
- Build issues with PyInstaller:
  - run `python release_tool/release_tool.py clean` and retry

## License

This project is dual-licensed:

- GNU General Public License v3.0 (GPL-3.0-only) for open-source use
- Commercial license for proprietary and closed-source use

You may choose the license that best fits your use case.

For commercial licensing, contact:
- info@duilio.cc
