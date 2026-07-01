#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path


CHSH_CLASSICAL_BOUND = 2.0
CHSH_SECURE_THRESHOLD = 2.4
QBER_SECURE_THRESHOLD = 0.08
QBER_INSECURE_THRESHOLD = 0.15


def load_summary(path: Path) -> list[dict]:
    if not path.exists():
        raise RuntimeError(f"Summary file not found: {path}")

    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    for row in rows:
        for field in [
            "noise_level",
            "eve_attack_probability",
            "abs_chsh_mean",
            "abs_chsh_stddev",
            "qber_mean",
            "qber_stddev",
        ]:
            row[field] = float(row[field])
    return rows


def require_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/e91_matplotlib_cache")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "matplotlib is required. Install it with: .venv/bin/python -m pip install matplotlib"
        ) from exc
    return plt


def save_chsh_plot(plt, rows: list[dict], x_field: str, title: str, xlabel: str, output_path: Path) -> None:
    x_values = [row[x_field] for row in rows]
    y_values = [row["abs_chsh_mean"] for row in rows]
    y_errors = [row["abs_chsh_stddev"] for row in rows]

    plt.figure(figsize=(8, 5))
    plt.errorbar(x_values, y_values, yerr=y_errors, marker="o", capsize=4)
    plt.axhline(CHSH_CLASSICAL_BOUND, color="red", linestyle="--", label="Classical bound = 2.0")
    plt.axhline(CHSH_SECURE_THRESHOLD, color="orange", linestyle="--", label="Secure threshold = 2.4")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("abs_chsh_mean")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def save_qber_plot(plt, rows: list[dict], x_field: str, title: str, xlabel: str, output_path: Path) -> None:
    x_values = [row[x_field] for row in rows]
    y_values = [row["qber_mean"] for row in rows]
    y_errors = [row["qber_stddev"] for row in rows]

    plt.figure(figsize=(8, 5))
    plt.errorbar(x_values, y_values, yerr=y_errors, marker="o", capsize=4)
    plt.axhline(QBER_SECURE_THRESHOLD, color="orange", linestyle="--", label="Secure threshold = 0.08")
    plt.axhline(QBER_INSECURE_THRESHOLD, color="red", linestyle="--", label="Insecure threshold = 0.15")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("qber_mean")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def save_combined_bar_plot(plt, rows: list[dict], metric: str, title: str, ylabel: str, output_path: Path) -> None:
    labels = [
        f"n={row['noise_level']:.2f}\ne={row['eve_attack_probability']:.2f}"
        for row in rows
    ]
    y_values = [row[metric] for row in rows]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, y_values)
    if metric == "abs_chsh_mean":
        plt.axhline(CHSH_CLASSICAL_BOUND, color="red", linestyle="--", label="Classical bound = 2.0")
        plt.axhline(CHSH_SECURE_THRESHOLD, color="orange", linestyle="--", label="Secure threshold = 2.4")
        plt.legend()
    if metric == "qber_mean":
        plt.axhline(QBER_SECURE_THRESHOLD, color="orange", linestyle="--", label="Secure threshold = 0.08")
        plt.axhline(QBER_INSECURE_THRESHOLD, color="red", linestyle="--", label="Insecure threshold = 0.15")
        plt.legend()
    plt.title(title)
    plt.xlabel("combined scenario")
    plt.ylabel(ylabel)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def plot_results(summary_path: Path, output_dir: Path) -> list[Path]:
    plt = require_matplotlib()
    rows = load_summary(summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    noise_rows = sorted(
        [row for row in rows if row["scenario"].startswith("noise_")],
        key=lambda row: row["noise_level"],
    )
    eve_rows = sorted(
        [row for row in rows if row["scenario"].startswith("eve_")],
        key=lambda row: row["eve_attack_probability"],
    )
    combined_rows = sorted(
        [row for row in rows if row["scenario"].startswith("combined_")],
        key=lambda row: (row["noise_level"], row["eve_attack_probability"]),
    )

    output_paths = [
        output_dir / "noise_abs_chsh.png",
        output_dir / "noise_qber.png",
        output_dir / "eve_abs_chsh.png",
        output_dir / "eve_qber.png",
        output_dir / "combined_abs_chsh.png",
        output_dir / "combined_qber.png",
    ]

    save_chsh_plot(
        plt,
        noise_rows,
        "noise_level",
        "Noise level vs abs(CHSH)",
        "noise_level",
        output_paths[0],
    )
    save_qber_plot(
        plt,
        noise_rows,
        "noise_level",
        "Noise level vs QBER",
        "noise_level",
        output_paths[1],
    )
    save_chsh_plot(
        plt,
        eve_rows,
        "eve_attack_probability",
        "Eve attack probability vs abs(CHSH)",
        "eve_attack_probability",
        output_paths[2],
    )
    save_qber_plot(
        plt,
        eve_rows,
        "eve_attack_probability",
        "Eve attack probability vs QBER",
        "eve_attack_probability",
        output_paths[3],
    )
    save_combined_bar_plot(
        plt,
        combined_rows,
        "abs_chsh_mean",
        "Combined scenarios vs abs(CHSH)",
        "abs_chsh_mean",
        output_paths[4],
    )
    save_combined_bar_plot(
        plt,
        combined_rows,
        "qber_mean",
        "Combined scenarios vs QBER",
        "qber_mean",
        output_paths[5],
    )
    return output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot E91 experiment summary results.")
    parser.add_argument("--summary-csv", default="results/experiment_summary.csv")
    parser.add_argument("--output-dir", default="results/plots")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_paths = plot_results(Path(args.summary_csv), Path(args.output_dir))
    for output_path in output_paths:
        print(f"Saved plot: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
