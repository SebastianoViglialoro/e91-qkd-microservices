# Report per Capitolo 5

Questo report raccoglie i dati reali presenti nel repository `e91-qkd-microservices` e li organizza come base tecnica per il Capitolo 5 della tesi magistrale. La pipeline principale analizzata è la pipeline Python/FastAPI a microservizi; Qiskit/AerSimulator è considerato solo come validazione circuitale opzionale della componente Bell/CHSH.

## 1. Campagna finale

Script verificato: `scripts/run_final_experiments.py`.

Comando previsto per la campagna completa:

```bash
python3 scripts/run_final_experiments.py --gateway-url http://localhost:18000 --shots 10000 --repeats 10
```

| Voce | Valore |
| --- | --- |
| Scenari finali | 36 |
| Ripetizioni per scenario | 10 |
| Run totali | 360 |
| Run fallite / errori | 0 |
| Cartella output | `results/final/` |
| File run CSV | `results/final/final_experiment_runs.csv` |
| File summary CSV | `results/final/final_experiment_summary.csv` |
| File summary JSON | `results/final/final_experiment_summary.json` |
| Cartella grafici | `results/final/plots/` |
| Numero PNG finali | 32 |

File di confronto sampler verificati: `results/final/final_sampler_comparison_runs.csv`, `results/final/final_sampler_comparison_summary.csv`, `results/final/final_sampler_comparison_summary.json`.

## 2. Scenari sperimentali

La tabella seguente elenca tutti gli scenari presenti in `final_experiment_runs.csv`. La famiglia è ricostruita dal campo reale `scenario_group`.

| scenario_name | famiglia | shots | repeats | link_loss | dist A km | dist B km | loss dB | link_status | noise | noise_type | noise_level | eve | attack_type | eve_prob | min_key |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | baseline | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | False | randomize | 0.00 | 256 |
| link_nominal_25_25 | link_loss | 10000 | 10 | True | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | False | randomize | 0.00 | 256 |
| link_degraded_150_150 | link_loss | 10000 | 10 | True | 150.0 | 150.0 | 6.00 | degraded | False | bit_flip | 0.00 | False | randomize | 0.00 | 256 |
| link_critical_200_200 | link_loss | 10000 | 10 | True | 200.0 | 200.0 | 8.00 | critical | False | bit_flip | 0.00 | False | randomize | 0.00 | 256 |
| link_critical_high_threshold | link_loss | 10000 | 10 | True | 200.0 | 200.0 | 8.00 | critical | False | bit_flip | 0.00 | False | randomize | 0.00 | 3000 |
| noise_bit_flip_0.00 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.00 | False | randomize | 0.00 | 256 |
| noise_bit_flip_0.02 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.02 | False | randomize | 0.00 | 256 |
| noise_bit_flip_0.05 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.05 | False | randomize | 0.00 | 256 |
| noise_bit_flip_0.10 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.10 | False | randomize | 0.00 | 256 |
| noise_bit_flip_0.20 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.20 | False | randomize | 0.00 | 256 |
| noise_bit_flip_0.25 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.25 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.00 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.00 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.02 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.02 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.05 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.05 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.10 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.10 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.20 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.20 | False | randomize | 0.00 | 256 |
| noise_depolarizing_0.25 | noise | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | depolarizing | 0.25 | False | randomize | 0.00 | 256 |
| eve_randomize_0.00 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.00 | 256 |
| eve_randomize_0.02 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.02 | 256 |
| eve_randomize_0.05 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.05 | 256 |
| eve_randomize_0.10 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.10 | 256 |
| eve_randomize_0.20 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.20 | 256 |
| eve_randomize_0.25 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | randomize | 0.25 | 256 |
| eve_intercept_resend_0.00 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.00 | 256 |
| eve_intercept_resend_0.02 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.02 | 256 |
| eve_intercept_resend_0.05 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.05 | 256 |
| eve_intercept_resend_0.10 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.10 | 256 |
| eve_intercept_resend_0.20 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.20 | 256 |
| eve_intercept_resend_0.25 | eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | False | bit_flip | 0.00 | True | intercept_resend | 0.25 | 256 |
| combined_0.02_0.02 | combined_noise_eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.02 | True | intercept_resend | 0.02 | 256 |
| combined_0.05_0.05 | combined_noise_eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.05 | True | intercept_resend | 0.05 | 256 |
| combined_0.10_0.10 | combined_noise_eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.10 | True | intercept_resend | 0.10 | 256 |
| combined_0.15_0.15 | combined_noise_eve | 10000 | 10 | False | 25.0 | 25.0 | 1.00 | nominal | True | bit_flip | 0.15 | True | intercept_resend | 0.15 | 256 |
| link_noise_eve_low | combined_link_noise_eve | 10000 | 10 | True | 150.0 | 150.0 | 6.00 | degraded | True | bit_flip | 0.02 | True | intercept_resend | 0.02 | 256 |
| link_noise_eve_medium | combined_link_noise_eve | 10000 | 10 | True | 150.0 | 150.0 | 6.00 | degraded | True | bit_flip | 0.05 | True | intercept_resend | 0.05 | 256 |
| link_noise_eve_high | combined_link_noise_eve | 10000 | 10 | True | 150.0 | 150.0 | 6.00 | degraded | True | bit_flip | 0.10 | True | intercept_resend | 0.10 | 256 |

## 3. Risultati globali

| Metrica | Valore |
| --- | --- |
| Totale run | 360 |
| Totale scenari | 36 |
| Ripetizioni per scenario | 10 |
| Numero errori | 0 |
| security_status secure | 228 |
| security_status degraded | 91 |
| security_status insecure | 41 |
| key_status generated | 218 |
| key_status discarded | 41 |
| key_status discarded_degraded | 91 |
| key_status insufficient_key_material | 10 |
| Run mancanti/anomale | nessuna nei CSV finali |

### Risultati aggregati per scenario

Le colonne `sifted_key_length_std` e `lost_pairs_std` non sono presenti in `final_experiment_summary.csv`; sono state ricostruite dai raw run in `final_experiment_runs.csv`.

| scenario_name | group | abs_mean | abs_std | qber_mean | qber_std | sifted_mean | sifted_std | lost_mean | lost_std | loss_dB | security counts | key counts | gen_rate | nota |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | baseline | 2.8291 | 0.0332 | 0.0000 | 0.0000 | 2235.3 | 41.5 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Baseline ideale: CHSH vicino a 2√2, QBER nullo, chiavi generate. |
| link_nominal_25_25 | link_loss_sweep | 2.8170 | 0.0569 | 0.0000 | 0.0000 | 1753.1 | 51.9 | 2066.0 | 43.1 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| link_degraded_150_150 | link_loss_sweep | 2.8433 | 0.1025 | 0.0000 | 0.0000 | 557.0 | 20.7 | 7502.2 | 22.7 | 6.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| link_critical_200_200 | link_loss_sweep | 2.7752 | 0.1084 | 0.0000 | 0.0000 | 353.5 | 16.5 | 8416.5 | 17.8 | 8.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| link_critical_high_threshold | link_loss_sweep | 2.8427 | 0.0696 | 0.0000 | 0.0000 | 349.5 | 16.1 | 8410.9 | 31.1 | 8.00 | secure:10, degraded:0, insecure:0 | generated:0, discarded_degraded:0, discarded:0, insufficient:10 | 0.00 | Canale secure ma materiale sifted insufficiente per la soglia richiesta. |
| noise_bit_flip_0.00 | noise_sweep_bit_flip | 2.8180 | 0.0252 | 0.0000 | 0.0000 | 2210.8 | 30.0 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| noise_bit_flip_0.02 | noise_sweep_bit_flip | 2.6998 | 0.0443 | 0.0205 | 0.0020 | 2185.2 | 32.0 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| noise_bit_flip_0.05 | noise_sweep_bit_flip | 2.5397 | 0.0318 | 0.0506 | 0.0041 | 2101.0 | 43.6 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| noise_bit_flip_0.10 | noise_sweep_bit_flip | 2.2891 | 0.0376 | 0.0965 | 0.0067 | 2024.4 | 27.0 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| noise_bit_flip_0.20 | noise_sweep_bit_flip | 1.6743 | 0.0632 | 0.1969 | 0.0073 | 1774.9 | 52.8 | 0.0 | 0.0 | 1.00 | secure:0, degraded:0, insecure:10 | generated:0, discarded_degraded:0, discarded:10, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |
| noise_bit_flip_0.25 | noise_sweep_bit_flip | 1.3726 | 0.0514 | 0.2465 | 0.0116 | 1678.0 | 40.5 | 0.0 | 0.0 | 1.00 | secure:0, degraded:0, insecure:10 | generated:0, discarded_degraded:0, discarded:10, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |
| noise_depolarizing_0.00 | noise_sweep_depolarizing | 2.8242 | 0.0619 | 0.0000 | 0.0000 | 2226.4 | 29.6 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| noise_depolarizing_0.02 | noise_sweep_depolarizing | 2.7894 | 0.0564 | 0.0105 | 0.0019 | 2208.9 | 46.6 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| noise_depolarizing_0.05 | noise_sweep_depolarizing | 2.6910 | 0.0475 | 0.0247 | 0.0038 | 2152.1 | 42.7 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| noise_depolarizing_0.10 | noise_sweep_depolarizing | 2.5421 | 0.0508 | 0.0493 | 0.0053 | 2124.1 | 50.3 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| noise_depolarizing_0.20 | noise_sweep_depolarizing | 2.2724 | 0.0469 | 0.1025 | 0.0056 | 1978.8 | 37.9 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| noise_depolarizing_0.25 | noise_sweep_depolarizing | 2.1138 | 0.0455 | 0.1268 | 0.0044 | 1952.6 | 22.9 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| eve_randomize_0.00 | eve_sweep_randomize | 2.8284 | 0.0279 | 0.0000 | 0.0000 | 2227.1 | 55.2 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| eve_randomize_0.02 | eve_sweep_randomize | 2.8062 | 0.0442 | 0.0100 | 0.0021 | 2187.7 | 49.0 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_randomize_0.05 | eve_sweep_randomize | 2.6927 | 0.0428 | 0.0250 | 0.0035 | 2144.3 | 29.5 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_randomize_0.10 | eve_sweep_randomize | 2.5650 | 0.0451 | 0.0508 | 0.0032 | 2093.5 | 35.2 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_randomize_0.20 | eve_sweep_randomize | 2.2720 | 0.0471 | 0.1019 | 0.0074 | 2009.5 | 28.2 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| eve_randomize_0.25 | eve_sweep_randomize | 2.1032 | 0.0686 | 0.1240 | 0.0060 | 1948.0 | 32.8 | 0.0 | 0.0 | 1.00 | secure:0, degraded:9, insecure:1 | generated:0, discarded_degraded:9, discarded:1, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |
| eve_intercept_resend_0.00 | eve_sweep_intercept_resend | 2.8431 | 0.0639 | 0.0000 | 0.0000 | 2201.8 | 53.6 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run secure con chiave generata. |
| eve_intercept_resend_0.02 | eve_sweep_intercept_resend | 2.7692 | 0.0356 | 0.0108 | 0.0027 | 2196.0 | 27.8 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_intercept_resend_0.05 | eve_sweep_intercept_resend | 2.7035 | 0.0333 | 0.0258 | 0.0032 | 2161.9 | 32.6 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_intercept_resend_0.10 | eve_sweep_intercept_resend | 2.5264 | 0.0456 | 0.0504 | 0.0044 | 2117.8 | 29.5 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| eve_intercept_resend_0.20 | eve_sweep_intercept_resend | 2.2959 | 0.0555 | 0.1008 | 0.0071 | 1988.2 | 57.4 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| eve_intercept_resend_0.25 | eve_sweep_intercept_resend | 2.1206 | 0.0398 | 0.1265 | 0.0089 | 1949.6 | 45.5 | 0.0 | 0.0 | 1.00 | secure:0, degraded:10, insecure:0 | generated:0, discarded_degraded:10, discarded:0, insufficient:0 | 0.00 | Scenario degradato: chiave scartata in parte o totalmente. |
| combined_0.02_0.02 | combined_noise_eve | 2.6519 | 0.0421 | 0.0296 | 0.0028 | 2168.7 | 50.1 | 0.0 | 0.0 | 1.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| combined_0.05_0.05 | combined_noise_eve | 2.4207 | 0.0430 | 0.0734 | 0.0072 | 2063.8 | 36.7 | 0.0 | 0.0 | 1.00 | secure:7, degraded:3, insecure:0 | generated:7, discarded_degraded:3, discarded:0, insufficient:0 | 0.70 | Scenario degradato: chiave scartata in parte o totalmente. |
| combined_0.10_0.10 | combined_noise_eve | 2.0057 | 0.0548 | 0.1381 | 0.0080 | 1913.3 | 33.5 | 0.0 | 0.0 | 1.00 | secure:0, degraded:4, insecure:6 | generated:0, discarded_degraded:4, discarded:6, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |
| combined_0.15_0.15 | combined_noise_eve | 1.6682 | 0.0633 | 0.2018 | 0.0101 | 1771.8 | 38.8 | 0.0 | 0.0 | 1.00 | secure:0, degraded:0, insecure:10 | generated:0, discarded_degraded:0, discarded:10, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |
| link_noise_eve_low | combined_link_noise_eve | 2.6671 | 0.1004 | 0.0306 | 0.0108 | 534.1 | 17.3 | 7484.9 | 33.8 | 6.00 | secure:10, degraded:0, insecure:0 | generated:10, discarded_degraded:0, discarded:0, insufficient:0 | 1.00 | Tutte le run generano chiave secondo le soglie operative. |
| link_noise_eve_medium | combined_link_noise_eve | 2.3604 | 0.0918 | 0.0729 | 0.0071 | 524.5 | 24.4 | 7482.5 | 37.0 | 6.00 | secure:1, degraded:9, insecure:0 | generated:1, discarded_degraded:9, discarded:0, insufficient:0 | 0.10 | Scenario degradato: chiave scartata in parte o totalmente. |
| link_noise_eve_high | combined_link_noise_eve | 2.0477 | 0.0955 | 0.1453 | 0.0235 | 470.4 | 29.7 | 7501.9 | 37.6 | 6.00 | secure:0, degraded:6, insecure:4 | generated:0, discarded_degraded:6, discarded:4, insufficient:0 | 0.00 | Scenario con run insecure: CHSH/QBER oltre soglie operative. |

## 4. Baseline

| Metrica | Valore |
| --- | --- |
| abs_chsh_mean ± std | 2.8291 ± 0.0332 |
| qber_mean ± std | 0.0000 ± 0.0000 |
| sifted_key_length_mean ± std | 2235.3 ± 41.5 |
| lost_pairs_mean ± std | 0.0 ± 0.0 |
| security_status counts | secure:10 |
| key_status counts | generated:10 |
| generated_key_rate | 1.00 |

Interpretazione: la baseline è coerente con il modello ideale E91. Il valore medio di `abs_chsh` è vicino a `2√2`, il QBER è nullo nei dati finali e tutte le run generano una chiave perché il materiale sifted supera `min_sifted_key_length = 256`.

## 5. Perdita di link

| scenario | dist A/B | loss dB | trans | link_status | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| link_nominal_25_25 | 25/25 | 1.00 | 0.7943 | nominal | 2.8170 ± 0.0569 | 0.0000 ± 0.0000 | 1753.1 | 2066.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| link_degraded_150_150 | 150/150 | 6.00 | 0.2512 | degraded | 2.8433 ± 0.1025 | 0.0000 ± 0.0000 | 557.0 | 7502.2 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| link_critical_200_200 | 200/200 | 8.00 | 0.1585 | critical | 2.7752 ± 0.1084 | 0.0000 ± 0.0000 | 353.5 | 8416.5 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| link_critical_high_threshold | 200/200 | 8.00 | 0.1585 | critical | 2.8427 ± 0.0696 | 0.0000 ± 0.0000 | 349.5 | 8410.9 | S:10 D:0 I:0 | G:0 DD:0 X:0 IK:10 | 0.00 |

Interpretazione: gli scenari di link loss confermano che la perdita di link riduce principalmente il numero di coppie sopravvissute e quindi il materiale sifted disponibile. Nei dati finali il QBER resta nullo negli scenari di sola attenuazione, perché la link loss non viene modellata come rumore sui round sopravvissuti. Lo scenario `link_critical_high_threshold` mostra una sessione sicura dal punto di vista CHSH/QBER ma senza chiave finale, a causa della soglia `min_sifted_key_length = 3000`.

## 6. Rumore non intenzionale

### Noise type: bit_flip
| scenario | noise_type | noise_level | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_bit_flip_0.00 | bit_flip | 0.00 | 2.8180 ± 0.0252 | 0.0000 ± 0.0000 | 2210.8 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_bit_flip_0.02 | bit_flip | 0.02 | 2.6998 ± 0.0443 | 0.0205 ± 0.0020 | 2185.2 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_bit_flip_0.05 | bit_flip | 0.05 | 2.5397 ± 0.0318 | 0.0506 ± 0.0041 | 2101.0 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_bit_flip_0.10 | bit_flip | 0.10 | 2.2891 ± 0.0376 | 0.0965 ± 0.0067 | 2024.4 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |
| noise_bit_flip_0.20 | bit_flip | 0.20 | 1.6743 ± 0.0632 | 0.1969 ± 0.0073 | 1774.9 | 0.0 | S:0 D:0 I:10 | G:0 DD:0 X:10 IK:0 | 0.00 |
| noise_bit_flip_0.25 | bit_flip | 0.25 | 1.3726 ± 0.0514 | 0.2465 ± 0.0116 | 1678.0 | 0.0 | S:0 D:0 I:10 | G:0 DD:0 X:10 IK:0 | 0.00 |

### Noise type: depolarizing
| scenario | noise_type | noise_level | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_depolarizing_0.00 | depolarizing | 0.00 | 2.8242 ± 0.0619 | 0.0000 ± 0.0000 | 2226.4 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_depolarizing_0.02 | depolarizing | 0.02 | 2.7894 ± 0.0564 | 0.0105 ± 0.0019 | 2208.9 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_depolarizing_0.05 | depolarizing | 0.05 | 2.6910 ± 0.0475 | 0.0247 ± 0.0038 | 2152.1 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_depolarizing_0.10 | depolarizing | 0.10 | 2.5421 ± 0.0508 | 0.0493 ± 0.0053 | 2124.1 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| noise_depolarizing_0.20 | depolarizing | 0.20 | 2.2724 ± 0.0469 | 0.1025 ± 0.0056 | 1978.8 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |
| noise_depolarizing_0.25 | depolarizing | 0.25 | 2.1138 ± 0.0455 | 0.1268 ± 0.0044 | 1952.6 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |

Interpretazione: `bit_flip` produce una degradazione più severa, con passaggio a `degraded` già a `noise_level = 0.10` e a `insecure` da `0.20`. Il modello `depolarizing` degrada più gradualmente: resta secure fino a `0.10` e diventa degraded a `0.20` e `0.25`.

## 7. Eve

### Attack type: randomize
| scenario | attack_type | eve_prob | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eve_randomize_0.00 | randomize | 0.00 | 2.8284 ± 0.0279 | 0.0000 ± 0.0000 | 2227.1 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_randomize_0.02 | randomize | 0.02 | 2.8062 ± 0.0442 | 0.0100 ± 0.0021 | 2187.7 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_randomize_0.05 | randomize | 0.05 | 2.6927 ± 0.0428 | 0.0250 ± 0.0035 | 2144.3 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_randomize_0.10 | randomize | 0.10 | 2.5650 ± 0.0451 | 0.0508 ± 0.0032 | 2093.5 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_randomize_0.20 | randomize | 0.20 | 2.2720 ± 0.0471 | 0.1019 ± 0.0074 | 2009.5 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |
| eve_randomize_0.25 | randomize | 0.25 | 2.1032 ± 0.0686 | 0.1240 ± 0.0060 | 1948.0 | 0.0 | S:0 D:9 I:1 | G:0 DD:9 X:1 IK:0 | 0.00 |

### Attack type: intercept_resend
| scenario | attack_type | eve_prob | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eve_intercept_resend_0.00 | intercept_resend | 0.00 | 2.8431 ± 0.0639 | 0.0000 ± 0.0000 | 2201.8 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_intercept_resend_0.02 | intercept_resend | 0.02 | 2.7692 ± 0.0356 | 0.0108 ± 0.0027 | 2196.0 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_intercept_resend_0.05 | intercept_resend | 0.05 | 2.7035 ± 0.0333 | 0.0258 ± 0.0032 | 2161.9 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_intercept_resend_0.10 | intercept_resend | 0.10 | 2.5264 ± 0.0456 | 0.0504 ± 0.0044 | 2117.8 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| eve_intercept_resend_0.20 | intercept_resend | 0.20 | 2.2959 ± 0.0555 | 0.1008 ± 0.0071 | 1988.2 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |
| eve_intercept_resend_0.25 | intercept_resend | 0.25 | 2.1206 ± 0.0398 | 0.1265 ± 0.0089 | 1949.6 | 0.0 | S:0 D:10 I:0 | G:0 DD:10 X:0 IK:0 | 0.00 |

Interpretazione: l’aumento della probabilità di attacco riduce `abs_chsh` e aumenta `qber`. In entrambi i modelli la transizione a degraded avviene intorno a probabilità 0.20; nel caso `randomize_0.25` compare anche una run insecure. Il confronto deve essere interpretato come modello simbolico di perturbazione intenzionale, non come simulazione completa di tutti gli attacchi QKD.

## 8. Scenari combinati

### Noise + Eve
| scenario | params | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combined_0.02_0.02 | noise bit_flip=0.02; eve intercept_resend=0.02 | 2.6519 ± 0.0421 | 0.0296 ± 0.0028 | 2168.7 | 0.0 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| combined_0.05_0.05 | noise bit_flip=0.05; eve intercept_resend=0.05 | 2.4207 ± 0.0430 | 0.0734 ± 0.0072 | 2063.8 | 0.0 | S:7 D:3 I:0 | G:7 DD:3 X:0 IK:0 | 0.70 |
| combined_0.10_0.10 | noise bit_flip=0.10; eve intercept_resend=0.10 | 2.0057 ± 0.0548 | 0.1381 ± 0.0080 | 1913.3 | 0.0 | S:0 D:4 I:6 | G:0 DD:4 X:6 IK:0 | 0.00 |
| combined_0.15_0.15 | noise bit_flip=0.15; eve intercept_resend=0.15 | 1.6682 ± 0.0633 | 0.2018 ± 0.0101 | 1771.8 | 0.0 | S:0 D:0 I:10 | G:0 DD:0 X:10 IK:0 | 0.00 |

### Link loss + Noise + Eve
| scenario | params | abs CHSH | QBER | Sifted mean | Lost mean | Security counts | Key counts | Gen rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| link_noise_eve_low | link 6.0 dB; noise bit_flip=0.02; eve intercept_resend=0.02 | 2.6671 ± 0.1004 | 0.0306 ± 0.0108 | 534.1 | 7484.9 | S:10 D:0 I:0 | G:10 DD:0 X:0 IK:0 | 1.00 |
| link_noise_eve_medium | link 6.0 dB; noise bit_flip=0.05; eve intercept_resend=0.05 | 2.3604 ± 0.0918 | 0.0729 ± 0.0071 | 524.5 | 7482.5 | S:1 D:9 I:0 | G:1 DD:9 X:0 IK:0 | 0.10 |
| link_noise_eve_high | link 6.0 dB; noise bit_flip=0.10; eve intercept_resend=0.10 | 2.0477 ± 0.0955 | 0.1453 ± 0.0235 | 470.4 | 7501.9 | S:0 D:6 I:4 | G:0 DD:6 X:4 IK:0 | 0.00 |

Interpretazione: gli scenari combinati mostrano l’effetto cumulativo delle degradazioni. `combined_0.05_0.05` produce un esito misto, con generated key rate pari a 0.70. A `combined_0.10_0.10` la media CHSH è vicina al limite classico e compaiono run insecure. Quando si aggiunge anche la link loss a 6 dB, il materiale sifted si riduce fortemente e già lo scenario medium genera chiave solo in 1 run su 10.

## 9. Validazione Qiskit

Codice verificato: `sifting-bell-test/app/qiskit_sampler.py`, endpoint esposto in `sifting-bell-test/app/main.py`.

| Voce | Valore |
| --- | --- |
| Endpoint | `POST /qiskit-chsh-test` sul servizio `sifting-bell-test` |
| URL locale | `http://localhost:8009/qiskit-chsh-test` |
| Payload usato | `{"shots_per_basis": 2500}` |
| Script confronto | `scripts/compare_final_samplers.py` |
| Comando confronto | `python3 scripts/compare_final_samplers.py --gateway-url http://localhost:18000 --sifting-bell-test-url http://localhost:8009 --shots 10000 --shots-per-basis 2500 --repeats 10` |
| Ripetizioni per sampler | 10 |

| sampler_mode | runs | failed | chsh_mean ± std | abs_chsh_mean ± std | qber_mean ± std |
| --- | --- | --- | --- | --- | --- |
| classical_singlet_sampler | 10 | 0 | -2.8260 ± 0.0363 | 2.8260 ± 0.0363 | 0.0000 ± 0.0000 |
| qiskit | 10 | 0 | 2.8346 ± 0.0253 | 2.8346 ± 0.0253 | N/A |

Interpretazione: il sampler classico della pipeline end-to-end e il sampler Qiskit/AerSimulator sono coerenti sul modulo di CHSH. Il segno algebrico di `chsh` differisce per convenzioni di stato, rotazioni e mapping dei bit; per questo il confronto corretto è su `abs_chsh`. Qiskit non è il motore della simulazione, ma una validazione circuitale della componente Bell/CHSH.

## 10. Grafici consigliati

| file | cosa rappresenta | uso consigliato |
| --- | --- | --- |
| baseline_summary.png | Sintesi baseline ideale: CHSH, QBER, generated key rate e sifted key length. | Capitolo 5 |
| combined_link_noise_eve_abs_chsh.png | Scenari link+noise+Eve: andamento di abs_chsh_mean. | Capitolo 5 |
| combined_link_noise_eve_generated_key_rate.png | Scenari link+noise+Eve: generated_key_rate. | Capitolo 5 |
| combined_link_noise_eve_key_status_distribution.png | Scenari link+noise+Eve: distribuzione key_status. | Supporto/appendice |
| combined_link_noise_eve_qber.png | Scenari link+noise+Eve: andamento di qber_mean. | Capitolo 5 |
| combined_noise_eve_abs_chsh.png | Scenari combinati noise+Eve: andamento di abs_chsh_mean. | Capitolo 5 |
| combined_noise_eve_generated_key_rate.png | Scenari combinati noise+Eve: generated_key_rate. | Capitolo 5 |
| combined_noise_eve_key_status_distribution.png | Scenari combinati noise+Eve: distribuzione key_status. | Supporto/appendice |
| combined_noise_eve_qber.png | Scenari combinati noise+Eve: andamento di qber_mean. | Capitolo 5 |
| eve_intercept_resend_abs_chsh.png | Eve intercept_resend: probabilità di attacco rispetto ad abs_chsh_mean. | Supporto/appendice |
| eve_intercept_resend_generated_key_rate.png | Eve intercept_resend: generated_key_rate. | Supporto/appendice |
| eve_intercept_resend_key_status_distribution.png | Eve intercept_resend: distribuzione key_status. | Supporto/appendice |
| eve_intercept_resend_qber.png | Eve intercept_resend: probabilità di attacco rispetto a qber_mean. | Supporto/appendice |
| eve_randomize_abs_chsh.png | Eve randomize: probabilità di attacco rispetto ad abs_chsh_mean. | Capitolo 5 |
| eve_randomize_generated_key_rate.png | Eve randomize: generated_key_rate. | Supporto/appendice |
| eve_randomize_key_status_distribution.png | Eve randomize: distribuzione key_status. | Supporto/appendice |
| eve_randomize_qber.png | Eve randomize: probabilità di attacco rispetto a qber_mean. | Capitolo 5 |
| global_generated_key_rate_by_scenario_group.png | Generated key rate aggregato per gruppo di scenario. | Capitolo 5 |
| global_key_status_distribution.png | Distribuzione globale dei key_status nella campagna finale. | Capitolo 5 |
| global_security_status_distribution.png | Distribuzione globale dei security_status nella campagna finale. | Capitolo 5 |
| link_loss_status_distribution.png | Distribuzione degli stati nominal/degraded/critical negli scenari link loss. | Supporto/appendice |
| link_loss_total_db_vs_generated_key_rate.png | Perdita totale in dB rispetto al tasso di chiavi generate. | Capitolo 5 |
| link_loss_total_db_vs_lost_pair_count.png | Perdita totale in dB rispetto al numero medio di coppie perse. | Capitolo 5 |
| link_loss_total_db_vs_sifted_key_length.png | Perdita totale in dB rispetto alla lunghezza media della chiave sifted. | Capitolo 5 |
| link_loss_total_distance_km_vs_generated_key_rate.png | Distanza totale del link rispetto al tasso di chiavi generate. | Capitolo 5 |
| link_loss_total_distance_km_vs_lost_pair_count.png | Distanza totale del link rispetto al numero medio di coppie perse. | Capitolo 5 |
| link_loss_total_distance_km_vs_sifted_key_length.png | Distanza totale del link rispetto alla lunghezza media della chiave sifted. | Capitolo 5 |
| noise_bit_flip_abs_chsh.png | Noise bit_flip: noise_level rispetto ad abs_chsh_mean. | Capitolo 5 |
| noise_bit_flip_generated_key_rate.png | Noise bit_flip: noise_level rispetto al generated_key_rate. | Supporto/appendice |
| noise_bit_flip_key_status_distribution.png | Noise bit_flip: distribuzione degli stati chiave. | Supporto/appendice |
| noise_bit_flip_qber.png | Noise bit_flip: noise_level rispetto a qber_mean. | Capitolo 5 |
| noise_depolarizing_abs_chsh.png | Noise depolarizing: noise_level rispetto ad abs_chsh_mean. | Supporto/appendice |
| noise_depolarizing_generated_key_rate.png | Noise depolarizing: generated_key_rate. | Supporto/appendice |
| noise_depolarizing_key_status_distribution.png | Noise depolarizing: distribuzione key_status. | Supporto/appendice |
| noise_depolarizing_qber.png | Noise depolarizing: noise_level rispetto a qber_mean. | Supporto/appendice |

Grafici migliori da inserire nel Capitolo 5:

- `results/final/plots/baseline_summary.png`
- `results/final/plots/combined_link_noise_eve_abs_chsh.png`
- `results/final/plots/combined_link_noise_eve_generated_key_rate.png`
- `results/final/plots/combined_link_noise_eve_qber.png`
- `results/final/plots/combined_noise_eve_abs_chsh.png`
- `results/final/plots/combined_noise_eve_generated_key_rate.png`
- `results/final/plots/combined_noise_eve_qber.png`
- `results/final/plots/eve_randomize_abs_chsh.png`
- `results/final/plots/eve_randomize_qber.png`
- `results/final/plots/global_generated_key_rate_by_scenario_group.png`
- `results/final/plots/global_key_status_distribution.png`
- `results/final/plots/global_security_status_distribution.png`
- `results/final/plots/link_loss_total_db_vs_generated_key_rate.png`
- `results/final/plots/link_loss_total_db_vs_lost_pair_count.png`
- `results/final/plots/link_loss_total_db_vs_sifted_key_length.png`
- `results/final/plots/link_loss_total_distance_km_vs_generated_key_rate.png`
- `results/final/plots/link_loss_total_distance_km_vs_lost_pair_count.png`
- `results/final/plots/link_loss_total_distance_km_vs_sifted_key_length.png`
- `results/final/plots/noise_bit_flip_abs_chsh.png`

Grafici che possono restare come supporto o appendice:

- `results/final/plots/combined_link_noise_eve_key_status_distribution.png`
- `results/final/plots/combined_noise_eve_key_status_distribution.png`
- `results/final/plots/eve_intercept_resend_abs_chsh.png`
- `results/final/plots/eve_intercept_resend_generated_key_rate.png`
- `results/final/plots/eve_intercept_resend_key_status_distribution.png`
- `results/final/plots/eve_intercept_resend_qber.png`
- `results/final/plots/eve_randomize_generated_key_rate.png`
- `results/final/plots/eve_randomize_key_status_distribution.png`
- `results/final/plots/link_loss_status_distribution.png`
- `results/final/plots/noise_bit_flip_generated_key_rate.png`
- `results/final/plots/noise_bit_flip_key_status_distribution.png`
- `results/final/plots/noise_depolarizing_abs_chsh.png`
- `results/final/plots/noise_depolarizing_generated_key_rate.png`
- `results/final/plots/noise_depolarizing_key_status_distribution.png`
- `results/final/plots/noise_depolarizing_qber.png`

## 11. Possibili frasi da usare nella tesi

- La campagna finale comprende 36 scenari, ciascuno ripetuto 10 volte, per un totale di 360 run senza fallimenti registrati nei CSV finali.
- La baseline ideale produce una violazione CHSH media compatibile con il valore atteso del protocollo E91, con QBER nullo e generazione della chiave in tutte le ripetizioni.
- La perdita di link non viene trattata come rumore: nei risultati riduce il numero di coppie utili e il materiale sifted, ma non aumenta direttamente il QBER dei round sopravvissuti.
- Gli scenari di rumore e attacco di Eve mostrano una degradazione progressiva di `abs_chsh` e un aumento del QBER, fino al passaggio da `secure` a `degraded` o `insecure` secondo le soglie operative della baseline.
- La distinzione tra `security_status` e `key_status` è necessaria: una sessione può essere secure rispetto a CHSH/QBER ma non generare chiave per insufficiente materiale sifted.
- Il confronto con Qiskit/AerSimulator conferma la coerenza della componente Bell/CHSH sul valore `abs_chsh`, mantenendo Qiskit come validazione circuitale opzionale e non come motore della simulazione.

## 12. File e comandi verificati

| File/comando | Esito |
| --- | --- |
| `scripts/run_final_experiments.py` | trovato |
| `scripts/plot_final_experiments.py` | trovato |
| `scripts/compare_final_samplers.py` | trovato |
| `sifting-bell-test/app/qiskit_sampler.py` | trovato |
| `results/final/final_experiment_runs.csv` | trovato, 360 righe |
| `results/final/final_experiment_summary.csv` | trovato, 36 scenari |
| `results/final/final_experiment_summary.json` | trovato |
| `results/final/final_sampler_comparison_runs.csv` | trovato, 20 righe |
| `results/final/final_sampler_comparison_summary.csv` | trovato, 2 righe |
| `results/final/plots/` | trovata, 32 PNG |
| `scenario_summary.csv` / `final_summary.csv` / `aggregated_results` | non trovato; i file finali effettivi sono `final_experiment_summary.csv/json` |

Comandi verificati o ricostruiti:

```bash
python3 scripts/run_final_experiments.py --gateway-url http://localhost:18000 --shots 10000 --repeats 10
python3 scripts/plot_final_experiments.py
python3 scripts/compare_final_samplers.py --gateway-url http://localhost:18000 --sifting-bell-test-url http://localhost:8009 --shots 10000 --shots-per-basis 2500 --repeats 10
curl -X POST http://localhost:8009/qiskit-chsh-test -H "Content-Type: application/json" -d '{"shots_per_basis": 2500}'
```

Nota: questo report non riesegue la campagna finale; analizza i file già presenti in `results/final/`.
