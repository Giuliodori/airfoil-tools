# Benchmarks

This folder contains a lightweight workflow to compare `airfoil_tools.py analyze` outputs against external reference data.

## Structure

- `cases/`: JSON configuration for each benchmark case, including source metadata.
- `data/`: reference datasets (`alpha_deg`, `cl_ref`, `cd_ref`).
- `results/`: generated CSV and Markdown reports.
- `compare_cli_vs_reference.py`: runner and report generator.

## Run

```bash
python benchmarks/compare_cli_vs_reference.py --case benchmarks/cases/naca0012_case.json
```

With no arguments, the runner processes all JSON cases in `benchmarks/cases`.

Each run also refreshes:

- `results/benchmark_summary.csv`: per-case aggregate metrics.
- `results/benchmark_summary.png`: aggregate chart for quick comparison.

## Current reference sets

- `naca0012_case.json`: high-Re NACA 0012 using Ladson tripped data exposed by the Turbulence Modeling Resource and attributed there to NASA TM-4074.
- `naca0015_nasa_re242k_case.json`: NACA 0015 reconstructed from NASA/CR-20205001147 Figure 7 plus the explicit low-Re Cd approximation in Eq. (9) at Reynolds about 242,000.
- `naca2414_case.json`: low-Re NACA 2414 drag-polar points from UIUC LSAT Vol. 2.
- `naca2415_case.json`: low-Re NACA 2415 drag-polar points from UIUC LSAT Vol. 2.
- `naca4415_nlr_re0p78e6_case.json`: NACA 4415 clean data from the NLR/OSU package at Reynolds about 0.78 million.
- `naca4415_nlr_re1p01e6_case.json`: NACA 4415 clean data from the NLR/OSU package at Reynolds about 1.01 million.
- `naca4415_nlr_re1p26e6_case.json`: NACA 4415 clean data from the NLR/OSU package at Reynolds about 1.26 million.
- `naca4418r_nasa_re3p24e6_case.json`: high-thickness NACA 4418R conservatively reconstructed from NACA-WR-L-451 Figure 4 and Table I at Reynolds about 3.24 million.
- `clarky_case.json`: low-Re Clark-Y drag-polar points from UIUC LSAT Vol. 3, compared against a NACA 2412 proxy because the app currently supports only NACA 4-digit analysis.

## Source quality notes

- `naca0012`, `naca2414`, `naca2415`, and `naca4415` are based on tabulated or directly extractable reference data.
- `naca0015` and `naca4418r` are official NASA-based cases, but their CSV files are reconstructed from figures and source text rather than copied from a published table.
- `clarky_case.json` is intentionally a proxy mismatch and should be read as an unsupported-profile stress test, not as a calibration target.

## Important notes

- The current app model is a quick estimate, not a CFD solver.
- Use this workflow only for validation/comparison tracking.
- Each case should match the Reynolds-number range and surface condition of its source before you compare errors.
