# Competitive Positioning for Manta AirLab

This note is meant to keep product positioning grounded in features that are already present in this repository.
It should not rely on broad marketing claims or on competitor limitations that may change over time.

## What Manta AirLab really does today

Manta AirLab is a lightweight desktop app for working with airfoil sections in dual source mode: `4-digit NACA` and `Library` profiles from local DB.

Confirmed capabilities in the current project:

- Generate 4-digit NACA profiles from the numeric code.
- Select reusable airfoils from `database/airfoil.db` (geometry + polars + metadata).
- Edit the main profile parameters directly: camber, camber position, thickness, chord, span, rotation.
- Work in both flat mode and curved mode with radius-based bending.
- Update the effective section scale directly from chord and span values, so geometry stays in practical downstream proportions.
- Export quickly to `.pts`, `.dxf`, `.csv`, and `.stl`.
- Choose output variants such as `DXF spline` or `polyline`, and `XY` or `XYZ` point formats.
- Adjust point density and decimal precision for downstream compatibility.
- Mirror geometry across axes when the workflow or use case requires it.
- Preview the section live in the GUI.
- Switch between `2D` and `3D` visualization in the same workflow.
- Preview the generated point output directly in the app and copy it without saving a file first.
- Show a quick aerodynamic estimate with `Re`, `Cl`, `Cd`, `lift`, `drag`, and `L/D`.
- Include `Cm` in aerodynamic outputs.
- Interpolate aerodynamic coefficients from DB polars (log-Re + linear-alpha) in Library mode.
- Mark out-of-domain force outputs as `ND` (without blocking geometry preview/export).
- Run a GUI `XFOIL Simulation` and override current aero coefficients live.
- Work with fluid presets for air, water, salt water, or custom properties.
- Include temperature-dependent fluid effects (`1..40 °C`) in Reynolds/force calculations.
- Allow custom aerodynamic overrides for parameters such as `cd0`, `k_drag`, `cl_max`, and `alpha_zero_lift_deg`.
- Run from GUI or CLI.
- Keep the workflow local on the machine, without requiring a web session.
- Expose benchmark material in the repo, including reference cases and summary plots.

Important limits to state clearly:

- It is optimized for NACA + Library first-pass workflows, not a full multi-physics design suite.
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
- mirror state
- curved/radius-based shaping

That means a designer can adjust the section visually and get live feedback on `lift`, `drag`, `Cl`, `Cd`, and `L/D` without stopping for a complex CFD workflow.
The practical value is that scaling, rotating, or mirroring the section is not a separate CAD cleanup step.
It happens in the same design loop where the user is already checking the aerodynamic response.

This is the clearest real value of the product: it helps users converge quickly on a reasonable wing or foil sizing with good practical approximation before deeper validation.

### 2. Reuse known profiles via local Library DB

The biggest evolution over the first version is that workflow is no longer only procedural NACA generation.
Users can now select existing profiles from local DB and apply the same transformation/export pipeline.

Practical impact:

- reuse known airfoils instead of regenerating from scratch
- compare procedural and library profiles in the same GUI flow
- use tabular aerodynamic data as baseline for quick decisions

### 3. Local desktop workflow

Manta AirLab runs as a desktop executable or from source.
This gives a few practical benefits that are worth stating:

- free to use in its open-source form
- no browser dependency
- no account or session requirement
- files stay local
- easy use in workshop, lab, or offline environments

This is more concrete than claiming to be "better" than web tools in general.

### 4. Export-first usability

Many tools are good at visualization or exploration but add friction when the user simply needs geometry ready for CAD or downstream processing.

Manta AirLab is strong when the user wants:

- `.dxf` for CAD curves
- `.pts` or `.csv` for point workflows
- `.stl` for quick 3D extrusion from chord + span
- a printable STL in a few seconds, ready to go into a 3D-print workflow without rebuilding the geometry elsewhere
- geometry exported already at the working chord and span, so import into CAD starts from practical proportions instead of a normalized profile that still needs rescaling

This export-first angle is one of the clearest real differentiators.

### 5. Curved section workflow in the same app

The curved-profile mode is an actual product advantage because it keeps:

- the same profile definition
- the same preview flow
- the same export path

That is useful when the target is not just a flat section but a bent or radius-based geometry.

### 6. Immediate 2D and 3D understanding of the same geometry

The app is not limited to a flat section plot.
It also supports direct `2D` / `3D` visualization of the same profile workflow.

That helps in two ways:

- `2D` view is faster for inspecting the section line and force directions
- `3D` view is better for understanding span, extrusion, and printable or CAD-ready volume

This is useful because the user does not have to imagine the extrusion or export first just to confirm whether the geometry looks right.

### 7. Transparent validation mindset

The repo includes benchmark cases, source notes, and summary outputs.
That does not mean the tool is "the most accurate", but it does support a stronger and more credible message:

- the estimates are not presented as magic
- validation material is visible
- assumptions and error ranges are documented

This is a better claim than generic "high accuracy".

### 8. Lower friction than legacy engineering workflows

This is true if phrased carefully.
The value is not that Manta AirLab replaces classic solvers, but that it reduces setup cost for common tasks:

- no terminal-first workflow for the main use case
- no multi-tool handoff just to get a section exported
- immediate visual and numeric feedback while editing

This is especially strong for early-stage geometry work and first-pass wing sizing.

## Positioning that should stay explicit

One message should remain very clear in all product copy:

- Manta AirLab does not replace CFD.
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
- focused scope that removes unnecessary setup for common 4-digit NACA work
- interactive GUI for first-pass design, with CLI available when repeatability matters
- commercial licensing path available in addition to open-source use

Avoid saying:

- "more accurate than X"
- "best solver"
- "better than Manta AirLab / XFOIL / foil.tools" without direct evidence
- "project management", "team collaboration", or "saved libraries" unless those features are actually implemented

## What competitor categories usually optimize for

A quick review of the main alternatives on the market today shows a recurring pattern:

- database-first tools are strong at searching, comparing, and browsing large airfoil libraries
- classic solver-driven tools are stronger for deeper aerodynamic analysis, inverse design, and multi-method studies
- larger legacy engineering tools often provide broader analysis depth, but ask for more setup, more domain knowledge, or more steps before geometry is ready for downstream use

That matters because Manta AirLab does not need to win on solver breadth.
It wins when the user wants the shortest path from a known 4-digit NACA idea to editable geometry, a quick engineering check, and exportable output.

## Additional advantages surfaced by competitor review

These are real, supportable advantages that are either missing or underplayed in the current text.

### 9. GUI first, but not GUI only

Many lightweight airfoil tools are either browser-first or analysis-first.
Manta AirLab already supports both direct interactive work and command-line usage:

- GUI for immediate shape tuning and visual feedback
- CLI for scripted export and repeatable analysis runs

This is a concrete advantage because the same product can serve both quick manual iteration and more systematic batch or documentation workflows.

### 10. Faster handoff from concept to fabrication

Some alternatives are excellent for studying polars or comparing profiles, but still leave the user to rebuild or reformat geometry before manufacturing use.

Manta AirLab already reduces that gap by letting the user:

- choose the section
- set chord and span
- preview the result
- export `.stl`, `.dxf`, `.pts`, or `.csv` directly

The practical message is not only "analysis", but "less geometry rework before CAD, CAM, or 3D printing".

### 11. Geometry is ready in working proportions, not only as a normalized profile

One subtle but important advantage is that the user is not only generating a theoretical section shape.
The tool already works with chord and span values as part of the same geometry flow.

That matters because many workflows lose time after export on tasks like:

- rescaling a normalized section in CAD
- rebuilding the extrusion length manually
- checking whether the printed or modeled part matches the intended size

Manta AirLab reduces that friction by preparing geometry in the proportions the user is already designing around.

### 12. Better fit for constrained or offline environments

Compared with browser-based workflows, a local executable remains easier to use when:

- internet access is limited or unwanted
- files should stay on the local machine
- the tool is used in a workshop, lab bench, classroom, or test environment

This is especially relevant for educational, prototyping, and maker use cases where simplicity matters more than cloud features.

### 13. Lower cognitive load than broad multi-method suites

A broad airfoil or wing-analysis suite can be powerful, but it also asks the user to navigate more concepts, more analysis modes, and more setup choices.

Manta AirLab benefits from being narrower:

- one clear geometry family
- one immediate editing model
- one fast preview loop
- one direct export path

That narrower scope is not a weakness for the intended use case.
It is a usability advantage for first-pass design work.

### 14. GPLv3 keeps the licensing model simple and explicit

The project uses GPL-3.0-only across the repository.
That is not a commercial-use differentiator, but it is a clarity advantage:

- one public license
- one set of redistribution terms
- one clear expectation for contributors and downstream users

That simplicity reduces ambiguity when evaluating whether the tool fits an engineering workflow.

### 15. Evidence-backed quick estimates instead of black-box claims

Some tools present aerodynamic outputs with little context on what is behind them.
Manta AirLab can make a better credibility claim because the repository already includes:

- benchmark cases
- reference datasets
- generated summary plots
- explicit wording about where the estimate is useful and where it is not

That supports a stronger positioning line:
the tool is not pretending to be deeper than it is, and that honesty is itself a product advantage.

### 16. Better downstream compatibility through export detail control

The advantage is not only that export exists.
It is that the export can be adapted to the receiving tool with less cleanup:

- `DXF` as spline or polyline
- `CSV` and `PTS` in `XY` or `XYZ`
- configurable decimal precision
- configurable point density

This matters because downstream tools often disagree on what "simple geometry export" should look like.
Even small controls like these reduce friction in CAD import, scripting pipelines, and CAM preparation.

### 17. Useful across air and water workflows

Many airfoil tools are presented mainly in an aircraft context.
Manta AirLab already supports a broader first-pass workflow by exposing fluid presets for:

- air
- water
- salt water
- custom fluid properties

That makes the positioning stronger for hydrofoils, marine appendages, water-channel tests, and mixed educational use cases, without pretending the model is a full specialist solver for each domain.

### 18. Simulation inputs are customizable without leaving the main tool

The quick aerodynamic model is not locked to one rigid preset.
The current app already supports meaningful customization of the simulation inputs, including:

- fluid presets
- custom density
- custom viscosity
- override values for `cd0`
- override values for `k_drag`
- override values for `cl_max`
- override values for `alpha_zero_lift_deg`

That is useful because it lets the user tune the first-pass estimate toward a more relevant scenario without leaving the tool or writing a separate script.

### 19. Handles orientation and mirrored use cases without redrawing geometry

In practical workflows, users often need to flip a section, invert a load convention, or prepare mirrored geometry for downstream use.
Manta AirLab already supports this directly through axis mirroring and rotation controls.

That is a small feature, but it is a real workflow advantage because it avoids:

- manual edits in CAD
- external scripts just to flip coordinates
- geometry mistakes introduced during rework

This is especially useful for control surfaces, opposite-side parts, inverted use cases, and downforce-oriented studies.

### 20. Point data is inspectable before export

Some tools generate output files but make the geometry data itself relatively opaque until it is opened elsewhere.
Manta AirLab already includes an in-app point preview and copy action.

That gives a few practical benefits:

- quick inspection of generated coordinates
- easier debugging of import issues
- faster handoff into spreadsheets, notebooks, scripts, or documentation

This is a small but meaningful usability edge for technical users who actually work with coordinate data.

### 21. STL output is already aligned with rapid 3D-print workflows

The STL value is not only that a mesh can be exported.
It is that the tool directly extrudes the current section using the chosen span and writes a ready-to-use ASCII STL.

That makes it practical for:

- prototype parts
- workshop checks
- quick shape validation in a slicer
- direct handoff to a 3D-print workflow without rebuilding the solid in another tool first

For the intended first-pass workflow, that is a real advantage over tools that stop at coordinates or 2D curves.

### 22. Better fit for teaching and first-pass engineering explanation

Because the tool is focused, visual, and explicit about limits, it is easier to use in contexts where the workflow itself must be understood, not only executed.

That makes it stronger for:

- teaching what NACA digits do geometrically
- showing how camber, thickness, and angle affect the section
- demonstrating how Reynolds number and fluid choice shift a quick estimate
- comparing practical geometry changes without introducing a full solver stack

This educational clarity is a real advantage over tools that are more powerful but harder to explain to non-specialists.

## Suggested positioning lines

These are aligned with the current product.

- "Design a 4-digit NACA wing section directly from the GUI and see lift and drag react in real time."
- "A fast desktop workflow for 4-digit NACA profiles, from geometry tuning to export."
- "Generate, inspect, bend, and export NACA sections in one local app."
- "Adjust the profile with sliders, get a quick aerodynamic check, and export ready-to-use geometry."
- "Built for practical 4-digit NACA work, not for bloated workflows."
- "Use the GUI for rapid iteration, then switch to the CLI when you need repeatable exports or analysis."
- "From first section idea to CAD- or print-ready geometry with less cleanup in between."
- "Focused on the part of the workflow that usually slows teams down: getting usable geometry out fast."
- "A practical first-pass design tool for 4-digit NACA sections, with clearer limits and less friction."
- "Flexible enough for CAD and scripting handoff, without turning into a heavyweight analysis suite."
- "Useful for wing, hydrofoil, and workshop geometry workflows where local speed matters more than solver complexity."
- "Inspect, tune, mirror, preview, and export the section without bouncing through extra tools."

## Competitor framing

Use competitor names sparingly.
The safest message is:

- web tools are convenient for lookup and exploration
- classic solvers are strong for deeper analysis
- broader suites are useful when the project needs many methods, but they usually add setup and learning overhead
- Manta AirLab is strongest when you need a fast, local, export-oriented workflow for 4-digit NACA sections

That positioning is honest and already supported by the repository.

## Core differentiators to keep

If only three advantages should survive into a landing page or store listing, use these:

1. Local desktop workflow with no browser friction.
2. Direct GUI-based profile tuning with live geometry and quick lift/drag feedback.
3. Geometry, quick aero estimate, and export in one tool for first-pass design work.

If five advantages can be kept, add:

4. GUI plus CLI workflow for both fast iteration and repeatable output.
5. Direct path from section setup to fabrication-ready export, including STL from chord + span.

If a longer list is acceptable, the next best additions are:

6. Export controls that better match downstream CAD and scripting requirements.
7. Local workflow that also fits offline, workshop, classroom, and lab usage.
8. Fluid presets that make the tool naturally usable for both air and water first-pass work.
9. Mirror and orientation controls that avoid manual geometry rework.
10. Validation material in the repository that supports a more credible quick-estimate message.
