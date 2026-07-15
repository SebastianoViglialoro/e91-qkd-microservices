# Capitolo 4 - Architettura software del simulatore E91 a microservizi

## 1. Introduzione al capitolo

Il presente capitolo descrive l'architettura software progettata e sviluppata per la simulazione del protocollo E91 di Quantum Key Distribution (QKD). Il progetto, denominato `e91-qkd-microservices`, realizza una baseline architetturale distribuita, composta da servizi indipendenti che collaborano attraverso API HTTP REST.

L'obiettivo principale non è costruire un simulatore fisico completo e definitivo, ma definire una piattaforma modulare, riproducibile ed estendibile per studiare il flusso del protocollo E91. La simulazione include la generazione di coppie entangled simboliche, la trasmissione su canale quantistico, la misura da parte di Alice e Bob, la riconciliazione classica, il calcolo del parametro CHSH, la stima del QBER, la generazione dimostrativa della chiave e la raccolta dei risultati in un repository di chiavi.

L'architettura è stata progettata per mantenere separati i ruoli principali del protocollo. Ogni servizio incapsula una responsabilità specifica: la sorgente entangled genera le coppie, il canale quantistico applica le condizioni di trasmissione, i servizi Alice e Bob scelgono le basi di misura, il canale classico effettua il sifting, il servizio Bell Test calcola CHSH e QBER, il servizio Key Processing deriva la chiave finale, mentre il Result Store conserva risultati e key record. Questa separazione rende il sistema osservabile, testabile e pronto per evoluzioni successive.

## 2. Obiettivo architetturale

La scelta di un'architettura a microservizi deriva dalla natura stessa del protocollo E91, che può essere scomposto in componenti concettuali distinti. In una simulazione monolitica, tutti i passaggi sarebbero concentrati in un unico script: generazione dello stato, scelta delle basi, rumore, attacco di Eve, sifting, calcolo CHSH, QBER e generazione della chiave. Tale approccio è più semplice in una fase iniziale, ma diventa rapidamente difficile da estendere, validare e spiegare dal punto di vista ingegneristico.

Nel progetto `e91-qkd-microservices` è stata invece adottata una decomposizione per responsabilità. Ogni servizio espone un'interfaccia chiara, riceve input strutturati e restituisce output serializzabili. Questo consente di sostituire o estendere un singolo componente senza riscrivere l'intero simulatore. Ad esempio:

- il `noise-model` può essere raffinato introducendo modelli fisici più realistici;
- `eve-service` può essere esteso con strategie di attacco più complesse;
- `sifting-bell-test` può integrare ulteriori controlli quantistici o validazioni Qiskit;
- `key-processing` può essere evoluto verso error correction e privacy amplification più vicine a una pipeline QKD reale;
- il modello di link loss può essere sostituito da un modello più fisico che includa detector, dark counts o efficienza di rivelazione.

La modularità è quindi un requisito architetturale, non solo implementativo. Il sistema è pensato come piattaforma sperimentale: ogni servizio rappresenta un punto di estensione e può essere analizzato in modo indipendente.

Un'altra scelta progettuale importante riguarda Qiskit. Qiskit non è stato usato come motore centrale dell'intera simulazione. Il flusso end-to-end usa un sampler classico delle correlazioni ideali dello stato di singoletto, mentre Qiskit è confinato al servizio `sifting-bell-test` come strumento opzionale di validazione Bell/CHSH. Questa decisione mantiene l'architettura coerente con il paradigma a microservizi: Qiskit è un componente mirato, non un monolite che ingloba l'intera logica del protocollo.

## 3. Tecnologie utilizzate

Il sistema è stato sviluppato utilizzando tecnologie leggere e riproducibili, orientate alla realizzazione di servizi indipendenti.

### Python, FastAPI, Uvicorn e Pydantic

Tutti i microservizi principali sono implementati in Python. FastAPI è stato scelto per esporre endpoint REST in modo semplice e tipizzato. Uvicorn viene utilizzato come server ASGI per l'esecuzione dei servizi. Pydantic consente di definire modelli di input e validare i payload ricevuti dagli endpoint.

Questa combinazione è adatta a una baseline di ricerca perché:

- riduce il boilerplate necessario per creare servizi HTTP;
- permette di definire contratti di input leggibili;
- rende semplice l'esecuzione locale e containerizzata;
- favorisce la documentazione automatica degli endpoint.

### Docker e Docker Compose

Docker viene utilizzato per containerizzare ogni servizio. Ogni microservizio dispone di un proprio `Dockerfile` e di un file `requirements.txt`. Docker Compose coordina l'avvio dell'intero sistema, definendo porte, rete comune e dipendenze logiche tra servizi.

Questo rende il progetto riproducibile: l'ambiente di esecuzione non dipende esclusivamente dalla configurazione locale della macchina, ma può essere ricreato tramite:

```bash
docker compose up --build
```

### HTTP REST

La comunicazione tra servizi avviene tramite chiamate HTTP REST. Non sono stati introdotti broker di messaggi, code Kafka o sistemi asincroni distribuiti. Questa scelta mantiene la baseline comprensibile e coerente con l'obiettivo della tesi: evidenziare la decomposizione architetturale senza aumentare inutilmente la complessità infrastrutturale.

### Qiskit e AerSimulator

Qiskit e Qiskit Aer sono integrati solo nel servizio `sifting-bell-test`, tramite il modulo `qiskit_sampler.py`. Il loro ruolo è validare il calcolo CHSH mediante circuiti quantistici simulati. Il servizio espone un endpoint dedicato, separato dal flusso principale, che permette di confrontare il sampler classico con una verifica basata su `QuantumCircuit` e `AerSimulator`.

### Dashboard HTML/CSS/JavaScript

Il frontend è una dashboard statica realizzata con HTML, CSS e JavaScript vanilla. Non utilizza React, Vite o backend aggiuntivi. Comunica esclusivamente con l'API Gateway e ha funzione dimostrativa: permette di lanciare simulazioni, visualizzare metriche, consultare il Mini KMS e osservare grafici recenti.

## 4. Architettura generale

Il flusso end-to-end del sistema è organizzato come una pipeline distribuita:

```text
API Gateway
  -> Orchestrator
    -> Entangled Source
    -> Quantum Channel
       -> Noise Model
       -> Eve Service
       -> Link Loss
    -> Alice Service
    -> Bob Service
    -> Classical Channel
    -> Sifting & Bell Test
    -> Key Processing
    -> Result Store / Mini KMS
  -> Dashboard
```

L'utente interagisce con il sistema tramite l'API Gateway o tramite la dashboard. L'API Gateway riceve la richiesta di simulazione e la inoltra all'Orchestrator. L'Orchestrator crea una sessione, genera un `session_id`, invoca i servizi nel corretto ordine e raccoglie i risultati parziali.

Il servizio `entangled-source` genera una lista di coppie simboliche identificate da `pair_id`. Il servizio `quantum-channel` riceve queste coppie, applica la perdita di link, chiama se necessario `noise-model` ed `eve-service`, e restituisce i qubit simbolici consegnati ad Alice e Bob. Alice e Bob scelgono basi di misura e producono misure simboliche. Il `classical-channel` confronta le basi pubbliche e divide i round in `key_subset`, `bell_subset` e `discarded_subset`.

Il servizio `sifting-bell-test` applica il sampler delle correlazioni E91, calcola CHSH e QBER, e determina lo stato di sicurezza. Il servizio `key-processing` genera la chiave finale solo se la sessione è sicura e se il materiale sifted è sufficiente. Infine, `result-store` salva il risultato completo e un record sintetico nel Mini KMS.

### Proposta di figura architetturale

**Figura 4.x - Architettura a microservizi del simulatore E91.**

La figura può rappresentare il flusso end-to-end della simulazione, evidenziando il ruolo dell'API Gateway come punto di accesso, dell'Orchestrator come coordinatore della sessione e dei servizi di dominio come componenti indipendenti. Il flusso principale dovrebbe mostrare la generazione delle coppie entangled, la trasmissione sul canale quantistico, le misure di Alice e Bob, il sifting sul canale classico, il calcolo CHSH/QBER, la generazione della chiave e la persistenza nel Result Store/Mini KMS.

Componenti da includere nella figura:

- `api-gateway`, come interfaccia verso utente, script e dashboard;
- `orchestrator`, come coordinatore della pipeline;
- `entangled-source`, `quantum-channel`, `alice-service` e `bob-service`, come componenti del flusso quantistico;
- `noise-model`, `eve-service` e modello di link loss, collegati al `quantum-channel`;
- `classical-channel`, `sifting-bell-test` e `key-processing`, come componenti di post-processing;
- `result-store` e Mini KMS, come persistenza dei risultati e dei key record;
- `monitoring` e dashboard, come elementi di osservabilità e visualizzazione.

## 5. Descrizione dei microservizi

La tabella seguente riassume responsabilità, input, output e ruolo di ciascun servizio.

| Servizio | Responsabilità | Input principali | Output principali | Ruolo nella simulazione E91 |
| --- | --- | --- | --- | --- |
| `api-gateway` | Espone l'interfaccia pubblica del sistema. Riceve richieste utente e inoltra all'Orchestrator. Espone anche endpoint di consultazione risultati e chiavi. | Parametri simulazione: `shots`, noise, Eve, link loss, soglia chiave. | Risultato simulazione, key records, summary Mini KMS. | Punto unico di accesso per client, dashboard e test. |
| `orchestrator` | Coordina l'intera sessione. Invoca i servizi nel corretto ordine e costruisce il risultato finale. | Richiesta simulazione inoltrata dall'API Gateway. | Oggetto risultato contenente sorgente, trasmissione, link metrics, Bell test e chiave. | Controller applicativo del flusso E91. |
| `entangled-source` | Genera coppie entangled simboliche. | `session_id`, `shots`. | Lista di `pair_id` con stato simbolico `EPR_PAIR`. | Rappresenta la sorgente di coppie entangled. |
| `quantum-channel` | Simula la trasmissione quantistica. Applica perdita di link e coordina noise/Eve. | Lista di coppie, parametri link loss, noise ed Eve. | Coppie consegnate, coppie perse, flag `noise_applied`, flag `eve_applied`, `link_metrics`. | Modella il canale quantistico tra sorgente, Alice e Bob. |
| `noise-model` | Seleziona probabilisticamente le coppie disturbate. | Coppie disponibili, `noise_level`, `noise_type`. | `disturbed_pair_ids`, `noise_applied_count`, `noise_type`. | Rappresenta rumore fisico non intenzionale. |
| `eve-service` | Seleziona probabilisticamente le coppie attaccate. | Coppie disponibili, `eve_attack_probability`, `attack_type`. | `attacked_pair_ids`, `eve_applied_count`, `attack_type`. | Rappresenta un attaccante intenzionale sul canale quantistico. |
| `alice-service` | Sceglie casualmente una base di Alice e produce una misura simbolica. | Qubit simbolici assegnati ad Alice. | Misure con `basis`, `basis_angle`, `outcome`, flag noise/Eve/link. | Modella il receiver Alice. |
| `bob-service` | Sceglie casualmente una base di Bob e produce una misura simbolica. | Qubit simbolici assegnati a Bob. | Misure con `basis`, `basis_angle`, `outcome`, flag noise/Eve/link. | Modella il receiver Bob. |
| `classical-channel` | Riconcilia le misure in base al `pair_id` e classifica le combinazioni di basi. | Misure di Alice e Bob, coppie perse. | `key_subset`, `bell_subset`, `discarded_subset`, basi pubblicate. | Rappresenta il canale classico di sifting. |
| `sifting-bell-test` | Calcola correlazioni, CHSH, QBER e stato di sicurezza. Integra il sampler classico e l'endpoint Qiskit opzionale. | Output del classical channel. | `chsh`, `abs_chsh`, `qber`, `security_status`, `correlations`, `key_records`. | Cuore del post-processing E91. |
| `key-processing` | Deriva la raw key, controlla la soglia minima e genera SHA-256 se consentito. | Risultato Bell/QBER, `key_subset`, `min_sifted_key_length`. | `raw_key_length`, `sifted_key_length`, `final_key`, `key_status`, `key_reason`. | Produce la chiave finale dimostrativa. |
| `result-store` | Salva risultati completi e key records sintetici. | Risultato finale della sessione. | Endpoint `/results`, `/keys`, `/keys/latest`, `/keys/summary`. | Persistenza in-memory e Mini KMS dimostrativo. |
| `monitoring` | Espone endpoint placeholder per eventi e metriche. | Eventi dai servizi. | Metriche placeholder. | Base per osservabilità e dashboard future. |
| `shared` | Centralizza definizioni comuni, in particolare il modello delle basi. | Non applicabile come servizio di dominio. | Costanti e helper: basi, ruoli, classificazione, CHSH terms. | Evita duplicazione logica tra servizi. |

## 6. Modello delle basi

Il modello finale delle basi è centralizzato in `shared/bases.py` ed è identificato da:

```text
basis_model = TWO_KEY_BASES_ONE_CHECK_BASIS
```

Il modello è stato progettato per distinguere esplicitamente le basi usate per la generazione della chiave dalle basi usate per la verifica Bell/CHSH.

Le basi di Alice sono:

| Base | Angolo | Ruolo |
| --- | ---: | --- |
| `C` | 0 gradi | check |
| `K0` | 45 gradi | key |
| `K1` | 90 gradi | key |

Le basi di Bob sono:

| Base | Angolo | Ruolo |
| --- | ---: | --- |
| `K0` | 45 gradi | key |
| `K1` | 90 gradi | key |
| `C` | -45 gradi | check |

Il `key_subset` è composto dai round in cui Alice e Bob scelgono la stessa base di chiave:

```text
K0/K0
K1/K1
```

Il `bell_subset`, usato per il calcolo CHSH, è composto dalle quattro combinazioni:

```text
C/K0
C/C
K1/K0
K1/C
```

La formula CHSH implementata è:

```text
S = E(C,K0) + E(C,C) + E(K1,K0) - E(K1,C)
```

dove `E(A,B)` rappresenta la media dei prodotti degli outcome di Alice e Bob per la specifica coppia di basi. Le altre combinazioni di basi sono classificate come `discarded_subset`.

Questa scelta consente di modellare una struttura a tre basi per parte, in cui due basi sono dedicate alla generazione della chiave e una base di controllo viene usata insieme ad alcune combinazioni non-key per stimare la violazione Bell.

## 7. CHSH, QBER e classificazione

Il servizio `sifting-bell-test` riceve dal `classical-channel` i sottoinsiemi riconciliati. Per i round del `bell_subset`, il sistema applica un sampler classico delle correlazioni ideali dello stato di singoletto. Il modello usa la relazione:

```text
E(a,b) = -cos(a - b)
```

dove `a` e `b` sono gli angoli delle basi di misura. Per ogni coppia, viene scelto casualmente l'outcome di Alice in `{-1, +1}`; l'outcome di Bob viene poi campionato in modo coerente con la probabilità di ottenere outcome uguali o differenti secondo la correlazione attesa.

Per ogni combinazione CHSH vengono calcolati i prodotti:

```text
outcome_alice * outcome_bob
```

La correlazione `E(A,B)` è la media di tali prodotti. Il parametro CHSH viene quindi ottenuto come:

```text
S = E(C,K0) + E(C,C) + E(K1,K0) - E(K1,C)
```

Il sistema restituisce sia `chsh` sia `abs_chsh`. Il valore assoluto è importante perché il segno del parametro può dipendere dalle convenzioni di stato, rotazioni e mapping dei bit. Ai fini della violazione Bell, il valore fisicamente rilevante è il modulo.

Le soglie utilizzate sono:

| Grandezza | Valore | Significato |
| --- | ---: | --- |
| Classical bound | 2.0 | Limite massimo classico per CHSH |
| Secure CHSH threshold | 2.4 | Soglia operativa per considerare preservata la violazione |
| QBER secure threshold | 0.08 | QBER massimo per classificazione secure |
| QBER insecure threshold | 0.15 | QBER oltre cui la sessione diventa insecure |

Il QBER viene calcolato sul `key_subset`, cioè solo sui round `K0/K0` e `K1/K1`. Poiché lo stato di singoletto produce outcome idealmente anti-correlati sulla stessa base, il bit di Bob viene corretto invertendolo prima del confronto. Il QBER è:

```text
QBER = error_count / compared_bits
```

La classificazione della sessione è la seguente:

- `secure`: violazione CHSH preservata (`abs_chsh >= 2.4`) e QBER sotto soglia (`qber <= 0.08`);
- `degraded`: violazione ancora presente ma vicina al limite classico, oppure QBER sopra la soglia secure ma non ancora oltre la soglia insecure;
- `insecure`: violazione Bell persa (`abs_chsh <= 2.0`) oppure QBER sopra soglia critica (`qber > 0.15`).

In caso di conflitto tra condizioni, lo stato `insecure` ha priorità.

## 8. Key-processing

Il servizio `key-processing` deriva la chiave dai round classificati nel `key_subset`. Le combinazioni usate sono:

```text
K0/K0
K1/K1
```

Per ogni round valido:

1. l'outcome di Alice, espresso in `{-1, +1}`, viene convertito in bit;
2. l'outcome di Bob viene convertito in bit;
3. il bit di Bob viene invertito per correggere l'anti-correlazione ideale dello stato di singoletto;
4. i bit validi vengono raccolti nella raw key.

La conversione usata è:

```text
+1 -> 1
-1 -> 0
```

Il servizio calcola:

- `raw_key_length`;
- `sifted_key_length`;
- `raw_key_preview`, limitata ai primi bit per debug;
- `key_basis_counts`;
- `key_basis_pairs`.

Prima di generare la chiave finale, viene controllata la soglia:

```text
min_sifted_key_length
```

Il valore di default è 256 bit. Questo parametro introduce una distinzione importante tra sicurezza del canale e disponibilità operativa della chiave. Una sessione può risultare `secure` dal punto di vista CHSH/QBER, ma non produrre sufficiente materiale sifted a causa di link loss o di un numero ridotto di round utili.

La chiave finale viene generata solo se:

```text
security_status = secure
sifted_key_length >= min_sifted_key_length
```

In tal caso:

```text
final_key = SHA256(raw_key_bits).hexdigest()
final_key_length = 256
key_status = generated
```

Gli stati possibili della chiave sono:

| `key_status` | Significato |
| --- | --- |
| `generated` | La sessione è secure e il materiale sifted è sufficiente. |
| `discarded_degraded` | La sessione è degradata; la chiave viene scartata. |
| `discarded` | La sessione è insecure; la chiave viene scartata. |
| `insufficient_key_material` | La sessione è secure, ma non ci sono abbastanza bit sifted. |

Il campo:

```text
privacy_amplification = simplified_hash_demo
```

indica che SHA-256 è usato come dimostrazione semplificata di privacy amplification. Non si tratta di una implementazione QKD completa di error correction e privacy amplification. In una implementazione reale, la fase di post-processing dovrebbe includere protocolli di riconciliazione informativa, stima della leakage information e privacy amplification con parametri legati alla sicurezza composabile.

## 9. Noise Model

Il rumore è modellato tramite un microservizio separato, `noise-model`. Il servizio riceve una lista di coppie disponibili e un parametro:

```text
noise_level in [0.0, 1.0]
```

Per ogni `pair_id`, il servizio decide probabilisticamente se marcare la coppia come disturbata. L'output contiene:

- `disturbed_pair_ids`;
- `noise_applied_count`;
- `noise_type`;
- `noise_level`.

Sono supportati due tipi di rumore:

| `noise_type` | Effetto semplificato |
| --- | --- |
| `bit_flip` | Nei round disturbati viene invertito l'outcome di Bob. |
| `depolarizing` | Nei round disturbati l'outcome di Bob viene randomizzato. |

Il servizio `noise-model` non conosce basi di misura, CHSH o QBER. La sua responsabilità è solo marcare le coppie disturbate. L'effetto fisico semplificato viene applicato nel servizio `sifting-bell-test`, che dispone delle basi e può quindi degradare le correlazioni e il key subset.

L'effetto atteso dell'aumento di `noise_level` è:

- riduzione progressiva di `abs_chsh`;
- aumento del QBER;
- transizione da `secure` a `degraded` o `insecure`;
- riduzione della probabilità di ottenere `key_status = generated`.

## 10. Eve Model

Il servizio `eve-service` modella un attaccante intenzionale sul canale quantistico. È separato dal `noise-model` per mantenere distinta la perturbazione fisica non intenzionale da un attacco di sicurezza.

Il parametro principale è:

```text
eve_attack_probability in [0.0, 1.0]
```

Per ogni coppia disponibile, Eve decide probabilisticamente se marcare il `pair_id` come attaccato. L'output contiene:

- `attacked_pair_ids`;
- `eve_applied_count`;
- `attack_type`;
- `eve_attack_probability`.

Sono supportati due modelli:

| `attack_type` | Effetto semplificato |
| --- | --- |
| `randomize` | Nei round attaccati l'outcome di Bob viene randomizzato. |
| `intercept_resend` | Modello simbolico di intercettazione e reinvio; rompe la correlazione entangled sui round attaccati. |

Come per il rumore, `eve-service` non calcola CHSH e non calcola QBER. L'applicazione dell'effetto avviene nel servizio `sifting-bell-test`, dove sono disponibili basi, outcome e sottoinsiemi riconciliati.

La differenza concettuale tra rumore ed Eve è rilevante: il rumore rappresenta degradazione fisica non intenzionale, mentre Eve rappresenta una perturbazione intenzionale del canale quantistico. Entrambi possono ridurre la violazione Bell e aumentare il QBER, ma hanno significato diverso nella valutazione di sicurezza del protocollo.

## 11. Link distance e attenuation

Il modello di link distance e attenuation introduce una componente ingegneristica legata alla distanza tra sorgente, Alice e Bob. I parametri principali sono:

- `source_alice_distance_km`;
- `source_bob_distance_km`;
- `attenuation_db_per_km`;
- `loss_degraded_threshold_db`;
- `loss_critical_threshold_db`;
- `enable_link_loss`.

Le formule usate sono:

```text
alice_loss_db = source_alice_distance_km * attenuation_db_per_km
bob_loss_db = source_bob_distance_km * attenuation_db_per_km
total_quantum_loss_db = alice_loss_db + bob_loss_db
transmittance = 10 ** (-total_quantum_loss_db / 10)
```

Lo stato del link è classificato come:

| `link_status` | Condizione |
| --- | --- |
| `nominal` | `total_quantum_loss_db < loss_degraded_threshold_db` |
| `degraded` | `loss_degraded_threshold_db <= total_quantum_loss_db < loss_critical_threshold_db` |
| `critical` | `total_quantum_loss_db >= loss_critical_threshold_db` |

La link loss non è trattata come rumore. Questa distinzione è centrale:

- non aumenta direttamente il QBER;
- non modifica direttamente il valore CHSH;
- riduce il numero di coppie utili;
- può ridurre il materiale di chiave disponibile;
- può condurre a `key_status = insufficient_key_material`.

Nel `quantum-channel`, alcune coppie vengono marcate come perse con probabilità:

```text
1 - transmittance
```

Le coppie perse non vengono consegnate ad Alice e Bob, non entrano nel `key_subset` o nel `bell_subset`, e vengono conteggiate nel `discarded_subset` con ragione `link_loss`.

Questa modellazione consente di rappresentare un effetto realistico a livello architetturale: aumentando la distanza o l'attenuazione, il canale può rimanere sicuro rispetto a CHSH/QBER, ma non generare abbastanza materiale utile per produrre una chiave finale.

## 12. Mini KMS

Il servizio `result-store` è stato esteso per includere un Mini KMS dimostrativo. Non si tratta di un Key Management System industriale, ma di un repository applicativo per conservare record sintetici delle chiavi generate o scartate.

Gli endpoint esposti tramite API Gateway sono:

```text
GET /keys
GET /keys/latest?limit=N
GET /keys/{session_id}
GET /keys/summary
```

Ogni key record contiene informazioni come:

- `session_id`;
- `created_at`;
- `basis_model`;
- `security_status`;
- `key_status`;
- `abs_chsh`;
- `chsh`;
- `qber`;
- `raw_key_length`;
- `sifted_key_length`;
- `min_sifted_key_length`;
- `final_key_length`;
- `final_key`, solo se `key_status = generated`;
- `key_reason`;
- metadati noise;
- metadati Eve;
- metadati link loss;
- `privacy_amplification`;
- `hash_function`.

La scelta di salvare `final_key` solo quando la chiave è effettivamente generata rende più chiaro il comportamento del sistema. Per sessioni `discarded`, `discarded_degraded` o `insufficient_key_material`, il campo `final_key` resta nullo.

Il Mini KMS è utile per mostrare sperimentalmente come rumore, Eve, attenuazione e soglia minima influenzano la disponibilità di chiavi. Inoltre fornisce alla dashboard una sorgente dati semplice per visualizzare storico, summary e trend.

## 13. Qiskit opzionale

Il modulo:

```text
sifting-bell-test/app/qiskit_sampler.py
```

integra Qiskit in modo confinato. Il modulo implementa una verifica CHSH tramite:

- `QuantumCircuit`;
- preparazione di una Bell pair tramite `H` e `CX`;
- rotazioni `RY` per rappresentare le basi di misura;
- misure sui due qubit;
- esecuzione con `AerSimulator`;
- conversione dei counts in valori di aspettazione;
- calcolo di CHSH secondo i termini definiti in `shared/bases.py`.

L'endpoint:

```text
POST /qiskit-chsh-test
```

permette di richiedere una stima CHSH Qiskit indicando `shots_per_basis`.

Il confronto finale tra sampler classico e Qiskit ha lo scopo di validare la coerenza della componente Bell/CHSH. Il sampler classico resta il default del flusso principale `/evaluate`, mentre Qiskit viene usato solo come controllo isolato. Questa scelta è coerente con il vincolo progettuale secondo cui Qiskit non deve diventare il centro dell'intera simulazione.

Il confronto usa in particolare `abs_chsh`, poiché il segno di `chsh` può cambiare a seconda delle convenzioni di stato, rotazione e mapping dei bit. La coerenza rilevante è quindi la vicinanza del valore assoluto alla violazione attesa.

## 14. Dashboard

La dashboard è implementata come frontend statico in:

```text
frontend/
  index.html
  styles.css
  app.js
```

Comunica esclusivamente con l'API Gateway locale. Non contiene logica ufficiale di simulazione fisica: i risultati validi sono quelli prodotti dai microservizi.

La dashboard include:

- pannello `Simulation Settings`, per configurare shots, rumore, Eve, link loss e soglia della chiave;
- `Protocol View`, che visualizza il flusso Source, Quantum Channel, Alice, Bob, Noise, Eve, Classical Channel, Bell Test, Key Processing e Mini KMS;
- `Latest Simulation Result`, con CHSH, QBER, key status, link metrics e chiave mascherata;
- `Mini KMS / Key Repository`, che mostra gli ultimi key records;
- `Key Summary`, con statistiche aggregate;
- grafici recenti per CHSH, QBER, link loss e stato chiavi;
- log client degli eventi.

La dashboard include anche una live preview euristica. Questa preview calcola in tempo reale stime di perdita di link, transmittance e materiale chiave atteso mentre l'utente modifica i controlli. Tuttavia, tale preview non sostituisce la simulazione ufficiale: serve solo per rendere l'interfaccia interattiva e intuitiva.

## 15. Limiti implementativi

Il progetto è una baseline architetturale e presenta limiti intenzionali.

Il modello di rumore è simbolico. I tipi `bit_flip` e `depolarizing` degradano gli outcome in modo controllato, ma non rappresentano ancora un modello fisico completo del canale quantistico, dei detector o dell'ambiente.

Il modello di Eve è anch'esso semplificato. Gli attacchi `randomize` e `intercept_resend` servono a rompere la correlazione in modo osservabile, ma non modellano tutte le strategie di attacco possibili in un sistema QKD reale.

La fase di key-processing usa SHA-256 come dimostrazione di privacy amplification. Non include ancora error correction QKD completa, leakage accounting, verifica di sicurezza composabile o privacy amplification parametrizzata in funzione del tasso di errore.

Il Mini KMS non è un KMS industriale. Non gestisce autenticazione, autorizzazione, rotazione sicura, lifecycle policy, secure storage o integrazione KMIP. È un repository dimostrativo utile alla tesi per visualizzare disponibilità e stato delle chiavi.

Il modello di link attenuation riduce il numero di coppie utili, ma non simula fotodetector, dark counts, efficienza di rivelazione, sincronizzazione temporale o propagazione fisica completa.

Non è presente hardware quantistico reale. La simulazione è interamente software.

Infine, Qiskit non è usato come motore end-to-end. Questa è una scelta progettuale voluta: Qiskit è una validazione mirata della componente CHSH, mentre l'architettura principale resta distribuita e basata su microservizi.

## 16. Conclusione del capitolo

L'architettura sviluppata nel progetto `e91-qkd-microservices` dimostra come il protocollo E91 possa essere organizzato in una pipeline modulare, distribuita e osservabile. La separazione in microservizi consente di isolare responsabilità distinte: generazione delle coppie, trasmissione, rumore, attacco, misure, sifting, Bell test, key processing, persistenza e visualizzazione.

Il modello finale delle basi, `TWO_KEY_BASES_ONE_CHECK_BASIS`, permette di separare in modo chiaro i round usati per la generazione della chiave da quelli usati per la verifica CHSH. Il sistema calcola CHSH e QBER, classifica la sicurezza della sessione, produce una chiave SHA-256 dimostrativa quando le condizioni sono soddisfatte, e conserva i risultati in un Mini KMS.

L'aggiunta di Noise Model, Eve Model e Link Loss rende possibile eseguire campagne sperimentali controllate e osservare l'effetto di perturbazioni, attacchi e attenuazione sulla disponibilità delle chiavi. La dashboard e gli script finali completano il sistema fornendo strumenti di esecuzione, analisi e visualizzazione.

Pur restando una baseline semplificata, il progetto offre una struttura estendibile. In sviluppi futuri, i singoli servizi potranno essere raffinati introducendo modelli fisici più accurati, post-processing QKD completo, persistenza robusta, autenticazione dei canali classici e integrazione più avanzata con simulatori quantistici o hardware reale.
