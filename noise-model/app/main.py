import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("noise-model")

app = FastAPI(title="E91 Noise Model")


class NoiseRequest(BaseModel):
    session_id: str
    pairs: list[dict]
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "noise-model"}


@app.post("/apply-noise")
def apply_noise(request: NoiseRequest) -> dict:
    logger.info("Applying symbolic noise level %.3f to %s", request.noise_level, request.session_id)
    pairs = [{**pair, "noise_applied": True, "noise_level": request.noise_level} for pair in request.pairs]
    return {"session_id": request.session_id, "pairs": pairs}
