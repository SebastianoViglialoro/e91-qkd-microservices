import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("key-processing")

app = FastAPI(title="E91 Key Processing")


class GenerateKeyRequest(BaseModel):
    session_id: str
    evaluation: dict
    reconciled: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "key-processing"}


@app.post("/generate-key")
def generate_key(request: GenerateKeyRequest) -> dict:
    logger.info("Generating symbolic key for %s", request.session_id)
    raw_bits = [str(bit) for bit in request.evaluation.get("key_bits", [])]
    raw_key_length = len(request.reconciled.get("matched_measurements", []))
    sifted_key_length = len(raw_bits)

    if request.evaluation.get("security_status") == "secure" and raw_bits:
        final_key = "".join(raw_bits[: min(64, len(raw_bits))])
        final_key_length = len(final_key)
        key_status = "generated"
    elif request.evaluation.get("security_status") == "secure":
        final_key = ""
        final_key_length = 0
        key_status = "not_generated_no_key_subset"
    elif request.evaluation.get("security_status") == "degraded":
        final_key = ""
        final_key_length = 0
        key_status = "discarded_degraded"
    else:
        final_key = ""
        final_key_length = 0
        key_status = "discarded"

    return {
        "session_id": request.session_id,
        "raw_key_length": raw_key_length,
        "sifted_key_length": sifted_key_length,
        "final_key_length": final_key_length,
        "final_key": final_key or "SYMBOLIC_EMPTY_KEY",
        "key_status": key_status,
    }
