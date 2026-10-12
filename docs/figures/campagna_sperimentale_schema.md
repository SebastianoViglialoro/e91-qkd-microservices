# Schema compatto della campagna — Capitolo 5, §5.1

Dimensioni native: 16,5 × 3,8 cm, esclusa la didascalia. Inserire a larghezza del testo senza dedicare una pagina alla figura. PDF e SVG sono vettoriali; PNG a 400 dpi.

**Didascalia:** Famiglie di scenari della campagna sperimentale: baseline, perdita di link, rumore, attacco Eve e condizioni combinate. La campagna comprende 36 scenari, ciascuno eseguito 10 volte, per un totale di 360 run.

I gruppi sono famiglie di esperimenti, non fasi consecutive della stessa run. Verifica sul CSV salvato: 1 baseline, 4 Link Loss, 12 Noise (6 bit_flip e 6 depolarizing), 12 Eve (6 randomize e 6 intercept_resend), 7 Combined (4 Noise + Eve e 3 Link Loss + Noise + Eve).

Il disegno non esegue simulazioni e non modifica i risultati. Rigenerazione:

```sh
MPLCONFIGDIR=/tmp/e91-mpl .venv/bin/python scripts/draw_thesis_campaign.py
```
