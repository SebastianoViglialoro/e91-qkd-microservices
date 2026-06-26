import logging
import math
import random

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sifting-bell-test")

app = FastAPI(title="E91 Sifting and Bell Test")


class EvaluateRequest(BaseModel):
    session_id: str
    reconciled: dict


CHSH_TERMS = {
    ("A0", "B0"): 1,
    ("A0", "B1"): 1,
    ("A1", "B0"): 1,
    ("A1", "B1"): -1,
}
OUTCOMES = (-1, 1)


def outcome_to_bit(outcome: int) -> int:
    return 1 if outcome == 1 else 0


def sample_singlet_outcomes(alice_angle_degrees: float, bob_angle_degrees: float) -> tuple[int, int]:
    alice_angle = math.radians(alice_angle_degrees)
    bob_angle = math.radians(bob_angle_degrees)
    expectation = -math.cos(alice_angle - bob_angle)
    same_probability = max(0.0, min(1.0, (1.0 + expectation) / 2.0))

    alice_outcome = random.choice(OUTCOMES)
    same_outcome = random.random() < same_probability
    bob_outcome = alice_outcome if same_outcome else -alice_outcome
    return alice_outcome, bob_outcome


def correlate_with_singlet_sampler(items: list[dict]) -> list[dict]:
    correlated = []
    for item in items:
        alice_outcome, bob_outcome = sample_singlet_outcomes(
            item["alice_basis_angle"],
            item["bob_basis_angle"],
        )
        correlated.append(
            {
                **item,
                "alice_outcome": alice_outcome,
                "bob_outcome": bob_outcome,
                "correlation_model": "classical_singlet_sampler",
            }
        )
    return correlated


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sifting-bell-test"}


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    logger.info("Evaluating CHSH/QBER from simulated post-processing data for %s", request.session_id)
    key_subset = request.reconciled.get("key_subset", [])
    bell_subset = request.reconciled.get("bell_subset", request.reconciled.get("bell_test_subset", []))
    correlated_bell_subset = correlate_with_singlet_sampler(bell_subset)
    correlated_key_subset = correlate_with_singlet_sampler(key_subset)

    compared_bits = len(correlated_key_subset)
    key_records = []
    error_count = 0
    for item in correlated_key_subset:
        alice_bit = outcome_to_bit(item["alice_outcome"])
        bob_raw_bit = outcome_to_bit(item["bob_outcome"])
        bob_corrected_bit = 1 - bob_raw_bit
        is_error = alice_bit != bob_corrected_bit
        error_count += int(is_error)
        key_records.append(
            {
                "pair_id": item["pair_id"],
                "alice_bit": alice_bit,
                "bob_corrected_bit": bob_corrected_bit,
                "error": is_error,
            }
        )
    qber = error_count / compared_bits if compared_bits else 0.0

    correlations = {}
    chsh = 0.0
    for basis_pair, sign in CHSH_TERMS.items():
        products = [
            item["alice_outcome"] * item["bob_outcome"]
            for item in correlated_bell_subset
            if (item["alice_basis"], item["bob_basis"]) == basis_pair
        ]
        expectation = sum(products) / len(products) if products else 0.0
        correlations[f"E({basis_pair[0]},{basis_pair[1]})"] = {
            "expectation": round(expectation, 4),
            "samples": len(products),
        }
        chsh += sign * expectation

    # Future integration point: Qiskit Bell/CHSH verification.
    chsh = round(chsh, 4)
    security_status = "secure" if abs(chsh) > 2.0 and qber < 0.11 else "insecure"

    return {
        "session_id": request.session_id,
        "chsh": chsh,
        "qber": round(qber, 4),
        "error_count": error_count,
        "compared_bits": compared_bits,
        "correlations": correlations,
        "correlation_model": "classical_singlet_sampler",
        "key_bits": [record["alice_bit"] for record in key_records if not record["error"]],
        "key_records": key_records,
        "security_status": security_status,
        "key_subset_size": len(correlated_key_subset),
        "bell_subset_size": len(correlated_bell_subset),
        "discarded_subset_size": len(request.reconciled.get("discarded_subset", [])),
    }
