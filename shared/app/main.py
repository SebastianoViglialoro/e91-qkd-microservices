import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("shared")

app = FastAPI(title="E91 Shared Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shared"}


@app.get("/metadata")
def metadata() -> dict[str, str]:
    return {
        "project": "e91-qkd-microservices",
        "role": "shared baseline service for future common schemas/utilities",
    }
