import logging
import math
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.qiskit_sampler import compute_chsh_qiskit, qiskit_available
from shared.bases import ALICE_BASIS_NAMES, BASIS_MODEL, BOB_BASIS_NAMES, get_chsh_terms

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sifting-bell-test")

app = FastAPI(title="E91 Sifting and Bell Test")


class EvaluateRequest(BaseModel):
    session_id: str
    reconciled: dict


class QiskitChshTestRequest(BaseModel):
    shots_per_basis: int = Field(default=2000, gt=0, le=100000)


CLASSICAL_BOUND = 2.0
TSIRELSON_BOUND = 2.8284271247461903
SECURE_CHSH_THRESHOLD = 2.4
SECURE_QBER_THRESHOLD = 0.08
INSECURE_QBER_THRESHOLD = 0.15
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


def classify_security(abs_chsh: float, qber: float, chsh_available: bool) -> tuple[str, str]:
    if not chsh_available:
        if qber > INSECURE_QBER_THRESHOLD:
            return "insecure", "QBER above insecure threshold; CHSH unavailable"
        return "degraded", "CHSH unavailable for current check-basis model"
    if abs_chsh <= CLASSICAL_BOUND:
        return "insecure", "Bell violation lost"
    if qber > INSECURE_QBER_THRESHOLD:
        return "insecure", "QBER above insecure threshold"
    if abs_chsh < SECURE_CHSH_THRESHOLD:
        return "degraded", "Bell violation close to classical bound"
    if qber > SECURE_QBER_THRESHOLD:
        return "degraded", "QBER above degraded threshold"
    return "secure", "Bell violation preserved and QBER below secure threshold"


def compute_chsh_from_check_subset(correlated_check_subset: list[dict]) -> dict:
    chsh_terms = get_chsh_terms()
    if len(chsh_terms) != 4:
        return {
            "chsh": 0.0,
            "abs_chsh": 0.0,
            "bell_violation": False,
            "chsh_available": False,
            "chsh_reason": "not enough check basis combinations",
            "correlations": {},
        }

    correlations = {}
    chsh = 0.0
    for term in chsh_terms:
        alice_basis = term["alice"]
        bob_basis = term["bob"]
        coefficient = term["coefficient"]
        products = [
            item["alice_outcome"] * item["bob_outcome"]
            for item in correlated_check_subset
            if item["alice_basis"] == alice_basis and item["bob_basis"] == bob_basis
        ]
        if not products:
            return {
                "chsh": 0.0,
                "abs_chsh": 0.0,
                "bell_violation": False,
                "chsh_available": False,
                "chsh_reason": "not enough check basis samples",
                "correlations": correlations,
            }
        expectation = sum(products) / len(products)
        correlations[f"E({alice_basis},{bob_basis})"] = {
            "expectation": round(expectation, 4),
            "samples": len(products),
            "coefficient": coefficient,
        }
        chsh += coefficient * expectation

    # Future integration point: Qiskit Bell/CHSH verification.
    chsh = round(chsh, 4)
    abs_chsh = abs(chsh)
    return {
        "chsh": chsh,
        "abs_chsh": round(abs_chsh, 4),
        "bell_violation": abs_chsh > CLASSICAL_BOUND,
        "chsh_available": True,
        "chsh_reason": "computed from configured check basis combinations",
        "correlations": correlations,
    }


def correlate_with_singlet_sampler(items: list[dict]) -> list[dict]:
    correlated = []
    for item in items:
        alice_outcome, bob_outcome = sample_singlet_outcomes(
            item["alice_basis_angle"],
            item["bob_basis_angle"],
        )
        noise_type = item.get("noise_type", "bit_flip")
        attack_type = item.get("attack_type", "randomize")

        # Symbolic controlled-noise strategies:
        # - bit_flip: Bob's sampled outcome is inverted.
        # - depolarizing: Bob's sampled outcome is randomized, approximating
        #   loss of directional information without modelling a full channel.
        if item.get("noise_applied", False):
            if noise_type == "depolarizing":
                bob_outcome = random.choice(OUTCOMES)
            else:
                bob_outcome = -bob_outcome

        # Symbolic Eve strategies:
        # - randomize: Bob's outcome is randomized on attacked rounds.
        # - intercept_resend: simplified intercept/resend model; Eve breaks
        #   the entangled correlation, implemented here as an independent Bob
        #   outcome while preserving a separate attack_type in the results.
        if item.get("eve_applied", False):
            bob_outcome = random.choice(OUTCOMES)
        correlated.append(
            {
                **item,
                "alice_outcome": alice_outcome,
                "bob_outcome": bob_outcome,
                "correlation_model": "classical_singlet_sampler",
                "noise_type": noise_type,
                "attack_type": attack_type,
            }
        )
    return correlated


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sifting-bell-test"}


@app.get("/qiskit-health")
def qiskit_health() -> dict:
    return {
        "status": "ok",
        "service": "sifting-bell-test",
        "qiskit_available": qiskit_available(),
        "sampler_mode": "qiskit_optional",
        "default_sampler_mode": "classical_singlet_sampler",
    }


@app.post("/qiskit-chsh-test")
def qiskit_chsh_test(request: QiskitChshTestRequest) -> dict:
    try:
        result = compute_chsh_qiskit(request.shots_per_basis)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "basis_model": BASIS_MODEL,
        "alice_bases": list(ALICE_BASIS_NAMES),
        "bob_bases": list(BOB_BASIS_NAMES),
        "shots_per_basis": request.shots_per_basis,
        **result,
    }


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    logger.info("Evaluating CHSH/QBER from simulated post-processing data for %s", request.session_id)
    key_subset = request.reconciled.get("key_subset", [])
    check_subset = request.reconciled.get(
        "check_subset",
        request.reconciled.get("bell_subset", request.reconciled.get("bell_test_subset", [])),
    )
    correlated_check_subset = correlate_with_singlet_sampler(check_subset)
    correlated_key_subset = correlate_with_singlet_sampler(key_subset)
    matched_measurements = request.reconciled.get("matched_measurements", [])
    noise_applied_count = sum(1 for item in matched_measurements if item.get("noise_applied", False))
    noise_levels = [
        item.get("noise_level", 0.0)
        for item in matched_measurements
        if item.get("noise_level", 0.0) > 0.0
    ]
    noise_level = max(noise_levels, default=0.0)
    noise_enabled = noise_level > 0.0
    noise_type = next(
        (
            item.get("noise_type", "bit_flip")
            for item in matched_measurements
            if item.get("noise_applied", False) or item.get("noise_level", 0.0) > 0.0
        ),
        "bit_flip",
    )
    eve_applied_count = sum(1 for item in matched_measurements if item.get("eve_applied", False))
    eve_attack_probabilities = [
        item.get("eve_attack_probability", 0.0)
        for item in matched_measurements
        if item.get("eve_attack_probability", 0.0) > 0.0
    ]
    eve_attack_probability = max(eve_attack_probabilities, default=0.0)
    eve_enabled = eve_attack_probability > 0.0
    attack_type = next(
        (
            item.get("attack_type", "randomize")
            for item in matched_measurements
            if item.get("eve_applied", False) or item.get("eve_attack_probability", 0.0) > 0.0
        ),
        "randomize",
    )

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

    chsh_result = compute_chsh_from_check_subset(correlated_check_subset)
    security_status, classification_reason = classify_security(
        chsh_result["abs_chsh"],
        qber,
        chsh_result["chsh_available"],
    )

    return {
        "session_id": request.session_id,
        "basis_model": BASIS_MODEL,
        "alice_bases": list(ALICE_BASIS_NAMES),
        "bob_bases": list(BOB_BASIS_NAMES),
        "chsh": chsh_result["chsh"],
        "abs_chsh": chsh_result["abs_chsh"],
        "classical_bound": CLASSICAL_BOUND,
        "tsirelson_bound": TSIRELSON_BOUND,
        "bell_violation": chsh_result["bell_violation"],
        "chsh_available": chsh_result["chsh_available"],
        "chsh_reason": chsh_result["chsh_reason"],
        "finite_sample_estimate": True,
        "qber": round(qber, 4),
        "error_count": error_count,
        "compared_bits": compared_bits,
        "noise_enabled": noise_enabled,
        "noise_level": noise_level,
        "noise_type": noise_type,
        "noise_applied_count": noise_applied_count,
        "eve_enabled": eve_enabled,
        "eve_attack_probability": eve_attack_probability,
        "attack_type": attack_type,
        "eve_applied_count": eve_applied_count,
        "correlations": chsh_result["correlations"],
        "correlation_model": "classical_singlet_sampler",
        "key_bits": [record["alice_bit"] for record in key_records if not record["error"]],
        "key_records": key_records,
        "security_status": security_status,
        "classification_reason": classification_reason,
        "key_subset_size": len(correlated_key_subset),
        "check_subset_size": len(correlated_check_subset),
        "bell_subset_size": len(correlated_check_subset),
        "discarded_subset_size": len(request.reconciled.get("discarded_subset", [])),
    }
