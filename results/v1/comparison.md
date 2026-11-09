# Base vs fine-tuned

| test set | n | base acc | tuned acc | base macro-F1 | tuned macro-F1 | base FPR | tuned FPR |
|---|---|---|---|---|---|---|---|
| aegis_test | 399 | 60.9% | 74.7% | 0.618 | 0.734 | 55.1% | 16.9% |
| openai_moderation | 1511 | 51.2% | 63.1% | 0.494 | 0.534 | 60.0% | 47.0% |
| overblock_jbb | 100 | 34.0% | 62.0% | 0.507 | 0.765 | 66.0% | 38.0% |
| overblock_xstest | 250 | 50.8% | 60.4% | 0.674 | 0.753 | 49.2% | 39.6% |
| prompt_attack_pib | 500 | 64.6% | 80.4% | 0.702 | 0.814 | 36.0% | 10.0% |
| safeguard_test_secondary | 200 | 76.5% | 94.0% | 0.817 | 0.959 | 26.0% | 7.0% |
| all_input_rows | 2826 | 55.4% | 69.3% | 0.479 | 0.582 | 53.2% | 36.4% |
| all_output_rows | 134 | 65.7% | 72.4% | 0.641 | 0.703 | 42.3% | 15.4% |
| overblocking_xstest+jbb | 350 | 46.0% | 60.9% | 0.630 | 0.757 | 54.0% | 39.1% |