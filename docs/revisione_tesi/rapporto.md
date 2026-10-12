# Confronto completo tra tesi e implementazione E91

Revisione del 26 settembre 2026 di `Sebastiano_Battista-4.pdf` (134 pagine PDF), confrontato con il repository locale `e91-qkd-microservices`. Riferimento Git: `7f15c5252f3de7dfb80cdd59a28c2161e78844da`, con modifiche locali già presenti al momento della revisione. Il confronto riguarda i file effettivamente presenti, non soltanto quelli del commit. Non sono stati modificati tesi, servizi, esperimenti originali o modifiche preesistenti.

**I numeri di pagina indicati sono quelli stampati nella tesi. Per raggiungerli nel lettore PDF bisogna aggiungere 5: pagina 80 della tesi = pagina 85 del PDF.**

## Giudizio complessivo

La tesi ha un contributo ingegneristico concreto: una pipeline a microservizi per simulare statistiche E91, applicare perturbazioni controllate, classificare le sessioni e organizzare esperimenti. I risultati tabellari controllati sono coerenti con i dati archiviati. Le principali difficoltà riguardano la descrizione dell'implementazione, alcune affermazioni teoriche troppo forti e parti delle appendici che descrivono interfacce o comportamenti diversi dal codice.

Non è corretto presentare questo software come implementazione completa di distribuzione di chiavi segrete, come certificazione device-independent, come simulazione fisica completa dell'intercept-resend o come prova sperimentale della non-località. È sostenibile presentarlo come simulatore statistico centralizzato delle correlazioni, distribuito in servizi software, con chiave dimostrativa e verifica circuitale mirata. La conclusione a pagina 81 riconosce già parte di questo perimetro: occorre estenderne la precisione a tutto il testo.

**Prima della consegna sono da correggere soprattutto:** definizione di materiale sifted, origine degli outcome, descrizione di Eve, stato preparato da Qiskit, persistenza, contratti API, formule delle deviazioni standard, figure mancanti e introduzione su PQC/sicurezza QKD.

## Verifiche eseguite e limiti

- Lettura del testo di tutti i capitoli, delle appendici A–F e della bibliografia.
- Lettura dei servizi Python, del modello comune delle basi, di Compose, degli script della campagna finale e del confronto Qiskit; controllo della dashboard e degli strumenti di test/documentazione pertinenti.
- Ricalcolo di tutte le statistiche aggregate dei 360 run della campagna, confrontate con entrambi i riepiloghi CSV e JSON: nessuna differenza numerica oltre la tolleranza di calcolo.
- Ricalcolo delle statistiche dei 20 run del confronto tra sampler e Qiskit: nessuna differenza rispetto ai riepiloghi CSV e JSON.
- Controllo delle tabelle numeriche principali del capitolo 5 rispetto ai riepiloghi, comprese medie, deviazioni standard e tassi riportati per gli scenari.
- Esecuzione di sette sessioni isolate da 10.000 round ciascuna attraverso le vere applicazioni FastAPI e l'orchestrazione, instradando le chiamate HTTP in memoria. Risultati nuovi separati dalla campagna originale; persistenza in directory temporanea.
- Prove mirate su rigenerazione degli outcome, equivalenza delle strategie Eve, hash della chiave, richieste con `basis_model`, endpoint mancanti, caricamento del Result Store e CHSH non disponibile.
- Verifica dello stato e delle correlazioni esatte tramite Qiskit Statevector; esecuzione del codice Aer con 2.500 shot per combinazione CHSH.
- Controllo visuale di pagine con formule lunghe e figure; verifiche bibliografiche mirate su fonti primarie.
- `docker compose config --quiet` passa. Il daemon Docker non è attivo: non sono stati verificati build, avvio, rete o integrazione dei container. Non è stata rieseguita la campagna completa di 360 sessioni su Docker.

Le prove isolate verificano logica, validazione e flusso applicativo; non misurano prestazioni della rete distribuita. Il seed fissato nelle prove riguarda il processo di audit: la pipeline ordinaria non espone un seed riproducibile. Non è possibile attestare retroattivamente la versione esatta del software che produsse i CSV, in assenza di un manifesto di esecuzione. Il sorgente LaTeX della tesi non è disponibile nel repository: le anomalie del PDF sono osservabili, ma la loro causa nel sorgente va verificata.

Evidenze: [JSON delle verifiche](evidenze_verifica.json). Script ripetibile dalla root del repository: `.venv/bin/python docs/revisione_tesi/verifica_isolata.py`. Scrive il nuovo risultato in `/tmp/e91-thesis-audit-evidence.json`, senza sovrascrivere gli esperimenti originali.

## Parti confermate

| Aspetto | Riscontro |
|---|---|
| Tre basi per Alice e Bob | Presente in `shared/bases.py` |
| Key subset K0/K0 e K1/K1 | Implementato e disgiunto dal Bell subset |
| Quattro coppie CHSH | C/K0, C/C, K1/K0, K1/C |
| Combinazione CHSH | Tre termini positivi e ultimo negativo |
| Anticorrelazione del singoletto | Riprodotta dal sampler; inversione del bit di Bob per QBER |
| Soglie operative | 2,4; 0,08; 0,15; limite classico 2,0 |
| Separazione security_status/key_status | Implementata; caso di materiale insufficiente presente |
| Perdita di link | Bernoulli con trasmittanza derivata dall'attenuazione totale |
| Perdite non aumentano direttamente il QBER | Coerente con il modello implementato |
| Qiskit ausiliario | Non interviene nella pipeline ordinaria |
| SHA-256 dimostrativo | Esplicitamente etichettato nel codice |
| Campagna finale | 36 scenari × 10 ripetizioni × 10.000 round |
| Dashboard HTML/CSS/JS e gateway | Presenti; la preview richiede le precisazioni riportate sotto |

Il sampler implementa correttamente, per le direzioni di misura scelte, `E(a,b) = -cos(a-b)`. Il calcolo delle correlazioni come media dei prodotti è corretto. Non troncare automaticamente una stima campionaria sopra `2√2` è corretto: il limite vincola il valore atteso quantistico, non ogni possibile stima su un campione finito.

## Problemi prioritari di coerenza e loro correzione

### 1. La definizione di Nsifted non coincide con il campo software

**Priorità alta — pp. 32–35, 96–97; tabelle del capitolo 5.**

La tesi definisce `Nsifted = |RKEY|`. In [key-processing/app/main.py](../../key-processing/app/main.py:80) il codice calcola invece:

```text
raw_key_length    = numero di tutti i round key
sifted_key_length = numero dei round key senza discordanza
```

Quindi, per la pipeline ordinaria:

```text
raw_key_length = key_subset_size = compared_bits = |RKEY|
sifted_key_length = |RKEY| - error_count
QBER = error_count / |RKEY|
```

La soglia `min_sifted_key_length` viene applicata al secondo numero. L'identità scritta in tesi è vera soltanto se il QBER è zero. Questo spiega anche perché nelle tabelle il materiale chiamato sifted diminuisca con rumore/Eve senza perdita di coppie.

Esempio originale: `noise_bit_flip_0.10` ha `raw_key_length_mean = 2240,6`, ma `sifted_key_length_mean = 2024,4`. Non sono due modi equivalenti di indicare la stessa quantità.

**Correzione proposta:** distinguere `Nkey = |RKEY|` e `Nclean = Nkey - Nerr`; dichiarare che il campo storico `sifted_key_length` misura `Nclean`. Il sifting propriamente detto seleziona le basi, non elimina gli errori. Eventuale rinomina del software comporta aggiornare contratti, dashboard e report; per riallineare il testo ai risultati esistenti basta precisare la semantica.

### 2. La chiave dimostrativa viene calcolata sui bit grezzi di Alice, compresi i round discordanti

**Priorità alta — pp. 16, 38, 54, 97–98, 81.**

Il codice controlla la soglia sul materiale senza errori, ma calcola:

```python
hashlib.sha256(raw_key_bits.encode("utf-8")).hexdigest()
```

in [key-processing/app/main.py](../../key-processing/app/main.py:97). Non applica l'hash a `sifted_key_bits` e non genera/verifica una seconda chiave indipendente di Bob.

La formula `SHA256(Kraw)` a pagina 97 è coerente con il codice. Non lo sono un'interpretazione come chiave già riconciliata né la derivazione dal materiale sifted suggerita a pagina 81 e dal messaggio `key_reason`. La prova controllata con 300 bit, dei quali 10 discordanti, produce `generated`: l'hash coincide con i 300 bit di Alice, non con i 290 concordi, né con l'hash dei 300 bit corretti di Bob.

Nei dati originali, **138 delle 218 sessioni `generated` hanno QBER non nullo**. Questo non rende falsi i risultati del simulatore, ma impedisce di interpretarli come 218 distribuzioni complete di chiavi identiche e segrete.

**Correzione proposta:** descrivere una «derivazione centralizzata dimostrativa di un digest di 256 bit dal registro grezzo di Alice, subordinata a criteri diagnostici e quantitativi». Se si vuole dimostrare una chiave condivisa, servono riconciliazione, verifica della concordanza, trattamento dell'informazione rivelata e privacy amplification adeguata. Passare semplicemente all'hash dei bit concordi risolve una parte della coerenza interna, non realizza un protocollo QKD sicuro.

### 3. Alice e Bob non producono gli outcome finali usati nelle metriche

**Priorità alta — pp. 30, 35–38, 48, 53, 95–96.**

In [alice-service](../../alice-service/app/main.py:20) e [bob-service](../../bob-service/app/main.py:20) gli outcome sono placeholder deterministici ricavati da SHA-256 di ruolo, `pair_id` e base. Il servizio [sifting-bell-test](../../sifting-bell-test/app/main.py:118) ignora questi valori per la valutazione e ricampiona congiuntamente entrambi gli outcome a partire dagli angoli, applicando poi rumore ed Eve. `/evaluate` lo fa separatamente su Bell subset e key subset, alle righe 198–199.

Una prova con 1.000 coppie sulla stessa base, tutte inizialmente concordi, produce dopo il ricampionamento 1.000 coppie anticorrelate. Dunque la diagnostica non analizza semplicemente le misure locali già raccolte.

**Correzione proposta:** rendere esplicita la generazione differita degli outcome fisicamente modellati. Il confine «quantistico prima dei receiver, puramente classico dopo» è concettuale, non corrisponde alla collocazione del sampler nel codice. In una futura riorganizzazione si può spostare il campionamento prima del post-processing; non è necessario farlo per descrivere onestamente il prototipo esistente.

### 4. Manca la descrizione matematica del componente centrale della simulazione

**Priorità alta — capitolo 3 e appendice E.**

Il testo richiama un sampler statistico, ma non espone la sua legge fondamentale né la distribuzione congiunta che implementa. Per il modello attuale occorre aggiungere:

```text
E(a,b) = -cos(a-b)
P(A=x, B=y | a,b) = [1 - xy cos(a-b)] / 4,    x,y ∈ {-1,+1}
P(A=B | a,b) = [1 - cos(a-b)] / 2
```

Il codice sceglie Alice uniformemente e decide la concordanza di Bob con quest'ultima probabilità. Questo riproduce la statistica del singoletto per le misure considerate.

Il sampler conosce entrambe le basi: è una simulazione centralizzata della distribuzione congiunta, non un modello locale a variabili nascoste che contraddice Bell. La separazione in processi HTTP non fornisce località fisica, indipendenza dei dispositivi o una certificazione sperimentale dell'entanglement. Qui CHSH verifica che il software riproduca le statistiche imposte dal modello.

### 5. randomize e intercept_resend sono la stessa legge stocastica

**Priorità alta — pp. 42, 68–70, 73, 77, 94, 106–107.**

Il [servizio Eve](../../eve-service/app/main.py:31) seleziona gli ID dei round con una Bernoulli. Nel [sampler](../../sifting-bell-test/app/main.py:138), qualunque sia `attack_type`, su quei round l'outcome di Bob viene estratto uniformemente e indipendentemente.

Non esistono base di Eve, suo esito di misura, stato reinviato o registro dell'informazione ottenuta. A parità di seed e input i due nomi producono esattamente gli stessi outcome, come verificato. Hanno inoltre la stessa legge osservabile del `depolarizing` simbolico isolato a pari probabilità.

**Correzione proposta:** dichiarare che i due identificatori rappresentano la stessa approssimazione di decorrelazione nella versione attuale. La differenza tra 9/10 degraded e 10/10 degraded a probabilità 0,25 non dimostra una differenza tra attacchi: è variazione campionaria. Per confrontare due strategie fisicamente diverse occorre implementarli diversamente e rifare quella parte della campagna.

### 6. L'appendice Qiskit descrive un circuito diverso da quello eseguito

**Priorità alta — p. 113; interpretazione del segno pp. 65, 112, 116.**

Il testo mostra `H → CX → X → Z` per preparare il singoletto. In [qiskit_sampler.py](../../sifting-bell-test/app/qiskit_sampler.py:55) compaiono soltanto `H` e `CX`: da `|00⟩` viene preparato `|Φ+⟩ = (|00⟩+|11⟩)/√2`. La verifica Statevector lo conferma esattamente.

Con gli osservabili nel piano X–Z usati nel codice:

```text
E_singlet(a,b) = -cos(a-b)
E_Phi+(a,b)    = +cos(a-b)
S_singlet     = -2√2
S_Phi+        = +2√2
```

È quindi ragionevole confrontare `|S|` per questa verifica specifica, purché si documentino lo stato differente e l'equivalenza delle correlazioni dopo una convenzione locale sugli esiti. Non si può affermare che il circuito implementato prepari il singoletto.

Invertire contemporaneamente il mapping degli esiti di entrambi gli utenti lascia invariato il prodotto; scambiare solamente l'ordine di lettura dei due bit lascia anch'esso invariato il prodotto. Perciò l'elenco generico di cause del cambio di segno a pagina 116 non spiega il caso concreto. La causa principale verificabile è la scelta dello stato di Bell.

**Correzione proposta:** documentare `Φ+` e la relazione precedente, mantenendo i risultati esistenti. Oppure implementare davvero il singoletto e ripetere il confronto, aggiornando segno, esempi e dati.

### 7. Gli angoli e il segno di CHSH vanno uniformati

**Priorità medio-alta — pp. 9, 12, 31–33, 113–114.**

La tabella effettiva in [shared/bases.py](../../shared/bases.py:19) è:

| Base | Alice | Bob |
|---|---:|---:|
| C | 0° | −45° |
| K0 | 45° | 45° |
| K1 | 90° | 90° |

A pagina 9 Bob ha invece 135° come terza direzione. È una scelta teorica legittima, ma richiede una diversa convenzione dei segni quando la si collega alla formula successiva. Usando 135° nella formula a tre più e un meno del codice non si ottiene la massima violazione. A pagina 12, con il singoletto e la configurazione indicata, il valore è `S = -2√2`; scrivere `|S| = 2√2` elimina l'ambiguità.

Gli angoli del modello sono direzioni sulla sfera di Bloch, non direttamente angoli di polarizzatori lineari: in quest'ultima convenzione compare il doppio angolo. Nel codice `ry(-2*radians(angle/2))` si semplifica in `ry(-radians(angle))`, coerentemente con una direzione di Bloch. Il commento sul «parametro half-angle» è fuorviante: la matrice RY contiene metà dell'angolo passato, ma l'argomento della porta è l'angolo di rotazione. [Documentazione IBM RYGate](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.RYGate).

### 8. Il sifting viene attribuito al microservizio sbagliato

**Priorità alta per il capitolo implementativo — pp. 38, 52–53, 90–101.**

È [classical-channel/app/main.py](../../classical-channel/app/main.py:31), endpoint `/reconcile`, che unisce i record, confronta le basi e costruisce i sottoinsiemi. `sifting-bell-test` riceve questi insiemi, ricampiona gli esiti e calcola le metriche.

Il servizio `classical-channel` è assente da varie tabelle e sequenze della tesi. Va inserito come componente esplicito; «sifting» e «riconciliazione degli errori» non vanno confusi: l'endpoint chiamato `/reconcile` non implementa un protocollo di correzione degli errori.

### 9. La persistenza completa delle sessioni non è implementata

**Priorità alta — pp. 39, 47, 49, 54, 99, 126.**

[Result Store](../../result-store/app/main.py:15) conserva le risposte complete in `RESULTS`, un dizionario in memoria. Su disco persiste solo `KEY_RECORDS`, un riepilogo per ogni sessione, anche quando la chiave non è generata.

Prova: una sessione è recuperabile con HTTP 200; svuotando lo stato in memoria e caricando il file come dopo un riavvio, la sessione completa restituisce 404, mentre il key record restituisce 200. Non vengono ricaricati configurazione completa, correlazioni dettagliate o singoli outcome di sessione.

**Correzione proposta:** distinguere memoria volatile delle sessioni, persistenza JSON dei key record e archiviazione CSV/JSON degli script. Se la tesi richiede davvero persistenza completa, implementarla e provarne il recupero dopo un riavvio.

### 10. Tracciabilità e metadati sono più limitati di quanto suggerisca il testo

**Priorità media — pp. 36, 39, 49, 94–95, 120–121.**

Il canale genera `disturbed_pair_ids`, `attacked_pair_ids` e `lost_pair_ids`, ma [l'orchestratore](../../orchestrator/app/main.py:116) non li include nella risposta finale. La risposta conserva conteggi, correlazioni aggregate e `key_records` con bit/errori dei round key; non conserva un audit completo di tutti i round e delle perturbazioni. I CSV della campagna non contengono questi ID né il registro completo delle misure.

**Correzione proposta:** separare informazioni disponibili negli output intermedi da quelle effettivamente restituite, archiviate e recuperabili. Non affermare una tracciabilità retrospettiva completa a partire dai soli file finali.

### 11. Gli endpoint dell'appendice F non coincidono con il gateway

**Priorità alta — p. 119.**

| Funzione | Tesi | Implementazione effettiva |
|---|---|---|
| Avvio | `POST /simulate` | `POST /simulations` |
| Risultato singolo | `GET /results/{session_id}` sul gateway | `GET /simulations/{session_id}` sul gateway |
| Elenco risultati | `GET /results` | Non implementato |
| Risultato interno | Non distinto chiaramente | `GET /results/{session_id}` solo su Result Store, porta 8011 |
| Ultimi key record | Un'ultima chiave | Lista degli ultimi record, `limit=10` predefinito |

I tre endpoint errati del gateway restituiscono 404 nelle prove isolate. Riferimento: [api-gateway/app/main.py](../../api-gateway/app/main.py:52).

### 12. Anche gli esempi JSON descrivono contratti diversi

**Priorità alta — pp. 120–123.**

La risposta ordinaria non è piatta. Le chiavi di primo livello sono:

```text
session_id, request, source, transmission, link_metrics, sifting_bell_test, key
```

CHSH, QBER e `security_status` si trovano in `sifting_bell_test`; stato e digest della chiave in `key`; `lost_pair_count` e stato del collegamento in `link_metrics`. Il blocco `metadata` disegnato in tesi non compare nella risposta corrente.

`/keys` e `/keys/latest` restituiscono record anche per le sessioni scartate o insufficienti. `/keys/latest` restituisce una lista, non un singolo oggetto e non necessariamente una chiave generata.

Qiskit restituisce correlazioni con nomi come `E(C,K0)` e valori oggetto contenenti `expectation`, `counts`, `shots`, `coefficient`. Non restituisce il dizionario di scalari `C_K0` più un blocco `counts` separato disegnato a pagina 123. Inoltre i conteggi esemplificativi di quella pagina danno `(1060+1070-190-180)/2500 = 0,704`, non esattamente 0,70: una semplificazione va dichiarata.

**Correzione proposta:** usare esempi reali anonimizzati e abbreviati, mantenendo struttura e tipi; distinguere chiaramente uno schema concettuale da un contratto API utilizzabile.

### 13. basis_model non è un parametro configurabile della richiesta

**Priorità media — pp. 52–53, 102–108, 119–120.**

I modelli Pydantic del gateway e dell'orchestratore non dichiarano `basis_model`; esso è una costante in `shared/bases.py`. Un valore estraneo inviato nel JSON viene ignorato. La prova con `basis_model="UNSUPPORTED"` lo conferma.

**Correzione proposta:** presentarlo come metadato del modello fisso, non come selettore di input. Gli scenari sono definiti tramite payload negli script, non in una directory `config/`.

### 14. Albero del repository e configurazione non rappresentano i file reali

**Priorità media — pp. 50–52, 110, 124.**

Il repository non contiene le directory `services/`, `config/`, `receiver-alice/`, `receiver-bob/` o `dashboard/` mostrate. Contiene `alice-service/`, `bob-service/`, `noise-model/`, `eve-service/`, `classical-channel/` e `frontend/` direttamente nella root. Lo schema di pagina 50 è introdotto come logico, ma il testo di pagina 52 afferma concretamente l'esistenza di file esterni in `config/`.

Anche `results/final/raw_runs/`, `summaries/`, `final_summary.csv` e `scenario_summary.csv` sono schemi ipotetici, non i nomi prodotti dalla campagna. Usare quelli corretti già riportati nel capitolo 5: `final_experiment_runs.csv`, `final_experiment_summary.csv`, `final_experiment_summary.json`, i file `final_sampler_comparison_*` e `plots/`.

### 15. Parametri degli esempi e campagna finale non sono sempre gli stessi

**Priorità media — pp. 102, 107–108.**

- `link_critical_high_threshold` usa **3000** in script, CSV e capitolo 5; pagina 108 mostra **1000** con lo stesso nome.
- La configurazione base dello script mantiene distanze **25/25 km** con perdita disattivata; pagina 102 mostra **0/0**. Gli outcome sono equivalenti quando la perdita è disattivata, ma le metriche descrittive del link non lo sono.
- L'esempio combinato di pagina 107 usa `depolarizing=0,03`, Eve=0,05; i tre scenari finali usano `bit_flip` e livelli accoppiati 0,02/0,02, 0,05/0,05, 0,10/0,10. È un esempio valido di configurazione possibile, ma non uno dei run della campagna descritta.

**Correzione proposta:** indicare esplicitamente gli esempi illustrativi e riportare senza variazioni i payload degli scenari realmente misurati.

### 16. La deviazione standard ha il denominatore sbagliato nel testo

**Priorità alta, correzione semplice — pp. 110 e 125.**

Le formule usano `1/n`; gli script usano la deviazione standard campionaria con `1/(n-1)`, come verificato ricalcolando i CSV. Per 10 ripetizioni la differenza è un fattore `sqrt(10/9) ≈ 1,0541`.

Scrivere:

```text
s_x = sqrt[ Σ_j (x_j - x̄)^2 / (n-1) ]
```

Le tabelle non devono essere cambiate per questa ragione: sono già coerenti con gli script. Chiarire nelle didascalie che `±` indica una deviazione standard tra run, non errore standard della media o intervallo di confidenza.

### 17. La preview della dashboard calcola stime proprie

**Priorità media — pp. 55–56 e 99.**

È vero che la dashboard non altera la classificazione restituita dai servizi. Tuttavia [estimateScenario](../../frontend/app.js:271) calcola QBER, CHSH, quantità di bit e stato stimato per la preview. La frase assoluta «non calcola le metriche» va quindi limitata ai risultati effettivi della sessione.

La preview presenta inoltre due problemi concreti:

- usa `q = 1-(1-p)(1-e/2) = p+e/2-pe/2`; il modello backend bit-flip più Eve ha `q = p(1-e)+e/2 = p+e/2-pe`;
- prevede una chiave di 256 bit se i bit puliti stimati sono semplicemente maggiori di zero, senza applicare la soglia minima di 256.

Per esempio 1.000 round ideali danno circa 222 bit key attesi: la preview può indicare chiave finale, il backend normalmente risponde materiale insufficiente. La UI ordinaria inoltre non espone tutti i selettori presenti nelle API: usa i default per tipo di rumore, tipo di attacco e soglia minima.

**Correzione proposta:** dichiarare la preview approssimata e distinta dalle misure; allinearne formula e soglia se deve rappresentare fedelmente il backend.

## Correttezza teorica e interpretazione dei risultati

### 18. La PQC affronta anche la costituzione di chiavi condivise

**Priorità alta — p. 3.**

La frase secondo cui i sistemi PQC non risolvono il problema della distribuzione sicura delle chiavi è troppo generale e fuorviante. Un KEM post-quantistico serve proprio a stabilire un segreto condiviso sotto ipotesi computazionali. L'autenticazione resta necessaria per contrastare un intermediario attivo; anche la QKD richiede un canale classico autenticato.

Inoltre ML-KEM (derivato da Kyber) e ML-DSA (derivato da Dilithium) sono standard finali dal 13 agosto 2024; presentarli soltanto come oggetto di standardizzazione è datato. La bibliografia contiene già la notizia NIST del 2024, creando anche un'incoerenza interna. [NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final), [annuncio NIST degli standard](https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards).

**Testo proposto:** «La PQC comprende meccanismi di costituzione di chiavi e firme digitali resistenti agli attacchi quantistici conosciuti, con garanzie basate su ipotesi computazionali. La QKD adotta un diverso modello di sicurezza, fondato sulla teoria quantistica e su specifiche assunzioni fisiche e di autenticazione».

### 19. E91, violazione di Bell e device independence non sono sinonimi automatici

**Priorità alta — pp. 4, 8–12.**

A pagina 4 E91 viene presentato come intrinsecamente DI e privo di assunzioni di fiducia; a pagina 8 è più correttamente chiamato precursore degli schemi DI. Una violazione CHSH può vincolare l'informazione di Eve sotto assunzioni definite, ma non prova da sola assenza di attacco, segretezza della chiave finale o sicurezza di un'implementazione.

Anche i protocolli DI assumono laboratori isolati, scelte casuali private, autenticazione della comunicazione classica e post-processing affidabile; occorrono inoltre trattamento statistico e delle inefficienze. [Esperimento DI-QKD per utenti distanti](https://www.nature.com/articles/s41586-022-04891-y).

Anche l'affermazione generale di pagina 9 secondo cui le correlazioni di uno stato entangled non ammettono descrizione locale va limitata: entanglement e violazione di Bell non sono equivalenti per stati misti generali. [Werner, 1989](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.4277).

Nel presente codice non esistono certificazione DI, bilancio di entropia di Eve, parametro di sicurezza composabile o analisi finite-key. Le soglie sono regole operative: la tesi lo dichiara correttamente a pagina 34 e deve usare lo stesso linguaggio nel resto del documento. «Secure» è un'etichetta del simulatore, non una certificazione crittografica.

### 20. Misura e rilevazione dell'intercettazione sono descritte in modo assoluto

**Priorità media — pp. 4–5, 8, 83–88.**

Una misura non altera necessariamente lo stato: una misura proiettiva sul relativo autostato lo lascia invariato. Il punto crittografico è l'impossibilità di discriminare perfettamente stati non ortogonali arbitrari senza conseguenze, non l'alterazione inevitabile di qualsiasi stato per qualsiasi osservazione.

Un disturbo non è identificabile con certezza in ogni singolo run finito, e QBER/CHSH da soli non identificano univocamente la causa. Nel codice depolarizing ed Eve isolati possono avere addirittura la stessa distribuzione osservabile. I metadati «Eve ha attaccato questo round» provengono dalla configurazione simulata, non da un'inferenza del protocollo.

La discussione prudente di pagina 22 è buona e va mantenuta; attenuare le affermazioni assolute dell'introduzione. Per la struttura della sicurezza QKD e il ruolo del canale classico autenticato si veda [Scarani et al.](https://arxiv.org/abs/0802.4155).

### 21. QBER globale e filtro degli errori usano conoscenza centralizzata

**Priorità alta per delimitare il modello — pp. 34, 96–98.**

La pipeline confronta tutti i bit del key subset e sa esattamente quali posizioni discordano. In un protocollo distribuito reale questo richiede comunicazione classica, stima parametrica e/o riconciliazione con un costo informativo; non si può assumere gratuitamente il registro completo di entrambi gli utenti.

In tesi distinguere questo QBER di simulazione dalla stima operativa su campioni e dichiarare che il filtro dei bit concordi usa conoscenza globale del simulatore. La disgiunzione key/Bell è corretta, ma non dimostra che tutti i bit key restino segreti durante il post-processing reale.

### 22. La formula del tasso segreto di pagina 26 non è una legge generale E91/DI

**Priorità medio-alta — p. 26.**

`R_sift[1-h2(Q)-f(Q)h2(Q)]` è una forma semplificata che richiede ipotesi su protocollo, errori di fase, regime asintotico e riconciliazione. La capacità classica di Shannon non basta a dedurre segretezza rispetto a Eve. In un'analisi DI il vincolo sull'informazione avversaria dipende anche dalla violazione di Bell, non soltanto dal QBER. [Analisi di Pironio et al. contro attacchi collettivi](https://arxiv.org/html/0903.4460v1).

Il termine `f(Q)h2(Q)` rappresenta il costo complessivo della riconciliazione nel modello, mentre `(f-1)h2(Q)` è l'eccesso rispetto al limite ideale. Il termine di privacy amplification non dovrebbe essere spiegato soltanto come generica perdita dovuta al rumore.

**Correzione proposta:** citare una derivazione con ipotesi esplicite e dichiarare che la formula ha funzione introduttiva e non viene calcolata dal simulatore. `generated_key_rate` è invece una frazione di run con digest generato, non bit segreti al secondo né frazione segreta dimostrata.

### 23. La perdita è indipendente da basi ed esiti: assunzione decisiva

**Priorità media — pp. 12, 27, 40, 65–66.**

Nel codice le perdite sono selezionate prima della scelta delle basi e indipendentemente dagli outcome. Per questo non modificano la correlazione attesa dei sopravvissuti; aumentano l'incertezza e riducono i bit disponibili. È un comportamento del modello, non una prova che le perdite reali siano sempre irrilevanti per la sicurezza. La postselezione e il detection loophole richiedono attenzione nei test DI. [Pironio et al., sezione sui loophole](https://arxiv.org/html/0903.4460v1).

A pagina 27 la distanza è descritta come combinazione di attenuazione e rumore, mentre dal capitolo 3 è solo perdita indipendente. Allineare la descrizione e distinguere effetti reali possibili da quelli effettivamente implementati. Anche la frase di pagina 12 su QBER che aumenta in presenza di perdite va qualificata.

### 24. 0,02 dB/km è un parametro equivalente, non una fibra ordinaria calibrata

**Priorità media — pp. 40, 65, 104.**

Il calcolo `Ltot = α(dA+dB)` e `T=10^(-Ltot/10)` è coerente. L'interpretazione in chilometri deve però rimanere quella di distanza equivalente. Come riferimento concreto, la specifica Corning SMF-28 Ultra riporta attenuazione massima di 0,18 dB/km a 1550 nm, non 0,02. [Scheda del produttore](https://www.corning.com/content/dam/corning/catalog/coc/documents/selection-guides/CRR-718-BEN.pdf).

Per mostrare la sensibilità del modello, con α=0,2 dB/km e 400 km totali si avrebbero 80 dB e T=10^-8, contro gli 8 dB e T≈0,1585 della campagna. Questo esempio non predice una rete reale completa, ma dimostra perché non si possa presentare la simulazione come validazione di QKD su 400 km di fibra standard.

### 25. I modelli di rumore sono perturbazioni degli outcome, non canali fisici completi

**Priorità media — pp. 19, 41, 67–68.**

`bit_flip` inverte il risultato di Bob dopo il campionamento: non applica una porta Pauli-X a una matrice densità propagata nel canale. `depolarizing` randomizza Bob nei round selezionati; sulle statistiche considerate riproduce una forma di attenuazione delle correlazioni, senza descrivere detector, dark count, tempi di coerenza o errori di porta.

Va mantenuta la qualifica «simbolico/statistico». Dire che bit-flip è più distruttivo a pari parametro è corretto per questo codice, perché ogni evento flip produce errore su basi key, mentre una randomizzazione produce errore solo con probabilità 1/2. Non è una graduatoria universale fra canali fisici.

### 26. Gestione dei campioni piccoli assente nelle formule della tesi

**Priorità media — pp. 33–35, 97.**

Se manca anche una combinazione Bell, il codice imposta `chsh_available=false`, `abs_chsh=0` come valore convenzionale e classifica `degraded`, salvo QBER > 0,15. La formula della tesi classificherebbe invece `insecure` per `|S|≤2`. Serve una condizione iniziale per CHSH non disponibile.

Se non ci sono bit key il codice restituisce QBER=0, che va interpretato come assenza di confronto e non come qualità perfetta. Non è imposto un minimo significativo di campioni per ciascun termine CHSH: basta almeno un prodotto. Con campioni piccoli sono possibili stime molto estreme, senza intervalli di confidenza né garanzie di falsa accettazione. Questa limitazione non altera le tabelle della campagna esaminata, ma va dichiarata per il perimetro generale delle API.

### 27. Dieci ripetizioni non sono una certificazione di affidabilità

**Priorità media — pp. 60–80.**

Le statistiche descrivono bene la campagna, ma 10/10 successi non equivalgono a probabilità di successo certa. Assumendo run Bernoulli indipendenti, l'intervallo binomiale esatto bilaterale al 95% per 10/10 è circa [0,692; 1]. Con 7/10 o 1/10 l'incertezza resta ampia.

Occorre distinguere deviazione standard tra run, errore standard della media e confidenza. I 360 run senza errori sono evidenza di buon funzionamento nella campagna, non dimostrazione di scalabilità, tolleranza ai guasti o sicurezza.

Le percentuali globali dipendono inoltre dalla scelta degli scenari: 63,3% secure non è una stima della probabilità che E91 sia sicuro «in generale».

### 28. Il confronto dei sampler usa campioni Bell di dimensione diversa

**Priorità media — pp. 64–65, 114–116.**

I 10.000 round del sampler classico vengono ripartiti casualmente: in media 4/9 servono a Bell. Nel file di confronto il Bell subset medio è **4443 round**, circa 1111 per coppia di basi. Qiskit usa 2500 shot per ciascuna delle quattro combinazioni, quindi 10.000 osservazioni Bell.

Le medie di |S| possono essere confrontate, ma le deviazioni standard non misurano la precisione dei due metodi a parità di campione o costo. Il modulo Qiskit usa le stesse definizioni di basi e segni importate dal modulo comune: è una realizzazione computazionale alternativa, non un controllo completamente indipendente della configurazione teorica.

Miglioramento: confrontare anche le quattro correlazioni con i segni allineati e usare lo stesso numero di campioni per termine. Non è un benchmark di velocità: non ci sono misure di durata comparabili.

### 29. Lo scenario con soglia 3000 verifica la soglia, ma non isola l'effetto delle perdite

**Priorità media — p. 66.**

Con 10.000 round e scelta uniforme delle basi, il materiale key ideale atteso senza perdite è 10.000×2/9 ≈ 2222 bit. Una soglia di 3000 è dunque già superiore all'atteso della baseline senza perdita. Il confronto riportato verifica correttamente la distinzione tra `secure` e `generated`, ma non dimostra che la sola attenuazione provochi il mancato superamento di una soglia altrimenti raggiungibile.

Miglioramento: mantenere una soglia fissa e confrontare canali con trasmittanze diverse, oppure aggiungere il controllo senza perdita a soglia 3000. Nel modello ideale la soglia 256 si incrocia in media intorno a 469 km totali equivalenti per α=0,02, non nei tre punti 50/300/400 km della campagna. Non serve alterare i dati esistenti: basta descrivere bene il test e aggiungere eventuali nuovi esperimenti separatamente.

I grafici del repository che connettono entrambi i punti a 400 km/8 dB, uno con soglia 256 e l'altro con 3000, mescolano due variabili. Annotare o separare la soglia per evitare di attribuire quel salto alla distanza.

### 30. Ripetibilità procedurale, riproduzione numerica e provenienza vanno distinte

**Priorità media — pp. 57–58, 126.**

Gli script rendono ripetibile la procedura; non garantiscono la stessa sequenza di outcome. Manca un seed propagato ai servizi e non sono fissati `seed_simulator` e `seed_transpiler`. Qiskit/Aer sono vincolati a intervalli di versioni, non a un lockfile esatto. I risultati non incorporano commit, dipendenze effettive e immagini Docker.

I CSV originali riportano timestamp dal 15 luglio 2026, 21:12:22 UTC al 15 luglio 2026, 21:17:14 UTC. Si possono ricalcolare esattamente gli aggregati da quei CSV; un nuovo esperimento produce statistiche compatibili, non necessariamente gli stessi numeri. Conservare un manifesto di campagna con versione del codice, ambiente, payload, seed e dati completi migliorerebbe la riproducibilità.

`run_final_experiments.py` salva tabelle, non genera direttamente i grafici: questi vengono prodotti separatamente da `plot_final_experiments.py`. La sequenza di pagina 57 va precisata. Il denominatore del generated key rate nello script è il numero dei run riusciti, non tutti i tentativi; nel dataset con zero errori i due coincidono.

## Altri rilievi software pertinenti al perimetro della tesi

### 31. Sicurezza applicativa e KMS sono dimostrativi

**Limite dichiarabile, non richiesta di trasformare la tesi in un prodotto.**

Le API espongono digest e, nella risposta completa, record con bit; la comunicazione interna è HTTP. Non è implementato un canale classico autenticato di protocollo, né controllo d'accesso ai key record. CORS non equivale ad autenticazione. L'uso di `random` è adatto a un esperimento statistico, non a generare segreti reali.

Le precisazioni su KMS dimostrativo a pagine 39 e 122 sono appropriate. Estenderle al perimetro della chiave: nessuna API va descritta come consegna sicura di segreti di produzione. `final_key` è una rappresentazione esadecimale di 64 caratteri di un digest di 256 bit, non una stringa di 256 caratteri.

### 32. La modularità esiste, ma la scalabilità non è stata misurata

Il gateway e l'orchestratore aspettano il completamento della sessione; le chiamate ai servizi sono sequenziali, incluse Alice e Bob. Non ci sono coda di lavoro, retry strutturati o compensazioni. Il Result Store è in memoria per le sessioni e riscrive il file JSON dei record; non è progettato come storage condiviso transazionale per più worker.

Compose espone anche le porte interne sull'host: il gateway è l'ingresso uniforme dei client ordinari, non l'unico ingresso tecnicamente raggiungibile. La dashboard viene avviata separatamente e non è un servizio Compose. `monitoring` e il servizio HTTP `shared` sono placeholder; il modulo Python `shared/bases.py`, invece, è effettivamente usato.

Questi fatti non annullano il contributo architetturale. Impediscono soltanto di dedurre vantaggi prestazionali o robustezza distribuita dai soli 360 run. Per il capitolo 4 aggiungere le scelte reali: FastAPI/Pydantic, HTTPX, Docker Compose, contratti annidati, timeout e strategia di persistenza.

### 33. Configurazioni limite e diagnostica migliorabili

Non si valida che soglia di perdita critica ≥ soglia degradata. Il numero di shot non ha un limite massimo nel gateway. In caso di perdita disattivata, `link_metrics` continua a riportare la trasmittanza teorica da distanza/attenuazione: per esempio la baseline salvata ha `T=0,794328` e zero coppie perse. Distinguere quindi trasmittanza configurata e sopravvivenza effettivamente applicata.

`noise_enabled` ed `eve_enabled` nella valutazione vengono dedotti dai parametri positivi delle misure sopravvissute, mentre la sezione `transmission` conserva i booleani della richiesta. A probabilità zero o nessuna coppia sopravvissuta possono discordare. Non cambia l'andamento misurato, ma può confondere la lettura degli output.

Il messaggio «Insufficient sifted key material after link loss» può comparire anche con pochi shot e perdita disattivata. La causa dichiarata è quindi più specifica di quella effettivamente verificata.

### 34. Test automatici e reingegnerizzazione vanno documentati con precisione

La CI corrente controlla compilazione Python e validità Compose; non esegue test comportamentali. Esiste uno smoke test end-to-end locale, ma non è integrato nel workflow verificato. Non presentare la sola CI come validazione completa del protocollo.

La cronologia disponibile parte già da una baseline a microservizi. Non ho trovato nel repository una versione monolitica precedente che permetta di verificare direttamente il prima/dopo raccontato alle pagine 46–50. Può esistere altrove, ma va citata; altrimenti formulare il contributo come progettazione e sviluppo incrementale dell'architettura. Aggiungere un riferimento verificabile al repository/versione e, se pertinente, al prototipo di partenza.

## Problemi del PDF e della bibliografia

### 35. Due figure citate sono assenti

**Priorità alta, bloccante editoriale — p. 80.**

Le Figure 6.1 e 6.2 hanno didascalia e richiami nel testo, ma non contengono il grafico. Verificato sul rendering della pagina, non soltanto sull'estrazione testuale: [pagina 80 renderizzata](pagina_80_figure_assenti.png).

I grafici corrispondenti esistono già nel repository:

- [combined_noise_eve_generated_key_rate.png](../../results/final/plots/combined_noise_eve_generated_key_rate.png)
- [combined_link_noise_eve_generated_key_rate.png](../../results/final/plots/combined_link_noise_eve_generated_key_rate.png)

Vanno inseriti realmente nel sorgente e va ricompilato il documento. L'assenza di immagini raster nell'intero PDF non è di per sé una prova di figure mancanti, perché potrebbero esistere figure vettoriali; in questo caso l'assenza dei due grafici è stata verificata visivamente.

### 36. Alcune formule e pipeline sono tagliate dal bordo

**Priorità alta, bloccante editoriale — esempi pp. 35 e 92.**

La sequenza della pipeline a pagina 35 esce dal margine destro. Il vettore dei parametri di link a pagina 92 arriva oltre il bordo della pagina e perde testo: [pagina 92 renderizzata](pagina_92_formula_tagliata.png). Occorre verificare tutte le espressioni lunghe, in particolare i vettori di configurazione/output alle pp. 36, 52–54, 97–98 e nelle appendici.

Usare simboli matematici brevi nelle formule e una tabella di mapping ai nomi software; andare a capo con ambienti multilinea. La pipeline è più leggibile come diagramma con due righe o livelli.

### 37. Citazioni non risolte e duplicati

**Priorità alta per la consegna — pp. 4, 17, 87, 128.**

Nel PDF sono visibili chiavi bibliografiche letterali:

- `bennett1984bb84` a pp. 4 e 87;
- `bell1964` a p. 17.

Ripristinare le chiavi nel `.bib` e ricompilare tutta la catena bibliografica. BB84 non compare come voce risolta nella bibliografia finale. Gisin è duplicato nelle voci [12]/[24]; Scarani nelle [13]/[25]. Unificare le voci e aggiornare i riferimenti.

### 38. La citazione su Micius non è quella più pertinente alla frase

**Priorità media — p. 25, riferimento [33].**

La frase riguarda la distribuzione di entanglement tra due stazioni terrestri separate da oltre 1200 km. Il riferimento [33] è invece *Satellite-to-Ground Entanglement-Based Quantum Key Distribution*, PRL 119, 200501, relativo a QKD tra satellite e osservatorio terrestre. Per la frase scritta usare [Yin et al., Satellite-Based Entanglement Distribution Over 1200 kilometers](https://arxiv.org/abs/1707.01339), distinguendolo dal [lavoro PRL citato](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.119.200501).

Altre fonti sono pertinenti come contesto generale ma non come sostegno diretto alla frase associata: per esempio report di transizione PQC a sostegno della DI-QKD o la citazione Qiskit per dettagli di infrastrutture fisiche. Verificare l'aderenza citazione–affermazione, senza cambiare fonti soltanto per aumentare il numero dei riferimenti.

### 39. Precisazioni nelle appendici teoriche

**Priorità media/bassa — pp. 83–89.**

- `|ψ⟩=α|0⟩+β|1⟩` descrive un qubit puro; per stati misti serve la matrice densità.
- Il sistema può avere uno stato quantistico definito pur non avendo un esito predeterminato per la misura scelta.
- Le trasformazioni unitarie descrivono l'evoluzione chiusa ideale; misure e rumore richiedono un formalismo più generale.
- La sezione chiamata «formalismo generale della misura» descrive misure proiettive, non le POVM generali.
- «Definitivamente nello stato osservato» va limitato all'immediato post-misura e alla successiva evoluzione considerata.
- Nell'appendice BB84, l'intercept-resend è un esempio di attacco, non una strategia obbligata di ogni Eve; anche attacchi più generali sono possibili.
- Esplicitare che le correlazioni entangled non permettono comunicazione controllata superluminale; la ricostruzione delle correlazioni richiede confronto classico.

Le formule di normalizzazione, Bloch, matrici X/H/Z e probabilità della misura proiettiva sono sostanzialmente corrette nel loro ambito.

### 40. Ripetizioni e riferimenti interni da rifinire

**Priorità editoriale — tutto il documento.**

Capitoli 3 e 4 e appendice C ripetono estesamente la stessa pipeline; sezioni 5.8, 5.9 e capitolo 6 ripetono quasi la stessa interpretazione. Si può utilizzare lo spazio per dettagli effettivamente mancanti: legge del sampler, tabella degli angoli, contratti reali, error filtering, test, assunzioni e limiti.

Le appendici contengono riferimenti cronologici non più appropriati («nel Capitolo 5 verranno discussi», «nei capitoli successivi», «paragrafo precedente» dopo lo spostamento del materiale). A.0.1/B.0.1 sono numerazioni poco curate; la doppia punteggiatura a pagina 8 va eliminata. Evitare di attribuire al protocollo fisico generale i limiti osservati del particolare modello simbolico.

## Modello quantitativo da aggiungere alla discussione

Le formule seguenti sono **derivate dal codice corrente**, non presentate come leggi universali della QKD. Consentono di spiegare i risultati senza limitarsi a ripetere che CHSH scende e QBER sale.

Con basi uniformi indipendenti:

```text
P(key) = 2/9
P(Bell) = 4/9
P(scarto tra i sopravvissuti) = 3/9
E[Nkey] = Nshots × T × 2/9
E[Nbell] = Nshots × T × 4/9
```

Usare T=1 se la perdita è disabilitata. Il campo software `discarded_subset` include anche i round persi: dunque, in una pipeline ordinaria completa, `key_subset_size + bell_subset_size + discarded_subset_size = shots`, non `delivered_pair_count`. L'insieme matematico RDISCARD limitato ai sopravvissuti è legittimo, ma non coincide direttamente con quel campo. Questo invariante è verificato in tutti i 360 run.

Indicando con p la probabilità di rumore e con e quella di Eve:

| Modello | QBER atteso | CHSH atteso con segno del singoletto |
|---|---|---|
| Ideale | 0 | −2√2 |
| Bit-flip sugli outcome | p | −2√2(1−2p) |
| Depolarizing simbolico | p/2 | −2√2(1−p) |
| Eve, entrambi i nomi | e/2 | −2√2(1−e) |
| Bit-flip + Eve | p(1−e)+e/2 | −2√2(1−2p)(1−e) |
| Depolarizing + Eve | [1−(1−p)(1−e)]/2 | −2√2(1−p)(1−e) |

Il modulo del valore atteso di S è una previsione asintotica per `abs_chsh`; a campione finito la media del modulo non coincide esattamente con il modulo della media, soprattutto vicino a S=0.

Nei livelli della campagna, p≤0,25, il decadimento è monotono. Non estendere automaticamente l'affermazione a tutto p∈[0,1]: per bit-flip la magnitudo torna a crescere oltre p=0,5, anche se il QBER resta inaccettabile.

Per il filtro implementato: `E[Nclean] = Nshots × T × (2/9) × (1−q)` sotto le assunzioni indipendenti del modello. Queste relazioni spiegano sia i valori di baseline intorno a 2222 bit, sia la riduzione apparente del materiale sifted con rumore/Eve.

Esempi: a p=0,10 il bit-flip prevede QBER≈0,10 e |S|≈2,2627; la randomizzazione con probabilità 0,10 prevede QBER≈0,05 e |S|≈2,5456. I valori salvati sono compatibili con queste previsioni. Il confronto a probabilità uguali incorpora già un fattore due nel QBER atteso.

## Riscontri numerici della campagna originale

| Grandezza | Verificato |
|---|---:|
| Scenari | 36 |
| Ripetizioni per scenario | 10 |
| Run e session_id distinti | 360 |
| Round per run | 10.000 |
| Errori registrati | 0 |
| Secure | 228 |
| Degraded | 91 |
| Insecure | 41 |
| Generated | 218 |
| Discarded degraded | 91 |
| Discarded | 41 |
| Insufficient key material | 10 |
| Generated con QBER non nullo | 138 |

Baseline: `|S| = 2,8291 ± 0,0332`, QBER=0, `Nclean = 2235,3 ± 41,5`; deviazioni standard campionarie tra 10 run. Confronto separato: sampler `2,8260 ± 0,0363`, Qiskit `2,8346 ± 0,0253`. I dati supportano queste cifre; non serve sostituirli soltanto perché altre parti della descrizione sono da correggere.

La tabella seguente è ricavata dai riepiloghi originali verificati. `Raw` corrisponde a |RKEY|; `Clean` è il campo software `sifted_key_length`; `Gen.` è il numero di run con chiave dimostrativa su 10.

| Scenario | Media abs_chsh ± SD | Media QBER | Raw medio | Clean medio | Gen. |
|---|---:|---:|---:|---:|---:|
| `baseline` | 2.8291 ± 0.0332 | 0.0000 | 2235.3 | 2235.3 | 10/10 |
| `link_nominal_25_25` | 2.8170 ± 0.0569 | 0.0000 | 1753.1 | 1753.1 | 10/10 |
| `link_degraded_150_150` | 2.8433 ± 0.1025 | 0.0000 | 557.0 | 557.0 | 10/10 |
| `link_critical_200_200` | 2.7752 ± 0.1084 | 0.0000 | 353.5 | 353.5 | 10/10 |
| `link_critical_high_threshold` | 2.8427 ± 0.0696 | 0.0000 | 349.5 | 349.5 | 0/10 |
| `noise_bit_flip_0.00` | 2.8180 ± 0.0252 | 0.0000 | 2210.8 | 2210.8 | 10/10 |
| `noise_bit_flip_0.02` | 2.6998 ± 0.0443 | 0.0205 | 2231.0 | 2185.2 | 10/10 |
| `noise_bit_flip_0.05` | 2.5397 ± 0.0318 | 0.0506 | 2213.0 | 2101.0 | 10/10 |
| `noise_bit_flip_0.10` | 2.2891 ± 0.0376 | 0.0965 | 2240.6 | 2024.4 | 0/10 |
| `noise_bit_flip_0.20` | 1.6743 ± 0.0632 | 0.1969 | 2209.9 | 1774.9 | 0/10 |
| `noise_bit_flip_0.25` | 1.3726 ± 0.0514 | 0.2465 | 2226.8 | 1678.0 | 0/10 |
| `noise_depolarizing_0.00` | 2.8242 ± 0.0619 | 0.0000 | 2226.4 | 2226.4 | 10/10 |
| `noise_depolarizing_0.02` | 2.7894 ± 0.0564 | 0.0105 | 2232.3 | 2208.9 | 10/10 |
| `noise_depolarizing_0.05` | 2.6910 ± 0.0475 | 0.0247 | 2206.6 | 2152.1 | 10/10 |
| `noise_depolarizing_0.10` | 2.5421 ± 0.0508 | 0.0493 | 2234.1 | 2124.1 | 10/10 |
| `noise_depolarizing_0.20` | 2.2724 ± 0.0469 | 0.1025 | 2204.7 | 1978.8 | 0/10 |
| `noise_depolarizing_0.25` | 2.1138 ± 0.0455 | 0.1268 | 2236.3 | 1952.6 | 0/10 |
| `eve_randomize_0.00` | 2.8284 ± 0.0279 | 0.0000 | 2227.1 | 2227.1 | 10/10 |
| `eve_randomize_0.02` | 2.8062 ± 0.0442 | 0.0100 | 2209.7 | 2187.7 | 10/10 |
| `eve_randomize_0.05` | 2.6927 ± 0.0428 | 0.0250 | 2199.4 | 2144.3 | 10/10 |
| `eve_randomize_0.10` | 2.5650 ± 0.0451 | 0.0508 | 2205.5 | 2093.5 | 10/10 |
| `eve_randomize_0.20` | 2.2720 ± 0.0471 | 0.1019 | 2237.7 | 2009.5 | 0/10 |
| `eve_randomize_0.25` | 2.1032 ± 0.0686 | 0.1240 | 2223.7 | 1948.0 | 0/10 |
| `eve_intercept_resend_0.00` | 2.8431 ± 0.0639 | 0.0000 | 2201.8 | 2201.8 | 10/10 |
| `eve_intercept_resend_0.02` | 2.7692 ± 0.0356 | 0.0108 | 2219.9 | 2196.0 | 10/10 |
| `eve_intercept_resend_0.05` | 2.7035 ± 0.0333 | 0.0258 | 2219.1 | 2161.9 | 10/10 |
| `eve_intercept_resend_0.10` | 2.5264 ± 0.0456 | 0.0504 | 2230.2 | 2117.8 | 10/10 |
| `eve_intercept_resend_0.20` | 2.2959 ± 0.0555 | 0.1008 | 2210.9 | 1988.2 | 0/10 |
| `eve_intercept_resend_0.25` | 2.1206 ± 0.0398 | 0.1265 | 2232.0 | 1949.6 | 0/10 |
| `combined_0.02_0.02` | 2.6519 ± 0.0421 | 0.0296 | 2234.8 | 2168.7 | 10/10 |
| `combined_0.05_0.05` | 2.4207 ± 0.0430 | 0.0734 | 2227.4 | 2063.8 | 7/10 |
| `combined_0.10_0.10` | 2.0057 ± 0.0548 | 0.1381 | 2219.8 | 1913.3 | 0/10 |
| `combined_0.15_0.15` | 1.6682 ± 0.0633 | 0.2018 | 2219.7 | 1771.8 | 0/10 |
| `link_noise_eve_low` | 2.6671 ± 0.1004 | 0.0306 | 551.0 | 534.1 | 10/10 |
| `link_noise_eve_medium` | 2.3604 ± 0.0918 | 0.0729 | 565.8 | 524.5 | 1/10 |
| `link_noise_eve_high` | 2.0477 ± 0.0955 | 0.1453 | 550.0 | 470.4 | 0/10 |

## Percorso di correzione consigliato

1. **Allineare il testo alla versione esistente prima di cambiare i risultati.** Correggere outcome differiti, sifted/clean, digest grezzo di Alice, stato Φ+ in Qiskit, Eve equivalente, sifting in Classical Channel, persistenza e API.
2. **Correggere le affermazioni teoriche.** PQC, E91/DI, misura non sempre perturbativa, significato diagnostico di secure, assunzioni sulla perdita, formula del tasso segreto e perimetro simbolico dei rumori.
3. **Correggere PDF e appendici.** Inserire i grafici mancanti, spezzare le formule, risolvere le citazioni, aggiornare alberi dei file, payload e denominatore della deviazione standard.
4. **Rafforzare la discussione sperimentale.** Aggiungere le leggi attese derivate dal modello, distinguere successo osservato e probabilità, chiarire campioni diversi nel confronto Qiskit e soglia artificiale nel test di insufficienza.
5. **Cambiare il codice soltanto se si vuole sostenere un contributo più forte.** Intercept-resend fisico, riconciliazione distribuita, persistenza completa e confidenza statistica sono estensioni sostanziali. Qualunque cambiamento alla legge del sampler o alla selezione della chiave richiede esperimenti nuovi, versionati separatamente, e aggiornamento coerente della tesi.

Un allineamento testuale rigoroso consente di conservare il valore del lavoro già svolto e gran parte dei risultati. Non è necessario trasformare il prototipo in una rete QKD di produzione per sostenere una tesi sulla sua architettura simulativa.

## Passaggi pronti da adattare nella tesi

**Perimetro del contributo**

> Il sistema sviluppato è un simulatore statistico del protocollo E91 organizzato in microservizi. Le correlazioni di misura vengono generate da un campionatore congiunto che riproduce la distribuzione del singoletto per le basi considerate. La classificazione delle sessioni applica soglie operative su CHSH e QBER; non costituisce una dimostrazione di sicurezza crittografica o una certificazione device-independent. La chiave finale è un digest dimostrativo e il prototipo non implementa una procedura completa di riconciliazione e privacy amplification.

**Distribuzione delle responsabilità**

> I receiver scelgono le basi e producono record contenenti esiti provvisori. Il Classical Channel associa i record per identificativo e costruisce i sottoinsiemi key, Bell e scarto. Il servizio Sifting & Bell Test genera gli outcome correlati effettivamente usati nella valutazione, applica le perturbazioni annotate nei record e calcola CHSH, QBER e classificazione. Il Key Processing determina l'esito della chiave e ne produce la derivazione dimostrativa.

**Semantica della chiave**

> Si distingue il numero di round selezionati per la chiave, Nkey, dal numero di posizioni concordi dopo l'inversione convenzionale del bit di Bob, Nclean=Nkey−Nerr. Nel software tali grandezze sono esposte rispettivamente come raw_key_length e sifted_key_length. Quest'ultimo nome identifica quindi un filtro ideale dei bit discordanti, reso possibile dalla conoscenza globale della simulazione. La soglia quantitativa è applicata a Nclean; nella versione analizzata, il digest SHA-256 viene calcolato sul registro grezzo di Alice.

**Modello di Eve**

> I tipi randomize e intercept_resend sono mantenuti come identificatori distinti di scenario, ma nella baseline corrente condividono la stessa approssimazione: l'outcome di Bob è randomizzato sui round selezionati per l'attacco. Il confronto tra tali etichette non rappresenta pertanto il confronto tra due leggi fisiche differenti di intercettazione. Non sono simulati la base di Eve, il suo esito o lo stato reinviato.

**Validazione Qiskit**

> Il circuito di controllo prepara lo stato Φ+ mediante Hadamard e CNOT. Per le misure nel piano X–Z considerate, le correlazioni hanno segno opposto rispetto al singoletto del sampler principale, mentre la magnitudo CHSH ideale coincide. Il confronto è pertanto limitato a questa equivalenza sulle statistiche Bell e non valida l'intera pipeline, i modelli di perturbazione o la generazione di chiavi segrete.

**Persistenza**

> Il Result Store mantiene in memoria il risultato completo delle sessioni e salva su JSON i key record sintetici. Gli script sperimentali archiviano separatamente i dati tabellari e i riepiloghi. Il riavvio del servizio conserva i key record ma non ricostruisce le risposte complete delle sessioni precedenti.

## Questioni da saper spiegare alla discussione

- **Dove si trova la simulazione quantistica?** Nella distribuzione congiunta campionata dal modulo di valutazione; i servizi di sorgente/canale trasportano rappresentazioni simboliche e metadati.
- **Perché un programma classico ottiene CHSH > 2?** Perché campiona conoscendo entrambe le impostazioni; non rispetta il vincolo di generazione locale su cui si basa il limite di Bell.
- **La chiave è segreta e condivisa?** È una derivazione dimostrativa centralizzata; il progetto non dimostra concordanza e segretezza di due chiavi finali indipendenti.
- **Perché le due Eve si comportano allo stesso modo?** Perché la legge implementata è identica; i nomi distinguono gli scenari, non il meccanismo statistico.
- **Perché Qiskit dà il segno opposto?** Prepara Φ+; il sampler usa la statistica di Ψ− nelle stesse direzioni del piano X–Z.
- **Perché la perdita non aumenta il QBER?** Nel modello elimina round indipendentemente da basi ed esiti; non altera i sopravvissuti.
- **Le distanze sono quelle di una fibra reale?** Sono distanze equivalenti con un coefficiente scelto per la campagna, senza calibrazione completa su un collegamento fisico.
- **Cosa significa secure?** Superamento delle soglie operative programmate, non una garanzia di sicurezza composabile.
- **Perché microservizi?** Separazione funzionale, ispezionabilità e possibilità di sostituire componenti; non è stato dimostrato un vantaggio prestazionale rispetto a un monolite.
- **Qual è il risultato sostenuto dalle evidenze?** La realizzazione e verifica di una pipeline statistica modulare, con risultati coerenti con il modello e con una campagna automatizzata tracciabile a livello tabellare.
