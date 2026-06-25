import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("classical-channel")

app = FastAPI(title="E91 Classical Channel")

KEY_BASIS_PAIRS = {("A0", "B0"), ("A1", "B1")}


class ReconcileRequest(BaseModel):
    session_id: str
    alice_measurements: list[dict]
    bob_measurements: list[dict]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "classical-channel"}


@app.post("/reconcile")
def reconcile(request: ReconcileRequest) -> dict:
    logger.info("Reconciling measurements for %s", request.session_id)
    bob_by_pair = {measurement["pair_id"]: measurement for measurement in request.bob_measurements}
    matched = []
    key_subset = []
    bell_subset = []

    for alice in request.alice_measurements:
        bob = bob_by_pair.get(alice["pair_id"])
        if not bob:
            continue
        item = {
            "pair_id": alice["pair_id"],
            "alice_basis": alice["basis"],
            "bob_basis": bob["basis"],
            "alice_bit": alice["bit"],
            "bob_bit": bob["bit"],
        }
        matched.append(item)
        if (alice["basis"], bob["basis"]) in KEY_BASIS_PAIRS:
            key_subset.append(item)
        else:
            bell_subset.append(item)

    public_bases = [
        {"pair_id": item["pair_id"], "alice_basis": item["alice_basis"], "bob_basis": item["bob_basis"]}
        for item in matched
    ]
    return {
        "session_id": request.session_id,
        "matched_measurements": matched,
        "public_bases": public_bases,
        "key_subset": key_subset,
        "bell_test_subset": bell_subset,
    }
