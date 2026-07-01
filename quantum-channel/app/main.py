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
    eve_attack_probability: float = 0.0


class TransmitRequest(BaseModel):
    session_id: str
    pairs: list[Pair]
    enable_noise: bool = False
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)
    enable_eve: bool = False
    eve_attack_probability: float = Field(default=0.0, ge=0.0, le=1.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quantum-channel"}


@app.post("/transmit")
async def transmit(request: TransmitRequest) -> dict:
    logger.info("Transmitting %s pairs for %s", len(request.pairs), request.session_id)
    pairs = [pair.model_dump() for pair in request.pairs]
    disturbed_pair_ids: list[str] = []
    attacked_pair_ids: list[str] = []
    noise_applied_count = 0
    eve_applied_count = 0

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
                json={
                    "session_id": request.session_id,
                    "pairs": pairs,
                    "eve_attack_probability": request.eve_attack_probability,
                },
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=response.text)
            eve_result = response.json()
            attacked_pair_ids = eve_result["attacked_pair_ids"]
            attacked_pair_id_set = set(attacked_pair_ids)
            eve_applied_count = eve_result["eve_applied_count"]
            pairs = [
                {
                    **pair,
                    "eve_applied": pair["pair_id"] in attacked_pair_id_set,
                    "eve_attack_probability": request.eve_attack_probability,
                }
                for pair in pairs
            ]

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
        "eve_attack_probability": request.eve_attack_probability,
        "eve_applied_count": eve_applied_count,
        "attacked_pair_ids": attacked_pair_ids,
    }
