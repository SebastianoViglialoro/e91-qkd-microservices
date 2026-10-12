# Figura per il Capitolo 3, §3.4

Inserire dopo la descrizione del flusso della pipeline, a larghezza del testo (circa 16 cm).

- `architettura_pipeline_tesi.pdf`: vettoriale per LaTeX e stampa.
- `architettura_pipeline_tesi.svg`: vettoriale modificabile.
- `architettura_pipeline_tesi.png`: 2520 × 3120 pixel, 400 dpi.

**Didascalia:** Architettura logica della pipeline E91 a microservizi, articolata in piano quantistico simulato, piano classico e infrastruttura software. Alice e Bob scelgono le basi e registrano gli outcome prodotti dal campionamento congiunto centralizzato eseguito dall’Orchestrator. Gli stessi outcome alimentano il calcolo di CHSH e QBER e la derivazione dimostrativa della chiave. Le frecce continue rappresentano il flusso logico dei dati; la freccia tratteggiata indica l’esecuzione del modello di campionamento da parte dell’Orchestrator.

La doppia rappresentazione di Alice e Bob indica due fasi degli stessi receiver, non servizi aggiuntivi. Noise/Eve selezionano i round interessati e producono flag; il campionatore applica le perturbazioni. Le frecce continue rappresentano il flusso logico dei dati, inoltrati dall’Orchestrator; la freccia tratteggiata ne esplicita la responsabilità di campionamento. La Dashboard consulta il Result Store tramite API Gateway (passaggio omesso per leggibilità). Il Result Store riceve il risultato completo della sessione, non soltanto la chiave.

Il campionamento è statistico e centralizzato: la separazione dei receiver non implica località fisica o sicurezza device-independent. Qiskit rimane una verifica opzionale separata dal flusso principale.

Rigenerazione dalla radice del repository:

```sh
MPLCONFIGDIR=/tmp/e91-mpl .venv/bin/python scripts/draw_thesis_architecture.py
```

Le descrizioni funzionali sono in italiano: «selezione della base» corrisponde a `/select-bases` e «registrazione outcome» a `/measure`. I box inferiori Alice/Bob rappresentano la seconda fase degli stessi receiver. Il sottotitolo «perturbazioni» di Noise/Eve indica il ruolo dei modelli: i servizi selezionano i round interessati, mentre le trasformazioni degli outcome sono applicate nel campionamento congiunto.
