# Capitolo 5 - Risultati sperimentali del simulatore E91

## 1. Introduzione

Questo capitolo presenta i risultati sperimentali ottenuti con il progetto `e91-qkd-microservices`. L'obiettivo non è valutare un sistema QKD fisico completo, ma verificare il comportamento della baseline architetturale sviluppata nel Capitolo 4 in presenza di condizioni controllate: canale ideale, perdita di link, rumore, attacco di Eve e combinazioni di tali perturbazioni.

Il modello finale utilizzato negli esperimenti è:

```text
basis_model = TWO_KEY_BASES_ONE_CHECK_BASIS
```

Nel modello implementato, i round di chiave sono quelli in cui Alice e Bob scelgono basi coincidenti di tipo `key`, mentre i round di controllo vengono usati per stimare la violazione Bell tramite CHSH. Il sistema calcola inoltre QBER sul key subset, genera una chiave dimostrativa tramite SHA-256 quando la sessione è sicura e registra i risultati sintetici nel Mini KMS.

I risultati analizzati in questo capitolo derivano dalla campagna sperimentale finale salvata nei file:

```text
results/final/final_experiment_runs.csv
results/final/final_experiment_summary.csv
results/final/final_experiment_summary.json
results/final/final_sampler_comparison_runs.csv
results/final/final_sampler_comparison_summary.csv
results/final/final_sampler_comparison_summary.json
results/final/plots/*.png
```

Tutti i dati numerici riportati nelle tabelle sono estratti dai file CSV finali. I grafici generati sono salvati nella directory:

```text
results/final/plots/
```

## 2. Setup sperimentale

La campagna finale è stata eseguita tramite API Gateway, utilizzando lo script:

```bash
python scripts/run_final_experiments.py --gateway-url http://localhost:18000 --shots 10000 --repeats 10
```

Il sistema era avviato tramite Docker Compose e ogni esperimento è stato eseguito invocando l'endpoint pubblico:

```text
POST /simulations
```

Ogni scenario è stato ripetuto 10 volte per ridurre l'effetto della variabilità statistica del campionamento. La tabella seguente riassume la configurazione sperimentale.

| Parametro | Valore |
| --- | ---: |
| Scenari totali | 36 |
| Ripetizioni per scenario | 10 |
| Run totali | 360 |
| Run fallite | 0 |
| Shots per run | 10000 |
| Basis model | `TWO_KEY_BASES_ONE_CHECK_BASIS` |
| Key subset | `K0/K0`, `K1/K1` |
| Bell subset | `C/K0`, `C/C`, `K1/K0`, `K1/C` |
| Soglia CHSH secure | 2.4 |
| Classical bound CHSH | 2.0 |
| Soglia QBER secure | 0.08 |
| Soglia QBER insecure | 0.15 |
| Min sifted key length default | 256 bit |

Le metriche principali raccolte per ogni run sono:

- `abs_chsh`, cioè il modulo del parametro CHSH;
- `qber`, calcolato sul key subset;
- `security_status`, con valori `secure`, `degraded`, `insecure`;
- `key_status`, con valori `generated`, `discarded_degraded`, `discarded`, `insufficient_key_material`;
- `sifted_key_length` e `final_key_length`;
- metriche di rumore, Eve e link loss;
- informazioni di Mini KMS.

I grafici finali includono linee di riferimento per le soglie CHSH e QBER. In particolare, nei grafici CHSH sono riportati il limite classico 2.0 e la soglia operativa secure 2.4; nei grafici QBER sono riportate le soglie 0.08 e 0.15.

### Nota metodologica su CHSH e campionamento finito

I valori di `abs_chsh` riportati nel capitolo sono stime empiriche ottenute da un numero finito di campioni. Per questo motivo, in alcuni scenari il valore stimato può risultare leggermente superiore a `2√2`, cioè al limite teorico di Tsirelson per il caso ideale. Il simulatore non applica un clipping artificiale al valore CHSH: conserva la stima prodotta dai campioni raccolti. Eventuali oscillazioni oltre `2√2` non devono quindi essere interpretate come un superamento fisico del limite teorico, ma come effetto statistico del campionamento finito.

## 3. Baseline ideale

Lo scenario `baseline` rappresenta il caso di riferimento senza rumore, senza Eve e senza perdita di link attiva:

```text
enable_noise = false
enable_eve = false
enable_link_loss = false
min_sifted_key_length = 256
```

La baseline consente di verificare che il sampler classico delle correlazioni E91 produca una violazione CHSH coerente con il comportamento atteso e che il QBER resti nullo nel caso ideale.

| Metrica | Valore medio |
| --- | ---: |
| Run | 10 |
| Failed runs | 0 |
| abs CHSH | 2.8291 |
| QBER | 0.0000 |
| Sifted key length | 2235.3 |
| Final key length | 256.0 |
| Security secure count | 10 |
| Key generated count | 10 |
| Generated key rate | 1.00 |

Il risultato mostra che la baseline ideale è stabile:

- `abs_chsh` è vicino al valore teorico massimo atteso per una violazione Bell ideale;
- `qber` è nullo;
- tutte le 10 run sono classificate come `secure`;
- tutte le 10 run generano una chiave finale SHA-256.

Il grafico di riferimento è:

```text
results/final/plots/baseline_summary.png
```

Didascalia suggerita: **Figura 5.x - Sintesi della baseline ideale.** Il grafico riassume i valori medi di CHSH, QBER, generated key rate e lunghezza della chiave sifted nello scenario senza rumore, Eve o link loss.

## 4. Link loss e attenuation

Il modello di link loss simula l'attenuazione dovuta alla distanza tra sorgente entangled, Alice e Bob. La perdita totale viene calcolata come:

```text
alice_loss_db = source_alice_distance_km * attenuation_db_per_km
bob_loss_db = source_bob_distance_km * attenuation_db_per_km
total_quantum_loss_db = alice_loss_db + bob_loss_db
transmittance = 10 ** (-total_quantum_loss_db / 10)
```

La link loss non viene trattata come rumore. Di conseguenza, non aumenta direttamente il QBER e non modifica direttamente le correlazioni CHSH. Il suo effetto è ridurre il numero di coppie utili, marcando una parte dei `pair_id` come persi. Tali coppie non entrano nel key subset o nel bell subset.

Gli scenari di link loss utilizzano `attenuation_db_per_km = 0.02`.

| Scenario | Loss dB | Transmittance | Lost pair count | Sifted key length | abs CHSH | QBER | Generated key rate | Insufficient count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `link_nominal_25_25` | 1.00 | 0.7943 | 2066.0 | 1753.1 | 2.8170 | 0.0000 | 1.00 | 0 |
| `link_degraded_150_150` | 6.00 | 0.2512 | 7502.2 | 557.0 | 2.8433 | 0.0000 | 1.00 | 0 |
| `link_critical_200_200` | 8.00 | 0.1585 | 8416.5 | 353.5 | 2.7752 | 0.0000 | 1.00 | 0 |
| `link_critical_high_threshold` | 8.00 | 0.1585 | 8410.9 | 349.5 | 2.8427 | 0.0000 | 0.00 | 10 |

I risultati confermano la distinzione tra sicurezza fisica del canale e disponibilità operativa della chiave. Nei primi tre scenari il sistema resta `secure`, con QBER nullo e CHSH ancora elevato. Tuttavia, aumentando la perdita totale, il numero medio di coppie perse cresce in modo marcato e il materiale sifted diminuisce.

Lo scenario `link_critical_high_threshold` mostra il ruolo della soglia `min_sifted_key_length`. In questo caso il canale resta sicuro rispetto a CHSH e QBER, ma la soglia minima richiesta per generare la chiave finale è più alta del materiale sifted disponibile. Il risultato è:

```text
key_status = insufficient_key_material
```

Questo comportamento è importante per la tesi: un link può essere sicuro dal punto di vista del protocollo, ma non produrre abbastanza materiale utile per una chiave operativa.

Grafici associati:

```text
results/final/plots/link_loss_total_db_vs_sifted_key_length.png
results/final/plots/link_loss_total_db_vs_lost_pair_count.png
results/final/plots/link_loss_total_db_vs_generated_key_rate.png
results/final/plots/link_loss_status_distribution.png
```

Didascalie suggerite:

- **Figura 5.x - Effetto della perdita di link sul materiale sifted.** Mostra la diminuzione della lunghezza media della chiave sifted al crescere della perdita totale in dB.
- **Figura 5.x - Coppie perse in funzione della perdita totale.** Evidenzia l'aumento dei `lost_pair_count` al crescere dell'attenuazione.
- **Figura 5.x - Generated key rate negli scenari di link loss.** Mostra il ruolo della soglia minima di materiale chiave.
- **Figura 5.x - Distribuzione dello stato del link.** Riassume la classificazione nominal/degraded/critical degli scenari di attenuazione.

## 5. Noise sweep

La campagna include due modelli semplificati di rumore:

- `bit_flip`: nei round disturbati viene invertito l'outcome di Bob;
- `depolarizing`: nei round disturbati l'outcome di Bob viene randomizzato.

In entrambi i casi, il servizio `noise-model` seleziona probabilisticamente le coppie disturbate in base a `noise_level`. L'effetto sui risultati viene applicato nel servizio `sifting-bell-test`, dove sono disponibili le basi e i subset riconciliati.

### 5.1 Noise type: bit_flip

| Scenario | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `noise_bit_flip_0.00` | 2.8180 | 0.0000 | 10 | 0 | 0 | 1.00 |
| `noise_bit_flip_0.02` | 2.6998 | 0.0205 | 10 | 0 | 0 | 1.00 |
| `noise_bit_flip_0.05` | 2.5397 | 0.0506 | 10 | 0 | 0 | 1.00 |
| `noise_bit_flip_0.10` | 2.2891 | 0.0965 | 0 | 10 | 0 | 0.00 |
| `noise_bit_flip_0.20` | 1.6743 | 0.1969 | 0 | 0 | 10 | 0.00 |
| `noise_bit_flip_0.25` | 1.3726 | 0.2465 | 0 | 0 | 10 | 0.00 |

Il rumore `bit_flip` degrada rapidamente la simulazione. Fino a `noise_level = 0.05`, il sistema resta secure. A `noise_level = 0.10`, `abs_chsh` scende sotto la soglia secure 2.4 e il QBER supera 0.08: tutte le run diventano `degraded` e la chiave viene scartata. A `noise_level = 0.20` e `0.25`, il QBER supera la soglia critica e la violazione CHSH risulta persa o molto ridotta, portando a `security_status = insecure`.

Grafici associati:

```text
results/final/plots/noise_bit_flip_abs_chsh.png
results/final/plots/noise_bit_flip_qber.png
results/final/plots/noise_bit_flip_generated_key_rate.png
results/final/plots/noise_bit_flip_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Effetto del rumore bit flip.** I grafici mostrano la riduzione di CHSH, l'aumento del QBER e la conseguente transizione dello stato della chiave al crescere di `noise_level`.

### 5.2 Noise type: depolarizing

| Scenario | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `noise_depolarizing_0.00` | 2.8242 | 0.0000 | 10 | 0 | 0 | 1.00 |
| `noise_depolarizing_0.02` | 2.7894 | 0.0105 | 10 | 0 | 0 | 1.00 |
| `noise_depolarizing_0.05` | 2.6910 | 0.0247 | 10 | 0 | 0 | 1.00 |
| `noise_depolarizing_0.10` | 2.5421 | 0.0493 | 10 | 0 | 0 | 1.00 |
| `noise_depolarizing_0.20` | 2.2724 | 0.1025 | 0 | 10 | 0 | 0.00 |
| `noise_depolarizing_0.25` | 2.1138 | 0.1268 | 0 | 10 | 0 | 0.00 |

Il modello `depolarizing` produce una degradazione più graduale rispetto a `bit_flip`. Fino a `noise_level = 0.10` la sessione resta secure. A `noise_level = 0.20` e `0.25`, il sistema passa a `degraded`, principalmente per la riduzione di CHSH sotto la soglia secure e per l'aumento del QBER oltre 0.08, ma senza raggiungere la classificazione `insecure` nelle 10 ripetizioni.

Grafici associati:

```text
results/final/plots/noise_depolarizing_abs_chsh.png
results/final/plots/noise_depolarizing_qber.png
results/final/plots/noise_depolarizing_generated_key_rate.png
results/final/plots/noise_depolarizing_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Effetto del rumore depolarizing.** I grafici mostrano una degradazione più graduale rispetto al modello bit flip, con passaggio a stato degraded ai livelli di rumore più elevati.

## 6. Eve sweep

Gli esperimenti su Eve valutano l'effetto di un attaccante intenzionale sul canale quantistico. Sono stati confrontati due modelli simbolici:

- `randomize`: l'outcome di Bob viene randomizzato nei round attaccati;
- `intercept_resend`: modello semplificato di intercettazione e reinvio, distinto semanticamente da `randomize` ma ancora implementato come rottura controllata della correlazione.

### 6.1 Attack type: randomize

| Scenario | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `eve_randomize_0.00` | 2.8284 | 0.0000 | 10 | 0 | 0 | 1.00 |
| `eve_randomize_0.02` | 2.8062 | 0.0100 | 10 | 0 | 0 | 1.00 |
| `eve_randomize_0.05` | 2.6927 | 0.0250 | 10 | 0 | 0 | 1.00 |
| `eve_randomize_0.10` | 2.5650 | 0.0508 | 10 | 0 | 0 | 1.00 |
| `eve_randomize_0.20` | 2.2720 | 0.1019 | 0 | 10 | 0 | 0.00 |
| `eve_randomize_0.25` | 2.1032 | 0.1240 | 0 | 9 | 1 | 0.00 |

Con `attack_type = randomize`, l'aumento della probabilità di attacco riduce progressivamente `abs_chsh` e aumenta il QBER. Il sistema resta secure fino a `eve_attack_probability = 0.10`. A `0.20` diventa degraded in tutte le run. A `0.25`, una run su dieci viene classificata come insecure.

Grafici associati:

```text
results/final/plots/eve_randomize_abs_chsh.png
results/final/plots/eve_randomize_qber.png
results/final/plots/eve_randomize_generated_key_rate.png
results/final/plots/eve_randomize_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Effetto dell'attacco Eve randomize.** I grafici mostrano come la randomizzazione dei round attaccati riduca la violazione Bell e aumenti il QBER.

### 6.2 Attack type: intercept_resend

| Scenario | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `eve_intercept_resend_0.00` | 2.8431 | 0.0000 | 10 | 0 | 0 | 1.00 |
| `eve_intercept_resend_0.02` | 2.7692 | 0.0108 | 10 | 0 | 0 | 1.00 |
| `eve_intercept_resend_0.05` | 2.7035 | 0.0258 | 10 | 0 | 0 | 1.00 |
| `eve_intercept_resend_0.10` | 2.5264 | 0.0504 | 10 | 0 | 0 | 1.00 |
| `eve_intercept_resend_0.20` | 2.2959 | 0.1008 | 0 | 10 | 0 | 0.00 |
| `eve_intercept_resend_0.25` | 2.1206 | 0.1265 | 0 | 10 | 0 | 0.00 |

Anche nel caso `intercept_resend`, il comportamento è coerente con l'obiettivo del modello: aumentando la probabilità di attacco, CHSH diminuisce e QBER aumenta. La transizione a `degraded` avviene a partire da `eve_attack_probability = 0.20`. Nelle condizioni testate, questo modello non produce run insecure, ma impedisce comunque la generazione della chiave per i livelli 0.20 e 0.25.

Grafici associati:

```text
results/final/plots/eve_intercept_resend_abs_chsh.png
results/final/plots/eve_intercept_resend_qber.png
results/final/plots/eve_intercept_resend_generated_key_rate.png
results/final/plots/eve_intercept_resend_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Effetto dell'attacco Eve intercept-resend.** I grafici mostrano la degradazione della correlazione entangled nel modello simbolico di intercettazione e reinvio.

## 7. Scenari combinati Noise + Eve

Gli scenari combinati valutano l'effetto simultaneo di rumore e attacco di Eve. In questi esperimenti sono stati usati:

```text
noise_type = bit_flip
attack_type = intercept_resend
enable_link_loss = false
```

| Scenario | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `combined_0.02_0.02` | 2.6519 | 0.0296 | 10 | 0 | 0 | 1.00 |
| `combined_0.05_0.05` | 2.4207 | 0.0734 | 7 | 3 | 0 | 0.70 |
| `combined_0.10_0.10` | 2.0057 | 0.1381 | 0 | 4 | 6 | 0.00 |
| `combined_0.15_0.15` | 1.6682 | 0.2018 | 0 | 0 | 10 | 0.00 |

L'effetto combinato è più severo rispetto agli sweep isolati. A livello 0.02/0.02 il sistema resta secure. A 0.05/0.05, 7 run su 10 restano secure ma 3 diventano degraded, con generated key rate pari a 0.70. A 0.10/0.10 il sistema è al limite della violazione Bell: il valore medio di `abs_chsh` è 2.0057 e 6 run su 10 sono insecure. A 0.15/0.15 tutte le run sono insecure.

Questo risultato evidenzia che perturbazioni moderate, se combinate, possono produrre un degrado significativo anche quando singolarmente sarebbero ancora tollerabili.

Grafici associati:

```text
results/final/plots/combined_noise_eve_abs_chsh.png
results/final/plots/combined_noise_eve_qber.png
results/final/plots/combined_noise_eve_generated_key_rate.png
results/final/plots/combined_noise_eve_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Scenari combinati rumore ed Eve.** I grafici evidenziano l'effetto cumulativo di rumore `bit_flip` e attacco `intercept_resend` su CHSH, QBER e generazione della chiave.

## 8. Scenari combinati Link Loss + Noise + Eve

Gli scenari finali combinano link loss, rumore ed Eve. La configurazione di link è:

```text
source_alice_distance_km = 150
source_bob_distance_km = 150
attenuation_db_per_km = 0.02
total_quantum_loss_db = 6.0
```

Il link è quindi nello stato `degraded`, con transmittance media pari a circa 0.2512. Sono stati usati:

```text
noise_type = bit_flip
attack_type = intercept_resend
```

| Scenario | Loss dB | Lost pair count | Sifted key length | abs CHSH | QBER | Secure count | Degraded count | Insecure count | Generated key rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `link_noise_eve_low` | 6.00 | 7484.9 | 534.1 | 2.6671 | 0.0306 | 10 | 0 | 0 | 1.00 |
| `link_noise_eve_medium` | 6.00 | 7482.5 | 524.5 | 2.3604 | 0.0729 | 1 | 9 | 0 | 0.10 |
| `link_noise_eve_high` | 6.00 | 7501.9 | 470.4 | 2.0477 | 0.1453 | 0 | 6 | 4 | 0.00 |

Questi risultati mostrano l'interazione tra disponibilità del materiale di chiave e sicurezza. La link loss riduce il numero di round utili, ma non aumenta direttamente il QBER. Noise ed Eve, invece, degradano le correlazioni e aumentano il QBER. Nel caso `link_noise_eve_medium`, il sistema conserva in media un QBER sotto la soglia insecure, ma CHSH scende sotto la soglia secure in gran parte delle run: solo 1 run su 10 genera la chiave. Nel caso `link_noise_eve_high`, nessuna run genera chiave e 4 run diventano insecure.

Grafici associati:

```text
results/final/plots/combined_link_noise_eve_abs_chsh.png
results/final/plots/combined_link_noise_eve_qber.png
results/final/plots/combined_link_noise_eve_generated_key_rate.png
results/final/plots/combined_link_noise_eve_key_status_distribution.png
```

Didascalia suggerita: **Figura 5.x - Scenari combinati link loss, rumore ed Eve.** I grafici mostrano l'interazione tra riduzione del materiale utile, degradazione CHSH e aumento del QBER.

## 9. Analisi globale Mini KMS

Il Mini KMS registra un record sintetico per ogni sessione. Nella campagna finale sono state registrate 360 sessioni senza errori.

La distribuzione globale dei `security_status` è:

| Security status | Conteggio | Percentuale |
| --- | ---: | ---: |
| `secure` | 228 | 63.33% |
| `degraded` | 91 | 25.28% |
| `insecure` | 41 | 11.39% |
| Totale | 360 | 100.00% |

La distribuzione globale dei `key_status` è:

| Key status | Conteggio | Percentuale |
| --- | ---: | ---: |
| `generated` | 218 | 60.56% |
| `discarded_degraded` | 91 | 25.28% |
| `discarded` | 41 | 11.39% |
| `insufficient_key_material` | 10 | 2.78% |
| Totale | 360 | 100.00% |

La differenza tra 228 sessioni `secure` e 218 chiavi generate è dovuta allo scenario `link_critical_high_threshold`, nel quale 10 sessioni sono sicure dal punto di vista CHSH/QBER ma non dispongono di sufficiente materiale sifted per generare la chiave finale.

Questo risultato giustifica la distinzione tra:

```text
security_status
key_status
```

Il primo descrive la sicurezza stimata della sessione; il secondo descrive l'esito operativo del processo di generazione della chiave.

Grafici globali associati:

```text
results/final/plots/global_security_status_distribution.png
results/final/plots/global_key_status_distribution.png
results/final/plots/global_generated_key_rate_by_scenario_group.png
```

Didascalia suggerita: **Figura 5.x - Distribuzioni globali della campagna sperimentale.** I grafici riassumono la classificazione delle sessioni, lo stato finale delle chiavi e il generated key rate per gruppo di scenario.

## 10. Confronto sampler classico vs Qiskit

Il confronto finale tra sampler classico e Qiskit è stato eseguito con:

```bash
python scripts/compare_final_samplers.py \
  --gateway-url http://localhost:18000 \
  --sifting-bell-test-url http://localhost:8009 \
  --shots 10000 \
  --shots-per-basis 2500 \
  --repeats 10
```

Il sampler classico è quello usato nel flusso end-to-end del sistema. Il sampler Qiskit, invece, è confinato al servizio `sifting-bell-test` ed è esposto tramite:

```text
POST /qiskit-chsh-test
```

Il confronto usa soprattutto `abs_chsh`, perché il segno di CHSH può cambiare in base alle convenzioni di preparazione dello stato, rotazione delle basi e mapping dei bit. Il valore fisicamente rilevante per la violazione Bell è il modulo.

| Sampler | Runs | Failed runs | chsh mean | chsh stddev | abs CHSH mean | abs CHSH stddev | QBER mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `classical_singlet_sampler` | 10 | 0 | -2.8260 | 0.0363 | 2.8260 | 0.0363 | 0.0000 |
| `qiskit` | 10 | 0 | 2.8346 | 0.0253 | 2.8346 | 0.0253 | N/A |

I risultati sono coerenti: entrambi i sampler producono un valore medio di `abs_chsh` vicino a 2.8. Il segno opposto del valore `chsh` non indica una discrepanza fisica, ma una differenza di convenzione tra il sampler classico e il circuito Qiskit. La coerenza del modulo conferma che il sampler classico usato nella pipeline end-to-end è allineato con la validazione circuitale tramite Qiskit/AerSimulator della componente Bell/CHSH.

## 11. Discussione complessiva

La campagna sperimentale conferma il comportamento previsto della baseline E91 a microservizi.

Nel caso ideale, il sistema produce una violazione CHSH stabile e QBER nullo. Questo dimostra che la pipeline composta da generazione, trasmissione, misura, sifting, Bell test e key-processing funziona in modo coerente.

Gli esperimenti di link loss mostrano che l'attenuazione agisce principalmente sulla quantità di materiale utile, non sulla sicurezza stimata dal Bell test. L'aumento della distanza riduce la transmittance, aumenta il numero di coppie perse e diminuisce il numero di bit sifted. Tuttavia, finché il materiale residuo è sufficiente e CHSH/QBER restano validi, la chiave può essere generata. Quando la soglia minima di materiale sifted viene aumentata, compare correttamente lo stato `insufficient_key_material`.

Gli sweep di rumore ed Eve mostrano una degradazione progressiva delle metriche di sicurezza. In generale:

- `abs_chsh` diminuisce al crescere della perturbazione;
- `qber` aumenta;
- il sistema passa da `secure` a `degraded` e poi, nei casi più severi, a `insecure`;
- la generazione della chiave viene disabilitata quando la sessione non è secure.

Gli scenari combinati sono i più significativi per la valutazione della robustezza. Anche perturbazioni moderate possono diventare critiche quando rumore ed Eve sono presenti insieme. L'aggiunta della link loss riduce ulteriormente il materiale disponibile, rendendo più evidente la differenza tra sicurezza del protocollo e disponibilità operativa della chiave.

Il Mini KMS consente di osservare questi effetti in forma aggregata. La distribuzione globale mostra che una parte delle sessioni produce chiavi, una parte viene scartata per degradazione o insicurezza, e una parte risulta sicura ma insufficiente dal punto di vista del materiale di chiave.

## 12. Limiti dei risultati

I risultati devono essere interpretati come validazione di una baseline architetturale, non come stima fisica definitiva di un sistema QKD reale.

Il rumore è modellato in modo simbolico. I modelli `bit_flip` e `depolarizing` permettono di osservare l'effetto su CHSH e QBER, ma non descrivono in modo completo canali quantistici reali, detector, dark counts, errori temporali o rumore ambientale.

Il modello di Eve è semplificato. Gli attacchi `randomize` e `intercept_resend` rompono le correlazioni in modo controllato, ma non rappresentano l'intero spazio degli attacchi possibili contro un protocollo QKD.

La link loss riduce il numero di coppie utili tramite una probabilità derivata dalla transmittance. Non sono modellati effetti di rivelazione, sincronizzazione, efficienza dei detector, dead time o conteggi di fondo.

Il key-processing usa SHA-256 come dimostrazione di privacy amplification, ma non implementa una pipeline QKD completa di error correction, leakage accounting e privacy amplification composabile.

Il confronto con Qiskit è confinato alla componente Bell/CHSH. Qiskit non governa il flusso end-to-end, che resta basato sul sampler classico e sulla decomposizione a microservizi.

Infine, tutti gli esperimenti sono simulazioni software. Non sono stati utilizzati hardware quantistico reale o misure fisiche su fibra ottica.

## 13. Conclusione

La campagna finale dimostra che il progetto `e91-qkd-microservices` è in grado di simulare in modo coerente il flusso principale del protocollo E91 in una architettura distribuita. La baseline ideale produce una violazione CHSH vicina al valore atteso, QBER nullo e generazione della chiave.

L'introduzione di link loss, rumore ed Eve consente di osservare in modo controllato la degradazione del sistema. La link loss riduce il materiale utile senza aumentare direttamente il QBER, mentre rumore ed Eve degradano le correlazioni e aumentano il tasso di errore. La soglia `min_sifted_key_length` rende esplicita la differenza tra una sessione sicura e una sessione effettivamente utilizzabile per generare una chiave.

Il Mini KMS e la dashboard permettono di visualizzare l'effetto di queste condizioni sulle chiavi generate o scartate. Gli script finali e i grafici PNG rendono la campagna riproducibile e adatta a supportare la discussione sperimentale della tesi.

Il confronto tra sampler classico e Qiskit conferma infine che la componente Bell/CHSH della pipeline è coerente con una validazione circuitale tramite Qiskit/AerSimulator, mantenendo però Qiskit nel ruolo previsto: uno strumento di verifica locale, non il centro dell'intera architettura.
