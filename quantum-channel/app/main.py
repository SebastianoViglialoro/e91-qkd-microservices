import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("quantum-channel")

app = FastAPI(title="E91 Quantum Channel")

NOISE_MODEL_URL = os.getenv("NOISE_MODEL_URL", "http://noise-model:8004")
EVE_URL = os.getenv("EVE_URL", "http://eve-service:8007")


class Pair(BaseModel):
    pair_id: str
    state: str
    noise_applied: bool = False
    noise_level: float = 0.0
    eve_applied: bool = False


class TransmitRequest(BaseModel):
    session_id: str
    pairs: list[Pair]
    enable_noise: bool = False
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)
    enable_eve: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quantum-channel"}


@app.post("/transmit")
async def transmit(request: TransmitRequest) -> dict:
    logger.info("Transmitting %s pairs for %s", len(request.pairs), request.session_id)
    pairs = [pair.model_dump() for pair in request.pairs]
    disturbed_pair_ids: list[str] = []
    noise_applied_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        if request.enable_noise:
            response = await client.post(
                f"{NOISE_MODEL_URL}/apply-noise",
                json={"session_id": request.session_id, "pairs": pairs, "noise_level": request.noise_level},
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=response.text)
            noise_result = response.json()
            disturbed_pair_ids = noise_result["disturbed_pair_ids"]
            disturbed_pair_id_set = set(disturbed_pair_ids)
            noise_applied_count = noise_result["noise_applied_count"]
            pairs = [
                {
                    **pair,
                    "noise_applied": pair["pair_id"] in disturbed_pair_id_set,
                    "noise_level": request.noise_level,
                }
                for pair in pairs
            ]

        if request.enable_eve:
            response = await client.post(
                f"{EVE_URL}/attack",
                json={"session_id": request.session_id, "pairs": pairs, "attack_probability": 0.05},
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=response.text)
            pairs = response.json()["pairs"]

    alice_qubits = [{"pair_id": pair["pair_id"], "owner": "alice", **pair} for pair in pairs]
    bob_qubits = [{"pair_id": pair["pair_id"], "owner": "bob", **pair} for pair in pairs]
    return {
        "session_id": request.session_id,
        "pairs": pairs,
        "alice_qubits": alice_qubits,
        "bob_qubits": bob_qubits,
        "noise_level": request.noise_level,
        "noise_applied_count": noise_applied_count,
        "disturbed_pair_ids": disturbed_pair_ids,
    }
