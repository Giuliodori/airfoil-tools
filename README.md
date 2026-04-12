# Manta AirLab

[![Latest Release](https://img.shields.io/github/v/release/giuliodori/airfoil-tools)](https://github.com/giuliodori/airfoil-tools/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/giuliodori/airfoil-tools/ci.yml?branch=main)](https://github.com/giuliodori/airfoil-tools/actions)

Manta AirLab is a local desktop app for designing, previewing, and exporting airfoils without bouncing between calculators, scripts, CAD cleanup, and heavyweight solver workflows.
You can work in dual source mode: fast procedural `NACA 4-digit` generation or `Library` profiles loaded from `database/airfoil.db` (geometry + polars + metadata).
Its main advantage is direct GUI-based design: move controls for chord, span, rotation, mirroring, curved shaping, and aerodynamic inputs, and immediately see how geometry plus `lift`/`drag` react.

Project sponsorship: `duilio.cc`

Created and maintained by `Fabio Giuliodori`.

![gui](images/gui.jpg)

Download the latest Windows release:

```text
https://github.com/giuliodori/airfoil-tools/releases/latest
```


## Why people use it

Most early airfoil work is not blocked by "lack of a solver". It is blocked by friction:

- finding the right profile
- generating clean geometry
- exporting in the format your downstream tool actually accepts
- getting a quick sanity check before moving on

Manta AirLab compresses that workflow into one local app. You can edit the profile directly from the GUI, move sliders, see the section update in real time, and watch the quick aerodynamic estimate react while changing parameters such as chord, span, rotation, mirroring, camber, and thickness.

The practical advantage is that geometry edits and quick aerodynamic feedback happen in the same loop. You do not need to rescale a normalized profile in CAD, flip coordinates in a script, or rebuild an extrusion elsewhere just to keep moving.

It does not replace CFD or experimental testing. It helps you arrive at a good first approximation faster, so early sizing and geometry decisions are easier before deeper validation.

## What you can do in a minute

- Instant generation of 4-digit NACA profiles
- Switch source between `NACA` and `Library` profiles from local DB
- Live preview while you adjust the section from the GUI
- Switch between `2D` and `3D` visualization of the same geometry
- Real-time response of `lift`, `drag`, `Cl`, `Cd`, `Cm`, and `L/D` while editing
- Change chord, span, rotation, mirroring, and curve shape and see the result immediately
- Export to `.pts`, `.dxf`, `.stl`, and `.csv`
- Export geometry already at the working chord and span instead of rescaling later
- Choose `DXF` spline or polyline output, plus `XY` or `XYZ` point formats
- Control point density and decimal precision for downstream compatibility
- Create an STL directly from profile + span for quick 3D workflows
- Generate a ready-to-use STL for rapid prototype and slicer workflows without rebuilding the solid in another tool first
- Switch between flat profile and curved profile (radius) modes
- Use fluid presets for air, water, salt water, or custom properties
- Include temperature (`1..40 °C`) in the Reynolds/force model
- Override key quick-model parameters such as `cd0`, `k_drag`, `cl_max`, and `alpha_zero_lift_deg`
- Run `XFOIL Simulation` from GUI to override interpolated/tabular coefficients live
- Preview the generated point data in-app and copy it directly when needed
- Use it for first-pass wing or foil sizing before CFD and physical tests


![Manta](images/manta.jpg)

## Who it is for

- Makers and builders who want geometry ready for CAD or 3D printing
- RC, marine, and hydrofoil experiments where speed matters more than deep solver setup
- Students and labs that need a simple way to inspect classic NACA sections
- Engineers doing early-stage concept work and preliminary sizing before CFD or detailed validation
- Technical users who want both a GUI workflow and a CLI path for repeatable export or analysis

## Fastest way to try it

For most users, the Windows executable is the right starting point.

### 1) Download the exe

Get it from the latest release:

If you cloned or downloaded the repository ZIP, the main Windows file is:
- `manta-airlab\dist\manta-airfoil-tools.exe`

On some Windows systems, a newly downloaded unsigned executable may show a SmartScreen prompt the first time it is opened.

### 2) Open it

- Double-click `manta-airlab\dist\manta-airfoil-tools.exe`.
- The GUI opens and you can generate and export a profile immediately.

Alternative quick start from the repository folder:
- Double-click `manta_airfoil_tools.bat`

## Python source (optional)

Use this section only if you want to run from source.

### Requirements (source only)

- Python 3.10+
- `numpy`
- `matplotlib`
- `ezdxf` (required for `.dxf` export)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Auto-install: if `numpy` or `matplotlib` are missing, the app will prompt you at launch.
If `ezdxf` is missing, the app will prompt you when saving `.dxf`.
Local runtime assets such as `database/airfoil.db` and `xfoil/xfoil.exe` are stored in local workspace folders and are not versioned.
Running setup again refreshes `airfoil.db` to the latest published release (unless you pass `--skip-airfoil-db`).

Bootstrap everything automatically:

```bash
python manta_airfoil_tools.py setup --yes
```

Run:

```bash
python manta_airfoil_tools.py
```

On Windows you can also use:
- `manta_airfoil_tools.bat`

## CLI (advanced / optional)

The GUI remains the primary workflow.

If you are a power user and want terminal commands, see the dedicated CLI guide:

- [`CLI.md`](CLI.md)
- [`ATTRIBUTION.md`](ATTRIBUTION.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

## Validation snapshot

The aerodynamic estimate is intended as a quick engineering check, not CFD and not a full XFOIL replacement.
To keep that claim honest, the repository includes a benchmark suite built from UIUC, NASA, and NLR/OSU reference data.
On the best-supported cases, mean `Cl` differences are around `0.3%` to `5%` and mean `Cd` differences around `6%` to `9%`.
Harder low-Reynolds cases can still reach about `20%` mean `Cl` difference, so the estimate should be treated as directional rather than final validation. Its role is to help with rapid first-pass sizing and catch obviously weak design directions before investing time in CFD or experiments.

The chart below is generated by `benchmarks/compare_cli_vs_reference.py` and gives a quick view of absolute and percentage error by case.

![benchmark summary](benchmarks/results/benchmark_summary.png)

Benchmark-source notices and required attributions: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

## Credits

Manta AirLab is created and maintained by `Fabio Giuliodori`.

Preferred credit when mentioning or showcasing the project:

`Manta AirLab — Airfoil Tools by Fabio Giuliodori | duilio.cc`

## CAD examples for `.pts`, `.dxf`, and `.csv`

One of the main workflow advantages of Manta AirLab is that export is not an afterthought.
You can define chord and span directly in the app, inspect the geometry in `2D` or `3D`, and export output that is already close to the form needed downstream.
That reduces rescaling, rebuilding, and format-conversion work before CAD, scripting, CAM, or 3D-print preparation.

### CAD/3D with DXF support

- AutoCAD
- CREO Parametric
- Fusion 360
- Inventor
- SolidWorks
- FreeCAD
- Rhino
- BricsCAD
- DraftSight
- QCAD
- LibreCAD
- Onshape (DXF workflow)

### Point cloud / `.pts` (XYZ) tools

- CloudCompare
- MeshLab
- MATLAB
- GNU Octave
- Python (NumPy / Pandas)
- CATIA (point import)
- Siemens NX (point import)
- Autodesk Alias (point set)

### CSV points

CSV export writes `x,y,z` with `z=0` and no header by default. In Advanced options you can switch to `x,y`
for tools that prefer 2D points. DXF export defaults to a spline, with a polyline option in Advanced options.
Commonly usable with:

- Rhino (CSV/XYZ/PTS points import)
- Fusion 360 (via point/curve import scripts)
- General point cloud or scripting workflows

## Why this workflow is different

Many airfoil tools are strong at lookup, comparison, or deeper solver work.
Manta AirLab is strongest when you already know you want a 4-digit NACA section and need the shortest path from idea to usable geometry.

That means:

- direct GUI editing with immediate geometry feedback
- quick aerodynamic response while changing the section
- geometry already scaled by chord and span for practical downstream use
- optional `2D` / `3D` confirmation before export
- local export to CAD- and prototype-friendly formats without browser dependency

That scope remains intentional: fast first-pass work with practical geometry/export flow, now extended with reusable Library profiles and DB-based aerodynamic interpolation.

## A short history of NACA profiles: the "LEGO" of aerodynamics

If you are designing a wing to lift an aircraft, a hydrofoil, or a racing car wing, you will eventually run into four key letters: `NACA`.

In the late 1920s and early 1930s, the National Advisory Committee for Aeronautics introduced a simple, powerful system: describe profile shapes with a numeric code. This brought order to a field driven by trial and error and made profiles comparable and reusable.

The 4-digit series is still widely used for preliminary design and prototypes. For example, `NACA 2412` means 2% max camber at 40% of the chord and 12% thickness.

Over time, more advanced families appeared (laminar series and supercritical profiles) to reduce drag at higher speeds. Classic NACA profiles remain a practical reference for wings, hydrofoils, control surfaces, and low-drag cooling ducts.

They are useful for designers and makers because they:

- come with decades of experimental data
- are easy to describe, generate, and compare
- let you start from a known geometry before CFD or advanced testing

`Manta AirLab` exists for this reason: take a known geometry and make it immediately usable, with `.pts`/`.dxf` export and a quick `lift` and `drag` estimate.

## Notes on 4-digit NACA profiles

4-digit NACA profiles are a historic family described by four numbers that encode geometry in a simple, repeatable way. They remain a solid reference for preliminary design, education, and quick comparisons.

### Digit meaning

The four digits are `M P TT`:

- `M` (first digit) is maximum camber as a percentage of chord.
- `P` (second digit) is the position of max camber in tenths of chord.
- `TT` (last two digits) is maximum thickness as a percentage of chord.

Example:

`NACA 2412` means 2% max camber at 40% chord, 12% thickness.

### How to read them quickly and where they are used

Symmetric profiles (zero camber) for applications where you need symmetric behavior:

- `NACA 0012` and `NACA 0015` for tail surfaces, rudders, and general profiles.

Profiles with moderate camber for wings and small aircraft:

- `NACA 2412` and `NACA 4412` for light wings and general applications needing good lift.

Thicker profiles for structural robustness or lower Reynolds numbers:

- `NACA 0018` and `NACA 4418` for structures with thickness constraints or lower Reynolds.

## License

This project is released under the GNU General Public License v3.0 only (`GPL-3.0-only`).

Project sponsorship: `duilio.cc`

Preferred project attribution: [`ATTRIBUTION.md`](ATTRIBUTION.md)

Third-party notices and attributions: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
