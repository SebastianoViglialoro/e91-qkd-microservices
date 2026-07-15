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

KEY_STATUS_FIELDS = [
    ("generated_count", "generated", "#39ff14"),
    ("discarded_degraded_count", "discarded_degraded", "#ffb300"),
    ("discarded_count", "discarded", "#ff3d3d"),
    ("insufficient_key_material_count", "insufficient", "#8b949e"),
]

SECURITY_STATUS_FIELDS = [
    ("secure_count", "secure", "#39ff14"),
    ("degraded_count", "degraded", "#ffb300"),
    ("insecure_count", "insecure", "#ff3d3d"),
]

LINK_SCENARIOS = [
    "link_nominal_25_25",
    "link_degraded_150_150",
    "link_critical_200_200",
    "link_critical_high_threshold",
]
COMBINED_SCENARIOS = [
    "combined_0.02_0.02",
    "combined_0.05_0.05",
    "combined_0.10_0.10",
    "combined_0.15_0.15",
]
COMBINED_LINK_SCENARIOS = [
    "link_noise_eve_low",
    "link_noise_eve_medium",
    "link_noise_eve_high",
]


def require_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/e91_matplotlib_cache")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError(
            "matplotlib is required. Activate the project venv or install it with: "
            ".venv/bin/python -m pip install matplotlib"
        ) from exc
    return plt


def as_float(value) -> float:
    if value in ("", None):
        return 0.0
    return float(value)


def as_int(value) -> int:
    if value in ("", None):
        return 0
    return int(float(value))


def load_summary(path: Path) -> list[dict]:
    if not path.exists():
        raise RuntimeError(f"Summary CSV not found: {path}")

    numeric_fields = {
        "runs",
        "failed_runs",
        "abs_chsh_mean",
        "abs_chsh_stddev",
        "qber_mean",
        "qber_stddev",
        "raw_key_length_mean",
        "sifted_key_length_mean",
        "final_key_length_mean",
        "total_quantum_loss_db_mean",
        "transmittance_mean",
        "lost_pair_count_mean",
        "secure_count",
        "degraded_count",
        "insecure_count",
        "generated_count",
        "discarded_degraded_count",
        "discarded_count",
        "insufficient_key_material_count",
        "generated_key_rate",
    }

    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    for row in rows:
        for field in numeric_fields:
            row[field] = as_float(row.get(field))
    return rows


def rows_by_name(rows: list[dict]) -> dict[str, dict]:
    return {row["scenario_name"]: row for row in rows}


def ordered_rows(rows: list[dict], scenario_names: list[str], warnings: list[str]) -> list[dict]:
    lookup = rows_by_name(rows)
    selected = []
    for name in scenario_names:
        row = lookup.get(name)
        if row is None:
            warnings.append(f"Missing scenario skipped: {name}")
            continue
        selected.append(row)
    return selected


def group_rows(rows: list[dict], group: str) -> list[dict]:
    return [row for row in rows if row["scenario_group"] == group]


def scenario_level(row: dict) -> float:
    return float(row["scenario_name"].rsplit("_", 1)[-1])


def combined_label(row: dict) -> str:
    name = row["scenario_name"]
    if name.startswith("combined_"):
        parts = name.replace("combined_", "").split("_")
        return f"n={parts[0]}\ne={parts[1]}"
    return name.replace("link_noise_eve_", "")


def short_label(name: str) -> str:
    replacements = {
        "link_nominal_25_25": "nominal\n25/25",
        "link_degraded_150_150": "degraded\n150/150",
        "link_critical_200_200": "critical\n200/200",
        "link_critical_high_threshold": "critical\nhigh threshold",
    }
    return replacements.get(name, name.replace("_", "\n"))


def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.28)


def save_figure(plt, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=170)
    plt.close()
    return output_path


def plot_baseline_summary(plt, baseline: dict, output_path: Path) -> Path:
    labels = ["abs_chsh", "qber", "key_rate", "sifted_bits"]
    values = [
        baseline["abs_chsh_mean"],
        baseline["qber_mean"],
        baseline["generated_key_rate"],
        baseline["sifted_key_length_mean"],
    ]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.axis("off")
    table_values = [[label, f"{value:.4f}" if label != "sifted_bits" else f"{value:.1f}"] for label, value in zip(labels, values)]
    table = ax.table(
        cellText=table_values,
        colLabels=["metric", "value"],
        loc="center",
        cellLoc="center",
        colLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.7)
    ax.set_title("Baseline summary", pad=18)
    return save_figure(plt, output_path)


def plot_chsh_sweep(plt, rows: list[dict], x_values: list[float], title: str, xlabel: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    y_values = [row["abs_chsh_mean"] for row in rows]
    y_errors = [row["abs_chsh_stddev"] for row in rows]
    ax.errorbar(x_values, y_values, yerr=y_errors, marker="o", capsize=4, color="#bd00ff")
    ax.axhline(CHSH_CLASSICAL_BOUND, color="#ff3d3d", linestyle="--", label="classical bound = 2.0")
    ax.axhline(CHSH_SECURE_THRESHOLD, color="#ffb300", linestyle="--", label="secure threshold = 2.4")
    style_axes(ax, title, xlabel, "abs_chsh_mean")
    ax.legend()
    return save_figure(plt, output_path)


def plot_qber_sweep(plt, rows: list[dict], x_values: list[float], title: str, xlabel: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    y_values = [row["qber_mean"] for row in rows]
    y_errors = [row["qber_stddev"] for row in rows]
    ax.errorbar(x_values, y_values, yerr=y_errors, marker="o", capsize=4, color="#ff3d3d")
    ax.axhline(QBER_SECURE_THRESHOLD, color="#ffb300", linestyle="--", label="secure threshold = 0.08")
    ax.axhline(QBER_INSECURE_THRESHOLD, color="#ff3d3d", linestyle="--", label="insecure threshold = 0.15")
    style_axes(ax, title, xlabel, "qber_mean")
    ax.legend()
    return save_figure(plt, output_path)


def plot_rate_sweep(plt, rows: list[dict], x_values: list[float], title: str, xlabel: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_values, [row["generated_key_rate"] for row in rows], marker="o", color="#39ff14")
    ax.set_ylim(-0.05, 1.05)
    style_axes(ax, title, xlabel, "generated_key_rate")
    return save_figure(plt, output_path)


def plot_key_status_distribution(plt, rows: list[dict], labels: list[str], title: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x_positions = list(range(len(rows)))
    bottoms = [0.0] * len(rows)
    for field, label, color in KEY_STATUS_FIELDS:
        values = [row[field] for row in rows]
        ax.bar(x_positions, values, bottom=bottoms, label=label, color=color)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    style_axes(ax, title, "scenario", "runs")
    ax.legend()
    return save_figure(plt, output_path)


def plot_link_metric(plt, rows: list[dict], metric: str, title: str, ylabel: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    x_values = [row["total_quantum_loss_db_mean"] for row in rows]
    y_values = [row[metric] for row in rows]
    labels = [short_label(row["scenario_name"]).replace("\n", " ") for row in rows]
    ax.plot(x_values, y_values, marker="o", color="#00e5ff")
    for x_value, y_value, label in zip(x_values, y_values, labels):
        ax.annotate(label, (x_value, y_value), textcoords="offset points", xytext=(4, 6), fontsize=8)
    style_axes(ax, title, "total_quantum_loss_db_mean", ylabel)
    return save_figure(plt, output_path)


def plot_category_metric(plt, rows: list[dict], metric: str, title: str, ylabel: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [combined_label(row) for row in rows]
    values = [row[metric] for row in rows]
    ax.bar(labels, values, color="#00e5ff")
    if metric == "abs_chsh_mean":
        ax.axhline(CHSH_CLASSICAL_BOUND, color="#ff3d3d", linestyle="--", label="classical bound = 2.0")
        ax.axhline(CHSH_SECURE_THRESHOLD, color="#ffb300", linestyle="--", label="secure threshold = 2.4")
        ax.legend()
    if metric == "qber_mean":
        ax.axhline(QBER_SECURE_THRESHOLD, color="#ffb300", linestyle="--", label="secure threshold = 0.08")
        ax.axhline(QBER_INSECURE_THRESHOLD, color="#ff3d3d", linestyle="--", label="insecure threshold = 0.15")
        ax.legend()
    if metric == "generated_key_rate":
        ax.set_ylim(-0.05, 1.05)
    style_axes(ax, title, "scenario", ylabel)
    return save_figure(plt, output_path)


def plot_global_status_distribution(plt, rows: list[dict], fields: list[tuple[str, str, str]], title: str, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = [label for _, label, _ in fields]
    values = [sum(row[field] for row in rows) for field, _, _ in fields]
    colors = [color for _, _, color in fields]
    ax.bar(labels, values, color=colors)
    style_axes(ax, title, "status", "runs")
    return save_figure(plt, output_path)


def plot_group_key_rate(plt, rows: list[dict], output_path: Path) -> Path:
    groups = sorted({row["scenario_group"] for row in rows})
    labels = []
    rates = []
    for group in groups:
        group_rows = [row for row in rows if row["scenario_group"] == group]
        generated = sum(row["generated_count"] for row in group_rows)
        successful = sum(row["runs"] - row["failed_runs"] for row in group_rows)
        labels.append(group.replace("_", "\n"))
        rates.append(generated / successful if successful else 0.0)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(labels, rates, color="#39ff14")
    ax.set_ylim(-0.05, 1.05)
    style_axes(ax, "Global generated key rate by scenario group", "scenario_group", "generated_key_rate")
    return save_figure(plt, output_path)


def plot_sweep_set(plt, rows: list[dict], prefix: str, title_prefix: str, xlabel: str, output_dir: Path) -> list[Path]:
    rows = sorted(rows, key=scenario_level)
    x_values = [scenario_level(row) for row in rows]
    labels = [f"{scenario_level(row):.2f}" for row in rows]
    return [
        plot_chsh_sweep(plt, rows, x_values, f"{title_prefix}: abs(CHSH)", xlabel, output_dir / f"{prefix}_abs_chsh.png"),
        plot_qber_sweep(plt, rows, x_values, f"{title_prefix}: QBER", xlabel, output_dir / f"{prefix}_qber.png"),
        plot_rate_sweep(plt, rows, x_values, f"{title_prefix}: generated key rate", xlabel, output_dir / f"{prefix}_generated_key_rate.png"),
        plot_key_status_distribution(plt, rows, labels, f"{title_prefix}: key status distribution", output_dir / f"{prefix}_key_status_distribution.png"),
    ]


def plot_results(summary_csv: Path, output_dir: Path) -> tuple[list[Path], list[str]]:
    plt = require_matplotlib()
    rows = load_summary(summary_csv)
    output_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    outputs: list[Path] = []

    lookup = rows_by_name(rows)
    baseline = lookup.get("baseline")
    if baseline:
        outputs.append(plot_baseline_summary(plt, baseline, output_dir / "baseline_summary.png"))
    else:
        warnings.append("Missing baseline scenario; baseline_summary.png skipped")

    sweep_specs = [
        ("noise_sweep_bit_flip", "noise_bit_flip", "Noise bit_flip", "noise_level"),
        ("noise_sweep_depolarizing", "noise_depolarizing", "Noise depolarizing", "noise_level"),
        ("eve_sweep_randomize", "eve_randomize", "Eve randomize", "eve_attack_probability"),
        ("eve_sweep_intercept_resend", "eve_intercept_resend", "Eve intercept_resend", "eve_attack_probability"),
    ]
    for group, prefix, title, xlabel in sweep_specs:
        selected = group_rows(rows, group)
        if selected:
            outputs.extend(plot_sweep_set(plt, selected, prefix, title, xlabel, output_dir))
        else:
            warnings.append(f"Missing group skipped: {group}")

    link_rows = ordered_rows(rows, LINK_SCENARIOS, warnings)
    if link_rows:
        labels = [short_label(row["scenario_name"]) for row in link_rows]
        outputs.extend(
            [
                plot_link_metric(
                    plt,
                    link_rows,
                    "sifted_key_length_mean",
                    "Link loss: total dB vs sifted key length",
                    "sifted_key_length_mean",
                    output_dir / "link_loss_total_db_vs_sifted_key_length.png",
                ),
                plot_link_metric(
                    plt,
                    link_rows,
                    "lost_pair_count_mean",
                    "Link loss: total dB vs lost pair count",
                    "lost_pair_count_mean",
                    output_dir / "link_loss_total_db_vs_lost_pair_count.png",
                ),
                plot_link_metric(
                    plt,
                    link_rows,
                    "generated_key_rate",
                    "Link loss: total dB vs generated key rate",
                    "generated_key_rate",
                    output_dir / "link_loss_total_db_vs_generated_key_rate.png",
                ),
                plot_key_status_distribution(
                    plt,
                    link_rows,
                    labels,
                    "Link loss: key status distribution",
                    output_dir / "link_loss_status_distribution.png",
                ),
            ]
        )

    combined_rows = ordered_rows(rows, COMBINED_SCENARIOS, warnings)
    if combined_rows:
        labels = [combined_label(row) for row in combined_rows]
        outputs.extend(
            [
                plot_category_metric(
                    plt,
                    combined_rows,
                    "abs_chsh_mean",
                    "Combined noise + Eve: abs(CHSH)",
                    "abs_chsh_mean",
                    output_dir / "combined_noise_eve_abs_chsh.png",
                ),
                plot_category_metric(
                    plt,
                    combined_rows,
                    "qber_mean",
                    "Combined noise + Eve: QBER",
                    "qber_mean",
                    output_dir / "combined_noise_eve_qber.png",
                ),
                plot_category_metric(
                    plt,
                    combined_rows,
                    "generated_key_rate",
                    "Combined noise + Eve: generated key rate",
                    "generated_key_rate",
                    output_dir / "combined_noise_eve_generated_key_rate.png",
                ),
                plot_key_status_distribution(
                    plt,
                    combined_rows,
                    labels,
                    "Combined noise + Eve: key status distribution",
                    output_dir / "combined_noise_eve_key_status_distribution.png",
                ),
            ]
        )

    combined_link_rows = ordered_rows(rows, COMBINED_LINK_SCENARIOS, warnings)
    if combined_link_rows:
        labels = [combined_label(row) for row in combined_link_rows]
        outputs.extend(
            [
                plot_category_metric(
                    plt,
                    combined_link_rows,
                    "abs_chsh_mean",
                    "Combined link loss + noise + Eve: abs(CHSH)",
                    "abs_chsh_mean",
                    output_dir / "combined_link_noise_eve_abs_chsh.png",
                ),
                plot_category_metric(
                    plt,
                    combined_link_rows,
                    "qber_mean",
                    "Combined link loss + noise + Eve: QBER",
                    "qber_mean",
                    output_dir / "combined_link_noise_eve_qber.png",
                ),
                plot_category_metric(
                    plt,
                    combined_link_rows,
                    "generated_key_rate",
                    "Combined link loss + noise + Eve: generated key rate",
                    "generated_key_rate",
                    output_dir / "combined_link_noise_eve_generated_key_rate.png",
                ),
                plot_key_status_distribution(
                    plt,
                    combined_link_rows,
                    labels,
                    "Combined link loss + noise + Eve: key status distribution",
                    output_dir / "combined_link_noise_eve_key_status_distribution.png",
                ),
            ]
        )

    outputs.extend(
        [
            plot_global_status_distribution(
                plt,
                rows,
                SECURITY_STATUS_FIELDS,
                "Global security status distribution",
                output_dir / "global_security_status_distribution.png",
            ),
            plot_global_status_distribution(
                plt,
                rows,
                KEY_STATUS_FIELDS,
                "Global key status distribution",
                output_dir / "global_key_status_distribution.png",
            ),
            plot_group_key_rate(plt, rows, output_dir / "global_generated_key_rate_by_scenario_group.png"),
        ]
    )

    return outputs, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate final plots for the E91 experiment campaign.")
    parser.add_argument("--summary-csv", default="results/final/final_experiment_summary.csv")
    parser.add_argument("--runs-csv", default="results/final/final_experiment_runs.csv")
    parser.add_argument("--output-dir", default="results/final/plots")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not Path(args.runs_csv).exists():
        print(f"Warning: runs CSV not found, continuing from summary only: {args.runs_csv}", file=sys.stderr)
    outputs, warnings = plot_results(Path(args.summary_csv), Path(args.output_dir))
    for output in outputs:
        print(f"Saved plot: {output}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"Generated {len(outputs)} plots in {args.output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
