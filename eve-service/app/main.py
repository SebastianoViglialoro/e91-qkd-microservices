import logging
import random

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("eve-service")

app = FastAPI(title="E91 Eve Service")


class AttackRequest(BaseModel):
    session_id: str
    pairs: list[dict]
    eve_attack_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    attack_probability: float | None = Field(default=None, ge=0.0, le=1.0)

    def effective_attack_probability(self) -> float:
        return self.attack_probability if self.attack_probability is not None else self.eve_attack_probability


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "eve-service"}


@app.post("/attack")
def attack(request: AttackRequest) -> dict:
    attack_probability = request.effective_attack_probability()
    logger.info("Applying symbolic Eve attack probability %.3f to %s", attack_probability, request.session_id)
    attacked_pair_ids = [
        pair["pair_id"]
        for pair in request.pairs
        if random.random() < attack_probability
    ]
    return {
        "session_id": request.session_id,
        "eve_attack_probability": attack_probability,
        "eve_applied_count": len(attacked_pair_ids),
        "attacked_pair_ids": attacked_pair_ids,
    }
