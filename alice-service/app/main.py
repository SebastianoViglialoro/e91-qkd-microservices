import logging
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from shared.bases import ALICE_BASIS_BY_NAME, ALICE_BASIS_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("alice-service")

app = FastAPI(title="E91 Alice Service")


class MeasureRequest(BaseModel):
    session_id: str
    qubits: list[dict]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "alice-service"}


@app.post("/select-bases")
def select_bases(request: MeasureRequest) -> dict:
    logger.info("Alice selecting bases for %s symbolic qubits for %s", len(request.qubits), request.session_id)
    measurements = []
    for qubit in request.qubits:
        basis = random.choice(ALICE_BASIS_NAMES)
        basis_definition = ALICE_BASIS_BY_NAME[basis]
        measurements.append(
            {
                "session_id": request.session_id,
                "pair_id": qubit["pair_id"],
                "party": "alice",
                "basis": basis,
                "basis_angle": basis_definition.angle_degrees,
                "basis_role": basis_definition.role,
                "noise_applied": qubit.get("noise_applied", False),
                "noise_level": qubit.get("noise_level", 0.0),
                "noise_type": qubit.get("noise_type", "bit_flip"),
                "eve_applied": qubit.get("eve_applied", False),
                "eve_attack_probability": qubit.get("eve_attack_probability", 0.0),
                "attack_type": qubit.get("attack_type", "randomize"),
            }
        )
    return {"session_id": request.session_id, "measurements": measurements}


@app.post("/measure")
def measure(request: MeasureRequest) -> dict:
    """Register final joint outcomes after this receiver's local basis selection.

    The simulator supplies the jointly sampled outcomes; no local resampling.
    """
    measurements = []
    seen = set()
    for record in request.qubits:
        basis = ALICE_BASIS_BY_NAME.get(record.get("basis"))
        if (basis is None or type(record.get("outcome")) is not int
                or record["outcome"] not in (-1, 1)
                or record.get("party") != "alice"
                or record.get("session_id") != request.session_id
                or not isinstance(record.get("pair_id"), str)
                or record["pair_id"] in seen
                or record.get("basis_angle") != basis.angle_degrees
                or record.get("basis_role") != basis.role):
            raise HTTPException(status_code=422, detail="Expected unique finalized alice records with selected bases and joint outcomes")
        seen.add(record["pair_id"])
        measurements.append(dict(record))
    return {"session_id": request.session_id, "measurements": measurements}
