## base Qwen3.5-2B  (606.0s)

| test set | n | accuracy [95% CI] | macro-F1 | flagged-FPR [95% CI] |
|---|---|---|---|---|
| aegis_test | 399 | 60.9% [56.0, 65.6] (n=399) | 0.618 | 55.1% [44.7, 65.0] (n=89) |
| openai_moderation | 1511 | 51.2% [48.6, 53.7] (n=1511) | 0.494 | 60.0% [57.0, 62.9] (n=1054) |
| overblock_jbb | 100 | 34.0% [25.5, 43.7] (n=100) | 0.507 | 66.0% [56.3, 74.5] (n=100) |
| overblock_xstest | 250 | 50.8% [44.6, 56.9] (n=250) | 0.674 | 49.2% [43.1, 55.4] (n=250) |
| prompt_attack_pib | 500 | 64.6% [60.3, 68.7] (n=500) | 0.702 | 36.0% [30.8, 41.6] (n=300) |
| safeguard_test_secondary | 200 | 76.5% [70.2, 81.8] (n=200) | 0.817 | 26.0% [18.4, 35.4] (n=100) |
| all_input_rows | 2826 | 55.4% [53.5, 57.2] (n=2826) | 0.479 | 53.2% [50.9, 55.4] (n=1867) |
| all_output_rows | 134 | 65.7% [57.3, 73.2] (n=134) | 0.641 | 42.3% [25.5, 61.1] (n=26) |
| overblocking_xstest+jbb | 350 | 46.0% [40.9, 51.2] (n=350) | 0.630 | 54.0% [48.8, 59.1] (n=350) |

### aegis_test: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 89 | 0.533 | 0.449 | 0.488 |
| B hate | 67 | 0.766 | 0.731 | 0.748 |
| C insults | 66 | 0.421 | 0.727 | 0.533 |
| D sexual | 66 | 0.939 | 0.697 | 0.800 |
| E violence | 42 | 0.565 | 0.310 | 0.400 |
| F misconduct | 69 | 0.810 | 0.681 | 0.740 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 40 | 5 | 25 | 1 | 2 | 3 | 13 |
| B | 2 | 49 | 14 | 0 | 0 | 2 | 0 |
| C | 7 | 5 | 48 | 2 | 2 | 2 | 0 |
| D | 4 | 0 | 11 | 46 | 2 | 2 | 1 |
| E | 10 | 4 | 12 | 0 | 13 | 2 | 1 |
| F | 12 | 1 | 4 | 0 | 4 | 47 | 1 |

### openai_moderation: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 1054 | 0.961 | 0.400 | 0.565 |
| B hate | 159 | 0.368 | 0.799 | 0.504 |
| C insults | 32 | 0.053 | 0.656 | 0.097 |
| D sexual | 175 | 0.827 | 0.874 | 0.850 |
| E violence | 91 | 0.600 | 0.363 | 0.452 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 422 | 194 | 325 | 29 | 20 | 55 | 9 |
| B | 1 | 127 | 29 | 1 | 0 | 1 | 0 |
| C | 0 | 8 | 21 | 2 | 0 | 1 | 0 |
| D | 0 | 4 | 14 | 153 | 2 | 1 | 1 |
| E | 16 | 12 | 27 | 0 | 33 | 3 | 0 |

### overblock_jbb: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 1.000 | 0.340 | 0.507 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 34 | 8 | 0 | 6 | 6 | 28 | 18 |

### overblock_xstest: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 250 | 1.000 | 0.508 | 0.674 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 127 | 37 | 26 | 3 | 37 | 19 | 1 |

### prompt_attack_pib: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 300 | 0.877 | 0.640 | 0.740 |
| G prompt_attack | 200 | 0.672 | 0.655 | 0.663 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 192 | 7 | 24 | 1 | 2 | 10 | 64 |
| G | 27 | 7 | 3 | 8 | 0 | 24 | 131 |

### safeguard_test_secondary: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 0.961 | 0.740 | 0.836 |
| G prompt_attack | 100 | 0.806 | 0.790 | 0.798 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 74 | 0 | 3 | 0 | 0 | 4 | 19 |
| G | 3 | 1 | 4 | 0 | 8 | 5 | 79 |

Note: with ~100 rows a 95% Wilson interval is roughly +/- 10 points; treat differences inside the interval as noise.