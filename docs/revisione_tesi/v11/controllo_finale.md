# Controllo finale — Sebastiano_Battista-11.pdf

Revisione del 6 ottobre 2026 rispetto al repository locale attuale e ai risultati già salvati. Le pagine indicate sono quelle stampate nella tesi; nel visualizzatore PDF occorre aggiungere 5. Nessuna modifica al codice applicativo o ai risultati della campagna durante questa revisione.

## Valutazione complessiva

La struttura concettuale è ormai coerente con il refactoring: scelta separata delle basi, campionamento congiunto centralizzato, registrazione degli outcome definitivi, utilizzo degli stessi outcome nelle metriche e derivazione dimostrativa della chiave dai soli bit concordi. Le figure di architettura e campagna sono leggibili e pertinenti. Restano alcune descrizioni precedenti al refactoring, esempi API inesatti e due formule da impaginare meglio.

Il controllo comprende il testo estratto delle 141 pagine, il confronto con il codice, verifiche numeriche sui file salvati e un controllo visivo mirato delle pagine con figure, formule e tabelle rilevanti. Non costituisce una verifica esterna di ogni riferimento bibliografico.

## Verifiche eseguite

- 36 scenari, 10 ripetizioni ciascuno: 360 run.
- `security_status`: 228 secure, 91 degraded, 41 insecure.
- `key_status`: 218 generated, 10 insufficient_key_material, 91 discarded_degraded, 41 discarded.
- Nessun run fallito nei risultati salvati.
- Ricalcolo dei riepiloghi della campagna: nessuna differenza rilevata rispetto ai file di sintesi.
- Confronto dei valori numerici estratti da 34 righe delle tabelle del Capitolo 5 con i risultati: nessuna discrepanza nei valori controllati.
- Riepiloghi del confronto Qiskit/sampler, su 20 esecuzioni salvate: nessuna differenza rilevata.
- Suite locale: 14 test superati in 5,269 secondi, con `python -m unittest discover -s tests -v`.
- La suite comprende equivalenza deterministica del sampler precedente e attuale, distribuzione statistica, outcome registrati e consumati dalla pipeline, key processing e controlli sulle decisioni salvate. I test di integrazione usano i servizi in memoria: non sono una nuova campagna Docker da 360 run.

Evidenze: `evidenze.json`, `verifica_dati.py` e `test.log` in questa directory.

## Correzioni da fare prima della consegna

### 1. Assegnare il sifting al servizio corretto

**Dove:** §3.5.2, p. 42; §4.5, pp. 57–59.

A p. 42 si attribuisce a Sifting-Bell-Test la partizione nei sottoinsiemi R_KEY, R_BELL e R_DISCARD. A p. 59 ritorna una descrizione analoga. Nel codice è `classical-channel/app/main.py` a costruire i sottoinsiemi; Sifting-Bell-Test riceve il risultato e calcola le metriche. La descrizione e la figura alle pp. 39–40 sono già corrette: bisogna uniformare gli altri passaggi.

**Testo sostitutivo:**

> Il Classical Channel associa i record di Alice e Bob mediante pair_id e costruisce i sottoinsiemi destinati alla chiave, al test di Bell e allo scarto. Il servizio Sifting-Bell-Test utilizza i sottoinsiemi ricevuti e gli outcome già registrati per calcolare QBER, correlazioni empiriche, CHSH e security_status, senza ricampionare gli outcome.

Nella sequenza sintetica di p. 57 inserire Classical Channel tra Receivers e Sifting-Bell-Test. Rimandare alla figura 3.2 per le due fasi dei receiver e il campionamento congiunto.

### 2. Correggere la descrizione di intercept_resend nella Tabella 6.1

**Dove:** p. 81, Tabella 6.1.

La dicitura «Perturbazione controllata da misura/reinvio» suggerisce una misura di Eve e un successivo reinvio che il codice non implementa. `shared/outcome_sampler.py` randomizza l'outcome di Bob sia per `randomize` sia per `intercept_resend` nei round attaccati. Il limite è spiegato correttamente in altre sezioni della tesi.

**Sostituire con:**

> Decorrelazione statistica dell'outcome di Bob; stessa implementazione di randomize.

La differenza fra le due etichette non va interpretata come confronto sperimentale tra due diversi modelli fisici di attacco.

### 3. Correggere il segno del valore CHSH ideale

**Dove:** §1.3.6, p. 12.

Con E(a,b) = −cos(a−b), gli angoli riportati e la combinazione E00 + E01 + E10 − E11, il valore ideale è S = −2√2. La tesi riporta il valore positivo senza modulo.

**Correzione minima:** scrivere `|S| = 2√2`. È coerente con la grandezza usata nella classificazione e nei risultati.

### 4. Allineare gli esempi API ai contratti effettivi

**Dove:** Appendice F, pp. 126–129; Appendice D, pp. 107–113.

- **F.4, p. 127:** `sifted_key_length` compare nel blocco `sifting_bell_test`, ma il servizio lo restituisce nel blocco `key`. Spostarlo lì e correggere anche la descrizione in prosa del materiale sifted. È una differenza di struttura, non un campo semplicemente omesso per brevità.
- **F.6, p. 129:** `/keys/latest` restituisce una lista di record. Racchiudere l'esempio in parentesi quadre oppure presentarlo esplicitamente come un singolo elemento della lista restituita.
- **F.3 e diversi JSON dell'Appendice D:** `basis_model` non è un parametro configurabile di `SimulationRequest`. Rimuoverlo dai payload di richiesta o identificarlo chiaramente come metadato descrittivo del modello fisso. La presenza nella risposta o nei riepiloghi non lo rende un parametro accettato e utilizzato in ingresso.
- **F.5, p. 128:** l'esempio è già chiamato «logico», quindi la semplificazione è ammissibile. Se si desidera presentarlo come risposta API reale, va invece rispettata la struttura annidata e usato `lost_pair_count` per il conteggio scalare delle perdite.

### 5. Esplicitare la provenienza della campagna rispetto al refactoring

**Dove:** §5.1, pp. 65–67, ed eventualmente F.11, p. 133.

I file della campagna riportano timestamp del 15 luglio 2026. La campagna conservata precede le modifiche finali al campionamento e al materiale usato per il digest. Presentare i dati storici insieme all'architettura finale senza una nota lascia ambiguo quale versione abbia generato i risultati.

**Nota proposta:**

> I risultati presentati si riferiscono alla campagna sperimentale archiviata. Successivamente sono stati introdotti un refactoring della registrazione degli outcome e una correzione della derivazione dimostrativa della chiave. Il primo conserva la legge statistica del campionamento e le regole decisionali; la seconda applica SHA-256 ai soli bit concordi. La versione finale è stata verificata mediante test mirati, senza rieseguire la campagna completa. I risultati archiviati restano pertanto quelli della campagna originaria.

La conservazione della legge statistica non implica una riproduzione identica delle singole sessioni: il refactoring modifica dove e in quale ordine vengono consumati i numeri casuali. I test non autorizzano a dichiarare che una nuova campagna produrrebbe necessariamente gli stessi conteggi. La correzione del digest, a parità di record, conserva invece lunghezze e classificazioni; nei dati storici 138 sessioni generated hanno QBER non nullo e quindi materiale grezzo diverso da quello concorde.

### 6. Sistemare due formule fuori margine

**Dove:** p. 37, definizione a casi di `key_status`; p. 103, insieme K_out.

Il controllo visivo mostra formule che oltrepassano il margine del testo o arrivano quasi al bordo della pagina. Spezzarle su più righe, usando `aligned` o una disposizione equivalente. Evitare di ridurre ulteriormente il carattere: gli identificatori software sono già lunghi.

### 7. Uniformare la spiegazione del segno nel confronto Qiskit

**Dove:** E.8, p. 122.

La sezione precedente spiega correttamente che il sampler usa le correlazioni del singoletto e il circuito prepara Φ+. E.8 ritorna invece a un elenco generico di convenzioni e parla di segno opposto «in alcune esecuzioni». Nel confronto implementato il motivo principale è strutturale e già noto. Il semplice scambio dell'ordine dei due bit non cambia il loro prodotto, quindi non basta a spiegare un cambio di segno della correlazione.

**Testo sostitutivo:**

> Nel confronto implementato, il sampler riproduce le correlazioni del singoletto Ψ−, mentre il circuito Qiskit prepara Φ+. Per gli angoli adottati, i valori CHSH ideali hanno segno opposto e uguale modulo. Il confronto utilizza pertanto |S|; le differenze residue fra le stime sono influenzate dal campionamento finito.

## Miglioramenti brevi che consiglio

### Ruolo dell'Orchestrator

A p. 43 e in C.10, p. 103, integrare la descrizione del coordinamento indicando che l'Orchestrator richiama il sampler centrale dopo aver ricevuto entrambe le basi e invia gli outcome definitivi ai receiver per la registrazione. La descrizione delle pp. 40 e 58 è già più precisa.

### Corrispondenza fra simboli e campi software

Inserire vicino alle definizioni del Capitolo 3:

| Simbolo | Campo software |
|---|---|
| N_key | raw_key_length |
| N_err | error_count |
| N_sifted | sifted_key_length |

Specificare QBER = N_err/N_key e N_sifted = N_key−N_err. La lunghezza della stringa binaria passata a SHA-256 è N_sifted; il risultato ha 256 bit ed è rappresentato da 64 caratteri esadecimali. La derivazione resta un filtraggio centralizzato dimostrativo.

### Angoli effettivamente usati

Aggiungere una tabella del modello implementato, ricavata da `shared/bases.py`: Alice C = 0°, K0 = 45°, K1 = 90°; Bob K0 = 45°, K1 = 90°, C = −45°. L'esempio teorico di p. 9 con 135° va distinto esplicitamente dalla convenzione adottata nel software. Non trattare orientamenti diversi come identici senza specificare anche la convenzione degli outcome.

### Round scartati e round persi

A p. 34 e nell'Appendice C distinguere R_DISCARD, definito sui round validi, dal contenitore software `discarded_subset`, che comprende anche i round persi. Nel flusso normale con record completi:

`discarded_subset_size = |R_DISCARD| + N_lost`.

Nei 360 risultati salvati risulta infatti `key_subset_size + bell_subset_size + discarded_subset_size = shots`.

### Dare concretezza al Capitolo 4

Il capitolo descrive bene le responsabilità, ma le tecnologie effettive restano poco visibili. Un breve paragrafo su FastAPI, Pydantic, HTTPX e Docker Compose, accompagnato da poche righe sui test di regressione, valorizzerebbe la componente di ingegneria del software. Indicare che i test verificano anche l'identità degli outcome registrati e utilizzati, l'equivalenza del sampler e la derivazione dai bit concordi.

### Precisazioni locali

- **P. 27:** l'attenuazione è un parametro di ingresso nel codice (`attenuation_db_per_km`), pur essendo un coefficiente equivalente non calibrato su un apparato reale. Evitare di includerla senza distinzione fra le grandezze non parametrizzate.
- **Pp. 36 e 102:** qualificare la formula di classificazione CHSH come applicabile quando `chsh_available=true`; la convenzione per CHSH non disponibile è già descritta in prosa e va resa chiaramente distinta.
- **Pp. 37, 49, 59 e 128:** dove si parla di superamento della soglia, preferire «raggiunge la soglia minima»: il confronto implementato è ≥, non >.
- **P. 63:** distinguere l'esecuzione della campagna dalla produzione dei grafici mediante lo script separato `scripts/plot_final_experiments.py`.
- **Notazione:** distinguere outcome ±1 e bit 0/1 nei passaggi fra Capitolo 3 e Appendice C. I receiver registrano già outcome ±1; non vengono convertiti in questa rappresentazione solo al momento del test CHSH.
- **Caso senza materiale:** se si vuole completare la definizione operativa del QBER, indicare la convenzione software 0.0 quando non ci sono bit confrontabili, evitando di interpretarla come evidenza di sicurezza.

## Ritocchi editoriali facoltativi

- Le tabelle riepilogative del Capitolo 6 ripetono parte del Capitolo 5; si può alleggerire la conclusione, ma non è necessario ristrutturarla alla vigilia della consegna.
- Le figure di architettura e campagna sono adatte alla tesi. Una precisazione nella caption dell'architettura può chiarire che le frecce rappresentano dipendenze logiche, non tutte le chiamate HTTP effettive.
- Nelle appendici correggere i rimandi «nei capitoli successivi» quando la trattazione richiamata si trova già nei capitoli precedenti.
- A p. 35: «numero di discordanza» → «numero di discordanze».
- Le percentuali arrotondate possono sommare a 100,1%: è un effetto dell'arrotondamento, non una discrepanza dei conteggi.
- Verificare sul frontespizio la qualifica istituzionale del correlatore; il controllo del codice non consente di validarla.

## Giudizio finale

Il contributo è descrivibile in modo solido come infrastruttura statistica centralizzata a microservizi con diagnostica CHSH/QBER e key processing dimostrativo. Le correzioni prioritarie riguardano la precisione del documento e la provenienza sperimentale. Le evidenze numeriche controllate sono coerenti con i risultati salvati, mentre le figure rendono più chiari i passaggi architetturali. Completate queste correzioni puntuali, il testo descriverà molto meglio il progetto effettivamente consegnato.
