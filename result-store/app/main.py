import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("result-store")

app = FastAPI(title="E91 Result Store")
RESULTS: dict[str, dict] = {}
KEY_RECORDS: dict[str, dict] = {}
KEY_RECORDS_PATH = Path(os.getenv("KEY_RECORDS_PATH", "/data/key-records.json"))


class Result(BaseModel):
    session_id: str
    request: dict
    source: dict
    transmission: dict
    link_metrics: dict = Field(default_factory=dict)
    sifting_bell_test: dict
    key: dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_key_record(result: dict) -> dict:
    session_id = result["session_id"]
    request = result.get("request", {})
    transmission = result.get("transmission", {})
    link_metrics = result.get("link_metrics", {})
    evaluation = result.get("sifting_bell_test", {})
    key = result.get("key", {})
    key_status = key.get("key_status")

    return {
        "session_id": session_id,
        "created_at": utc_now_iso(),
        "basis_model": evaluation.get("basis_model"),
        "security_status": evaluation.get("security_status"),
        "key_status": key_status,
        "abs_chsh": evaluation.get("abs_chsh"),
        "chsh": evaluation.get("chsh"),
        "qber": evaluation.get("qber"),
        "raw_key_length": key.get("raw_key_length"),
        "sifted_key_length": key.get("sifted_key_length"),
        "final_key_length": key.get("final_key_length"),
        "final_key": key.get("final_key") if key_status == "generated" else None,
        "key_reason": key.get("key_reason"),
        "noise_enabled": transmission.get("noise_enabled", request.get("enable_noise", False)),
        "noise_level": transmission.get("noise_level", request.get("noise_level", 0.0)),
        "noise_type": transmission.get(
            "noise_type",
            evaluation.get("noise_type", request.get("noise_type", "bit_flip")),
        ),
        "eve_enabled": transmission.get("eve_enabled", request.get("enable_eve", False)),
        "eve_attack_probability": transmission.get(
            "eve_attack_probability",
            request.get("eve_attack_probability", 0.0),
        ),
        "attack_type": transmission.get(
            "attack_type",
            evaluation.get("attack_type", request.get("attack_type", "randomize")),
        ),
        "source_alice_distance_km": link_metrics.get(
            "source_alice_distance_km",
            request.get("source_alice_distance_km"),
        ),
        "source_bob_distance_km": link_metrics.get(
            "source_bob_distance_km",
            request.get("source_bob_distance_km"),
        ),
        "total_quantum_loss_db": link_metrics.get("total_quantum_loss_db"),
        "link_status": link_metrics.get("link_status"),
        "transmittance": link_metrics.get("transmittance"),
        "privacy_amplification": key.get("privacy_amplification"),
        "hash_function": key.get("hash_function"),
    }


def average_numeric(records: list[dict], field: str) -> float:
    values = [record[field] for record in records if isinstance(record.get(field), (int, float))]
    return round(mean(values), 4) if values else 0.0


def load_key_records() -> None:
    if not KEY_RECORDS_PATH.exists():
        logger.info("No persisted key records found at %s", KEY_RECORDS_PATH)
        return

    try:
        with KEY_RECORDS_PATH.open(encoding="utf-8") as key_records_file:
            payload = json.load(key_records_file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Cannot load persisted key records from %s: %s", KEY_RECORDS_PATH, exc)
        return

    records = payload.get("key_records", {})
    if not isinstance(records, dict):
        logger.warning("Ignoring invalid key records payload at %s", KEY_RECORDS_PATH)
        return

    KEY_RECORDS.update(records)
    logger.info("Loaded %s persisted key records from %s", len(KEY_RECORDS), KEY_RECORDS_PATH)


def persist_key_records() -> None:
    payload = {"key_records": KEY_RECORDS}
    try:
        KEY_RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp_path = KEY_RECORDS_PATH.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as key_records_file:
            json.dump(payload, key_records_file, indent=2)
        temp_path.replace(KEY_RECORDS_PATH)
    except OSError as exc:
        logger.warning("Cannot persist key records to %s: %s", KEY_RECORDS_PATH, exc)


@app.on_event("startup")
def startup() -> None:
    load_key_records()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "result-store"}


@app.post("/results")
def save_result(result: Result) -> dict[str, str]:
    logger.info("Saving result %s", result.session_id)
    result_payload = result.model_dump()
    RESULTS[result.session_id] = result_payload
    KEY_RECORDS[result.session_id] = build_key_record(result_payload)
    persist_key_records()
    return {"status": "saved", "session_id": result.session_id}


@app.get("/results/{session_id}")
def get_result(session_id: str) -> dict:
    result = RESULTS.get(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@app.get("/keys")
def list_keys() -> list[dict]:
    return sorted(KEY_RECORDS.values(), key=lambda record: record["created_at"])


@app.get("/keys/summary")
def keys_summary() -> dict:
    records = list(KEY_RECORDS.values())
    total_sessions = len(records)
    generated_keys = sum(1 for record in records if record.get("key_status") == "generated")
    discarded_degraded = sum(
        1 for record in records if record.get("key_status") == "discarded_degraded"
    )
    discarded_insecure = sum(1 for record in records if record.get("key_status") == "discarded")
    insufficient_key_material = sum(
        1 for record in records if record.get("key_status") == "insufficient_key_material"
    )

    return {
        "total_sessions": total_sessions,
        "generated_keys": generated_keys,
        "discarded_degraded": discarded_degraded,
        "discarded_insecure": discarded_insecure,
        "insufficient_key_material": insufficient_key_material,
        "average_qber": average_numeric(records, "qber"),
        "average_abs_chsh": average_numeric(records, "abs_chsh"),
        "generated_key_rate": round(generated_keys / total_sessions, 4) if total_sessions else 0.0,
    }


@app.get("/keys/latest")
def latest_keys(limit: int = 10) -> list[dict]:
    sorted_records = sorted(KEY_RECORDS.values(), key=lambda record: record["created_at"], reverse=True)
    return sorted_records[: max(0, limit)]


@app.get("/keys/{session_id}")
def get_key(session_id: str) -> dict:
    record = KEY_RECORDS.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Key record not found")
    return record
