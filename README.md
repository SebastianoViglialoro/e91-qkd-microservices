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
  -d '{"shots": 1000, "enable_noise": false, "noise_level": 0.0, "enable_eve": false}'
```

La risposta contiene un `session_id`. Per leggere il risultato salvato:

```bash
curl http://localhost:8000/simulations/<session_id>
```

Esempio con rumore ed Eve abilitati:

```bash
curl -X POST http://localhost:8000/simulations \
  -H "Content-Type: application/json" \
  -d '{"shots": 1000, "enable_noise": true, "noise_level": 0.05, "enable_eve": true}'
```

## Esperimenti automatici

Con i microservizi avviati, puoi eseguire una raccolta automatica di risultati:

```bash
python scripts/run_experiments.py
```

Lo script chiama l'API Gateway, stampa una tabella in console e salva:

- `results/experiment_runs.csv`, con ogni run singola
- `results/experiment_summary.csv`, con medie, deviazioni standard e distribuzione degli status
- `results/experiment_summary.json`, con lo stesso summary in formato JSON

Per impostare il numero di ripetizioni indipendenti per scenario:

```bash
python scripts/run_experiments.py --repeats 10
```

Per usare una porta diversa da `8000`:

```bash
python scripts/run_experiments.py --gateway-url http://localhost:18000 --repeats 10
```

Per generare i grafici dai risultati aggregati:

```bash
python scripts/plot_experiment_results.py
```

I PNG vengono salvati in `results/plots/`.

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

Il valore CHSH restituito e' una stima statistica su campioni finiti. Il risultato include anche:

- `abs_chsh`
- `classical_bound = 2.0`
- `tsirelson_bound = 2.8284271247461903`
- `bell_violation`, vero quando `abs_chsh > classical_bound`
- `finite_sample_estimate = true`

Il valore non viene limitato artificialmente al bound di Tsirelson: con pochi shot puo' oscillare leggermente oltre `2√2`; aumentando il numero di shot converge verso il valore teorico atteso.

Il QBER e' calcolato sul `key_subset` come:

```text
QBER = error_count / compared_bits
```

Nei round `K/K`, lo stato di singoletto produce outcome idealmente anti-correlati. Per derivare la chiave, il bit di Bob viene quindi invertito prima del confronto con Alice.

## Noise Model

Il Noise Model e' ancora simbolico e controllato. La richiesta di simulazione accetta:

```json
{
  "shots": 10000,
  "enable_noise": true,
  "noise_level": 0.05,
  "enable_eve": false,
  "eve_attack_probability": 0.0
}
```

`noise_level` e' un valore tra `0.0` e `1.0`. Il parametro viene propagato da `api-gateway` a `orchestrator`, poi a `quantum-channel`, che chiama il servizio `noise-model`.

Il servizio `noise-model` non conosce basi, CHSH o QBER. Il suo ruolo e' solo marcare alcune coppie come disturbate: per ogni `pair_id`, con probabilita' `noise_level`, restituisce quel `pair_id` in `disturbed_pair_ids`.

Il `quantum-channel` allega quindi `noise_applied=true` ai pair disturbati. Alice e Bob preservano questo flag nelle misure, il `classical-channel` lo mantiene nei subset riconciliati, e `sifting-bell-test` usa il flag per degradare le correlazioni.

Strategia simbolica attuale: dopo aver generato gli outcome ideali del singoletto, se un round ha `noise_applied=true`, `sifting-bell-test` applica un flip all'outcome di Bob. Questo riduce progressivamente `abs_chsh` sui round Bell e aumenta il QBER sui round `K/K`.

## Eve Attack

Eve e' distinta dal Noise Model:

- `noise-model` rappresenta rumore fisico non intenzionale.
- `eve-service` rappresenta un attacco intenzionale sul `quantum-channel`.

La richiesta di simulazione puo' abilitare Eve:

```json
{
  "shots": 10000,
  "enable_noise": false,
  "noise_level": 0.0,
  "enable_eve": true,
  "eve_attack_probability": 0.10
}
```

`eve_attack_probability` e' un valore tra `0.0` e `1.0`. Il parametro viene propagato da `api-gateway` a `orchestrator`, poi a `quantum-channel`, che chiama il servizio `eve-service`.

Il servizio `eve-service` non conosce basi, CHSH o QBER. Il suo ruolo e' marcare alcune coppie come attaccate: per ogni `pair_id`, con probabilita' `eve_attack_probability`, restituisce quel `pair_id` in `attacked_pair_ids`.

Il `quantum-channel` allega `eve_applied=true` ai pair attaccati. Alice e Bob preservano questo flag nelle misure, il `classical-channel` lo mantiene nei subset riconciliati, e `sifting-bell-test` usa il flag per degradare le correlazioni.

Strategia simbolica attuale: dopo aver generato gli outcome ideali del singoletto, se un round ha `eve_applied=true`, `sifting-bell-test` randomizza l'outcome di Bob. Questo rappresenta un attacco simbolico tipo intercettazione/perturbazione del canale quantistico, rompe la correlazione Alice/Bob, riduce `abs_chsh` e aumenta il QBER. Non e' ancora un modello fisico completo.

Classificazione:

- `secure`: `abs_chsh >= 2.4` e `qber <= 0.08`
- `degraded`: `abs_chsh > 2.0` e `abs_chsh < 2.4`, oppure `qber > 0.08` e `qber <= 0.15`
- `insecure`: `abs_chsh <= 2.0` oppure `qber > 0.15`

In caso di conflitto, prevale `insecure`; altrimenti prevale `degraded` su `secure`. Il risultato include `classification_reason`, una stringa breve che spiega la classificazione.

## Note implementative

- Comunicazione tra servizi: HTTP REST.
- Persistenza: in-memory nel servizio `result-store`.
- Nessun Kafka o message broker.
- Misure iniziali, Noise Model e attacco Eve sono placeholder simbolici.
- Il Noise Model marca coppie disturbate, mentre il Bell/QBER service usa quei flag per degradare correlazioni e chiave.
- Eve marca coppie attaccate, mentre il Bell/QBER service usa quei flag per rompere simbolicamente le correlazioni.
- Il Bell test usa un sampler classico delle correlazioni ideali E91, non Qiskit.
- CHSH e QBER sono calcolati dai risultati simulati usati nel post-processing.
- Non e' ancora un modello fisico completo.
- `shared` e' predisposto come servizio baseline per futuri schemi o utility comuni.
