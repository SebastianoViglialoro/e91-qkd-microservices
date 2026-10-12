#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from urllib import error, request


DEFAULT_GATEWAY_URL = os.getenv("E91_API_GATEWAY_URL", "http://localhost:18000")
DEFAULT_SIFTING_BELL_TEST_URL = os.getenv(
    "E91_SIFTING_BELL_TEST_URL",
    "http://localhost:8009",
)
BASIS_MODEL = "TWO_KEY_BASES_ONE_CHECK_BASIS"


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def get_json(url: str, timeout: float) -> dict | list:
    try:
        with request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


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


def extract_metrics(response: dict) -> dict:
    evaluation = response.get("sifting_bell_test", {})
    key = response.get("key", {})
    link_metrics = response.get("link_metrics", {})
    return {
        "session_id": response.get("session_id"),
        "basis_model": evaluation.get("basis_model"),
        "security_status": evaluation.get("security_status"),
        "key_status": key.get("key_status"),
        "abs_chsh": evaluation.get("abs_chsh"),
        "qber": evaluation.get("qber"),
        "final_key_length": key.get("final_key_length"),
        "sifted_key_length": key.get("sifted_key_length"),
        "link_status": link_metrics.get("link_status"),
        "lost_pair_count": link_metrics.get("lost_pair_count"),
    }


def format_metrics(metrics: dict) -> str:
    return (
        f"session={metrics.get('session_id')} "
        f"security={metrics.get('security_status')} "
        f"key={metrics.get('key_status')} "
        f"abs_chsh={metrics.get('abs_chsh')} "
        f"qber={metrics.get('qber')} "
        f"sifted={metrics.get('sifted_key_length')} "
        f"final_len={metrics.get('final_key_length')}"
    )


def check_baseline(gateway_url: str, shots: int, timeout: float) -> CheckResult:
    payload = base_payload(shots)
    response = post_json(f"{gateway_url.rstrip('/')}/simulations", payload, timeout)
    metrics = extract_metrics(response)
    passed = (
        metrics["basis_model"] == BASIS_MODEL
        and metrics["security_status"] == "secure"
        and metrics["key_status"] == "generated"
        and metrics["final_key_length"] == 256
        and metrics["qber"] == 0
    )
    return CheckResult("baseline", passed, format_metrics(metrics))


def check_noise_degraded(gateway_url: str, shots: int, timeout: float) -> CheckResult:
    payload = base_payload(shots)
    payload.update({"enable_noise": True, "noise_level": 0.10, "noise_type": "bit_flip"})
    response = post_json(f"{gateway_url.rstrip('/')}/simulations", payload, timeout)
    metrics = extract_metrics(response)
    passed = (
        metrics["basis_model"] == BASIS_MODEL
        and metrics["security_status"] == "degraded"
        and metrics["key_status"] == "discarded_degraded"
        and metrics["final_key_length"] == 0
        and float(metrics["qber"]) > 0
    )
    return CheckResult("noise_degraded", passed, format_metrics(metrics))


def check_noise_insecure(gateway_url: str, shots: int, timeout: float) -> CheckResult:
    payload = base_payload(shots)
    payload.update({"enable_noise": True, "noise_level": 0.25, "noise_type": "bit_flip"})
    response = post_json(f"{gateway_url.rstrip('/')}/simulations", payload, timeout)
    metrics = extract_metrics(response)
    passed = (
        metrics["basis_model"] == BASIS_MODEL
        and metrics["security_status"] == "insecure"
        and metrics["key_status"] == "discarded"
        and metrics["final_key_length"] == 0
        and float(metrics["qber"]) > 0.15
    )
    return CheckResult("noise_insecure", passed, format_metrics(metrics))


def check_key_summary(gateway_url: str, timeout: float) -> CheckResult:
    summary = get_json(f"{gateway_url.rstrip('/')}/keys/summary", timeout)
    latest = get_json(f"{gateway_url.rstrip('/')}/keys/latest?limit=3", timeout)
    passed = (
        isinstance(summary, dict)
        and isinstance(latest, list)
        and summary.get("total_sessions", 0) >= 3
        and len(latest) >= 3
    )
    details = (
        f"total={summary.get('total_sessions')} "
        f"generated={summary.get('generated_keys')} "
        f"discarded_degraded={summary.get('discarded_degraded')} "
        f"discarded_insecure={summary.get('discarded_insecure')} "
        f"latest={len(latest)}"
    )
    return CheckResult("mini_kms_summary", passed, details)


def check_qiskit(
    sifting_bell_test_url: str,
    shots_per_basis: int,
    timeout: float,
    require_qiskit: bool,
) -> CheckResult:
    health = get_json(f"{sifting_bell_test_url.rstrip('/')}/qiskit-health", timeout)
    if not health.get("qiskit_available"):
        details = "qiskit_available=false"
        return CheckResult("qiskit_chsh", not require_qiskit, details)

    response = post_json(
        f"{sifting_bell_test_url.rstrip('/')}/qiskit-chsh-test",
        {"shots_per_basis": shots_per_basis},
        timeout,
    )
    abs_chsh = response.get("abs_chsh")
    passed = (
        response.get("basis_model") == BASIS_MODEL
        and response.get("sampler_mode") == "qiskit"
        and isinstance(abs_chsh, (int, float))
        and abs_chsh > 2.0
    )
    details = (
        f"sampler={response.get('sampler_mode')} "
        f"abs_chsh={response.get('abs_chsh')} "
        f"shots_per_basis={response.get('shots_per_basis')}"
    )
    return CheckResult("qiskit_chsh", passed, details)


def print_results(results: list[CheckResult]) -> None:
    width = max(len(result.name) for result in results)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name.ljust(width)} {result.details}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a quick end-to-end smoke test for E91 microservices.")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL)
    parser.add_argument("--sifting-bell-test-url", default=DEFAULT_SIFTING_BELL_TEST_URL)
    parser.add_argument("--shots", type=int, default=10000)
    parser.add_argument("--qiskit-shots-per-basis", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--require-qiskit",
        action="store_true",
        help="Fail if Qiskit is not available in sifting-bell-test.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[CheckResult] = []

    try:
        health = get_json(f"{args.gateway_url.rstrip('/')}/health", args.timeout)
        results.append(CheckResult("api_gateway_health", health.get("status") == "ok", str(health)))
    except Exception as exc:  # noqa: BLE001 - smoke test must report a readable failure.
        results.append(CheckResult("api_gateway_health", False, str(exc)))
        print_results(results)
        return 1

    checks = [
        lambda: check_baseline(args.gateway_url, args.shots, args.timeout),
        lambda: check_noise_degraded(args.gateway_url, args.shots, args.timeout),
        lambda: check_noise_insecure(args.gateway_url, args.shots, args.timeout),
        lambda: check_key_summary(args.gateway_url, args.timeout),
        lambda: check_qiskit(
            args.sifting_bell_test_url,
            args.qiskit_shots_per_basis,
            args.timeout,
            args.require_qiskit,
        ),
    ]

    for check in checks:
        try:
            results.append(check())
        except Exception as exc:  # noqa: BLE001 - keep reporting every completed check.
            name = getattr(check, "__name__", "check")
            results.append(CheckResult(name, False, str(exc)))

    print_results(results)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
