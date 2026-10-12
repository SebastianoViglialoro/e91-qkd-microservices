# Diagramma decisionale per il §3.3

Inserire dopo le formule di classificazione. PDF e SVG sono vettoriali; il PNG è a 400 dpi (2880 × 1880 pixel).

**Didascalia:** Relazione tra classificazione della sessione (`security_status`) ed esito della generazione della chiave (`key_status`). Solo le sessioni `secure` accedono al controllo quantitativo sul materiale sifted: la chiave viene generata se N_sifted ≥ L_min, altrimenti l’esito è `insufficient_key_material`. Le sessioni `degraded` e `insecure` conducono rispettivamente a `discarded_degraded` e `discarded`. N_sifted indica `sifted_key_length` e L_min indica la soglia `min_sifted_key_length`. La classificazione iniziale tiene conto di CHSH, QBER e della disponibilità della stima CHSH, secondo le regole descritte nel testo.

N_sifted corrisponde a `sifted_key_length`; L_min a `min_sifted_key_length`. I quattro nodi terminali sono valori di `key_status`. La generazione resta dimostrativa.

**Richiamo ai risultati da inserire nel testo:** Nella campagna sperimentale, alle 228 sessioni classificate come `secure` corrispondono 218 chiavi generate; le restanti 10 sessioni presentano materiale sifted insufficiente.

Il diagramma è stato confrontato con `classify_security` in `sifting-bell-test/app/main.py` e `generate_key` in `key-processing/app/main.py`. Nessuna campagna è stata rieseguita.

Rigenerazione:

```sh
MPLCONFIGDIR=/tmp/e91-mpl .venv/bin/python scripts/draw_thesis_status_decision.py
```
