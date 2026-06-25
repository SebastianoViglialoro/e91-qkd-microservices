import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("eve-service")

app = FastAPI(title="E91 Eve Service")


class AttackRequest(BaseModel):
    session_id: str
    pairs: list[dict]
    attack_probability: float = Field(default=0.0, ge=0.0, le=1.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "eve-service"}


@app.post("/attack")
def attack(request: AttackRequest) -> dict:
    logger.info("Applying symbolic Eve attack probability %.3f to %s", request.attack_probability, request.session_id)
    pairs = [
        {**pair, "eve_applied": True, "attack_probability": request.attack_probability}
        for pair in request.pairs
    ]
    return {"session_id": request.session_id, "pairs": pairs}
