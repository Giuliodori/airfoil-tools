# Competitive Positioning for Airfoil Tools

This note is meant to keep product positioning grounded in features that are already present in this repository.
It should not rely on broad marketing claims or on competitor limitations that may change over time.

## What Airfoil Tools really does today

Airfoil Tools is a lightweight desktop app for working with 4-digit NACA sections.

Confirmed capabilities in the current project:

- Generate 4-digit NACA profiles from the numeric code.
- Edit the main profile parameters directly: camber, camber position, thickness, chord, span, rotation.
- Work in both flat mode and curved mode with radius-based bending.
- Export quickly to `.pts`, `.dxf`, `.csv`, and `.stl`.
- Preview the section live in the GUI.
- Show a quick aerodynamic estimate with `Re`, `Cl`, `Cd`, `lift`, `drag`, and `L/D`.
- Run from GUI or CLI.
- Keep the workflow local on the machine, without requiring a web session.
- Expose benchmark material in the repo, including reference cases and summary plots.

Important limits to state clearly:

- It is focused on 4-digit NACA profiles, not a general airfoil design suite.
- The aerodynamic model is a quick estimate, not CFD and not a full XFOIL replacement.
- The tool is optimized for speed and practicality, not for high-end solver depth.

## Real advantages to emphasize

These are the advantages that are defensible from the current codebase and docs.

### 1. Direct wing-section design from the GUI

The strongest advantage is not just "fast export". It is direct interactive design.

In the GUI, the user can move sliders and immediately see how the airfoil and the quick aerodynamic response change while editing:

- camber
- camber position
- thickness
- chord
- span
- section rotation
- curved/radius-based shaping

That means a designer can adjust the section visually and get live feedback on `lift`, `drag`, `Cl`, `Cd`, and `L/D` without stopping for a complex CFD workflow.

This is the clearest real value of the product: it helps users converge quickly on a reasonable wing or foil sizing with good practical approximation before deeper validation.

### 2. Local desktop workflow

Airfoil Tools runs as a desktop executable or from source.
This gives a few practical benefits that are worth stating:

- free to use in its open-source form
- no browser dependency
- no account or session requirement
- files stay local
- easy use in workshop, lab, or offline environments

This is more concrete than claiming to be "better" than web tools in general.

### 3. Export-first usability

Many tools are good at visualization or exploration but add friction when the user simply needs geometry ready for CAD or downstream processing.

Airfoil Tools is strong when the user wants:

- `.dxf` for CAD curves
- `.pts` or `.csv` for point workflows
- `.stl` for quick 3D extrusion from chord + span
- a printable STL in a few seconds, ready to go into a 3D-print workflow without rebuilding the geometry elsewhere

This export-first angle is one of the clearest real differentiators.

### 4. Curved section workflow in the same app

The curved-profile mode is an actual product advantage because it keeps:

- the same profile definition
- the same preview flow
- the same export path

That is useful when the target is not just a flat section but a bent or radius-based geometry.

### 5. Transparent validation mindset

The repo includes benchmark cases, source notes, and summary outputs.
That does not mean the tool is "the most accurate", but it does support a stronger and more credible message:

- the estimates are not presented as magic
- validation material is visible
- assumptions and error ranges are documented

This is a better claim than generic "high accuracy".

### 6. Lower friction than legacy engineering workflows

This is true if phrased carefully.
The value is not that Airfoil Tools replaces classic solvers, but that it reduces setup cost for common tasks:

- no terminal-first workflow for the main use case
- no multi-tool handoff just to get a section exported
- immediate visual and numeric feedback while editing

This is especially strong for early-stage geometry work and first-pass wing sizing.

## Positioning that should stay explicit

One message should remain very clear in all product copy:

- Airfoil Tools does not replace CFD.
- It does not replace wind-tunnel work or experimental validation.
- It does help designers reach a good first approximation faster, directly from the GUI.

That is a credible and useful claim, and stronger than pretending to be a full analysis suite.

## Safer comparison angles

When comparing against competitors, stay on these angles:

- simpler local workflow
- faster export to usable geometry
- integrated geometry + quick estimate in one place
- easier onboarding for non-specialists
- transparent "quick estimate" positioning instead of overpromising solver depth

Avoid saying:

- "more accurate than X"
- "best solver"
- "better than Airfoil Tools / XFOIL / foil.tools" without direct evidence
- "project management", "team collaboration", or "saved libraries" unless those features are actually implemented

## Suggested positioning lines

These are aligned with the current product.

- "Design a 4-digit NACA wing section directly from the GUI and see lift and drag react in real time."
- "A fast desktop workflow for 4-digit NACA profiles, from geometry tuning to export."
- "Generate, inspect, bend, and export NACA sections in one local app."
- "Adjust the profile with sliders, get a quick aerodynamic check, and export ready-to-use geometry."
- "Built for practical 4-digit NACA work, not for bloated workflows."

## Competitor framing

Use competitor names sparingly.
The safest message is:

- web tools are convenient for lookup and exploration
- classic solvers are strong for deeper analysis
- Airfoil Tools is strongest when you need a fast, local, export-oriented workflow for 4-digit NACA sections

That positioning is honest and already supported by the repository.

## Core differentiators to keep

If only three advantages should survive into a landing page or store listing, use these:

1. Local desktop workflow with no browser friction.
2. Direct GUI-based profile tuning with live geometry and quick lift/drag feedback.
3. Geometry, quick aero estimate, and export in one tool for first-pass design work.
