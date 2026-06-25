import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("result-store")

app = FastAPI(title="E91 Result Store")
RESULTS: dict[str, dict] = {}


class Result(BaseModel):
    session_id: str
    request: dict
    source: dict
    transmission: dict
    sifting_bell_test: dict
    key: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "result-store"}


@app.post("/results")
def save_result(result: Result) -> dict[str, str]:
    logger.info("Saving result %s", result.session_id)
    RESULTS[result.session_id] = result.model_dump()
    return {"status": "saved", "session_id": result.session_id}


@app.get("/results/{session_id}")
def get_result(session_id: str) -> dict:
    result = RESULTS.get(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
