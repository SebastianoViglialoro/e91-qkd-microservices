# e91-qkd-microservices

Baseline architetturale a microservizi per una simulazione del protocollo E91 per Quantum Key Distribution.

Questa versione definisce servizi FastAPI avviabili con Docker Compose e un flusso REST end-to-end. La logica quantistica e fisica e' volutamente simbolica: non e' ancora una simulazione fisica completa del protocollo E91. Qiskit non e' usato come centro della simulazione; potra' essere integrato in seguito nel servizio `sifting-bell-test` per la verifica Bell/CHSH.

## Servizi

- `api-gateway` porta `8000`
- `orchestrator` porta `8001`
- `entangled-source` porta `8002`
- `quantum-channel` porta `8003`
- `noise-model` porta `8004`
- `alice-service` porta `8005`
- `bob-service` porta `8006`
- `eve-service` porta `8007`
- `classical-channel` porta `8008`
- `sifting-bell-test` porta `8009`
- `key-processing` porta `8010`
- `result-store` porta `8011`
- `monitoring` porta `8012`
- `shared` porta `8013`

Ogni servizio espone `GET /health`.

## Avvio

```bash
docker compose up --build
```

## Test rapido

Avvia una simulazione dalla porta pubblica dell'API Gateway:

```bash
curl -X POST http://localhost:8000/simulations \
  -H "Content-Type: application/json" \
  -d '{"shots": 1000, "enable_noise": false, "enable_eve": false}'
```

La risposta contiene un `session_id`. Per leggere il risultato salvato:

```bash
curl http://localhost:8000/simulations/<session_id>
```

Esempio con rumore ed Eve abilitati:

```bash
curl -X POST http://localhost:8000/simulations \
  -H "Content-Type: application/json" \
  -d '{"shots": 1000, "enable_noise": true, "enable_eve": true}'
```

## Flusso baseline

`api-gateway` inoltra la richiesta all'`orchestrator`, che coordina:

1. `entangled-source /generate`
2. `quantum-channel /transmit`
3. `alice-service /measure`
4. `bob-service /measure`
5. `classical-channel /reconcile`
6. `sifting-bell-test /evaluate`
7. `key-processing /generate-key`
8. `result-store /results`

## Note implementative

- Comunicazione tra servizi: HTTP REST.
- Persistenza: in-memory nel servizio `result-store`.
- Nessun Kafka o message broker.
- Misure, rumore, attacco Eve, CHSH e QBER sono placeholder simbolici.
- `shared` e' predisposto come servizio baseline per futuri schemi o utility comuni.
