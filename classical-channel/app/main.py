import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("classical-channel")

app = FastAPI(title="E91 Classical Channel")

CHSH_BASIS_PAIRS = {("A0", "B0"), ("A0", "B1"), ("A1", "B0"), ("A1", "B1")}
KEY_BASIS_PAIRS = {("K", "K")}


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
    discarded_subset = []

    for alice in request.alice_measurements:
        bob = bob_by_pair.get(alice["pair_id"])
        if not bob:
            discarded_subset.append({"pair_id": alice["pair_id"], "reason": "missing_bob_measurement"})
            continue
        item = {
            "session_id": request.session_id,
            "pair_id": alice["pair_id"],
            "alice_basis": alice["basis"],
            "alice_basis_angle": alice["basis_angle"],
            "alice_outcome": alice["outcome"],
            "bob_basis": bob["basis"],
            "bob_basis_angle": bob["basis_angle"],
            "bob_outcome": bob["outcome"],
            "noise_applied": alice.get("noise_applied", False) or bob.get("noise_applied", False),
            "noise_level": max(alice.get("noise_level", 0.0), bob.get("noise_level", 0.0)),
            "eve_applied": alice.get("eve_applied", False) or bob.get("eve_applied", False),
            "eve_attack_probability": max(
                alice.get("eve_attack_probability", 0.0),
                bob.get("eve_attack_probability", 0.0),
            ),
        }
        matched.append(item)
        basis_pair = (alice["basis"], bob["basis"])
        if basis_pair in CHSH_BASIS_PAIRS:
            bell_subset.append(item)
        elif basis_pair in KEY_BASIS_PAIRS:
            key_subset.append(item)
        else:
            discarded_subset.append({**item, "reason": "unsupported_basis_pair"})

    public_bases = [
        {
            "pair_id": item["pair_id"],
            "alice_basis": item["alice_basis"],
            "alice_basis_angle": item["alice_basis_angle"],
            "bob_basis": item["bob_basis"],
            "bob_basis_angle": item["bob_basis_angle"],
        }
        for item in matched
    ]
    return {
        "session_id": request.session_id,
        "matched_measurements": matched,
        "public_bases": public_bases,
        "key_subset": key_subset,
        "bell_subset": bell_subset,
        "bell_test_subset": bell_subset,
        "discarded_subset": discarded_subset,
    }
