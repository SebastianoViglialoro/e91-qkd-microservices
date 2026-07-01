import hashlib
import logging
import random

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bob-service")

app = FastAPI(title="E91 Bob Service")
BASES = {
    "B0": 45.0,
    "B1": -45.0,
    "K": 0.0,
}


class MeasureRequest(BaseModel):
    session_id: str
    qubits: list[dict]


def simulated_outcome(pair_id: str, basis: str) -> int:
    """Placeholder measurement model, replaceable by a Qiskit-backed simulator later."""
    digest = hashlib.sha256(f"bob:{pair_id}:{basis}".encode("utf-8")).digest()
    return 1 if digest[0] % 2 == 0 else -1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bob-service"}


@app.post("/measure")
def measure(request: MeasureRequest) -> dict:
    logger.info("Bob measuring %s symbolic qubits for %s", len(request.qubits), request.session_id)
    measurements = []
    for qubit in request.qubits:
        basis = random.choice(list(BASES))
        outcome = simulated_outcome(qubit["pair_id"], basis)
        measurements.append(
            {
                "session_id": request.session_id,
                "pair_id": qubit["pair_id"],
                "party": "bob",
                "basis": basis,
                "basis_angle": BASES[basis],
                "outcome": outcome,
                "noise_applied": qubit.get("noise_applied", False),
                "noise_level": qubit.get("noise_level", 0.0),
                "eve_applied": qubit.get("eve_applied", False),
                "eve_attack_probability": qubit.get("eve_attack_probability", 0.0),
            }
        )
    return {"session_id": request.session_id, "measurements": measurements}
