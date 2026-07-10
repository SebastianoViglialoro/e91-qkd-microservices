# Mapping del repository `VishuVish/E91-QKD-Using-Qiskit`

Repository analizzato: <https://github.com/VishuVish/E91-QKD-Using-Qiskit>

Data analisi: 2026-07-02

Obiettivo del report: capire quali parti del repository possono essere riutilizzate o adattate nella baseline `e91-qkd-microservices`, mantenendo Qiskit confinato a un uso mirato nel servizio `sifting-bell-test`.

Nota importante: il repository esterno non deve essere importato come centro della simulazione. La nostra architettura resta a microservizi REST; Qiskit, quando verra' introdotto, dovra' essere un modulo interno e sostituibile del solo servizio `sifting-bell-test`, per verifica Bell/CHSH e campionamento quantistico delle correlazioni.

## 1. Struttura del repository analizzato

Il repository pubblico contiene una struttura molto piccola:

| File | Descrizione |
| --- | --- |
| `E91_QKD_Protocol.py` | Script Python monolitico che implementa una simulazione E91 con Qiskit/AerSimulator. Crea circuiti Bell, sceglie basi, misura, calcola correlazioni CHSH, produce un grafico e stima QBER. |
| `README.md` | Descrive lo scopo del progetto: dimostrazione E91 in Qiskit, generazione di coppie entangled, scelta di tre basi, CHSH, raw key e QBER. Riporta anche limitazioni: ogni Bell pair e' simulata in un circuito separato e il runtime cresce con il numero di coppie. |
| `bits_for_E91.txt` | File di bit casuali in una singola riga, circa 1.19 MB, usato dallo script come sorgente di randomness per la scelta delle basi. Secondo il README, deriva da un progetto esterno di generazione casuale. |

Osservazione: non risulta un file `LICENSE` nel file tree principale. Per questo motivo, il riuso diretto di codice dovrebbe essere evitato finche' la licenza non e' chiarita; il repository e' piu' adatto come riferimento algoritmico.

## 2. Funzioni, classi e blocchi principali

| File | Nome funzione/classe/blocco | Cosa fa | Usa Qiskit? | Input principali | Output principali | Serve alla nostra tesi? | Microservizio di destinazione | Note di adattamento |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `E91_QKD_Protocol.py` | Import Qiskit/AerSimulator | Importa `QuantumCircuit`, `transpile` e `AerSimulator`. | Si | Nessuno | Oggetti Qiskit disponibili nello script | Si | `sifting-bell-test` | Da trasformare in dipendenza locale opzionale del solo servizio `sifting-bell-test`, non globale al progetto. |
| `E91_QKD_Protocol.py` | Lettura `bits_for_E91.txt` | Carica una stringa di bit da file e la usa come randomness. | No | File testuale con bit | Stringa `bits` | Parziale | `shared` oppure Alice/Bob, solo in futuro | Utile come idea per randomness riproducibile; non va introdotto ora perche' la baseline usa scelta casuale interna. |
| `E91_QKD_Protocol.py` | `run_E91(N, bits)` | Funzione principale: crea N circuiti, sceglie basi, simula misure, calcola correlazioni e ritorna S-value e risultati Qiskit. | Si | Numero di coppie `N`, bitstream `bits` | `S`, `results` | Si | `sifting-bell-test` | Da spezzare. La parte utile e' il nucleo di simulazione/campionamento, non la funzione monolitica. |
| `E91_QKD_Protocol.py` | Creazione Bell pair | Per ogni round crea un circuito a 2 qubit, applica `H` e `CX`. | Si | Indice round | Circuito Qiskit con entanglement | Si | `sifting-bell-test` | Nella nostra architettura `entangled-source` resta simbolico; la verifica Qiskit dovrebbe stare nel post-processing, non nella source. |
| `E91_QKD_Protocol.py` | Scelta basi Alice/Bob | Usa tre angoli per Alice e tre per Bob, selezionati tramite blocchi di 4 bit. | Parziale | `bits`, indice round | Indici e angoli di misura | Parziale | `shared/bases.py` come riferimento concettuale | I valori non coincidono con la nostra baseline `CHSH_PLUS_KEY_BASIS`. Non riusare direttamente gli angoli. |
| `E91_QKD_Protocol.py` | Rotazioni `ry(-2 * angle)` | Applica la rotazione di base prima della misura. | Si | Angolo Alice, angolo Bob | Circuito ruotato nelle basi scelte | Si | `sifting-bell-test` | Parte importante per un futuro `qiskit_sampler.py`. Va resa funzione pura e parametrica sugli angoli di `shared/bases.py`. |
| `E91_QKD_Protocol.py` | Misura dei qubit | Misura entrambi i qubit classici nel circuito. | Si | Circuito Qiskit | Counts del backend | Si | `sifting-bell-test` | Da adattare per restituire outcome `{-1,+1}` compatibili con il nostro post-processing. |
| `E91_QKD_Protocol.py` | `AerSimulator`, `transpile`, `run` | Esegue tutti i circuiti con `AerSimulator`, usando `shots=10`. | Si | Lista circuiti | Oggetto `results` Qiskit | Si | `sifting-bell-test` | Utile, ma va incapsulato. Valutare batching e numero shot configurabile. |
| `E91_QKD_Protocol.py` | `bit_to_pm1(bit)` | Converte bit classici in valori `+1/-1`. | No | Bit `'0'` o `'1'` | `+1` o `-1` | Si | `sifting-bell-test` | Riutilizzabile come idea; la nostra baseline ha gia' conversioni equivalenti. |
| `E91_QKD_Protocol.py` | Calcolo correlazioni | Per ogni circuito calcola la media del prodotto degli outcome Alice/Bob. | Parziale | Counts Qiskit | Lista di correlazioni | Si | `sifting-bell-test` | Molto rilevante per sostituire il sampler classico con counts Qiskit. |
| `E91_QKD_Protocol.py` | Estrazione raw key | Usa i round con basi uguali e prende l'esito piu' frequente. | Parziale | Counts, basi Alice/Bob | `raw_key`, `key_bits` | Parziale | `key-processing` / `sifting-bell-test` | Non riusare direttamente: nella nostra baseline la chiave usa solo `K/K` e Bob va invertito per il singoletto. |
| `E91_QKD_Protocol.py` | Funzione logica `E(ax, by)` | Filtra correlazioni per coppia di basi e ne calcola la media. | No | Indici basi | Valore medio E | Si | `sifting-bell-test` | Concetto gia' presente nella nostra implementazione; puo' guidare la versione Qiskit. |
| `E91_QKD_Protocol.py` | Calcolo CHSH `S` | Combina quattro correlazioni per ottenere lo S-value. | No | `E00`, `E01`, `E10`, `E11` | Valore `S` | Si | `sifting-bell-test` | Alta priorita'. Adattare segni e coppie al nostro `CHSH_TERMS` in `shared/bases.py`. |
| `E91_QKD_Protocol.py` | Sweep grafico su N | Calcola S per diversi numeri di bit e disegna un grafico con bound classico e quantistico. | Parziale | Lista `num_qubits` | Grafico matplotlib | Parziale | `scripts/plot_experiment_results.py` | Non serve importare: abbiamo gia' script esperimenti e plotting. Utile solo come confronto visuale. |
| `E91_QKD_Protocol.py` | Stima QBER | Seleziona basi coincidenti, conta mismatch e calcola QBER. | Parziale | Counts e basi | `qber` | Si | `sifting-bell-test` / `key-processing` | Da usare solo come riferimento. La nostra QBER e' su `key_subset K/K` con inversione Bob. |
| `README.md` | Descrizione protocollo | Spiega che il progetto dimostra E91 con Bell pairs, tre basi, CHSH, raw key e QBER. | No | Testo | Documentazione | Si | Documentazione tesi | Buon riferimento per motivare la separazione tra verifica Bell e key extraction. |
| `README.md` | Limitazioni simulator | Evidenzia uso di AerSimulator, un circuito per Bell pair e crescita del runtime. | No | Testo | Note di limitazione | Si | `sifting-bell-test` / documentazione | Importante per progettare batching, test piccoli e uso mirato di Qiskit. |
| `bits_for_E91.txt` | Bitstream casuale | Sorgente esterna di bit per scegliere basi. | No | File statico | Bitstream | Parziale | Nessuno ora; possibile `shared` in futuro | Non importare ora. Potrebbe servire per esperimenti riproducibili o confronto con randomness esterna. |

## 3. Mappatura verso i microservizi

| Componente GitHub | Microservizio destinazione | Tipo di riuso | Motivo |
| --- | --- | --- | --- |
| Creazione circuito Bell pair con `QuantumCircuit`, `H`, `CX` | `sifting-bell-test` | Adattamento | Serve per verificare o campionare correlazioni quantistiche, ma non deve sostituire `entangled-source`. |
| `AerSimulator` + `transpile` + `run` | `sifting-bell-test` | Adattamento | E' il nucleo Qiskit utile, da incapsulare in un futuro `qiskit_sampler.py`. |
| Rotazioni di misura `ry(-2 * angle)` | `sifting-bell-test` | Adattamento | Tecnica utile per misurare in basi parametrizzate. Gli angoli vanno presi da `shared/bases.py`, non dallo script esterno. |
| Calcolo correlazioni dai counts | `sifting-bell-test` | Adattamento | Puo' sostituire il sampler classico quando introdurremo Qiskit. |
| Formula CHSH | `sifting-bell-test` | Solo riferimento | La nostra formula e i nostri segni sono gia' centralizzati tramite `CHSH_TERMS`. Verificare convenzioni di stato e basi. |
| Scelta di tre basi per parte | `shared/bases.py` | Solo riferimento | Il concetto e' allineato, ma la nostra baseline usa `A0/A1/K` e `B0/B1/K`, con ruoli espliciti `bell` e `key`. |
| Raw key su basi uguali | `key-processing` | Solo riferimento | Non compatibile direttamente: noi usiamo solo `K/K` e correggiamo Bob per anti-correlazione del singoletto. |
| QBER su basi coincidenti | `sifting-bell-test` | Solo riferimento | La logica generale e' utile, ma il nostro QBER va calcolato solo sul `key_subset`. |
| Grafico CHSH vs N | `scripts/plot_experiment_results.py` | Non usato | Abbiamo gia' esperimenti automatici, CSV/JSON e grafici con soglie. |
| `bits_for_E91.txt` | Nessun microservizio ora | Solo riferimento | Interessante per randomness riproducibile, ma non necessario alla baseline attuale. |
| README del repository | Documentazione tesi | Solo riferimento | Utile per citare obiettivi e limiti di un approccio Qiskit monolitico. |

## 4. Parti da NON riutilizzare

- Lo script completo `E91_QKD_Protocol.py` non va importato direttamente: e' monolitico, mescola simulazione, post-processing, plotting e QBER nello stesso file.
- La struttura non e' coerente con microservizi: non separa source, channel, Alice, Bob, classical channel, Bell test, key processing e storage.
- La scelta delle basi non va copiata direttamente: il repository usa un modello a tre angoli diverso dal nostro `CHSH_PLUS_KEY_BASIS`, mentre noi separiamo esplicitamente basi Bell e base K.
- La raw key su basi uguali non va copiata: nella nostra baseline la chiave e' generata solo dai round `K/K`, con inversione del bit di Bob per lo stato di singoletto.
- Il plotting integrato nello script non serve: nel nostro progetto gli esperimenti e i grafici sono gia' separati in `scripts/run_experiments.py` e `scripts/plot_experiment_results.py`.
- Il file `bits_for_E91.txt` non va importato ora: introdurrebbe un input statico grande e non necessario; puo' restare un riferimento per future prove di randomness riproducibile.
- Non conviene spostare Qiskit in `entangled-source`, `quantum-channel`, `alice-service` o `bob-service`: violerebbe il vincolo che Qiskit non deve diventare il centro della simulazione.
- Il codice esterno non va riusato direttamente senza chiarire la licenza, dato che nel repository pubblico non appare un file `LICENSE`.

## 5. Parti piu' importanti da recuperare

Priorita' 1: calcolo CHSH

- Recuperare come riferimento la pipeline: counts -> outcome `+1/-1` -> prodotti Alice/Bob -> medie E -> S-value.
- Adattare pero' i segni e le coppie di basi al nostro `CHSH_TERMS`.
- Destinazione: `sifting-bell-test`.

Priorita' 2: generazione/campionamento Qiskit

- Recuperare il pattern `QuantumCircuit(2, 2)`, preparazione Bell, rotazioni di base e misura.
- Creare in futuro un modulo isolato, per esempio `sifting-bell-test/app/qiskit_sampler.py`.
- Il modulo dovrebbe ricevere round gia' riconciliati con `alice_basis_angle`, `bob_basis_angle`, `noise_applied`, `eve_applied`.
- Output atteso: outcome `alice_outcome`, `bob_outcome`, eventualmente counts e metadati backend.

Priorita' 3: scelta basi

- Recuperare solo l'idea di tre scelte per parte.
- Non recuperare direttamente gli angoli: la nostra baseline usa:
  - Alice: `A0 = 0 deg`, `A1 = 90 deg`, `K = 0 deg`
  - Bob: `B0 = 45 deg`, `B1 = -45 deg`, `K = 0 deg`
- Destinazione: gia' coperta da `shared/bases.py`.

Priorita' 4: raw key/QBER

- Recuperare come riferimento il concetto di stimare QBER confrontando bit su un sottoinsieme valido.
- Non recuperare la regola "basi uguali" in modo generico.
- La nostra regola resta: QBER solo su `key_subset K/K`, con inversione del bit di Bob.

Priorita' 5: randomness da `bits_for_E91.txt`

- Utile solo per esperimenti riproducibili o per una sezione tesi sulla generazione di randomness.
- Non necessario alla baseline e non va introdotto ora.
- Se in futuro serve, meglio usare un piccolo adapter locale o fixture di test, non dipendere da un file esterno grande.

## 6. Raccomandazione finale

Il repository `E91-QKD-Using-Qiskit` va trattato prima come riferimento algoritmico, non come dipendenza o codice da importare direttamente.

Percorso consigliato:

1. Mantenere invariata l'architettura attuale: `api-gateway`, `orchestrator`, `entangled-source`, `quantum-channel`, `noise-model`, `alice-service`, `bob-service`, `eve-service`, `classical-channel`, `sifting-bell-test`, `key-processing`, `result-store`, `monitoring`, `shared/bases.py`.
2. Continuare a usare `shared/bases.py` come fonte unica delle basi e dei ruoli.
3. Quando sara' il momento di introdurre Qiskit, creare un modulo interno al servizio `sifting-bell-test`, per esempio:

```text
sifting-bell-test/app/qiskit_sampler.py
```

4. Il modulo dovrebbe avere un'interfaccia piccola, per esempio:

```text
sample_quantum_correlations(rounds, shots_per_round, backend_config) -> correlated_rounds
```

5. `sifting-bell-test/app/main.py` dovrebbe poter scegliere tra:

```text
classical_singlet_sampler
qiskit_sampler
```

senza cambiare gli endpoint REST.

6. Non modificare `api-gateway`, `orchestrator`, `classical-channel` o `key-processing` per introdurre Qiskit. Questi servizi devono continuare a scambiarsi lo stesso JSON.

7. Noise ed Eve devono restare separati: `noise-model` ed `eve-service` marcano i pair disturbati/attaccati; il futuro sampler Qiskit nel `sifting-bell-test` potra' usare quei flag per alterare o confrontare i risultati, senza spostare responsabilita' tra servizi.

Conclusione: la parte piu' utile del repository esterno e' il nucleo Qiskit per costruire circuiti Bell, ruotare le basi, simulare counts e derivare correlazioni. Tutto il resto va considerato materiale di confronto o documentazione, non codice da importare direttamente.
