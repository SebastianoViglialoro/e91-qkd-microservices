import logging
import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("orchestrator")

app = FastAPI(title="E91 Orchestrator")

ENTANGLED_SOURCE_URL = os.getenv("ENTANGLED_SOURCE_URL", "http://entangled-source:8002")
QUANTUM_CHANNEL_URL = os.getenv("QUANTUM_CHANNEL_URL", "http://quantum-channel:8003")
ALICE_URL = os.getenv("ALICE_URL", "http://alice-service:8005")
BOB_URL = os.getenv("BOB_URL", "http://bob-service:8006")
CLASSICAL_CHANNEL_URL = os.getenv("CLASSICAL_CHANNEL_URL", "http://classical-channel:8008")
SIFTING_BELL_TEST_URL = os.getenv("SIFTING_BELL_TEST_URL", "http://sifting-bell-test:8009")
KEY_PROCESSING_URL = os.getenv("KEY_PROCESSING_URL", "http://key-processing:8010")
RESULT_STORE_URL = os.getenv("RESULT_STORE_URL", "http://result-store:8011")


class RunSessionRequest(BaseModel):
    shots: int = Field(default=1000, gt=0)
    enable_noise: bool = False
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)
    enable_eve: bool = False


async def post_json(client: httpx.AsyncClient, url: str, payload: dict) -> dict:
    logger.info("POST %s", url)
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Service call failed: {url}: {response.text}")
    return response.json()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.post("/run-session")
async def run_session(request: RunSessionRequest) -> dict:
    session_id = str(uuid4())
    logger.info("Starting E91 baseline session %s", session_id)

    async with httpx.AsyncClient(timeout=60.0) as client:
        source = await post_json(
            client,
            f"{ENTANGLED_SOURCE_URL}/generate",
            {"session_id": session_id, "shots": request.shots},
        )
        transmitted = await post_json(
            client,
            f"{QUANTUM_CHANNEL_URL}/transmit",
            {
                "session_id": session_id,
                "pairs": source["pairs"],
                "enable_noise": request.enable_noise,
                "noise_level": request.noise_level,
                "enable_eve": request.enable_eve,
            },
        )
        alice = await post_json(
            client,
            f"{ALICE_URL}/measure",
            {"session_id": session_id, "qubits": transmitted["alice_qubits"]},
        )
        bob = await post_json(
            client,
            f"{BOB_URL}/measure",
            {"session_id": session_id, "qubits": transmitted["bob_qubits"]},
        )
        reconciled = await post_json(
            client,
            f"{CLASSICAL_CHANNEL_URL}/reconcile",
            {
                "session_id": session_id,
                "alice_measurements": alice["measurements"],
                "bob_measurements": bob["measurements"],
            },
        )
        evaluation = await post_json(
            client,
            f"{SIFTING_BELL_TEST_URL}/evaluate",
            {"session_id": session_id, "reconciled": reconciled},
        )
        key = await post_json(
            client,
            f"{KEY_PROCESSING_URL}/generate-key",
            {"session_id": session_id, "evaluation": evaluation, "reconciled": reconciled},
        )

        result = {
            "session_id": session_id,
            "request": request.model_dump(),
            "source": {"pair_count": len(source["pairs"])},
            "transmission": {
                "pair_count": len(transmitted["pairs"]),
                "noise_enabled": request.enable_noise,
                "noise_level": request.noise_level,
                "noise_applied_count": transmitted.get("noise_applied_count", 0),
                "eve_enabled": request.enable_eve,
            },
            "sifting_bell_test": evaluation,
            "key": key,
        }
        await post_json(client, f"{RESULT_STORE_URL}/results", result)

    logger.info("Completed E91 baseline session %s", session_id)
    return result
