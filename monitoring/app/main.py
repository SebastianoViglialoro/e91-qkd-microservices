import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("monitoring")

app = FastAPI(title="E91 Monitoring")
EVENTS: list[dict] = []


class Event(BaseModel):
    service: str
    event_type: str
    payload: dict = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "monitoring"}


@app.post("/events")
def receive_event(event: Event) -> dict[str, int | str]:
    logger.info("Event from %s: %s", event.service, event.event_type)
    EVENTS.append(event.model_dump())
    return {"status": "accepted", "event_count": len(EVENTS)}


@app.get("/metrics")
def metrics() -> dict:
    return {
        "service": "monitoring",
        "events_received": len(EVENTS),
        "metrics_status": "placeholder",
    }
