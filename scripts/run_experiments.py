#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib import error, request


DEFAULT_GATEWAY_URL = os.getenv("E91_API_GATEWAY_URL", "http://localhost:8000")
RUN_FIELDS = [
    "scenario",
    "run_index",
    "shots",
    "noise_level",
    "eve_attack_probability",
    "abs_chsh",
    "qber",
    "key_subset_size",
    "bell_subset_size",
    "final_key_length",
    "security_status",
    "key_status",
    "noise_applied_count",
    "eve_applied_count",
    "session_id",
]
SUMMARY_FIELDS = [
    "scenario",
    "runs",
    "shots",
    "noise_level",
    "eve_attack_probability",
    "abs_chsh_mean",
    "abs_chsh_stddev",
    "qber_mean",
    "qber_stddev",
    "key_subset_size_mean",
    "security_status_distribution",
    "key_status_distribution",
]


def build_experiments(shots: int) -> list[dict]:
    experiments = [
        {
            "scenario": "baseline",
            "payload": {
                "shots": shots,
                "enable_noise": False,
                "noise_level": 0.0,
                "enable_eve": False,
                "eve_attack_probability": 0.0,
            },
        }
    ]

    for noise_level in [0.0, 0.02, 0.05, 0.10, 0.20]:
        experiments.append(
            {
                "scenario": f"noise_{noise_level:.2f}",
                "payload": {
                    "shots": shots,
                    "enable_noise": True,
                    "noise_level": noise_level,
                    "enable_eve": False,
                    "eve_attack_probability": 0.0,
                },
            }
        )

    for eve_attack_probability in [0.0, 0.02, 0.05, 0.10, 0.20]:
        experiments.append(
            {
                "scenario": f"eve_{eve_attack_probability:.2f}",
                "payload": {
                    "shots": shots,
                    "enable_noise": False,
                    "noise_level": 0.0,
                    "enable_eve": True,
                    "eve_attack_probability": eve_attack_probability,
                },
            }
        )

    for noise_level, eve_attack_probability in [(0.02, 0.02), (0.05, 0.05), (0.10, 0.10)]:
        experiments.append(
            {
                "scenario": f"combined_n{noise_level:.2f}_e{eve_attack_probability:.2f}",
                "payload": {
                    "shots": shots,
                    "enable_noise": True,
                    "noise_level": noise_level,
                    "enable_eve": True,
                    "eve_attack_probability": eve_attack_probability,
                },
            }
        )

    return experiments


def post_simulation(gateway_url: str, payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        f"{gateway_url.rstrip('/')}/simulations",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from API Gateway: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Cannot reach API Gateway at {gateway_url}: {exc.reason}") from exc


def extract_result(scenario: str, run_index: int, payload: dict, response: dict) -> dict:
    evaluation = response.get("sifting_bell_test", {})
    key = response.get("key", {})

    return {
        "scenario": scenario,
        "run_index": run_index,
        "shots": payload["shots"],
        "noise_level": payload["noise_level"],
        "eve_attack_probability": payload["eve_attack_probability"],
        "abs_chsh": evaluation.get("abs_chsh"),
        "qber": evaluation.get("qber"),
        "key_subset_size": evaluation.get("key_subset_size"),
        "bell_subset_size": evaluation.get("bell_subset_size"),
        "final_key_length": key.get("final_key_length"),
        "security_status": evaluation.get("security_status"),
        "key_status": key.get("key_status"),
        "noise_applied_count": evaluation.get("noise_applied_count", 0),
        "eve_applied_count": evaluation.get("eve_applied_count", 0),
        "session_id": response.get("session_id"),
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def distribution(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def summarize_runs(rows: list[dict]) -> list[dict]:
    by_scenario: dict[str, list[dict]] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario"], []).append(row)

    summaries = []
    for scenario, scenario_rows in by_scenario.items():
        first = scenario_rows[0]
        abs_chsh_values = [float(row["abs_chsh"]) for row in scenario_rows if row["abs_chsh"] is not None]
        qber_values = [float(row["qber"]) for row in scenario_rows if row["qber"] is not None]
        key_subset_values = [
            float(row["key_subset_size"])
            for row in scenario_rows
            if row["key_subset_size"] is not None
        ]
        summaries.append(
            {
                "scenario": scenario,
                "runs": len(scenario_rows),
                "shots": first["shots"],
                "noise_level": first["noise_level"],
                "eve_attack_probability": first["eve_attack_probability"],
                "abs_chsh_mean": mean(abs_chsh_values),
                "abs_chsh_stddev": sample_stddev(abs_chsh_values),
                "qber_mean": mean(qber_values),
                "qber_stddev": sample_stddev(qber_values),
                "key_subset_size_mean": mean(key_subset_values),
                "security_status_distribution": distribution(
                    [row["security_status"] for row in scenario_rows]
                ),
                "key_status_distribution": distribution([row["key_status"] for row in scenario_rows]),
            }
        )
    return summaries


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
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

    runs_csv_path = output_dir / "experiment_runs.csv"
    write_csv(runs_csv_path, run_rows, RUN_FIELDS)

    summary_csv_path = output_dir / "experiment_summary.csv"
    write_csv(summary_csv_path, summary_rows, SUMMARY_FIELDS)

    summary_json_path = output_dir / "experiment_summary.json"
    with summary_json_path.open("w", encoding="utf-8") as json_file:
        json.dump(summary_rows, json_file, indent=2)

    print(f"\nSaved runs CSV: {runs_csv_path}")
    print(f"Saved summary CSV: {summary_csv_path}")
    print(f"Saved summary JSON: {summary_json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run E91 QKD microservice experiments through the API Gateway.")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="API Gateway base URL.")
    parser.add_argument("--shots", type=int, default=10000, help="Number of shots for each experiment.")
    parser.add_argument("--repeats", type=int, default=10, help="Independent runs per scenario.")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds per experiment.")
    parser.add_argument("--output-dir", default="results", help="Directory for CSV/JSON outputs.")
    parser.add_argument("--pause", type=float, default=0.0, help="Optional pause between requests in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_rows = []

    for experiment in build_experiments(args.shots):
        scenario = experiment["scenario"]
        payload = experiment["payload"]
        for run_index in range(1, args.repeats + 1):
            print(f"Running {scenario} [{run_index}/{args.repeats}]...")
            response = post_simulation(args.gateway_url, payload, args.timeout)
            run_rows.append(extract_result(scenario, run_index, payload, response))
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
