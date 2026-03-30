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

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


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


@dataclass
class CaseSummary:
    case_id: str
    case_path: str
    source_name: str
    source_url: str
    points: int
    mean_cl_abs_err: float
    rmse_cl: float
    max_cl_abs_err: float
    mean_cl_pct_err: float
    mean_cd_abs_err: float
    rmse_cd: float
    max_cd_abs_err: float
    mean_cd_pct_err: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare CLI analyze values to reference Cl/Cd data.")
    parser.add_argument("--case", help="Path to benchmark case JSON. If omitted, run all JSON cases in benchmarks/cases.")
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


def discover_case_paths(case_arg: str | None) -> list[Path]:
    if case_arg:
        return [Path(case_arg)]
    case_dir = Path("benchmarks/cases")
    case_paths = sorted(case_dir.glob("*.json"))
    if not case_paths:
        raise ValueError(f"No benchmark case JSON files found in {case_dir}")
    return case_paths


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


def build_case_summary(case: dict, case_path: Path, points: list[PointResult]) -> CaseSummary:
    cl_abs = [p.cl_abs_err for p in points]
    cd_abs = [p.cd_abs_err for p in points]
    cl_pct = [p.cl_pct_err for p in points]
    cd_pct = [p.cd_pct_err for p in points]
    return CaseSummary(
        case_id=str(case["case_id"]),
        case_path=case_path.as_posix(),
        source_name=str(case.get("source", {}).get("name", "-")),
        source_url=str(case.get("source", {}).get("url", "-")),
        points=len(points),
        mean_cl_abs_err=_safe_mean(cl_abs),
        rmse_cl=_rmse([p.cl_model - p.cl_ref for p in points]),
        max_cl_abs_err=max(cl_abs),
        mean_cl_pct_err=_safe_mean(cl_pct),
        mean_cd_abs_err=_safe_mean(cd_abs),
        rmse_cd=_rmse([p.cd_model - p.cd_ref for p in points]),
        max_cd_abs_err=max(cd_abs),
        mean_cd_pct_err=_safe_mean(cd_pct),
    )


def write_summary_csv(path: Path, summaries: list[CaseSummary]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id",
            "case_path",
            "source_name",
            "source_url",
            "points",
            "mean_cl_abs_err",
            "rmse_cl",
            "max_cl_abs_err",
            "mean_cl_pct_err",
            "mean_cd_abs_err",
            "rmse_cd",
            "max_cd_abs_err",
            "mean_cd_pct_err",
        ])
        for s in summaries:
            writer.writerow([
                s.case_id,
                s.case_path,
                s.source_name,
                s.source_url,
                s.points,
                f"{s.mean_cl_abs_err:.6g}",
                f"{s.rmse_cl:.6g}",
                f"{s.max_cl_abs_err:.6g}",
                f"{s.mean_cl_pct_err:.6g}" if not math.isnan(s.mean_cl_pct_err) else "nan",
                f"{s.mean_cd_abs_err:.6g}",
                f"{s.rmse_cd:.6g}",
                f"{s.max_cd_abs_err:.6g}",
                f"{s.mean_cd_pct_err:.6g}" if not math.isnan(s.mean_cd_pct_err) else "nan",
            ])


def write_summary_chart(path: Path, summaries: list[CaseSummary]) -> Path | None:
    if plt is None or not summaries:
        return None
    labels = [s.case_id for s in summaries]
    cl_vals = [s.mean_cl_abs_err for s in summaries]
    cd_vals = [s.mean_cd_abs_err for s in summaries]
    cl_pct_vals = [s.mean_cl_pct_err for s in summaries]
    cd_pct_vals = [s.mean_cd_pct_err for s in summaries]
    x = list(range(len(summaries)))
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    axes[0, 0].bar(x, cl_vals, color="#1f77b4")
    axes[0, 0].set_title("Mean |Cl error| by case")
    axes[0, 0].set_ylabel("Mean |Cl error|")
    axes[0, 0].set_xticks(x, labels, rotation=30, ha="right")
    axes[0, 0].grid(axis="y", linestyle="--", alpha=0.4)

    axes[0, 1].bar(x, cd_vals, color="#d62728")
    axes[0, 1].set_title("Mean |Cd error| by case")
    axes[0, 1].set_ylabel("Mean |Cd error|")
    axes[0, 1].set_xticks(x, labels, rotation=30, ha="right")
    axes[0, 1].grid(axis="y", linestyle="--", alpha=0.4)

    axes[1, 0].bar(x, cl_pct_vals, color="#17a2b8")
    axes[1, 0].set_title("Mean Cl % error by case")
    axes[1, 0].set_ylabel("Mean Cl % error")
    axes[1, 0].set_xticks(x, labels, rotation=30, ha="right")
    axes[1, 0].grid(axis="y", linestyle="--", alpha=0.4)

    axes[1, 1].bar(x, cd_pct_vals, color="#ff7f0e")
    axes[1, 1].set_title("Mean Cd % error by case")
    axes[1, 1].set_ylabel("Mean Cd % error")
    axes[1, 1].set_xticks(x, labels, rotation=30, ha="right")
    axes[1, 1].grid(axis="y", linestyle="--", alpha=0.4)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def run_case(case_path: Path, args: argparse.Namespace) -> tuple[Path, Path, CaseSummary]:
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
    summary = build_case_summary(case, case_path, points)
    return csv_path, report_path, summary


def main() -> int:
    args = parse_args()
    case_paths = discover_case_paths(args.case)
    summaries: list[CaseSummary] = []
    for case_path in case_paths:
        csv_path, report_path, summary = run_case(case_path, args)
        summaries.append(summary)
        print(f"Processed case: {case_path}")
        print(f"Generated CSV: {csv_path}")
        print(f"Generated report: {report_path}")
    summary_csv_path = Path(args.output_dir) / "benchmark_summary.csv"
    write_summary_csv(summary_csv_path, summaries)
    print(f"Generated summary CSV: {summary_csv_path}")
    chart_path = write_summary_chart(Path(args.output_dir) / "benchmark_summary.png", summaries)
    if chart_path is not None:
        print(f"Generated summary chart: {chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
