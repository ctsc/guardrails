# Base vs fine-tuned

| test set | n | base acc | tuned acc | base macro-F1 | tuned macro-F1 | base FPR | tuned FPR |
|---|---|---|---|---|---|---|---|
| aegis_test | 399 | 60.9% | 70.2% | 0.618 | 0.698 | 55.1% | 18.0% |
| openai_moderation | 1511 | 51.2% | 64.7% | 0.494 | 0.543 | 60.0% | 43.2% |
| overblock_jbb | 100 | 34.0% | 62.0% | 0.507 | 0.765 | 66.0% | 38.0% |
| overblock_xstest | 250 | 50.8% | 76.4% | 0.674 | 0.866 | 49.2% | 23.6% |
| prompt_attack_pib | 500 | 64.6% | 82.8% | 0.702 | 0.833 | 36.0% | 6.3% |
| safeguard_test_secondary | 200 | 76.5% | 94.5% | 0.817 | 0.964 | 26.0% | 7.0% |
| all_input_rows | 2826 | 55.4% | 71.3% | 0.479 | 0.585 | 53.2% | 31.7% |
| all_output_rows | 134 | 65.7% | 73.1% | 0.641 | 0.718 | 42.3% | 11.5% |
| overblocking_xstest+jbb | 350 | 46.0% | 72.3% | 0.630 | 0.839 | 54.0% | 27.7% |