# e91-qkd-microservices

Baseline architetturale a microservizi per una simulazione del protocollo E91 per Quantum Key Distribution.

Questa versione definisce servizi FastAPI avviabili con Docker Compose e un flusso REST end-to-end. Gli outcome non sono ancora prodotti da Qiskit: il servizio `sifting-bell-test` usa un sampler classico delle correlazioni ideali E91 per lo stato di singoletto. CHSH e QBER sono calcolati dal post-processing dei risultati simulati. Qiskit non e' usato come centro della simulazione; potra' essere integrato in seguito nel servizio `sifting-bell-test` per la verifica Bell/CHSH.

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

## Post-processing CHSH e QBER

Le misure prodotte da `alice-service` e `bob-service` includono:

- `session_id`
- `pair_id`
- `party`
- `basis`
- `basis_angle`
- `outcome`, con valore `-1` o `+1`

Le basi per Bell/CHSH sono:

- Alice: `A0 = 0 deg`, `A1 = 90 deg`
- Bob: `B0 = 45 deg`, `B1 = -45 deg`

La base dedicata alla key extraction e' separata:

- Alice: `K = 0 deg`
- Bob: `K = 0 deg`

Il `classical-channel` riconcilia le misure per `pair_id` e produce:

- `bell_subset`, per le combinazioni `A0/B0`, `A0/B1`, `A1/B0`, `A1/B1`
- `key_subset`, per i round `K/K`
- `discarded_subset`, per tutte le altre combinazioni

Nel servizio `sifting-bell-test`, gli outcome usati per Bell test e key subset sono ricampionati con un modello classico semplificato dello stato di singoletto:

```text
E(a,b) = -cos(a - b)
P(same outcome) = (1 + E) / 2
P(different outcome) = (1 - E) / 2
```

Il servizio poi calcola:

```text
S = E(A0,B0) + E(A0,B1) + E(A1,B0) - E(A1,B1)
```

dove `E(A,B)` e' la media dei prodotti `outcome_alice * outcome_bob` per la coppia di basi considerata.

Il QBER e' calcolato sul `key_subset` come:

```text
QBER = error_count / compared_bits
```

Nei round `K/K`, lo stato di singoletto produce outcome idealmente anti-correlati. Per derivare la chiave, il bit di Bob viene quindi invertito prima del confronto con Alice.

## Note implementative

- Comunicazione tra servizi: HTTP REST.
- Persistenza: in-memory nel servizio `result-store`.
- Nessun Kafka o message broker.
- Misure iniziali, rumore e attacco Eve sono placeholder simbolici.
- Il Bell test usa un sampler classico delle correlazioni ideali E91, non Qiskit.
- CHSH e QBER sono calcolati dai risultati simulati usati nel post-processing.
- `shared` e' predisposto come servizio baseline per futuri schemi o utility comuni.
