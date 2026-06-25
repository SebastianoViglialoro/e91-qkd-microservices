import logging
import random

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sifting-bell-test")

app = FastAPI(title="E91 Sifting and Bell Test")


class EvaluateRequest(BaseModel):
    session_id: str
    reconciled: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sifting-bell-test"}


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    logger.info("Evaluating simplified CHSH/QBER for %s", request.session_id)
    key_subset = request.reconciled.get("key_subset", [])
    mismatches = sum(1 for item in key_subset if item["alice_bit"] != item["bob_bit"])
    qber = mismatches / len(key_subset) if key_subset else 0.0

    # Future integration point: Qiskit Bell/CHSH verification.
    chsh = round(2.65 + random.uniform(-0.08, 0.08) - (qber * 0.6), 4)
    security_status = "secure" if chsh > 2.0 and qber < 0.11 else "insecure"

    return {
        "session_id": request.session_id,
        "chsh": chsh,
        "qber": round(qber, 4),
        "security_status": security_status,
        "key_subset_size": len(key_subset),
        "bell_subset_size": len(request.reconciled.get("bell_test_subset", [])),
    }
