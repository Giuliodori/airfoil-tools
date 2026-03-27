# Airfoil Tools

Airfoil Tools is a desktop GUI app to generate NACA 4-digit profiles and export them to `.pts` and `.dxf`.

![gui](images/gui.png)
![Manta](images/manta.jpg)

## Executable (recommended)

For most users, use the executable package.

### 0) Clone

```bash
git clone <repo-url>
cd airfoil-tools
```

### 1) Download

- Download the latest executable package from the project release page (or from the package shared by your team).
- Main Windows executable name:
  - `airfoil-tools.exe`

### 2) Start

- Double-click `airfoil-tools.exe`.
- The GUI opens and you can immediately generate and export profiles.

Alternative quick start from repository folder:
- Double-click `airfoil-tools.bat`

## Python source (optional)

Use this only if you want to run from source.

### Requirements (Python source only)

- Python 3.10+
- `numpy`
- `matplotlib`
- `ezdxf` (needed for `.dxf` export)

Install dependencies:

```bash
python -m pip install numpy matplotlib ezdxf
```

Run:

```bash
python airfoil_tools.py
```

On Windows, you can also use:
- `airfoil-tools.bat`

## CAD software examples for `.pts` and `.dxf`

### Common CAD/3D tools with DXF support

- AutoCAD
- Fusion 360
- SolidWorks
- FreeCAD
- Rhino
- BricsCAD
- DraftSight
- QCAD
- LibreCAD
- Onshape (DXF import workflows)

### Tools commonly used with point files (`.pts`/XYZ text)

- CloudCompare
- MeshLab
- MATLAB
- GNU Octave
- Python (NumPy / Pandas workflows)
- CATIA (point import workflows)
- Siemens NX (point import workflows)
- Autodesk Alias (point set workflows)

## License

This project is dual-licensed:

- GNU General Public License v3.0 (GPL-3.0-only) for open-source use
- Commercial license for proprietary and closed-source use

For commercial licensing, contact:
- info@duilio.cc
