# Benchmarks

This folder contains a lightweight workflow to compare `airfoil_tools.py analyze` outputs against external reference data.

## Structure

- `cases/`: JSON configuration for each benchmark case.
- `data/`: reference datasets (`alpha_deg`, `cl_ref`, `cd_ref`).
- `results/`: generated CSV and Markdown reports.
- `compare_cli_vs_reference.py`: runner and report generator.

## Run

```bash
python benchmarks/compare_cli_vs_reference.py --case benchmarks/cases/naca0012_case.json
```

## Important notes

- The current app model is a quick estimate, not a CFD solver.
- Use this workflow only for validation/comparison tracking.
- Replace sample reference values with values from trusted sources before drawing conclusions.
