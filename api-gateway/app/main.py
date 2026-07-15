import logging
import os
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("api-gateway")

app = FastAPI(title="E91 API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")
RESULT_STORE_URL = os.getenv("RESULT_STORE_URL", "http://result-store:8011")


class SimulationRequest(BaseModel):
    shots: int = Field(default=1000, gt=0)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/simulations")
async def create_simulation(request: SimulationRequest) -> dict:
    logger.info("Forwarding simulation request to orchestrator")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{ORCHESTRATOR_URL}/run-session", json=request.model_dump())
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/simulations/{session_id}")
async def get_simulation(session_id: str) -> dict:
    logger.info("Fetching simulation result %s", session_id)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{RESULT_STORE_URL}/results/{session_id}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/keys")
async def list_keys() -> list[dict]:
    logger.info("Fetching key records")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{RESULT_STORE_URL}/keys")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/keys/summary")
async def keys_summary() -> dict:
    logger.info("Fetching key summary")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{RESULT_STORE_URL}/keys/summary")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/keys/latest")
async def latest_keys(limit: int = 10) -> list[dict]:
    logger.info("Fetching latest key records")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{RESULT_STORE_URL}/keys/latest", params={"limit": limit})
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/keys/{session_id}")
async def get_key(session_id: str) -> dict:
    logger.info("Fetching key record %s", session_id)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{RESULT_STORE_URL}/keys/{session_id}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Key record not found")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
