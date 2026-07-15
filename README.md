# e91-qkd-microservices

Baseline architetturale a microservizi per una simulazione del protocollo E91 per Quantum Key Distribution.

Questa versione definisce servizi FastAPI avviabili con Docker Compose e un flusso REST end-to-end. Il flusso principale usa ancora un sampler classico delle correlazioni ideali E91 per lo stato di singoletto. Qiskit e' integrato solo in modo opzionale nel servizio `sifting-bell-test`, tramite `app/qiskit_sampler.py`, per una prima verifica Bell/CHSH con AerSimulator. Qiskit non governa l'intera architettura e non e' usato come centro della simulazione.

## Servizi

- `api-gateway` porta host `18000` -> container `8000`
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
curl -X POST http://localhost:18000/simulations \
  -H "Content-Type: application/json" \
  -d '{"shots": 1000, "enable_noise": false, "noise_level": 0.0, "enable_eve": false}'
```

La risposta contiene un `session_id`. Per leggere il risultato salvato:

```bash
curl http://localhost:18000/simulations/<session_id>
```

Esempio con rumore ed Eve abilitati:

```bash
curl -X POST http://localhost:18000/simulations \
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

Per esplicitare l'URL dell'API Gateway:

```bash
python scripts/run_experiments.py --gateway-url http://localhost:18000 --repeats 10
```

Per generare i grafici dai risultati aggregati:

```bash
python scripts/plot_experiment_results.py
```

I PNG vengono salvati in `results/plots/`.

Per confrontare il sampler classico della pipeline end-to-end con il sampler Qiskit opzionale:

```bash
python scripts/compare_samplers.py
```

Lo script esegue 10 ripetizioni con `shots=10000` per la pipeline classica e `shots_per_basis=2500` per `/qiskit-chsh-test`, poi salva:

- `results/sampler_comparison_runs.csv`
- `results/sampler_comparison_summary.csv`
- `results/sampler_comparison_summary.json`

Il sampler classico resta quello del flusso end-to-end; il sampler Qiskit viene usato come validazione isolata della verifica Bell/CHSH.

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

## Post-processing basi, check e QBER

Le misure prodotte da `alice-service` e `bob-service` includono:

- `session_id`
- `pair_id`
- `party`
- `basis`
- `basis_angle`
- `outcome`, con valore `-1` o `+1`

La baseline usa il modello `TWO_KEY_BASES_ONE_CHECK_BASIS`, definito in modo centralizzato in `shared/bases.py`.

Correzione del modello: la versione precedente usava due basi dedicate a Bell/CHSH e una sola base per la chiave (`CHSH_PLUS_KEY_BASIS`). Questa struttura e' stata superata. La baseline corretta usa due basi per la generazione della chiave, in stile BB84, e una terza base per il controllo dello stato quantistico.

Ogni receiver sceglie casualmente tra tre basi di misura:

- Alice: `C = 0 deg`, ruolo `check`
- Alice: `K0 = 45 deg`, ruolo `key`
- Alice: `K1 = 90 deg`, ruolo `key`
- Bob: `K0 = 45 deg`, ruolo `key`
- Bob: `K1 = 90 deg`, ruolo `key`
- Bob: `C = -45 deg`, ruolo `check`

Gli angoli sono centralizzati e restano modificabili in `shared/bases.py`. La logica di handshake/randomizzazione piu' raffinata per il canale di check potra' essere aggiunta in una fase successiva.

Le basi `K0/K0` e `K1/K1` sono riservate alla generazione della chiave. CHSH richiede invece quattro combinazioni di misura: la base `C` viene usata come base di controllo insieme ad alcune combinazioni non-key.

Il `classical-channel` riconcilia le misure per `pair_id` e produce:

- `key_subset`, per i round `K0/K0` e `K1/K1`
- `bell_subset`, per le combinazioni `C/K0`, `C/C`, `K1/K0`, `K1/C`
- `check_subset`, alias compatibile di `bell_subset`
- `discarded_subset`, per tutte le altre combinazioni

Il risultato del post-processing include anche:

- `basis_model = "TWO_KEY_BASES_ONE_CHECK_BASIS"`
- `alice_bases = ["C", "K0", "K1"]`
- `bob_bases = ["K0", "K1", "C"]`

Nel servizio `sifting-bell-test`, gli outcome usati per check subset e key subset sono ricampionati con un modello classico semplificato dello stato di singoletto:

```text
E(a,b) = -cos(a - b)
P(same outcome) = (1 + E) / 2
P(different outcome) = (1 - E) / 2
```

Il servizio calcola CHSH sul `bell_subset` usando i termini configurati in `shared/bases.py`:

```text
S = E(C,K0) + E(C,C) + E(K1,K0) - E(K1,C)
```

Il risultato include:

- `chsh`
- `abs_chsh`
- `chsh_available`, vero quando tutte le quattro combinazioni hanno almeno un campione
- `correlations`, con `E(C,K0)`, `E(C,C)`, `E(K1,K0)`, `E(K1,C)`

Il QBER e' calcolato sul `key_subset` come:

```text
QBER = error_count / compared_bits
```

Nei round `K0/K0` e `K1/K1`, lo stato di singoletto produce outcome idealmente anti-correlati. Per derivare la chiave, il bit di Bob viene quindi invertito prima del confronto con Alice.

## Key processing

Il servizio `key-processing` deriva la chiave dai soli round del `key_subset`:

- `K0/K0`
- `K1/K1`

Per ogni round valido:

1. l'outcome di Alice viene convertito in bit `0/1`;
2. l'outcome di Bob viene convertito in bit `0/1`;
3. il bit di Bob viene invertito, per correggere l'anti-correlazione ideale dello stato di singoletto;
4. i bit corretti vengono usati per costruire la raw key binaria.

Se `security_status = "secure"` e il materiale di chiave e' sufficiente, il servizio calcola:

```text
final_key = SHA256(raw_key_bits).hexdigest()
```

Il risultato include:

- `raw_key_length`
- `sifted_key_length`
- `raw_key_preview`, primi 32 bit per debug
- `final_key`, stringa esadecimale SHA-256
- `final_key_length = 256`
- `hash_function = "SHA-256"`
- `privacy_amplification = "simplified_hash_demo"`
- `key_basis_pairs = ["K0/K0", "K1/K1"]`

Se la sessione e' `degraded` o `insecure`, la chiave finale non viene generata e `final_key = null`. L'uso di SHA-256 e' una dimostrazione semplificata di distillazione/privacy amplification: non e' ancora una implementazione completa di error correction e privacy amplification QKD.

## Mini KMS dimostrativo

Il servizio `result-store` mantiene anche un archivio di key record sintetici. Non e' un KMS industriale: serve a mostrare come la disponibilita' delle chiavi cambia al variare di rumore ed Eve, e sara' usato dalla dashboard HTML/JS.

Quando una simulazione termina, `result-store` salva:

- il risultato completo della sessione;
- un key record sintetico con stato della chiave, QBER, CHSH, rumore, Eve e metadati di hashing.

Con Docker Compose, i key record sintetici vengono persistiti in `data/key-records.json` tramite volume locale. Il risultato completo della sessione resta invece in memoria.

La chiave finale viene salvata solo se `key_status = "generated"`. Per sessioni `discarded`, `discarded_degraded` o `insufficient_key_material`, `final_key = null`.

Endpoint esposti dall'API Gateway:

```bash
curl http://localhost:18000/keys
curl http://localhost:18000/keys/<session_id>
curl http://localhost:18000/keys/summary
curl http://localhost:18000/keys/latest?limit=10
```

## Frontend Dashboard

La cartella `frontend/` contiene una dashboard dimostrativa HTML/CSS/JavaScript vanilla, ispirata allo stile del QKD-Simulator del professore. Non usa React, Vite o TypeScript e non contiene logica di simulazione: visualizza solo i risultati prodotti dai microservizi tramite API Gateway.

Per avviarla:

```bash
cd frontend
python3 -m http.server 5173
```

Poi apri:

```text
http://localhost:5173
```

La dashboard usa l'API Gateway locale:

```text
http://localhost:18000
```

Endpoint usati:

- `POST /simulations`
- `GET /keys/summary`
- `GET /keys/latest?limit=10`
- `GET /keys/{session_id}`, previsto per dettaglio sessione
- `GET /keys`, previsto per storico completo

Pannelli principali:

- `Simulation Settings`, per configurare shots, rumore, Eve, distanza Source-Alice, distanza Source-Bob, attenuazione dB/km ed eventuale link loss;
- `Protocol View`, vista dinamica del flusso E91 con Source, Quantum Channel, Alice/Bob, Noise, Eve, Classical Channel, Bell Test, Key Processing e Mini KMS; sul canvas vengono mostrate anche distanza, perdita in dB e stato del link;
- `Latest Simulation Result`, con CHSH, QBER, security status, key status e metriche `link_metrics`;
- `Key Summary`, con statistiche aggregate del repository chiavi;
- `Mini KMS / Key Repository`, tabella delle ultime sessioni con perdita totale e `link_status`;
- `Recent Charts`, con grafici canvas nativi per preview chiave, `abs_CHSH`, QBER, perdita totale di link e conteggio delle chiavi;
- `Logs / Session History`, con eventi client ed errori.

Il mini KMS resta un repository dimostrativo, non un KMS industriale. Serve a mostrare come rumore ed Eve influenzano la disponibilita' delle chiavi. I key record sintetici vengono persistiti in `data/key-records.json` quando il servizio gira con Docker Compose; la cartella `data/` e' ignorata da Git per evitare di committare materiale runtime.

La dashboard include anche:

- pulsanti scenario per baseline, degraded/insecure via noise e link nominal/degraded/critical;
- grafico canvas dinamico con Entangled Source, Alice, Bob, Eve, Noise e Mini KMS;
- preview live dei parametri: Eve, noise, shots, distanze e attenuazione aggiornano subito colori, link, perdita stimata, coppie perse e stima della chiave;
- grafico live della chiave stimata dai controlli correnti;
- animazione leggera del canale quantistico durante le run e nella vista E91;
- refresh automatico ogni 15 secondi;
- dettaglio sessione cliccando una riga del Mini KMS.

La preview live serve solo per rendere interattiva la dashboard mentre si modificano i parametri. Per il link calcola euristicamente:

```text
loss_db = distance_km * attenuation_db_per_km
transmittance = 10 ** (-total_quantum_loss_db / 10)
```

I valori ufficiali della simulazione restano quelli restituiti dai microservizi dopo `POST /simulations` e salvati nel mini KMS.

La dashboard gira su `localhost:5173` e chiama `localhost:18000`; per questo l'API Gateway abilita CORS solo per:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Se il browser mostra errori CORS, verifica che l'immagine/container `api-gateway` sia stata ricostruita dopo questa modifica.

## Verifica Qiskit opzionale

Il servizio `sifting-bell-test` contiene un modulo isolato:

```text
sifting-bell-test/app/qiskit_sampler.py
```

Il modulo usa Qiskit solo per validare/campionare il Bell/CHSH test quando esiste una mappatura CHSH configurata:

- crea un circuito a 2 qubit e 2 bit classici;
- prepara una Bell pair con `H` sul qubit 0 e `CX(0, 1)`;
- applica rotazioni `RY` per rappresentare le basi di misura;
- misura entrambi i qubit;
- usa `AerSimulator`;
- converte i counts in correlazioni `E(A,B)`;
- calcola CHSH dai termini configurati nel modello condiviso.

Il sampler classico resta il default dell'endpoint `/evaluate`. La verifica Qiskit e' esposta solo tramite endpoint di test del servizio `sifting-bell-test`:

```bash
curl -X POST http://localhost:8009/qiskit-chsh-test \
  -H "Content-Type: application/json" \
  -d '{"shots_per_basis": 2000}'
```

Risultato atteso: `sampler_mode = "qiskit"` e `abs_chsh` vicino a `2.8`, con oscillazioni statistiche dovute al numero finito di shot. L'endpoint resta una verifica isolata: Qiskit non governa il flusso end-to-end.

Per controllare se le dipendenze Qiskit sono disponibili nel container:

```bash
curl http://localhost:8009/qiskit-health
```

## Link distance e attenuation

La richiesta di simulazione supporta un modello dimostrativo di distanza e attenuazione dei link quantistici:

```json
{
  "shots": 10000,
  "enable_link_loss": true,
  "source_alice_distance_km": 25.0,
  "source_bob_distance_km": 25.0,
  "attenuation_db_per_km": 0.02,
  "loss_degraded_threshold_db": 5.0,
  "loss_critical_threshold_db": 7.0
}
```

Il modello calcola:

```text
alice_loss_db = source_alice_distance_km * attenuation_db_per_km
bob_loss_db = source_bob_distance_km * attenuation_db_per_km
total_quantum_loss_db = alice_loss_db + bob_loss_db
transmittance = 10 ** (-total_quantum_loss_db / 10)
```

Classificazione del link:

- `nominal`: `total_quantum_loss_db < loss_degraded_threshold_db`
- `degraded`: `loss_degraded_threshold_db <= total_quantum_loss_db < loss_critical_threshold_db`
- `critical`: `total_quantum_loss_db >= loss_critical_threshold_db`

La perdita di link non e' rumore: non aumenta direttamente QBER e non modifica direttamente CHSH. Viene applicata nel `quantum-channel` marcando alcuni `pair_id` come persi con probabilita' `1 - transmittance`. I pair persi non vengono inviati ad Alice/Bob, non entrano in `key_subset` o `bell_subset`, e vengono contati nel `discarded_subset` come `link_loss`.

Se `enable_link_loss=false`, la metrica viene comunque calcolata, ma non vengono persi pair e il comportamento resta compatibile con le versioni precedenti.

Il risultato finale include `link_metrics`:

- `source_alice_distance_km`
- `source_bob_distance_km`
- `attenuation_db_per_km`
- `alice_loss_db`
- `bob_loss_db`
- `total_quantum_loss_db`
- `transmittance`
- `link_status`
- `lost_pair_count`
- `loss_degraded_threshold_db`
- `loss_critical_threshold_db`

Il Mini KMS salva anche `source_alice_distance_km`, `source_bob_distance_km`, `total_quantum_loss_db`, `link_status` e `transmittance`.

## Noise Model

Il Noise Model e' ancora simbolico e controllato. La richiesta di simulazione accetta:

```json
{
  "shots": 10000,
  "enable_noise": true,
  "noise_level": 0.05,
  "noise_type": "bit_flip",
  "enable_eve": false,
  "eve_attack_probability": 0.0
}
```

`noise_level` e' un valore tra `0.0` e `1.0`. Il parametro viene propagato da `api-gateway` a `orchestrator`, poi a `quantum-channel`, che chiama il servizio `noise-model`.

`noise_type` e' opzionale e mantiene compatibilita' con le richieste precedenti. Valori supportati:

- `bit_flip`, default: nei round disturbati `sifting-bell-test` inverte l'outcome di Bob;
- `depolarizing`: nei round disturbati `sifting-bell-test` randomizza l'outcome di Bob.

Il servizio `noise-model` non conosce basi, CHSH o QBER. Il suo ruolo e' solo marcare alcune coppie come disturbate: per ogni `pair_id`, con probabilita' `noise_level`, restituisce quel `pair_id` in `disturbed_pair_ids`.

Il `quantum-channel` allega quindi `noise_applied=true` ai pair disturbati. Alice e Bob preservano questo flag nelle misure, il `classical-channel` lo mantiene nei subset riconciliati, e `sifting-bell-test` usa il flag per degradare le correlazioni.

Questi modelli sono ancora semplificati: servono a confrontare perturbazioni diverse su CHSH, QBER e disponibilita' della chiave, non rappresentano ancora un modello fisico completo del canale.

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
  "eve_attack_probability": 0.10,
  "attack_type": "intercept_resend"
}
```

`eve_attack_probability` e' un valore tra `0.0` e `1.0`. Il parametro viene propagato da `api-gateway` a `orchestrator`, poi a `quantum-channel`, che chiama il servizio `eve-service`.

`attack_type` e' opzionale e mantiene compatibilita' con le richieste precedenti. Valori supportati:

- `randomize`, default: nei round attaccati `sifting-bell-test` randomizza l'outcome di Bob;
- `intercept_resend`: modello semplificato di intercettazione e reinvio; Eve rompe la correlazione entangled e il servizio lo implementa come outcome di Bob indipendente, mantenendo pero' il tipo di attacco distinto nel risultato.

Il servizio `eve-service` non conosce basi, CHSH o QBER. Il suo ruolo e' marcare alcune coppie come attaccate: per ogni `pair_id`, con probabilita' `eve_attack_probability`, restituisce quel `pair_id` in `attacked_pair_ids`.

Il `quantum-channel` allega `eve_applied=true` ai pair attaccati. Alice e Bob preservano questo flag nelle misure, il `classical-channel` lo mantiene nei subset riconciliati, e `sifting-bell-test` usa il flag per degradare le correlazioni.

Anche questi attacchi sono simbolici e controllati: servono a confrontare diverse perturbazioni intenzionali su CHSH, QBER e disponibilita' della chiave, non sono ancora una simulazione fisica completa di Eve.

Classificazione:

- `secure`: `abs_chsh >= 2.4` e `qber <= 0.08`
- `degraded`: `abs_chsh > 2.0` e `abs_chsh < 2.4`, oppure `qber > 0.08` e `qber <= 0.15`
- `insecure`: `abs_chsh <= 2.0` oppure `qber > 0.15`

Se una run non contiene campioni per tutte le quattro combinazioni CHSH, `chsh_available=false` e lo stato viene marcato `degraded`. In caso di conflitto, prevale `insecure`; altrimenti prevale `degraded` su `secure`. Il risultato include `classification_reason`, una stringa breve che spiega la classificazione.

## Note implementative

- Comunicazione tra servizi: HTTP REST.
- Persistenza: risultati completi in memoria; key record sintetici del Mini KMS persistiti in `data/key-records.json` quando si usa Docker Compose.
- Nessun Kafka o message broker.
- Misure iniziali, Noise Model e attacco Eve sono placeholder simbolici.
- Il Noise Model marca coppie disturbate, mentre il Bell/QBER service usa quei flag per degradare correlazioni e chiave.
- Eve marca coppie attaccate, mentre il Bell/QBER service usa quei flag per rompere simbolicamente le correlazioni.
- Il Bell test del flusso principale usa un sampler classico delle correlazioni ideali E91.
- Qiskit e' disponibile solo come verifica opzionale nel servizio `sifting-bell-test`.
- QBER e check subset sono calcolati dai risultati simulati usati nel post-processing; CHSH viene calcolato solo quando il modello di basi fornisce quattro combinazioni check complete.
- Non e' ancora un modello fisico completo.
- `shared` e' predisposto come servizio baseline per futuri schemi o utility comuni.
