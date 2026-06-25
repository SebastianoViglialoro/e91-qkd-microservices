import hashlib
import logging
import random

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("alice-service")

app = FastAPI(title="E91 Alice Service")
BASIS_CHOICES = ["A0", "A1", "A2"]


class MeasureRequest(BaseModel):
    session_id: str
    qubits: list[dict]


def stable_bit(pair_id: str) -> int:
    digest = hashlib.sha256(pair_id.encode("utf-8")).digest()
    return digest[0] % 2


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "alice-service"}


@app.post("/measure")
def measure(request: MeasureRequest) -> dict:
    logger.info("Alice measuring %s symbolic qubits for %s", len(request.qubits), request.session_id)
    measurements = []
    for qubit in request.qubits:
        basis = random.choice(BASIS_CHOICES)
        measurements.append({"pair_id": qubit["pair_id"], "basis": basis, "bit": stable_bit(qubit["pair_id"])})
    return {"session_id": request.session_id, "measurements": measurements}
