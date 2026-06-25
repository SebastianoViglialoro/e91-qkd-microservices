import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("entangled-source")

app = FastAPI(title="E91 Entangled Source")


class GenerateRequest(BaseModel):
    session_id: str
    shots: int = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "entangled-source"}


@app.post("/generate")
def generate(request: GenerateRequest) -> dict:
    logger.info("Generating %s symbolic EPR pairs for %s", request.shots, request.session_id)
    pairs = [
        {"pair_id": f"{request.session_id}-{index}", "state": "EPR_PAIR"}
        for index in range(request.shots)
    ]
    return {"session_id": request.session_id, "pairs": pairs}
