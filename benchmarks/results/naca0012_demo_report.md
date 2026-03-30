# Benchmark report: naca0012_demo

Generated: 2026-03-30T15:22:02.807073+00:00

Description: Demo benchmark case for NACA 0012 in air

## Source

- Name: REPLACE_WITH_TRUSTED_SOURCE
- URL: https://tmbwg.github.io/turbmodels/naca0012_val.html
- Notes: Populate benchmarks/data/naca0012_reference.csv with validated source values before analysis

## Summary metrics

- Points: 6
- Mean |Cl error|: 0.028
- RMSE Cl: 0.0348903
- Max |Cl error|: 0.054
- Mean Cl % error: 6.8803
- Mean |Cd error|: 0.00345
- RMSE Cd: 0.0037932
- Max |Cd error|: 0.0046
- Mean Cd % error: 28.6761

## Output files

- CSV comparison: `benchmarks/results/naca0012_demo_comparison.csv`
- Markdown report: `benchmarks/results/naca0012_demo_report.md`

## Point-by-point

| alpha_deg | Cl_ref | Cl_model | |err| | Cd_ref | Cd_model | |err| |
|---:|---:|---:|---:|---:|---:|---:|
| -2.000 | -0.2100 | -0.2020 | 0.0080 | 0.0115 | 0.0156 | 0.0041 |
| 0.000 | 0.0000 | 0.0000 | 0.0000 | 0.0105 | 0.0150 | 0.0045 |
| 2.000 | 0.2200 | 0.2020 | 0.0180 | 0.0110 | 0.0156 | 0.0046 |
| 4.000 | 0.4400 | 0.4040 | 0.0360 | 0.0130 | 0.0173 | 0.0043 |
| 6.000 | 0.6600 | 0.6060 | 0.0540 | 0.0170 | 0.0201 | 0.0031 |
| 8.000 | 0.8600 | 0.8080 | 0.0520 | 0.0240 | 0.0241 | 0.0001 |
