# Capitolo 3 - Modello del protocollo E91 adottato nella tesi

## 1. Introduzione al capitolo

Il presente capitolo descrive il modello del protocollo E91 adottato nella tesi magistrale:

```text
Progettazione e sviluppo di un'architettura a microservizi per la simulazione del protocollo E91 di Quantum Key Distribution
```

L'obiettivo del capitolo è definire il riferimento teorico e metodologico su cui si basano l'architettura software del Capitolo 4 e la campagna sperimentale del Capitolo 5. In particolare, vengono descritti il ruolo dell'entanglement, la scelta delle basi di misura, la distinzione tra round usati per la generazione della chiave e round usati per il controllo di sicurezza, il calcolo del parametro CHSH, il calcolo del QBER e la classificazione finale delle sessioni.

Il modello adottato non ha l'obiettivo di rappresentare in modo completo tutti gli aspetti fisici di un sistema QKD reale. Si tratta invece di una baseline controllata, pensata per rendere espliciti i passaggi principali del protocollo E91 e per consentire una loro implementazione modulare in un'architettura a microservizi. Questa scelta permette di separare chiaramente il modello logico del protocollo dalle componenti software che lo realizzano.

## 2. Protocollo E91

Il protocollo E91, proposto da Artur Ekert nel 1991, è un protocollo di Quantum Key Distribution basato sull'uso di coppie di particelle entangled. A differenza di protocolli prepare-and-measure come BB84, in E91 la sicurezza è collegata alla presenza di correlazioni quantistiche non classiche tra le misure effettuate da Alice e Bob.

Nel modello generale, una sorgente produce coppie entangled e invia un qubit ad Alice e l'altro a Bob attraverso un canale quantistico. Alice e Bob scelgono basi di misura, misurano i rispettivi qubit e ottengono risultati casuali ma correlati. Successivamente, attraverso un canale classico autenticato, i due partecipanti comunicano le basi usate, ma non rivelano direttamente i bit destinati alla chiave finale.

Il protocollo può essere interpretato come una sequenza di fasi:

- generazione di coppie entangled da parte della sorgente;
- distribuzione dei qubit ad Alice e Bob tramite canale quantistico;
- scelta delle basi di misura;
- misura dei qubit;
- comunicazione classica delle basi;
- separazione dei round utili alla chiave dai round utili al test di sicurezza;
- stima della violazione Bell;
- stima del QBER;
- generazione della chiave finale, se le condizioni di sicurezza sono soddisfatte.

Il canale quantistico trasporta i qubit ed è la parte del sistema in cui possono manifestarsi attenuazione, rumore fisico o attacchi intenzionali. Il canale classico, invece, viene usato per il sifting e per la pubblicazione controllata delle informazioni necessarie a stimare la sicurezza. Nel modello adottato, il canale classico non rivela direttamente la chiave finale.

L'elemento distintivo di E91 è l'uso della violazione di una disuguaglianza di Bell come indicatore di sicurezza. Se le correlazioni osservate da Alice e Bob non possono essere spiegate da un modello classico locale, allora la presenza di entanglement è considerata preservata. Una riduzione significativa della violazione Bell, o un aumento del QBER, può indicare rumore eccessivo, attacco di Eve o perdita di affidabilità del canale.

## 3. Stato entangled e correlazioni

Il riferimento teorico del modello è lo stato di singoletto, spesso indicato nella forma:

```text
|ψ-> = (|01> - |10>) / sqrt(2)
```

Questo stato rappresenta una coppia di qubit massimamente entangled. Una proprietà importante del singoletto è l'anti-correlazione ideale quando Alice e Bob misurano lungo la stessa base. In termini operativi, se Alice e Bob scelgono la stessa direzione di misura, i loro outcome risultano idealmente opposti.

Nel simulatore, gli outcome sono rappresentati come valori:

```text
{-1, +1}
```

Quando le basi di misura non coincidono, la correlazione dipende dall'angolo relativo tra le due basi. Il modello adottato usa la relazione:

```text
E(a,b) = -cos(a - b)
```

dove:

- `a` è l'angolo della base di Alice;
- `b` è l'angolo della base di Bob;
- `E(a,b)` è il valore atteso della correlazione tra gli outcome.

Il segno negativo è coerente con l'uso dello stato di singoletto: misure sulla stessa base producono anti-correlazione ideale. Ad esempio, se `a = b`, allora:

```text
E(a,b) = -cos(0) = -1
```

Questo significa che il prodotto medio degli outcome di Alice e Bob è pari a `-1`, cioè gli outcome sono opposti. La relazione `E(a,b) = -cos(a - b)` è il nucleo del sampler classico usato nella pipeline principale del simulatore.

## 4. Modello delle basi adottato

Il modello finale delle basi adottato nella tesi è:

```text
basis_model = TWO_KEY_BASES_ONE_CHECK_BASIS
```

Questo modello usa tre possibili scelte di misura per Alice e tre per Bob. Due basi sono dedicate alla generazione della chiave, mentre una base è usata come base di controllo. Alcune combinazioni non-key vengono poi utilizzate per il calcolo del parametro CHSH.

Le basi di Alice sono:

| Base | Ruolo |
| --- | --- |
| `C` | check |
| `K0` | key |
| `K1` | key |

Le basi di Bob sono:

| Base | Ruolo |
| --- | --- |
| `K0` | key |
| `K1` | key |
| `C` | check |

La scelta di usare due basi per la chiave e una base di controllo deriva dall'esigenza di separare, nel modello software, i round destinati alla key extraction dai round destinati alla stima della sicurezza. Le basi key vengono usate quando Alice e Bob scelgono la stessa base; la base check e alcune combinazioni non coincidenti vengono invece usate per costruire il test CHSH.

Il modello è centralizzato nel codice in `shared/bases.py`, in modo che Alice, Bob, Classical Channel, Sifting & Bell Test e Key Processing utilizzino la stessa definizione di basi e la stessa logica di classificazione.

## 5. Key subset

Il `key_subset` contiene i round usati per generare la chiave grezza. Nel modello adottato, i round di chiave sono:

```text
K0/K0
K1/K1
```

Queste combinazioni corrispondono ai casi in cui Alice e Bob scelgono la stessa base di tipo key. L'uso di basi coincidenti è necessario perché, nel caso ideale, le misure sulla stessa base dello stato di singoletto producono anti-correlazione deterministica. Questa proprietà consente ad Alice e Bob di derivare bit coerenti dopo una correzione convenzionale.

Gli outcome sono inizialmente rappresentati come:

```text
-1, +1
```

Nel key-processing vengono convertiti in bit secondo la convenzione:

```text
-1 -> 0
+1 -> 1
```

Poiché lo stato di singoletto genera outcome idealmente anti-correlati sulla stessa base, il bit di Bob viene invertito prima del confronto e della costruzione della chiave:

```text
bob_corrected_bit = 1 - bob_bit
```

In questo modo, in assenza di rumore, Eve o errori di trasmissione, i bit di Alice e i bit corretti di Bob coincidono. Il risultato è una raw key binaria derivata dai round `K0/K0` e `K1/K1`.

## 6. Bell subset e CHSH

Il `bell_subset` contiene i round usati per stimare la violazione Bell. Nel modello finale non si usa una coppia separata di basi CHSH per Alice e Bob, ma una struttura a due basi key più una base check. Le combinazioni selezionate per CHSH sono:

```text
C/K0
C/C
K1/K0
K1/C
```

La formula implementata è:

```text
S = E(C,K0) + E(C,C) + E(K1,K0) - E(K1,C)
```

dove `E(A,B)` rappresenta la media dei prodotti degli outcome di Alice e Bob per la specifica combinazione di basi:

```text
E(A,B) = average(outcome_alice * outcome_bob)
```

Il parametro `S` è il valore CHSH stimato. Nel caso classico locale, il valore assoluto di CHSH è limitato da:

```text
|S| <= 2
```

Nel caso quantistico ideale, usando opportune basi di misura, il valore può avvicinarsi a:

```text
2√2 ≈ 2.828
```

Nel software vengono restituiti sia `chsh` sia `abs_chsh`. L'uso di `abs_chsh` è importante perché il segno del parametro può dipendere dalle convenzioni scelte per lo stato, per le rotazioni delle basi e per il mapping degli outcome. Ai fini della violazione Bell, il valore rilevante è il modulo.

Di conseguenza, un valore di `abs_chsh` superiore al limite classico indica che le correlazioni osservate sono compatibili con un comportamento quantistico non classico. Al contrario, una riduzione verso il limite classico può indicare perdita di entanglement, rumore elevato o perturbazione del canale.

## 7. QBER

Il QBER, Quantum Bit Error Rate, è calcolato sul `key_subset`, quindi solo sui round:

```text
K0/K0
K1/K1
```

Nel modello adottato, il QBER misura la frazione di bit in cui Alice e Bob, dopo la correzione dell'anti-correlazione del singoletto, non concordano. La formula è:

```text
QBER = error_count / compared_bits
```

dove:

- `compared_bits` è il numero di bit confrontabili nel key subset;
- `error_count` è il numero di bit discordanti dopo l'inversione del bit di Bob.

In condizioni ideali, il QBER atteso è pari a zero. L'aumento del QBER indica che una parte dei round di chiave è stata perturbata. Nel modello sperimentale della tesi, le soglie operative usate sono:

| Condizione | Interpretazione |
| --- | --- |
| `qber <= 0.08` | compatibile con stato secure, se CHSH è sufficiente |
| `qber > 0.15` | condizione insecure |

Queste soglie non rappresentano limiti universali di tutti i sistemi QKD, ma parametri operativi scelti per classificare la baseline sperimentale.

## 8. Classificazione della sessione

Ogni sessione viene classificata in base a `abs_chsh` e `qber`. Gli stati possibili sono:

- `secure`;
- `degraded`;
- `insecure`.

La classificazione usata nella baseline è:

| Stato | Condizione |
| --- | --- |
| `secure` | `abs_chsh >= 2.4` e `qber <= 0.08` |
| `degraded` | condizioni intermedie, con violazione Bell ridotta o QBER moderato |
| `insecure` | `abs_chsh <= 2.0` oppure `qber > 0.15` |

Lo stato `secure` indica che la violazione Bell è sufficientemente preservata e che il QBER è sotto la soglia operativa. Lo stato `degraded` indica una condizione intermedia: il sistema non è necessariamente compromesso in modo totale, ma non soddisfa più i requisiti per generare una chiave finale utilizzabile. Lo stato `insecure` indica invece perdita della violazione Bell o QBER oltre la soglia critica.

Le soglie `2.4`, `0.08` e `0.15` sono soglie operative della baseline software. Non devono essere interpretate come limiti fisici universali. Servono a rendere riproducibile la classificazione sperimentale e a mostrare il comportamento del sistema al variare di rumore, Eve e perdita di link.

## 9. Distinzione tra security_status e key_status

Il modello distingue due concetti:

```text
security_status
key_status
```

`security_status` descrive la sicurezza stimata della sessione sulla base di CHSH e QBER. `key_status`, invece, descrive l'esito operativo della generazione della chiave.

Questa distinzione è necessaria perché una sessione può essere sicura dal punto di vista di CHSH e QBER, ma non disporre di sufficiente materiale sifted per generare una chiave finale. Questo caso può verificarsi, ad esempio, in presenza di forte link loss: le coppie rimaste possono essere sicure, ma troppo poche per soddisfare la soglia minima richiesta.

Gli stati della chiave sono:

| key_status | Significato |
| --- | --- |
| `generated` | La sessione è secure e il materiale sifted è sufficiente. |
| `discarded_degraded` | La sessione è degraded e la chiave viene scartata. |
| `discarded` | La sessione è insecure e la chiave viene scartata. |
| `insufficient_key_material` | La sessione è secure, ma il materiale sifted è inferiore alla soglia minima. |

Nel progetto, la soglia minima è indicata dal parametro:

```text
min_sifted_key_length
```

Il valore di default è 256 bit. Se la sessione è secure e il materiale sifted supera tale soglia, il key-processing deriva una raw key e produce una chiave finale dimostrativa tramite SHA-256.

## 10. Rumore, Eve e link loss nel modello

Il modello distingue tre forme di degradazione o perturbazione:

- rumore fisico non intenzionale;
- attacco intenzionale di Eve;
- perdita di link dovuta ad attenuazione.

Il rumore è rappresentato come una perturbazione non intenzionale del canale quantistico. Nel simulatore sono presenti modelli simbolici come `bit_flip` e `depolarizing`. Il loro effetto è degradare le correlazioni e aumentare il QBER.

Eve rappresenta invece un attaccante intenzionale. I modelli `randomize` e `intercept_resend` sono astrazioni controllate che rompono o degradano le correlazioni tra Alice e Bob. Anche in questo caso, l'effetto atteso è una diminuzione di `abs_chsh` e un aumento del QBER.

La link loss ha un significato diverso. Essa rappresenta la perdita di coppie dovuta alla distanza e all'attenuazione del canale. La perdita di link:

- non aumenta direttamente il QBER;
- non modifica direttamente CHSH;
- riduce il numero di coppie utili;
- può ridurre il materiale disponibile per la chiave;
- può portare a `key_status = insufficient_key_material`.

La distinzione tra rumore, Eve e link loss è importante perché permette di interpretare correttamente i risultati sperimentali. Un canale può essere sicuro rispetto a CHSH e QBER ma poco produttivo in termini di chiave, oppure può avere abbastanza round utili ma risultare degradato o insicuro a causa di rumore o attacco.

## 11. Ruolo di Qiskit

Qiskit non è usato come motore dell'intera simulazione. Questa è una scelta progettuale esplicita della tesi. Il flusso principale del simulatore usa un sampler classico delle correlazioni dello stato di singoletto, basato sulla relazione:

```text
E(a,b) = -cos(a - b)
```

Qiskit viene usato solo come validazione circuitale della componente Bell/CHSH, tramite Qiskit AerSimulator. Il modulo Qiskit costruisce circuiti quantistici, prepara una Bell pair, applica rotazioni coerenti con le basi di misura, esegue le misure e calcola le correlazioni a partire dai counts.

Il confronto tra sampler classico e Qiskit deve essere interpretato sul valore:

```text
abs_chsh
```

Il segno di `chsh` può cambiare per convenzioni diverse di stato, rotazioni e mapping dei bit. Il modulo, invece, permette di confrontare la presenza della violazione Bell in modo coerente.

In questo modo Qiskit rimane confinato al ruolo previsto: strumento di verifica della componente Bell/CHSH, non centro dell'architettura e non sostituto della pipeline a microservizi.

## 12. Limiti del modello

Il modello adottato è volutamente semplificato. I principali limiti sono:

- il sampler principale è classico e riproduce le correlazioni ideali del singoletto, ma non simula ogni dettaglio fisico della misura quantistica;
- i modelli di rumore sono simbolici e non includono detector, dark counts, inefficienze, sincronizzazione temporale o altri effetti fisici;
- i modelli di Eve sono astrazioni controllate e non coprono l'intero spazio degli attacchi possibili a un sistema QKD reale;
- la link loss riduce probabilisticamente il numero di coppie utili, ma non modella una catena fisica completa di trasmissione e rivelazione;
- la generazione della chiave usa SHA-256 come dimostrazione semplificata di privacy amplification;
- non è implementata una fase completa di error correction;
- non è implementata una privacy amplification QKD con sicurezza composabile;
- non è presente hardware quantistico reale.

Questi limiti non invalidano il modello, ma ne definiscono il perimetro. L'obiettivo della tesi è progettare e sviluppare una piattaforma modulare per la simulazione e l'analisi del protocollo E91, non realizzare un sistema QKD fisico completo.

## 13. Collegamento al Capitolo 4

Il modello descritto in questo capitolo costituisce la base concettuale dell'architettura software presentata nel Capitolo 4. Ogni elemento del modello viene tradotto in una responsabilità applicativa:

- la sorgente entangled diventa il servizio `entangled-source`;
- il canale quantistico diventa il servizio `quantum-channel`;
- rumore, Eve e link loss vengono modellati come componenti separati o metadati del canale;
- Alice e Bob diventano servizi indipendenti di misura;
- il canale classico diventa il servizio `classical-channel`;
- il calcolo CHSH e QBER viene incapsulato in `sifting-bell-test`;
- la generazione della chiave viene gestita da `key-processing`;
- i risultati e i key record vengono salvati in `result-store` e nel Mini KMS.

Il Capitolo 4 mostra quindi come il modello del protocollo E91 venga realizzato attraverso una architettura a microservizi. Il Capitolo 5, successivamente, analizza sperimentalmente il comportamento del sistema al variare di rumore, Eve, attenuazione e soglia minima di materiale chiave.
