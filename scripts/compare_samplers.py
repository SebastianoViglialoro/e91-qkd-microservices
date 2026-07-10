#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib import error, request


DEFAULT_GATEWAY_URL = os.getenv("E91_API_GATEWAY_URL", "http://localhost:8000")
DEFAULT_SIFTING_BELL_TEST_URL = os.getenv(
    "E91_SIFTING_BELL_TEST_URL",
    "http://localhost:8009",
)
RUN_FIELDS = [
    "repeat_id",
    "sampler_mode",
    "shots",
    "shots_per_basis",
    "chsh",
    "abs_chsh",
    "qber",
    "security_status",
]
SUMMARY_FIELDS = [
    "sampler_mode",
    "runs",
    "abs_chsh_mean",
    "abs_chsh_stddev",
    "chsh_mean",
    "chsh_stddev",
    "qber_mean",
    "qber_stddev",
]


def post_json(url: str, payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


def run_classical(gateway_url: str, repeat_id: int, shots: int, timeout: float) -> dict:
    payload = {
        "shots": shots,
        "enable_noise": False,
        "noise_level": 0.0,
        "enable_eve": False,
        "eve_attack_probability": 0.0,
    }
    response = post_json(f"{gateway_url.rstrip('/')}/simulations", payload, timeout)
    evaluation = response.get("sifting_bell_test", {})
    return {
        "repeat_id": repeat_id,
        "sampler_mode": evaluation.get("correlation_model", "classical_singlet_sampler"),
        "shots": shots,
        "shots_per_basis": "",
        "chsh": evaluation.get("chsh"),
        "abs_chsh": evaluation.get("abs_chsh"),
        "qber": evaluation.get("qber"),
        "security_status": evaluation.get("security_status"),
    }


def run_qiskit(sifting_bell_test_url: str, repeat_id: int, shots_per_basis: int, timeout: float) -> dict:
    payload = {"shots_per_basis": shots_per_basis}
    response = post_json(
        f"{sifting_bell_test_url.rstrip('/')}/qiskit-chsh-test",
        payload,
        timeout,
    )
    return {
        "repeat_id": repeat_id,
        "sampler_mode": response.get("sampler_mode", "qiskit"),
        "shots": "",
        "shots_per_basis": shots_per_basis,
        "chsh": response.get("chsh"),
        "abs_chsh": response.get("abs_chsh"),
        "qber": "",
        "security_status": "",
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def numeric_values(rows: list[dict], field: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(field)
        if value in ("", None):
            continue
        values.append(float(value))
    return values


def summarize_runs(rows: list[dict]) -> list[dict]:
    by_sampler: dict[str, list[dict]] = {}
    for row in rows:
        by_sampler.setdefault(row["sampler_mode"], []).append(row)

    summaries = []
    for sampler_mode, sampler_rows in by_sampler.items():
        abs_chsh_values = numeric_values(sampler_rows, "abs_chsh")
        chsh_values = numeric_values(sampler_rows, "chsh")
        qber_values = numeric_values(sampler_rows, "qber")
        summaries.append(
            {
                "sampler_mode": sampler_mode,
                "runs": len(sampler_rows),
                "abs_chsh_mean": mean(abs_chsh_values),
                "abs_chsh_stddev": sample_stddev(abs_chsh_values),
                "chsh_mean": mean(chsh_values),
                "chsh_stddev": sample_stddev(chsh_values),
                "qber_mean": mean(qber_values) if qber_values else "",
                "qber_stddev": sample_stddev(qber_values) if qber_values else "",
            }
        )
    return summaries


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return "" if value is None else str(value)


def print_table(rows: list[dict], fields: list[str]) -> None:
    widths = {
        field: max(len(field), *(len(format_value(row[field])) for row in rows))
        for field in fields
    }
    header = " | ".join(field.ljust(widths[field]) for field in fields)
    separator = "-+-".join("-" * widths[field] for field in fields)
    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(format_value(row[field]).ljust(widths[field]) for field in fields))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_results(run_rows: list[dict], summary_rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    runs_csv_path = output_dir / "sampler_comparison_runs.csv"
    write_csv(runs_csv_path, run_rows, RUN_FIELDS)

    summary_csv_path = output_dir / "sampler_comparison_summary.csv"
    write_csv(summary_csv_path, summary_rows, SUMMARY_FIELDS)

    summary_json_path = output_dir / "sampler_comparison_summary.json"
    with summary_json_path.open("w", encoding="utf-8") as json_file:
        json.dump(summary_rows, json_file, indent=2)

    print(f"\nSaved runs CSV: {runs_csv_path}")
    print(f"Saved summary CSV: {summary_csv_path}")
    print(f"Saved summary JSON: {summary_json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare classical and Qiskit E91 Bell samplers.")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="API Gateway base URL.")
    parser.add_argument(
        "--sifting-bell-test-url",
        default=DEFAULT_SIFTING_BELL_TEST_URL,
        help="Sifting/Bell service base URL.",
    )
    parser.add_argument("--shots", type=int, default=10000, help="Shots for the classical pipeline.")
    parser.add_argument(
        "--shots-per-basis",
        type=int,
        default=2500,
        help="Shots for each Qiskit CHSH basis pair.",
    )
    parser.add_argument("--repeats", type=int, default=10, help="Independent runs per sampler.")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds per request.")
    parser.add_argument("--output-dir", default="results", help="Directory for CSV/JSON outputs.")
    parser.add_argument("--pause", type=float, default=0.0, help="Optional pause between repeats in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_rows = []

    for repeat_id in range(1, args.repeats + 1):
        print(f"Running classical sampler [{repeat_id}/{args.repeats}]...")
        run_rows.append(run_classical(args.gateway_url, repeat_id, args.shots, args.timeout))

        print(f"Running Qiskit sampler [{repeat_id}/{args.repeats}]...")
        run_rows.append(
            run_qiskit(
                args.sifting_bell_test_url,
                repeat_id,
                args.shots_per_basis,
                args.timeout,
            )
        )

        if args.pause > 0:
            time.sleep(args.pause)

    summary_rows = summarize_runs(run_rows)

    print()
    print_table(summary_rows, SUMMARY_FIELDS)
    save_results(run_rows, summary_rows, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
