#!/usr/bin/env python3
"""Compare Airfoil Tools CLI analyze output against reference Cl/Cd data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class PointResult:
    alpha_deg: float
    cl_ref: float
    cd_ref: float
    cl_model: float
    cd_model: float
    re_model: float

    @property
    def cl_abs_err(self) -> float:
        return abs(self.cl_model - self.cl_ref)

    @property
    def cd_abs_err(self) -> float:
        return abs(self.cd_model - self.cd_ref)

    @property
    def cl_pct_err(self) -> float:
        if abs(self.cl_ref) < 1e-12:
            return float("nan")
        return self.cl_abs_err / abs(self.cl_ref) * 100.0

    @property
    def cd_pct_err(self) -> float:
        if abs(self.cd_ref) < 1e-12:
            return float("nan")
        return self.cd_abs_err / abs(self.cd_ref) * 100.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare CLI analyze values to reference Cl/Cd data.")
    parser.add_argument("--case", required=True, help="Path to benchmark case JSON.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run CLI.")
    parser.add_argument("--cli", default="airfoil_tools.py", help="Path to airfoil_tools.py.")
    parser.add_argument("--output-dir", default="benchmarks/results", help="Directory for generated report files.")
    return parser.parse_args()


def load_case(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)
    required = ("case_id", "cli", "reference_csv")
    missing = [key for key in required if key not in case]
    if missing:
        raise ValueError(f"Missing keys in case file {path}: {', '.join(missing)}")
    return case


def load_reference_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Reference CSV has no rows: {path}")
    for i, row in enumerate(rows, start=2):
        for key in ("alpha_deg", "cl_ref", "cd_ref"):
            if key not in row:
                raise ValueError(f"Reference CSV missing column '{key}' in {path}")
            if row[key] is None or str(row[key]).strip() == "":
                raise ValueError(f"Empty value for '{key}' at line {i} in {path}")
    return rows


def _parse_float_line(prefix: str, output: str) -> float:
    for line in output.splitlines():
        if line.startswith(prefix):
            value_text = line.split(":", 1)[1].strip().split()[0]
            return float(value_text)
    raise ValueError(f"Missing '{prefix}' line in CLI output")


def run_cli_analyze(python_exe: str, cli_path: str, code: str, velocity_kmh: float, span_mm: float, chord_mm: float, fluid: str, alpha_deg: float) -> tuple[float, float, float]:
    cmd = [
        python_exe,
        cli_path,
        "analyze",
        str(code),
        "--velocity-kmh",
        str(velocity_kmh),
        "--span-mm",
        str(span_mm),
        "--chord-mm",
        str(chord_mm),
        "--alpha-deg",
        str(alpha_deg),
        "--fluid",
        str(fluid),
    ]
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    stdout = completed.stdout
    re_model = _parse_float_line("Reynolds", stdout)
    cl_model = _parse_float_line("Cl", stdout)
    cd_model = _parse_float_line("Cd", stdout)
    return re_model, cl_model, cd_model


def write_comparison_csv(path: Path, points: list[PointResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "alpha_deg",
            "re_model",
            "cl_ref",
            "cl_model",
            "cl_abs_err",
            "cl_pct_err",
            "cd_ref",
            "cd_model",
            "cd_abs_err",
            "cd_pct_err",
        ])
        for p in points:
            writer.writerow([
                f"{p.alpha_deg:.6g}",
                f"{p.re_model:.6g}",
                f"{p.cl_ref:.6g}",
                f"{p.cl_model:.6g}",
                f"{p.cl_abs_err:.6g}",
                f"{p.cl_pct_err:.6g}" if not math.isnan(p.cl_pct_err) else "nan",
                f"{p.cd_ref:.6g}",
                f"{p.cd_model:.6g}",
                f"{p.cd_abs_err:.6g}",
                f"{p.cd_pct_err:.6g}" if not math.isnan(p.cd_pct_err) else "nan",
            ])


def _safe_mean(values: list[float]) -> float:
    clean = [v for v in values if not math.isnan(v)]
    return statistics.mean(clean) if clean else float("nan")


def _rmse(values: list[float]) -> float:
    return math.sqrt(statistics.mean([v * v for v in values])) if values else float("nan")


def write_markdown_report(path: Path, case: dict, points: list[PointResult], csv_path: Path) -> None:
    cl_abs = [p.cl_abs_err for p in points]
    cd_abs = [p.cd_abs_err for p in points]
    cl_pct = [p.cl_pct_err for p in points]
    cd_pct = [p.cd_pct_err for p in points]

    content = []
    content.append(f"# Benchmark report: {case['case_id']}")
    content.append("")
    content.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    content.append("")
    if "description" in case:
        content.append(f"Description: {case['description']}")
        content.append("")
    if "source" in case:
        source = case["source"]
        content.append("## Source")
        content.append("")
        content.append(f"- Name: {source.get('name', '-')}")
        content.append(f"- URL: {source.get('url', '-')}")
        content.append(f"- Notes: {source.get('notes', '-')}")
        content.append("")

    content.append("## Summary metrics")
    content.append("")
    content.append(f"- Points: {len(points)}")
    content.append(f"- Mean |Cl error|: {_safe_mean(cl_abs):.6g}")
    content.append(f"- RMSE Cl: {_rmse([p.cl_model - p.cl_ref for p in points]):.6g}")
    content.append(f"- Max |Cl error|: {max(cl_abs):.6g}")
    content.append(f"- Mean Cl % error: {_safe_mean(cl_pct):.6g}")
    content.append(f"- Mean |Cd error|: {_safe_mean(cd_abs):.6g}")
    content.append(f"- RMSE Cd: {_rmse([p.cd_model - p.cd_ref for p in points]):.6g}")
    content.append(f"- Max |Cd error|: {max(cd_abs):.6g}")
    content.append(f"- Mean Cd % error: {_safe_mean(cd_pct):.6g}")
    content.append("")

    content.append("## Output files")
    content.append("")
    content.append(f"- CSV comparison: `{csv_path.as_posix()}`")
    content.append(f"- Markdown report: `{path.as_posix()}`")
    content.append("")

    content.append("## Point-by-point")
    content.append("")
    content.append("| alpha_deg | Cl_ref | Cl_model | |err| | Cd_ref | Cd_model | |err| |")
    content.append("|---:|---:|---:|---:|---:|---:|---:|")
    for p in points:
        content.append(
            f"| {p.alpha_deg:.3f} | {p.cl_ref:.4f} | {p.cl_model:.4f} | {p.cl_abs_err:.4f} | {p.cd_ref:.4f} | {p.cd_model:.4f} | {p.cd_abs_err:.4f} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    case_path = Path(args.case)
    case = load_case(case_path)
    ref_path = Path(case["reference_csv"])
    rows = load_reference_rows(ref_path)

    cli = case["cli"]
    required_cli = ("code", "velocity_kmh", "span_mm", "chord_mm", "fluid")
    missing_cli = [key for key in required_cli if key not in cli]
    if missing_cli:
        raise ValueError(f"Missing cli settings in case file {case_path}: {', '.join(missing_cli)}")

    points: list[PointResult] = []
    for row in rows:
        alpha = float(row["alpha_deg"])
        cl_ref = float(row["cl_ref"])
        cd_ref = float(row["cd_ref"])
        re_model, cl_model, cd_model = run_cli_analyze(
            python_exe=args.python,
            cli_path=args.cli,
            code=str(cli["code"]),
            velocity_kmh=float(cli["velocity_kmh"]),
            span_mm=float(cli["span_mm"]),
            chord_mm=float(cli["chord_mm"]),
            fluid=str(cli["fluid"]),
            alpha_deg=alpha,
        )
        points.append(
            PointResult(
                alpha_deg=alpha,
                cl_ref=cl_ref,
                cd_ref=cd_ref,
                cl_model=cl_model,
                cd_model=cd_model,
                re_model=re_model,
            )
        )

    output_dir = Path(args.output_dir)
    case_id = str(case["case_id"])
    csv_path = output_dir / f"{case_id}_comparison.csv"
    report_path = output_dir / f"{case_id}_report.md"

    write_comparison_csv(csv_path, points)
    write_markdown_report(report_path, case, points, csv_path)

    print(f"Generated CSV: {csv_path}")
    print(f"Generated report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
