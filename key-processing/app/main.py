import hashlib
import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("key-processing")

app = FastAPI(title="E91 Key Processing")

KEY_BASIS_PAIRS = ("K0/K0", "K1/K1")
MIN_SIFTED_KEY_BITS = 256
HASH_FUNCTION = "SHA-256"
PRIVACY_AMPLIFICATION = "simplified_hash_demo"


class GenerateKeyRequest(BaseModel):
    session_id: str
    evaluation: dict
    reconciled: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "key-processing"}


def outcome_to_bit(outcome: int) -> int:
    return 1 if outcome == 1 else 0


def basis_pair(item: dict) -> str:
    return f"{item.get('alice_basis')}/{item.get('bob_basis')}"


def build_key_records(key_subset: list[dict], evaluation_records: list[dict]) -> list[dict]:
    evaluation_by_pair = {
        record.get("pair_id"): record
        for record in evaluation_records
        if record.get("pair_id") is not None
    }
    records = []

    for item in key_subset:
        pair_basis = basis_pair(item)
        if pair_basis not in KEY_BASIS_PAIRS:
            continue

        evaluation_record = evaluation_by_pair.get(item.get("pair_id"))
        if evaluation_record and "alice_bit" in evaluation_record and "bob_corrected_bit" in evaluation_record:
            alice_bit = int(evaluation_record["alice_bit"])
            bob_corrected_bit = int(evaluation_record["bob_corrected_bit"])
            error = bool(evaluation_record.get("error", alice_bit != bob_corrected_bit))
        else:
            alice_bit = outcome_to_bit(int(item["alice_outcome"]))
            bob_raw_bit = outcome_to_bit(int(item["bob_outcome"]))
            bob_corrected_bit = 1 - bob_raw_bit
            error = alice_bit != bob_corrected_bit

        records.append(
            {
                "pair_id": item.get("pair_id"),
                "basis_pair": pair_basis,
                "alice_bit": alice_bit,
                "bob_corrected_bit": bob_corrected_bit,
                "error": error,
            }
        )

    return records


@app.post("/generate-key")
def generate_key(request: GenerateKeyRequest) -> dict:
    logger.info("Generating hashed key material for %s", request.session_id)
    key_subset = request.reconciled.get("key_subset", [])
    key_records = build_key_records(key_subset, request.evaluation.get("key_records", []))
    raw_key_bits = "".join(str(record["alice_bit"]) for record in key_records)
    sifted_key_bits = "".join(str(record["alice_bit"]) for record in key_records if not record["error"])
    raw_key_length = len(raw_key_bits)
    sifted_key_length = len(sifted_key_bits)
    key_basis_counts = {}
    for record in key_records:
        key_basis_counts[record["basis_pair"]] = key_basis_counts.get(record["basis_pair"], 0) + 1

    security_status = request.evaluation.get("security_status")

    if sifted_key_length < MIN_SIFTED_KEY_BITS:
        final_key = None
        final_key_length = 0
        key_status = "insufficient_key_material"
        key_reason = f"Need at least {MIN_SIFTED_KEY_BITS} sifted key bits"
    elif security_status == "secure":
        final_key = hashlib.sha256(raw_key_bits.encode("utf-8")).hexdigest()
        final_key_length = 256
        key_status = "generated"
        key_reason = "Secure session; final key derived from corrected key subset bits"
    elif security_status == "degraded":
        final_key = None
        final_key_length = 0
        key_status = "discarded_degraded"
        key_reason = "Session degraded; final key discarded"
    else:
        final_key = None
        final_key_length = 0
        key_status = "discarded"
        key_reason = "Session insecure; final key discarded"

    return {
        "session_id": request.session_id,
        "raw_key_length": raw_key_length,
        "sifted_key_length": sifted_key_length,
        "raw_key_source": "key_subset",
        "raw_key_preview": raw_key_bits[:32],
        "key_basis_counts": key_basis_counts,
        "key_basis_pairs": list(KEY_BASIS_PAIRS),
        "hash_function": HASH_FUNCTION,
        "privacy_amplification": PRIVACY_AMPLIFICATION,
        "final_key_length": final_key_length,
        "final_key": final_key,
        "key_status": key_status,
        "key_reason": key_reason,
    }
