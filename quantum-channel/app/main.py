import logging
import os
import random
from typing import Literal

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
    noise_type: Literal["bit_flip", "depolarizing"] = "bit_flip"
    lost: bool = False
    eve_applied: bool = False
    eve_attack_probability: float = 0.0
    attack_type: Literal["randomize", "intercept_resend"] = "randomize"


class TransmitRequest(BaseModel):
    session_id: str
    pairs: list[Pair]
    enable_link_loss: bool = True
    source_alice_distance_km: float = Field(default=25.0, ge=0.0)
    source_bob_distance_km: float = Field(default=25.0, ge=0.0)
    attenuation_db_per_km: float = Field(default=0.02, ge=0.0)
    loss_degraded_threshold_db: float = Field(default=5.0, ge=0.0)
    loss_critical_threshold_db: float = Field(default=7.0, ge=0.0)
    enable_noise: bool = False
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)
    noise_type: Literal["bit_flip", "depolarizing"] = "bit_flip"
    enable_eve: bool = False
    eve_attack_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    attack_type: Literal["randomize", "intercept_resend"] = "randomize"


def link_status(total_loss_db: float, degraded_threshold: float, critical_threshold: float) -> str:
    if total_loss_db >= critical_threshold:
        return "critical"
    if total_loss_db >= degraded_threshold:
        return "degraded"
    return "nominal"


def build_link_metrics(request: TransmitRequest, lost_pair_count: int) -> dict:
    alice_loss_db = request.source_alice_distance_km * request.attenuation_db_per_km
    bob_loss_db = request.source_bob_distance_km * request.attenuation_db_per_km
    total_loss_db = alice_loss_db + bob_loss_db
    transmittance = 10 ** (-total_loss_db / 10)
    return {
        "enable_link_loss": request.enable_link_loss,
        "source_alice_distance_km": request.source_alice_distance_km,
        "source_bob_distance_km": request.source_bob_distance_km,
        "attenuation_db_per_km": request.attenuation_db_per_km,
        "alice_loss_db": round(alice_loss_db, 4),
        "bob_loss_db": round(bob_loss_db, 4),
        "total_quantum_loss_db": round(total_loss_db, 4),
        "transmittance": round(transmittance, 6),
        "link_status": link_status(
            total_loss_db,
            request.loss_degraded_threshold_db,
            request.loss_critical_threshold_db,
        ),
        "lost_pair_count": lost_pair_count,
        "loss_degraded_threshold_db": request.loss_degraded_threshold_db,
        "loss_critical_threshold_db": request.loss_critical_threshold_db,
    }


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
    alice_loss_db = request.source_alice_distance_km * request.attenuation_db_per_km
    bob_loss_db = request.source_bob_distance_km * request.attenuation_db_per_km
    total_loss_db = alice_loss_db + bob_loss_db
    transmittance = 10 ** (-total_loss_db / 10)
    loss_probability = 1 - transmittance if request.enable_link_loss else 0.0
    lost_pair_ids = [
        pair["pair_id"]
        for pair in pairs
        if random.random() < loss_probability
    ]
    lost_pair_id_set = set(lost_pair_ids)
    pairs = [
        {
            **pair,
            "lost": pair["pair_id"] in lost_pair_id_set,
        }
        for pair in pairs
    ]
    lost_pairs = [
        {
            "session_id": request.session_id,
            "pair_id": pair["pair_id"],
            "reason": "link_loss",
        }
        for pair in pairs
        if pair.get("lost", False)
    ]
    link_metrics = build_link_metrics(request, len(lost_pair_ids))
    available_pairs = [pair for pair in pairs if not pair.get("lost", False)]

    async with httpx.AsyncClient(timeout=30.0) as client:
        if request.enable_noise:
            response = await client.post(
                f"{NOISE_MODEL_URL}/apply-noise",
                json={
                    "session_id": request.session_id,
                    "pairs": available_pairs,
                    "noise_level": request.noise_level,
                    "noise_type": request.noise_type,
                },
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=response.text)
            noise_result = response.json()
            disturbed_pair_ids = noise_result["disturbed_pair_ids"]
            disturbed_pair_id_set = set(disturbed_pair_ids)
            noise_applied_count = noise_result["noise_applied_count"]
            noise_type = noise_result.get("noise_type", request.noise_type)
            pairs = [
                {
                    **pair,
                    "noise_applied": pair["pair_id"] in disturbed_pair_id_set,
                    "noise_level": request.noise_level,
                    "noise_type": noise_type,
                }
                for pair in pairs
            ]

        if request.enable_eve:
            response = await client.post(
                f"{EVE_URL}/attack",
                json={
                    "session_id": request.session_id,
                    "pairs": available_pairs,
                    "eve_attack_probability": request.eve_attack_probability,
                    "attack_type": request.attack_type,
                },
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=response.text)
            eve_result = response.json()
            attacked_pair_ids = eve_result["attacked_pair_ids"]
            attacked_pair_id_set = set(attacked_pair_ids)
            eve_applied_count = eve_result["eve_applied_count"]
            attack_type = eve_result.get("attack_type", request.attack_type)
            pairs = [
                {
                    **pair,
                    "eve_applied": pair["pair_id"] in attacked_pair_id_set,
                    "eve_attack_probability": request.eve_attack_probability,
                    "attack_type": attack_type,
                }
                for pair in pairs
            ]
        available_pairs = [pair for pair in pairs if not pair.get("lost", False)]

    alice_qubits = [{"pair_id": pair["pair_id"], "owner": "alice", **pair} for pair in available_pairs]
    bob_qubits = [{"pair_id": pair["pair_id"], "owner": "bob", **pair} for pair in available_pairs]
    return {
        "session_id": request.session_id,
        "pairs": pairs,
        "alice_qubits": alice_qubits,
        "bob_qubits": bob_qubits,
        "lost_pairs": lost_pairs,
        "lost_pair_ids": lost_pair_ids,
        "link_metrics": link_metrics,
        "noise_level": request.noise_level,
        "noise_type": request.noise_type,
        "noise_applied_count": noise_applied_count,
        "disturbed_pair_ids": disturbed_pair_ids,
        "eve_attack_probability": request.eve_attack_probability,
        "attack_type": request.attack_type,
        "eve_applied_count": eve_applied_count,
        "attacked_pair_ids": attacked_pair_ids,
    }
