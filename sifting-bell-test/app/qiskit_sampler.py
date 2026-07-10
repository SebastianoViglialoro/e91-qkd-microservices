from __future__ import annotations

import math
from typing import Any

from shared.bases import ALICE_BASIS_BY_NAME, BOB_BASIS_BY_NAME, get_chsh_terms


def qiskit_available() -> bool:
    try:
        import qiskit  # noqa: F401
        import qiskit_aer  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _load_qiskit() -> tuple[Any, Any, Any]:
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Qiskit is not installed. Install qiskit and qiskit-aer in sifting-bell-test."
        ) from exc
    return QuantumCircuit, transpile, AerSimulator


def _bit_to_outcome(bit: str) -> int:
    return 1 if bit == "0" else -1


def _counts_to_expectation(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0

    weighted_sum = 0.0
    for bitstring, count in counts.items():
        compact_bitstring = bitstring.replace(" ", "")
        if len(compact_bitstring) < 2:
            continue
        alice_outcome = _bit_to_outcome(compact_bitstring[-1])
        bob_outcome = _bit_to_outcome(compact_bitstring[-2])
        weighted_sum += alice_outcome * bob_outcome * count
    return weighted_sum / total


def compute_expectation_qiskit(alice_angle_deg: float, bob_angle_deg: float, shots: int) -> dict:
    QuantumCircuit, transpile, AerSimulator = _load_qiskit()

    if shots <= 0:
        raise ValueError("shots must be greater than zero")

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)

    # shared/bases.py stores physical measurement angles in degrees. Qiskit's
    # RY convention uses the half-angle parameter, then applies RY(-2 * angle).
    alice_qiskit_angle = math.radians(alice_angle_deg / 2.0)
    bob_qiskit_angle = math.radians(bob_angle_deg / 2.0)
    circuit.ry(-2.0 * alice_qiskit_angle, 0)
    circuit.ry(-2.0 * bob_qiskit_angle, 1)
    circuit.measure(0, 0)
    circuit.measure(1, 1)

    simulator = AerSimulator()
    transpiled_circuit = transpile(circuit, simulator)
    result = simulator.run(transpiled_circuit, shots=shots).result()
    counts = {str(key): int(value) for key, value in result.get_counts().items()}
    expectation = _counts_to_expectation(counts)

    return {
        "expectation": round(expectation, 4),
        "counts": counts,
        "shots": shots,
    }


def compute_chsh_qiskit(shots_per_basis: int) -> dict:
    if shots_per_basis <= 0:
        raise ValueError("shots_per_basis must be greater than zero")

    correlations = {}
    chsh = 0.0
    for term in get_chsh_terms():
        alice_basis_name = term["alice"]
        bob_basis_name = term["bob"]
        coefficient = term["coefficient"]
        alice_basis = ALICE_BASIS_BY_NAME[alice_basis_name]
        bob_basis = BOB_BASIS_BY_NAME[bob_basis_name]
        result = compute_expectation_qiskit(
            alice_basis.angle_degrees,
            bob_basis.angle_degrees,
            shots_per_basis,
        )
        result["coefficient"] = coefficient
        correlations[f"E({alice_basis_name},{bob_basis_name})"] = result
        chsh += coefficient * result["expectation"]

    chsh = round(chsh, 4)
    return {
        "chsh": chsh,
        "abs_chsh": round(abs(chsh), 4),
        "correlations": correlations,
        "sampler_mode": "qiskit",
    }
