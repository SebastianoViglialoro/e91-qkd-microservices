# Figura Architetturale - E91 QKD Microservices

Questo file contiene una proposta di figura architetturale pulita da usare nella tesi. Il diagramma evidenzia il ruolo dell'API Gateway, dell'Orchestrator, dei microservizi di dominio, del Mini KMS e della dashboard.

## Titolo Suggerito

**Figura 4.x - Architettura a microservizi del simulatore E91 QKD.**

## Diagramma Mermaid

```mermaid
flowchart LR
    user[Utente / Browser]
    dashboard[Dashboard HTML/CSS/JS]
    gateway[API Gateway<br/>:18000]
    orchestrator[Orchestrator<br/>campionamento congiunto + rumore/Eve<br/>:8001]

    source[Entangled Source<br/>:8002]
    qchannel[Quantum Channel<br/>:8003]
    noise[Noise Model<br/>:8004]
    eve[Eve Service<br/>:8007]
    alice[Alice Service<br/>:8005]
    bob[Bob Service<br/>:8006]
    classical[Classical Channel<br/>:8008]
    bell[Sifting & Bell Test<br/>CHSH / QBER<br/>:8009]
    qiskit[Qiskit / AerSimulator<br/>validazione CHSH opzionale]
    keyproc[Key Processing<br/>SHA-256 demo<br/>:8010]
    store[Result Store<br/>Mini KMS<br/>:8011]

    user --> dashboard
    user --> gateway
    dashboard -->|REST| gateway
    gateway -->|POST /simulations| orchestrator

    orchestrator --> source
    source --> orchestrator
    orchestrator --> qchannel
    qchannel -. metadati rumore .-> noise
    qchannel -. metadati attacco .-> eve
    noise --> qchannel
    eve --> qchannel
    qchannel --> orchestrator

    orchestrator -->|1. select-bases / 3. measure| alice
    orchestrator -->|1. select-bases / 3. measure| bob
    alice -->|basi locali / record definitivi| orchestrator
    bob -->|basi locali / record definitivi| orchestrator
    orchestrator -->|2. una coppia di outcome per round consegnato| orchestrator

    orchestrator -->|record definitivi| classical
    classical --> orchestrator
    orchestrator -->|subset con gli stessi outcome| bell
    bell -. POST /qiskit-chsh-test .-> qiskit
    bell --> orchestrator
    orchestrator --> keyproc
    keyproc --> orchestrator
    orchestrator --> store

    gateway -->|GET /keys, /keys/summary| store
    store --> gateway
    gateway --> dashboard
```

## Diagramma di sequenza della misura e del sifting

Le chiamate REST trasportano liste di round; gli indici `i` indicano un singolo
round consegnato. Il campionamento è centralizzato nell'Orchestrator.

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant Q as Quantum Channel
    participant A as Alice Receiver
    participant B as Bob Receiver
    participant C as Classical Channel
    participant S as Sifting-Bell-Test
    O->>Q: POST /transmit
    Q-->>O: Qubit consegnati, round persi, flag rumore/Eve
    Note over O,Q: Link loss esclude i round prima della misura utile
    O->>A: POST /select-bases (qubit Alice)
    A->>A: Scelta locale delle basi A_i
    A-->>O: Selezioni Alice, senza outcome
    O->>B: POST /select-bases (qubit Bob)
    B->>B: Scelta locale delle basi B_i
    B-->>O: Selezioni Bob, senza outcome
    O->>O: Associa le basi per pair_id
    O->>O: Campiona una sola coppia (a_i, b_i), E = -cos(A_i - B_i)
    O->>O: Applica eventuale rumore, poi Eve, secondo i flag
    O->>A: POST /measure (record con A_i, a_i definitivi)
    A-->>O: Record Alice validati e registrati
    O->>B: POST /measure (record con B_i, b_i definitivi)
    B-->>O: Record Bob validati e registrati
    O->>C: POST /reconcile (record Alice/Bob e round persi)
    C->>C: Associa per pair_id e classifica le basi
    C-->>O: R_KEY, R_BELL e round scartati
    O->>S: POST /evaluate (subset con gli outcome registrati)
    S->>S: QBER e materiale di chiave da R_KEY, CHSH da R_BELL
    Note over O,S: Stessi outcome dei receiver, nessun ricampionamento nel sifting
    S-->>O: Metriche, key_records e security_status
```

`R_KEY` corrisponde a `key_subset`; `R_BELL` a `bell_subset` (alias
`check_subset`). La separazione dei subset avviene nel Classical Channel;
il Sifting-Bell-Test li utilizza per le metriche. `/measure` registra nei record
della risposta gli outcome già campionati: non introduce persistenza durevole.
La scelta delle basi resta locale ai receiver, ma non implica località fisica o
sicurezza device-independent. Qiskit resta una verifica opzionale separata.

## Descrizione Del Flusso

L'utente può interagire con il sistema tramite la dashboard oppure tramite chiamate dirette all'API Gateway. L'API Gateway rappresenta il punto unico di accesso pubblico e inoltra le richieste di simulazione all'Orchestrator.

L'Orchestrator coordina la pipeline E91. Prima richiede la generazione delle coppie entangled, poi invoca il canale quantistico, che applica il modello di attenuazione dei link e propaga i metadati di rumore ed Eve. Per le coppie consegnate, Alice e Bob scelgono separatamente le basi con `/select-bases`. L'Orchestrator campiona congiuntamente gli outcome una sola volta, applica rumore/Eve e li invia ai receiver tramite `/measure` per registrarli nei record definitivi. Il Classical Channel effettua il sifting, separando key subset, Bell subset e round scartati.

Il servizio Sifting & Bell Test calcola CHSH, `abs_chsh`, QBER e `security_status` usando gli stessi outcome registrati, senza ricampionamento. Qiskit/AerSimulator rimane confinato a un endpoint opzionale di validazione circuitale della componente CHSH. Il servizio Key Processing genera la chiave finale dimostrativa solo quando la sessione è sicura e il materiale sifted raggiunge la soglia minima. Il Result Store salva il risultato completo e un record sintetico nel Mini KMS, usato dalla dashboard per visualizzare storico e statistiche.

## Componenti Da Includere Nella Figura

- Client: utente, dashboard statica e API Gateway.
- Coordinamento e campionamento congiunto: Orchestrator.
- Sorgente e canale: Entangled Source, Quantum Channel, Link Loss, Noise Model, Eve Service.
- Misura e sifting: Alice Service, Bob Service, Classical Channel.
- Valutazione: Sifting & Bell Test, CHSH, QBER, Qiskit/AerSimulator opzionale.
- Chiave e persistenza: Key Processing, Result Store, Mini KMS.
- Flussi dati principali: `POST /simulations`, chiamate REST interne, `GET /keys`, `GET /keys/summary`.

## Didascalia Suggerita

**Figura 4.x - Architettura a microservizi del simulatore E91 QKD.** La figura mostra il flusso end-to-end della simulazione: l'API Gateway riceve la richiesta, l'Orchestrator coordina i servizi di generazione, trasmissione, misura, sifting, Bell test e key-processing, con scelta locale delle basi, campionamento congiunto centralizzato e registrazione degli outcome nei receiver prima del post-processing; il Result Store conserva risultati e key record nel Mini KMS. Qiskit/AerSimulator è usato solo come validazione circuitale opzionale della componente CHSH.
