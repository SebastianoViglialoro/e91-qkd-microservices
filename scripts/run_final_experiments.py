#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib import error, request


DEFAULT_GATEWAY_URL = os.getenv("E91_API_GATEWAY_URL", "http://localhost:18000")
NOISE_LEVELS = [0.00, 0.02, 0.05, 0.10, 0.20, 0.25]
EVE_PROBABILITIES = [0.00, 0.02, 0.05, 0.10, 0.20, 0.25]

RUN_FIELDS = [
    "scenario_name",
    "scenario_group",
    "repeat_id",
    "shots",
    "session_id",
    "basis_model",
    "noise_enabled",
    "noise_level",
    "noise_type",
    "eve_enabled",
    "eve_attack_probability",
    "attack_type",
    "enable_link_loss",
    "source_alice_distance_km",
    "source_bob_distance_km",
    "attenuation_db_per_km",
    "total_quantum_loss_db",
    "transmittance",
    "link_status",
    "lost_pair_count",
    "min_sifted_key_length",
    "chsh",
    "abs_chsh",
    "qber",
    "security_status",
    "key_status",
    "key_reason",
    "key_subset_size",
    "bell_subset_size",
    "discarded_subset_size",
    "raw_key_length",
    "sifted_key_length",
    "final_key_length",
    "noise_applied_count",
    "eve_applied_count",
    "timestamp",
    "error_message",
]

SUMMARY_FIELDS = [
    "scenario_name",
    "scenario_group",
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
]

TABLE_FIELDS = [
    "scenario_name",
    "runs",
    "failed_runs",
    "abs_chsh_mean",
    "qber_mean",
    "sifted_key_length_mean",
    "total_quantum_loss_db_mean",
    "secure_count",
    "generated_count",
    "insufficient_key_material_count",
    "generated_key_rate",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def base_payload(shots: int) -> dict:
    return {
        "shots": shots,
        "enable_noise": False,
        "noise_level": 0.0,
        "noise_type": "bit_flip",
        "enable_eve": False,
        "eve_attack_probability": 0.0,
        "attack_type": "randomize",
        "enable_link_loss": False,
        "source_alice_distance_km": 25.0,
        "source_bob_distance_km": 25.0,
        "attenuation_db_per_km": 0.02,
        "loss_degraded_threshold_db": 5.0,
        "loss_critical_threshold_db": 7.0,
        "min_sifted_key_length": 256,
    }


def scenario(name: str, group: str, shots: int, overrides: dict) -> dict:
    payload = base_payload(shots)
    payload.update(overrides)
    return {"scenario_name": name, "scenario_group": group, "payload": payload}


def build_scenarios(shots: int) -> list[dict]:
    scenarios = [
        scenario(
            "baseline",
            "baseline",
            shots,
            {
                "enable_noise": False,
                "enable_eve": False,
                "enable_link_loss": False,
                "min_sifted_key_length": 256,
            },
        )
    ]

    link_base = {
        "enable_link_loss": True,
        "attenuation_db_per_km": 0.02,
        "enable_noise": False,
        "enable_eve": False,
        "min_sifted_key_length": 256,
    }
    scenarios.extend(
        [
            scenario(
                "link_nominal_25_25",
                "link_loss_sweep",
                shots,
                {**link_base, "source_alice_distance_km": 25, "source_bob_distance_km": 25},
            ),
            scenario(
                "link_degraded_150_150",
                "link_loss_sweep",
                shots,
                {**link_base, "source_alice_distance_km": 150, "source_bob_distance_km": 150},
            ),
            scenario(
                "link_critical_200_200",
                "link_loss_sweep",
                shots,
                {**link_base, "source_alice_distance_km": 200, "source_bob_distance_km": 200},
            ),
            scenario(
                "link_critical_high_threshold",
                "link_loss_sweep",
                shots,
                {
                    **link_base,
                    "source_alice_distance_km": 200,
                    "source_bob_distance_km": 200,
                    "min_sifted_key_length": 3000,
                },
            ),
        ]
    )

    for noise_type in ["bit_flip", "depolarizing"]:
        for noise_level in NOISE_LEVELS:
            scenarios.append(
                scenario(
                    f"noise_{noise_type}_{noise_level:.2f}",
                    f"noise_sweep_{noise_type}",
                    shots,
                    {
                        "enable_noise": True,
                        "noise_type": noise_type,
                        "noise_level": noise_level,
                        "enable_eve": False,
                        "enable_link_loss": False,
                    },
                )
            )

    for attack_type in ["randomize", "intercept_resend"]:
        for attack_probability in EVE_PROBABILITIES:
            scenarios.append(
                scenario(
                    f"eve_{attack_type}_{attack_probability:.2f}",
                    f"eve_sweep_{attack_type}",
                    shots,
                    {
                        "enable_eve": True,
                        "attack_type": attack_type,
                        "eve_attack_probability": attack_probability,
                        "enable_noise": False,
                        "enable_link_loss": False,
                    },
                )
            )

    for level in [0.02, 0.05, 0.10, 0.15]:
        scenarios.append(
            scenario(
                f"combined_{level:.2f}_{level:.2f}",
                "combined_noise_eve",
                shots,
                {
                    "enable_noise": True,
                    "noise_type": "bit_flip",
                    "noise_level": level,
                    "enable_eve": True,
                    "attack_type": "intercept_resend",
                    "eve_attack_probability": level,
                    "enable_link_loss": False,
                },
            )
        )

    for name, level in [
        ("link_noise_eve_low", 0.02),
        ("link_noise_eve_medium", 0.05),
        ("link_noise_eve_high", 0.10),
    ]:
        scenarios.append(
            scenario(
                name,
                "combined_link_noise_eve",
                shots,
                {
                    "enable_link_loss": True,
                    "attenuation_db_per_km": 0.02,
                    "source_alice_distance_km": 150,
                    "source_bob_distance_km": 150,
                    "enable_noise": True,
                    "noise_type": "bit_flip",
                    "noise_level": level,
                    "enable_eve": True,
                    "attack_type": "intercept_resend",
                    "eve_attack_probability": level,
                },
            )
        )

    return scenarios


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


def empty_run_row(scenario_def: dict, repeat_id: int) -> dict:
    payload = scenario_def["payload"]
    return {
        "scenario_name": scenario_def["scenario_name"],
        "scenario_group": scenario_def["scenario_group"],
        "repeat_id": repeat_id,
        "shots": payload.get("shots"),
        "session_id": "",
        "basis_model": "",
        "noise_enabled": payload.get("enable_noise"),
        "noise_level": payload.get("noise_level"),
        "noise_type": payload.get("noise_type"),
        "eve_enabled": payload.get("enable_eve"),
        "eve_attack_probability": payload.get("eve_attack_probability"),
        "attack_type": payload.get("attack_type"),
        "enable_link_loss": payload.get("enable_link_loss"),
        "source_alice_distance_km": payload.get("source_alice_distance_km"),
        "source_bob_distance_km": payload.get("source_bob_distance_km"),
        "attenuation_db_per_km": payload.get("attenuation_db_per_km"),
        "total_quantum_loss_db": "",
        "transmittance": "",
        "link_status": "",
        "lost_pair_count": "",
        "min_sifted_key_length": payload.get("min_sifted_key_length"),
        "chsh": "",
        "abs_chsh": "",
        "qber": "",
        "security_status": "",
        "key_status": "",
        "key_reason": "",
        "key_subset_size": "",
        "bell_subset_size": "",
        "discarded_subset_size": "",
        "raw_key_length": "",
        "sifted_key_length": "",
        "final_key_length": "",
        "noise_applied_count": "",
        "eve_applied_count": "",
        "timestamp": utc_now_iso(),
        "error_message": "",
    }


def extract_run_row(scenario_def: dict, repeat_id: int, response: dict) -> dict:
    row = empty_run_row(scenario_def, repeat_id)
    evaluation = response.get("sifting_bell_test", {})
    key = response.get("key", {})
    transmission = response.get("transmission", {})
    link_metrics = response.get("link_metrics", {})
    request_payload = response.get("request", scenario_def["payload"])

    row.update(
        {
            "session_id": response.get("session_id", ""),
            "basis_model": evaluation.get("basis_model", ""),
            "noise_enabled": transmission.get("noise_enabled", request_payload.get("enable_noise")),
            "noise_level": transmission.get("noise_level", request_payload.get("noise_level")),
            "noise_type": transmission.get("noise_type", request_payload.get("noise_type")),
            "eve_enabled": transmission.get("eve_enabled", request_payload.get("enable_eve")),
            "eve_attack_probability": transmission.get(
                "eve_attack_probability",
                request_payload.get("eve_attack_probability"),
            ),
            "attack_type": transmission.get("attack_type", request_payload.get("attack_type")),
            "enable_link_loss": link_metrics.get(
                "enable_link_loss",
                request_payload.get("enable_link_loss"),
            ),
            "source_alice_distance_km": link_metrics.get(
                "source_alice_distance_km",
                request_payload.get("source_alice_distance_km"),
            ),
            "source_bob_distance_km": link_metrics.get(
                "source_bob_distance_km",
                request_payload.get("source_bob_distance_km"),
            ),
            "attenuation_db_per_km": link_metrics.get(
                "attenuation_db_per_km",
                request_payload.get("attenuation_db_per_km"),
            ),
            "total_quantum_loss_db": link_metrics.get("total_quantum_loss_db", ""),
            "transmittance": link_metrics.get("transmittance", ""),
            "link_status": link_metrics.get("link_status", ""),
            "lost_pair_count": link_metrics.get("lost_pair_count", ""),
            "min_sifted_key_length": key.get(
                "min_sifted_key_length",
                request_payload.get("min_sifted_key_length"),
            ),
            "chsh": evaluation.get("chsh", ""),
            "abs_chsh": evaluation.get("abs_chsh", ""),
            "qber": evaluation.get("qber", ""),
            "security_status": evaluation.get("security_status", ""),
            "key_status": key.get("key_status", ""),
            "key_reason": key.get("key_reason", ""),
            "key_subset_size": evaluation.get("key_subset_size", ""),
            "bell_subset_size": evaluation.get("bell_subset_size", ""),
            "discarded_subset_size": evaluation.get("discarded_subset_size", ""),
            "raw_key_length": key.get("raw_key_length", ""),
            "sifted_key_length": key.get("sifted_key_length", ""),
            "final_key_length": key.get("final_key_length", ""),
            "noise_applied_count": transmission.get(
                "noise_applied_count",
                evaluation.get("noise_applied_count", ""),
            ),
            "eve_applied_count": transmission.get(
                "eve_applied_count",
                evaluation.get("eve_applied_count", ""),
            ),
            "timestamp": utc_now_iso(),
            "error_message": "",
        }
    )
    return row


def numeric_values(rows: list[dict], field: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(field)
        if value in ("", None):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def sample_stddev(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def count_value(rows: list[dict], field: str, expected: str) -> int:
    return sum(1 for row in rows if row.get(field) == expected)


def summarize_runs(run_rows: list[dict]) -> list[dict]:
    by_scenario: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        by_scenario[row["scenario_name"]].append(row)

    summaries = []
    for scenario_name, rows in by_scenario.items():
        first = rows[0]
        failed_runs = sum(1 for row in rows if row.get("error_message"))
        successful_runs = len(rows) - failed_runs
        generated_count = count_value(rows, "key_status", "generated")
        summaries.append(
            {
                "scenario_name": scenario_name,
                "scenario_group": first["scenario_group"],
                "runs": len(rows),
                "failed_runs": failed_runs,
                "abs_chsh_mean": mean(numeric_values(rows, "abs_chsh")),
                "abs_chsh_stddev": sample_stddev(numeric_values(rows, "abs_chsh")),
                "qber_mean": mean(numeric_values(rows, "qber")),
                "qber_stddev": sample_stddev(numeric_values(rows, "qber")),
                "raw_key_length_mean": mean(numeric_values(rows, "raw_key_length")),
                "sifted_key_length_mean": mean(numeric_values(rows, "sifted_key_length")),
                "final_key_length_mean": mean(numeric_values(rows, "final_key_length")),
                "total_quantum_loss_db_mean": mean(numeric_values(rows, "total_quantum_loss_db")),
                "transmittance_mean": mean(numeric_values(rows, "transmittance")),
                "lost_pair_count_mean": mean(numeric_values(rows, "lost_pair_count")),
                "secure_count": count_value(rows, "security_status", "secure"),
                "degraded_count": count_value(rows, "security_status", "degraded"),
                "insecure_count": count_value(rows, "security_status", "insecure"),
                "generated_count": generated_count,
                "discarded_degraded_count": count_value(rows, "key_status", "discarded_degraded"),
                "discarded_count": count_value(rows, "key_status", "discarded"),
                "insufficient_key_material_count": count_value(
                    rows,
                    "key_status",
                    "insufficient_key_material",
                ),
                "generated_key_rate": (
                    generated_count / successful_runs if successful_runs > 0 else None
                ),
            }
        )
    return summaries


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return ""
    return str(value)


def print_table(rows: list[dict], fields: list[str]) -> None:
    if not rows:
        print("No rows to display.")
        return
    widths = {
        field: max(len(field), *(len(format_value(row.get(field))) for row in rows))
        for field in fields
    }
    header = " | ".join(field.ljust(widths[field]) for field in fields)
    separator = "-+-".join("-" * widths[field] for field in fields)
    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(format_value(row.get(field)).ljust(widths[field]) for field in fields))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_outputs(run_rows: list[dict], summary_rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    runs_path = output_dir / "final_experiment_runs.csv"
    summary_csv_path = output_dir / "final_experiment_summary.csv"
    summary_json_path = output_dir / "final_experiment_summary.json"

    write_csv(runs_path, run_rows, RUN_FIELDS)
    write_csv(summary_csv_path, summary_rows, SUMMARY_FIELDS)
    with summary_json_path.open("w", encoding="utf-8") as json_file:
        json.dump(summary_rows, json_file, indent=2)

    print(f"\nSaved runs CSV: {runs_path}")
    print(f"Saved summary CSV: {summary_csv_path}")
    print(f"Saved summary JSON: {summary_json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the final E91 QKD microservice experiment campaign.")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="API Gateway base URL.")
    parser.add_argument("--shots", type=int, default=10000, help="Shots per simulation.")
    parser.add_argument("--repeats", type=int, default=10, help="Independent runs per scenario.")
    parser.add_argument("--output-dir", default="results/final", help="Output directory for final CSV/JSON files.")
    parser.add_argument(
        "--sleep-between-runs",
        type=float,
        default=0.2,
        help="Pause in seconds between API calls.",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds per run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.shots <= 0:
        raise RuntimeError("--shots must be positive")
    if args.repeats <= 0:
        raise RuntimeError("--repeats must be positive")

    scenarios = build_scenarios(args.shots)
    total_runs = len(scenarios) * args.repeats
    run_rows = []
    run_number = 0

    print(
        f"Running {len(scenarios)} scenarios x {args.repeats} repeats "
        f"({total_runs} total runs) via {args.gateway_url}"
    )

    for scenario_def in scenarios:
        for repeat_id in range(1, args.repeats + 1):
            run_number += 1
            label = scenario_def["scenario_name"]
            print(f"[{run_number}/{total_runs}] {label} repeat {repeat_id}...", flush=True)
            try:
                response = post_simulation(args.gateway_url, scenario_def["payload"], args.timeout)
                row = extract_run_row(scenario_def, repeat_id, response)
            except Exception as exc:  # noqa: BLE001 - keep the campaign running and persist the error.
                row = empty_run_row(scenario_def, repeat_id)
                row["error_message"] = str(exc)
                print(f"  error: {exc}", file=sys.stderr, flush=True)
            run_rows.append(row)
            if args.sleep_between_runs > 0:
                time.sleep(args.sleep_between_runs)

    summary_rows = summarize_runs(run_rows)
    print()
    print_table(summary_rows, TABLE_FIELDS)
    save_outputs(run_rows, summary_rows, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
