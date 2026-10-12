# Registrazione degli outcome e post-processing

Il simulatore resta un'infrastruttura statistica centralizzata a microservizi.
Non implementa località fisica, sicurezza device-independent o sicurezza composable.
Qiskit resta un controllo opzionale separato dalla pipeline ordinaria.

## Flusso

1. Il quantum channel applica il modello di perdita esistente e trasporta i flag di
   rumore/Eve. I round persi non arrivano alla scelta delle basi o al campionatore.
2. Alice e Bob ricevono separatamente `/select-bases`: ciascun receiver sceglie
   localmente la propria base con la distribuzione precedente. I record in questa
   fase contengono basi e metadati, ma nessun outcome provvisorio.
3. Dopo entrambe le risposte, l'orchestratore chiama
   `shared.outcome_sampler.sample_receiver_records`. Le selezioni vengono unite
   per `pair_id`. Si campiona una sola coppia per ogni round consegnato, secondo
   la legge preesistente E(a,b) = -cos(a-b). Le funzioni di campionamento e le
   trasformazioni di rumore ed Eve sono state spostate senza cambiarne la logica:
   prima rumore, poi Eve, sul risultato di Bob. I flag non vengono ricampionati.
4. L'orchestratore invia i record completi ai rispettivi receiver tramite
   `/measure`. Il receiver valida sessione, parte, base, angolo, ruolo, unicità
   degli identificatori e outcome ±1, quindi restituisce i record definitivi.
   La registrazione è nei record della risposta, non in un nuovo archivio
   persistente. I servizi restano stateless: il coordinatore trasporta le basi
   selezionate, senza una prova crittografica della loro provenienza.
5. Solo queste risposte definitive entrano nel classical channel. Il sifting usa
   gli outcome ricevuti per QBER, correlazioni, CHSH e key_records; non genera
   outcome e non applica di nuovo rumore/Eve.
6. Il key processing conserva la precedente correzione: SHA-256 dei soli bit
   concordi dopo inversione convenzionale di Bob, come dimostrazione centralizzata.

## Contratti e compatibilità

L'API esterna dell'orchestratore e i risultati non cambiano. Nessun campo dei
record definitivi viene rinominato. Nuovo endpoint interno `/select-bases` in
entrambi i receiver, con la precedente richiesta `{session_id, qubits}`.
La risposta ha `{session_id, measurements}`, temporaneamente senza `outcome`.

`/measure` mantiene l'involucro `{session_id, qubits}`, ma richiede ora in `qubits`
i record completi restituiti dalla selezione, arricchiti con `outcome`. Chiamanti
esterni che inviavano soltanto qubit simbolici devono adottare le due fasi;
le vecchie richieste vengono rifiutate con 422 anziché produrre outcome fittizi.
È necessario ricostruire e aggiornare insieme receiver, orchestratore e sifting.
Il Dockerfile dell'orchestratore usa il contesto root per includere il sampler.

## Verifiche e limiti della riproducibilità

Eseguire `.venv/bin/python -m unittest discover -s tests -v`.
I test confrontano esattamente outcome, metriche e chiavi con un sampler precedente
congelato, a parità di basi, flag e sequenza casuale, per tutte le combinazioni di
rumore/Eve. Verificano anche distribuzione, QBER e CHSH dai record, registrazione
senza ricampionamento, classificazioni, perdita prima della misura e pipeline HTTP
in memoria. L'archivio dei risultati è sostituito soltanto nei test da uno store in
memoria, quindi nessun risultato sperimentale viene scritto.

I test sul CSV salvato verificano le decisioni delle 360 righe: 228 secure,
91 degraded, 41 insecure, 218 generated, 10 insufficient_key_material. Non sono
una nuova campagna e non attestano nuovi risultati sperimentali.

Prima si campionavano nel sifting i round Bell e poi quelli di chiave; ora vengono
campionati tutti i round consegnati nell'ordine dei record Alice, inclusi quelli
successivamente scartati per combinazione di basi. Cambiano processo e ordine di
consumo della casualità. La legge statistica e le regole decisionali rimangono le
stesse, ma un seed globale o una nuova campagna non garantiscono gli stessi singoli
outcome, digest o conteggi aggregati. I dati consegnati restano risultati storici
della versione precedente, non vanno attribuiti a una riesecuzione del refactoring.

## Indicazioni per la tesi

Aggiornare flusso architetturale/diagramma di sequenza, descrizione dei receiver,
responsabilità dell'orchestratore e paragrafo sul sifting. Formula consigliata:
«I receiver scelgono localmente le basi; una volta note entrambe le scelte,
il simulatore centralizzato campiona congiuntamente gli outcome e li associa ai
record registrati dai receiver. QBER e CHSH sono calcolati sugli stessi record,
senza ricampionamento nel post-processing.»

Distinguere scelta locale delle basi da generazione congiunta centralizzata;
precisare che la registrazione non implica persistenza durevole o misura fisica
locale. Mantenere la descrizione dimostrativa del filtraggio e dell'hash, e indicare
la versione della pipeline che ha prodotto la campagna consegnata. L'abstract non
richiede modifiche per i vincoli indicati; evitare interpretazioni che attribuiscano
ai receiver generatori fisicamente indipendenti o a Qiskit il ruolo di motore E2E.
