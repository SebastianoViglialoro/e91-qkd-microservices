# QKD-Simulator UI Mapping

Report di analisi del repository:

https://github.com/florianocaprio/QKD-Simulator

Obiettivo: capire come e' organizzata la dashboard/interfaccia grafica del simulatore QKD del professore e derivare una proposta leggera per `e91-qkd-microservices`, senza importare codice o backend.

## 1. Struttura del repository del professore

### Cartelle principali

| Percorso | Ruolo |
| --- | --- |
| `.agents/memory/` | Note architetturali interne del progetto, soprattutto sulla Network Designer UI e sulle scelte React Flow. |
| `artifacts/qkd-simulator/` | Frontend principale: SPA React/Vite/TypeScript del simulatore QKD. |
| `artifacts/api-server/` | Backend Node/Express che espone API di simulazione, preset e validazione topologia. |
| `artifacts/mockup-sandbox/` | Sandbox Vite per mockup UI. |
| `lib/api-spec/` | Specifica OpenAPI, usata per generare client e tipi. |
| `lib/api-client-react/` | Client React generato per chiamare l'API. |
| `lib/api-zod/` | Schemi Zod generati dalla specifica API. |
| `lib/db/` | Configurazione DB/PostgreSQL/Drizzle. |
| `attached_assets/` | Screenshot e prompt/prototipi allegati. |

### Framework rilevato

| Livello | Tecnologia |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| Routing | `wouter` |
| Stato client | `zustand` |
| API/data fetching | TanStack Query + client generato da OpenAPI |
| UI components | Radix/shadcn-style components |
| Stile | Tailwind CSS, tema dark custom |
| Grafici | Recharts |
| Network designer | `@xyflow/react` / React Flow |
| Backend | Express 5, TypeScript |
| DB | PostgreSQL + Drizzle ORM |

### File principali dell'interfaccia

| File | Descrizione |
| --- | --- |
| `artifacts/qkd-simulator/src/App.tsx` | Definisce le route della SPA: simulator, network, communications, parameters, analysis. |
| `src/components/layout.tsx` | Shell applicativa con sidebar, topbar, status globale, QBER, SKR, pulsanti Run/Reset. |
| `src/pages/simulator.tsx` | Pagina principale del simulatore: scelta protocollo, canvas, grafici, metriche, pannello parametri, Eve e KMS. |
| `src/components/photon-canvas.tsx` | Canvas animato con Alice, Bob, EPR/Charlie, canale quantistico, canale classico, Eve, KMS e customer. |
| `src/pages/network.tsx` | Network Designer basato su React Flow: nodi, domini, customer, Alice/Bob/EPR/KMS/KMIP/Eve, link e risultati. |
| `src/pages/communications.tsx` | Pagina di analisi delle comunicazioni customer-to-customer, path, demand/supply, KMS buffer. |
| `src/pages/parameters.tsx` | Pannelli per parametri fisici, detector, sorgenti, error correction e privacy amplification. |
| `src/pages/analysis.tsx` | Grafici sweep SKR/QBER per protocollo e distanza, preset ed export CSV. |
| `src/store/simulation-store.ts` | Parametri simulazione, risultato, time series e input builder. |
| `src/store/network-store.ts` | Snapshot condiviso della network simulation. |
| `src/index.css` | Tema dark e palette QKD: cyan, green, amber, red, purple. |

### Componenti UI importanti

- Sidebar di navigazione con sezioni: Protocol Simulator, Network Designer, Customer Communications, Physical Parameters, Analysis & Reports.
- Topbar con protocollo corrente, stato operativo, QBER, SKR, Run e Reset.
- Canvas visuale del protocollo con Alice/Bob/EPR/Eve/KMS.
- Pannello parametri laterale con slider, switch, radio/segmented buttons.
- Cards metriche compatte.
- Grafici time-series.
- Network graph interattivo con nodi e link colorati.
- Tabelle risultati e badge di sicurezza.
- Mini KMS visualizzato come buffer/tank di chiavi.

## 2. Descrizione della dashboard del professore

### Layout generale

La dashboard e' una SPA full-screen con:

- sidebar sinistra fissa;
- topbar compatta con stato, QBER, SKR e comandi;
- area centrale per canvas/grafici/network graph;
- pannello laterale destro per parametri;
- sezione risultati in basso nella pagina Network Designer.

Il layout e' operativo, non da landing page: l'utente entra direttamente nello strumento.

### Pannelli principali

| Pannello | Funzione |
| --- | --- |
| Protocol Simulator | Simulazione singola multi-protocollo. |
| Network Designer | Disegno di topologie QKD con nodi, domini, customer, KMS e link. |
| Customer Communications | Analisi dei path applicativi e della disponibilita' delle chiavi. |
| Physical Parameters | Parametri fisici, sorgenti, detector, error correction, privacy amplification. |
| Analysis & Reports | Sweep, grafici, confronto protocolli ed export CSV. |

### Flusso utente

1. Sceglie protocollo o configura topologia.
2. Modifica parametri con slider/switch.
3. Avvia simulazione.
4. Legge stato sicurezza, QBER, SKR e risultati.
5. Consulta grafici e/o path di rete.
6. In caso di network mode, osserva disponibilita' KMS e comunicazioni cliente.

### Colori e stile

Palette rilevata:

| Elemento | Colore prevalente |
| --- | --- |
| Background | `#0D1117` |
| Cards/sidebar | `#161B22` |
| Border | `#30363D` |
| Testo primario | `#F0F6FC` |
| Testo secondario | `#8B949E` |
| Alice / primary | cyan `#00E5FF` |
| Bob / secure | green `#39FF14` |
| Warning / degraded | amber `#FFB300` |
| Insecure / Eve | red `#FF3D3D` |
| EPR / CHSH / entanglement | purple `#BD00FF` |

Lo stile e' tecnico, scuro, con font sans per UI e monospace per metriche. Usa badge colorati, bordi luminosi, linee tratteggiate e cards compatte.

### Elementi visuali

| Elemento | Come appare nel repo del professore |
| --- | --- |
| Alice | Box/nodo cyan. |
| Bob | Box/nodo verde. |
| Eve/Eva | Nodo rosso, badge rosso, stato intercettazione. |
| EPR source | Diamante/nodo viola per E91. |
| Canale quantistico | Linee colorate, spesso animate o tratteggiate. |
| Canale classico | Linea tratteggiata blu/grigia con frecce bidirezionali. |
| KMS | Tank/buffer chiavi con livello e TTL. |
| Customer | Box arancione collegato al KMS. |
| Risultati | Cards metriche, badge status, tabella link, grafici Recharts. |

## 3. Elementi da replicare nella nostra dashboard

| Elemento UI del repo del professore | Funzione | Utile per noi? | Adattamento a E91 microservices |
| --- | --- | --- | --- |
| Shell scura con header operativo | Dare identita' tecnica e accesso rapido allo stato. | Si' | Header con `E91 QKD Microservices`, gateway status, basis model e pulsante refresh. |
| Topbar con status/QBER/SKR | Mostrare salute della simulazione a colpo d'occhio. | Si' | Sostituire SKR con `key_status`, `final_key_length`, `generated_key_rate`. |
| Protocol tabs multi-protocollo | Cambiare protocollo. | No | Il nostro progetto e' solo E91; mostrare invece badge fisso `TWO_KEY_BASES_ONE_CHECK_BASIS`. |
| Canvas Alice/Bob/EPR/Eve/KMS | Visualizzare flusso quantistico/classico. | Si' | Versione statica HTML/CSS: Entangled Source -> Quantum Channel -> Alice/Bob, Noise/Eve sul canale, Classical Channel -> Bell Test -> Key Processing -> Key Repository. |
| Photon animation | Rendere visivo il canale quantistico. | Parziale | Non necessaria ora; eventualmente una animazione CSS leggera o linee evidenziate dopo una run. |
| Right-side parameter panel | Configurare parametri. | Si' | Pannello `Simulation Settings`: shots, enable_noise, noise_level, enable_eve, eve_attack_probability. |
| Slider numerici | Modifica ergonomica dei parametri. | Parziale | Usiamo number input per precisione; slider opzionali per noise/eve. |
| Eve red badge | Segnalare attacco attivo. | Si' | Evidenziare Eve e canale in rosso quando `enable_eve=true` o `eve_applied_count>0`. |
| KMS tank/buffer | Mostrare disponibilita' chiavi. | Parziale | Usiamo tabella mini KMS e summary cards; niente TTL/buffer dinamico per ora. |
| Metrics cards | Leggere risultati principali. | Si' | Cards per `abs_chsh`, `qber`, `security_status`, `key_status`, `key_subset_size`, `final_key_length`. |
| Time-series charts | Mostrare andamento delle run. | Si' | Chart.js con ultime sessioni da `/keys/latest`: abs_CHSH, QBER e conteggio status chiavi. |
| Network Designer React Flow | Disegnare topologie complesse. | No per ora | Troppo complesso e fuori scope; la nostra architettura e' microservizi fissi, non topologia variabile. |
| Results table | Elencare risultati e link. | Si' | Tabella Mini KMS con ultime 10 sessioni. |
| Communications page | Customer demand/supply. | Parziale | Futuro: spiegare uso delle chiavi generate; ora basta repository chiavi. |
| Analysis sweep page | Campagne sperimentali e grafici. | Parziale | Gli script Python gia' producono CSV/plot; la dashboard puo' solo mostrare trend recenti live. |
| Export CSV | Scaricare risultati. | Parziale | Non prioritario; i CSV sono gia' generati da `scripts/run_experiments.py`. |

## 4. Elementi da NON replicare

| Elemento | Motivo |
| --- | --- |
| Backend Express/API del professore | La nostra architettura e' gia' FastAPI a microservizi; la GUI deve chiamare solo API Gateway. |
| Client OpenAPI generato/TanStack Query | Utile in React, ma eccessivo per dashboard HTML/JS vanilla. |
| React/Vite completo | Non necessario per dashboard dimostrativa; aumenterebbe dipendenze e complessita'. |
| React Flow Network Designer | Troppo legato a topologie multi-nodo, KMS/KMIP/federazione e customer path; noi abbiamo un flusso E91 fisso. |
| Multi-protocollo BB84/E91/MDI/TF/PM/SNS | La nostra tesi e' focalizzata su E91. |
| Parametri fisici avanzati: detector, wavelength, dark count, satellite, free-space | Non sono ancora modellati nei microservizi attuali. Rischiano di creare aspettative false. |
| SKR industriale e customer demand/supply | Il nostro key-processing produce una chiave dimostrativa SHA-256, non un rate fisico industriale. |
| KMS TTL/retention/FIFO buffer | Il nostro mini KMS e' repository dimostrativo in-memory; niente KMS industriale. |
| Preset, salvataggio topologie, localStorage network draft | Non servono per l'attuale dashboard E91. |
| Database/Drizzle/Postgres | Il nostro result-store e' in-memory per baseline dimostrativa. |

## 5. Proposta layout per la nostra dashboard

```text
Header
  - Titolo: E91 QKD Microservices Dashboard
  - Badge: TWO_KEY_BASES_ONE_CHECK_BASIS
  - API Gateway: http://localhost:18000
  - Status colore: idle / running / secure / degraded / insecure

Main Grid

  Left Column
    Simulation Control Panel
      - shots
      - enable_noise
      - noise_level
      - enable_eve
      - eve_attack_probability
      - Run Simulation

    Protocol Visualization
      - Entangled Source
      - Quantum Channel
      - Alice / Bob
      - Noise Model collegato al Quantum Channel
      - Eve collegata al Quantum Channel
      - Classical Channel
      - Sifting & Bell Test
      - Key Processing
      - Key Repository
      - colori dinamici: secure verde, degraded ambra, insecure rosso

  Center / Right Column
    Latest Simulation Result
      - session_id
      - basis_model
      - chsh / abs_chsh
      - qber
      - security_status
      - key_status
      - subset sizes
      - final_key abbreviata
      - hash_function / privacy_amplification

    Key Summary
      - total_sessions
      - generated_keys
      - discarded_degraded
      - discarded_insecure
      - insufficient_key_material
      - average_qber
      - average_abs_chsh
      - generated_key_rate

Bottom Section
  Mini KMS / Key Repository
    - tabella ultime 10 sessioni

  Charts
    - abs_CHSH ultime sessioni
    - QBER ultime sessioni
    - generated/discarded_degraded/discarded count

  Logs / Session History
    - messaggi UI: request inviata, session_id ricevuta, KMS aggiornato
```

## 6. Mapping endpoint nostro -> UI

| Endpoint nostro | Dati restituiti/usati | Componente UI |
| --- | --- | --- |
| `POST /simulations` | Risultato completo sessione: `session_id`, `sifting_bell_test`, `key`, request e metadati. | `Simulation Control Panel`, `Latest Simulation Result`, aggiornamento colori `Protocol Visualization`, refresh Mini KMS. |
| `GET /keys` | Lista completa key record. | Non necessario nella prima dashboard; utile per export o storico completo. |
| `GET /keys/{session_id}` | Record sintetico singola sessione. | Dettaglio sessione cliccando una riga KMS. |
| `GET /keys/summary` | Aggregati: total_sessions, generated_keys, discarded_degraded, discarded_insecure, insufficient_key_material, medie QBER/CHSH, generated_key_rate. | `Key Summary`, chart conteggi chiavi. |
| `GET /keys/latest?limit=N` | Ultimi N key record con `abs_chsh`, `qber`, status, rumore, Eve, timestamp. | `Mini KMS / Key Repository`, grafici recenti CHSH/QBER, session history. |

## 7. Raccomandazione tecnica finale

Raccomandazione: **A. dashboard HTML/CSS/JavaScript vanilla ispirata allo stile del professore**.

Motivi:

- La dashboard e' dimostrativa e deve valorizzare l'architettura a microservizi, non diventare un secondo progetto frontend complesso.
- I nostri endpoint sono pochi e gia' stabili; `fetch()` verso API Gateway e' sufficiente.
- HTML/CSS/JS vanilla e' facile da spiegare al professore: la GUI non introduce logica di simulazione, visualizza soltanto dati prodotti dai microservizi.
- Chart.js puo' bastare per tre grafici semplici: CHSH, QBER e stato delle chiavi.
- Manteniamo il backend invariato e la GUI comunica solo con `http://localhost:18000`.

Opzione B, piccolo frontend TypeScript, puo' essere considerata in seguito se la dashboard cresce molto. Opzione C, React/Vite, e' tecnicamente valida ma al momento non conviene: replicherebbe una parte dell'impostazione del professore con costi di setup, build e dipendenze superiori al valore dimostrativo immediato.

### Linea guida progettuale

Ispirarsi al repo del professore per:

- palette scura e colori semantici;
- visualizzazione Alice/Bob/Eve/EPR/KMS;
- cards metriche compatte;
- grafici chiari;
- tabella repository chiavi.

Non replicare:

- network designer;
- backend;
- multi-protocollo;
- KMS industriale;
- modelli fisici non ancora presenti nei nostri microservizi.

La dashboard proposta deve essere una "control room" leggera per il nostro flusso E91:

```text
API Gateway -> Orchestrator -> servizi E91 -> Result Store / Mini KMS -> Dashboard
```

Il valore da mostrare in tesi e' che ogni elemento visibile della GUI corrisponde a un microservizio o a un risultato reale del backend.
