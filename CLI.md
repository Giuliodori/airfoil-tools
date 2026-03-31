# Airfoil Tools CLI

This page documents the optional command-line interface for advanced users.

> The GUI remains the main workflow of the project.
> Running without CLI arguments still opens the GUI.

## Quick help

```bash
python airfoil_tools.py --help
```

## Supported commands

- `export`: export a NACA 4-digit profile to `.pts`, `.dxf`, or `.stl`
- `analyze`: print a quick aerodynamic estimate (`Re`, `Cl`, `Cd`, `lift`, `drag`, `L/D`)

---

## `export`

Export `.pts` (default format):

```bash
python airfoil_tools.py export 2412 -o NACA2412.pts
```

Export `.dxf`:

```bash
python airfoil_tools.py export 0012 --format dxf -o NACA0012.dxf
```

Main options:

- `code` (required): NACA 4-digit code (example: `2412`)
- `--format {pts,dxf,stl}` (default: `pts`)
- `-o, --output` output file path
- `--chord-mm` chord in millimeters (default: `100`)
- `--span-mm` span in millimeters for `.stl` (default: `200`)
- `--points-side` points per side (default: `100`)
- `--rotation-deg` clockwise rotation angle (default: `0`)
- `--mirror-x` mirror over X axis
- `--mirror-y` mirror over Y axis
- `--decimals` decimals for `.pts` output (default: `6`)

If `--output` is omitted, the default filename is `NACA<code>.<format>`.

---

## `analyze`

Quick estimate:

```bash
python airfoil_tools.py analyze 2412 --velocity-kmh 60 --span-mm 250 --chord-mm 120 --alpha-deg 3
```

Custom fluid:

```bash
python airfoil_tools.py analyze 0012 --fluid custom --density 1.225 --viscosity 1.81e-5
```

Main options:

- `code` (required): NACA 4-digit code
- `--velocity-kmh` flow speed (default: `50`)
- `--span-mm` span (default: `200`)
- `--chord-mm` chord (default: `100`)
- `--alpha-deg` angle of attack (default: `0`)
- `--fluid {air,water,salt water,custom}` (default: `water`)
- `--density` required with `--fluid custom`
- `--viscosity` required with `--fluid custom`

Output is concise and includes Reynolds number, aerodynamic coefficients, and force estimate.
