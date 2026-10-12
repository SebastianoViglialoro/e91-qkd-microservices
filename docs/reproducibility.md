# Checklist Di Riproducibilità

Questa checklist riassume i comandi minimi per avviare, verificare e riprodurre i risultati finali del progetto `e91-qkd-microservices`.

## 1. Avvio Dei Microservizi

Dalla root del progetto:

```bash
docker compose up --build
```

In alternativa, se le immagini sono già state costruite:

```bash
docker compose up -d
```

Verifica dei container:

```bash
docker compose ps
```

Verifica API Gateway:

```bash
curl http://localhost:18000/health
```

## 2. Smoke Test End-To-End

Lo smoke test esegue:

- health check dell'API Gateway;
- simulazione baseline;
- simulazione con rumore degradato;
- simulazione con rumore insecure;
- verifica Mini KMS tramite `/keys/summary` e `/keys/latest`;
- verifica opzionale Qiskit tramite `/qiskit-chsh-test`.

Comando:

```bash
python scripts/smoke_test.py \
  --gateway-url http://localhost:18000 \
  --sifting-bell-test-url http://localhost:8009 \
  --shots 10000
```

Se si vuole rendere obbligatoria la disponibilità di Qiskit:

```bash
python scripts/smoke_test.py \
  --gateway-url http://localhost:18000 \
  --sifting-bell-test-url http://localhost:8009 \
  --shots 10000 \
  --require-qiskit
```

## 3. Dashboard

La dashboard è statica e comunica solo con l'API Gateway.

```bash
cd frontend
python3 -m http.server 5173
```

Aprire:

```text
http://localhost:5173
```

## 4. Campagna Sperimentale Finale

Prova ridotta:

```bash
python scripts/run_final_experiments.py \
  --gateway-url http://localhost:18000 \
  --shots 1000 \
  --repeats 2
```

Campagna completa usata per la tesi:

```bash
python scripts/run_final_experiments.py \
  --gateway-url http://localhost:18000 \
  --shots 10000 \
  --repeats 10
```

Output attesi:

```text
results/final/final_experiment_runs.csv
results/final/final_experiment_summary.csv
results/final/final_experiment_summary.json
```

## 5. Grafici Finali

Generazione dei grafici:

```bash
python scripts/plot_final_experiments.py
```

Output:

```text
results/final/plots/
```

I grafici di link loss includono sia l'asse in dB sia l'asse in chilometri totali:

```text
link_loss_total_db_vs_sifted_key_length.png
link_loss_total_db_vs_lost_pair_count.png
link_loss_total_db_vs_generated_key_rate.png
link_loss_total_distance_km_vs_sifted_key_length.png
link_loss_total_distance_km_vs_lost_pair_count.png
link_loss_total_distance_km_vs_generated_key_rate.png
```

## 6. Confronto Sampler Classico Vs Qiskit

```bash
python scripts/compare_final_samplers.py \
  --gateway-url http://localhost:18000 \
  --sifting-bell-test-url http://localhost:8009 \
  --shots 10000 \
  --shots-per-basis 2500 \
  --repeats 10
```

Output:

```text
results/final/final_sampler_comparison_runs.csv
results/final/final_sampler_comparison_summary.csv
results/final/final_sampler_comparison_summary.json
```

Il confronto va interpretato su `abs_chsh`, perché il segno di `chsh` può dipendere dalle convenzioni di stato, rotazioni e mapping dei bit.

## 7. File Da Conservare Per La Tesi

- `docs/chapter3_protocol_model_report.md`
- `docs/chapter4_architecture_report.md`
- `docs/chapter5_results_report.md`
- `docs/chapter5_final_campaign_report.md`
- `docs/architecture_diagram.md`
- `results/final/*.csv`
- `results/final/*.json`
- `results/final/plots/*.png`
- `frontend/`
- `scripts/`

## 8. Note

- Il modello delle basi resta `TWO_KEY_BASES_ONE_CHECK_BASIS`.
- Qiskit non è il motore della simulazione end-to-end: è una validazione circuitale opzionale della componente CHSH.
- Il Mini KMS è dimostrativo e non rappresenta un KMS industriale.
- La dashboard non contiene logica di simulazione: visualizza i risultati prodotti dai microservizi.
