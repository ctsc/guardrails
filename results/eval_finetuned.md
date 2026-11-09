## fine-tuned Qwen3.5-2B (LoRA r=16)  (549.1s)

| test set | n | accuracy [95% CI] | macro-F1 | flagged-FPR [95% CI] |
|---|---|---|---|---|
| aegis_test | 399 | 70.2% [65.5, 74.5] (n=399) | 0.698 | 18.0% [11.4, 27.2] (n=89) |
| openai_moderation | 1511 | 64.7% [62.2, 67.0] (n=1511) | 0.543 | 43.2% [40.2, 46.2] (n=1054) |
| overblock_jbb | 100 | 62.0% [52.2, 70.9] (n=100) | 0.765 | 38.0% [29.1, 47.8] (n=100) |
| overblock_xstest | 250 | 76.4% [70.8, 81.2] (n=250) | 0.866 | 23.6% [18.8, 29.2] (n=250) |
| prompt_attack_pib | 500 | 82.8% [79.2, 85.9] (n=500) | 0.833 | 6.3% [4.1, 9.7] (n=300) |
| safeguard_test_secondary | 200 | 94.5% [90.4, 96.9] (n=200) | 0.964 | 7.0% [3.4, 13.7] (n=100) |
| all_input_rows | 2826 | 71.3% [69.6, 72.9] (n=2826) | 0.585 | 31.7% [29.6, 33.8] (n=1867) |
| all_output_rows | 134 | 73.1% [65.1, 79.9] (n=134) | 0.718 | 11.5% [4.0, 29.0] (n=26) |
| overblocking_xstest+jbb | 350 | 72.3% [67.4, 76.7] (n=350) | 0.839 | 27.7% [23.3, 32.6] (n=350) |

### aegis_test: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 89 | 0.575 | 0.820 | 0.676 |
| B hate | 67 | 0.857 | 0.716 | 0.780 |
| C insults | 66 | 0.568 | 0.379 | 0.455 |
| D sexual | 66 | 0.964 | 0.818 | 0.885 |
| E violence | 42 | 0.492 | 0.714 | 0.583 |
| F misconduct | 69 | 0.909 | 0.725 | 0.806 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 73 | 3 | 6 | 1 | 4 | 2 | 0 |
| B | 11 | 48 | 7 | 0 | 1 | 0 | 0 |
| C | 21 | 5 | 25 | 1 | 12 | 2 | 0 |
| D | 4 | 0 | 2 | 54 | 6 | 0 | 0 |
| E | 7 | 0 | 4 | 0 | 30 | 1 | 0 |
| F | 11 | 0 | 0 | 0 | 8 | 50 | 0 |

### openai_moderation: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 1054 | 0.971 | 0.568 | 0.717 |
| B hate | 159 | 0.429 | 0.516 | 0.469 |
| C insults | 32 | 0.099 | 0.812 | 0.177 |
| D sexual | 175 | 0.698 | 0.926 | 0.796 |
| E violence | 91 | 0.458 | 0.714 | 0.558 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 599 | 106 | 199 | 61 | 68 | 17 | 4 |
| B | 3 | 82 | 52 | 6 | 15 | 1 | 0 |
| C | 2 | 1 | 26 | 3 | 0 | 0 | 0 |
| D | 0 | 0 | 5 | 162 | 8 | 0 | 0 |
| E | 13 | 2 | 8 | 1 | 65 | 2 | 0 |

### overblock_jbb: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 1.000 | 0.620 | 0.765 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 62 | 5 | 0 | 8 | 6 | 19 | 0 |

### overblock_xstest: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 250 | 1.000 | 0.764 | 0.866 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 191 | 17 | 0 | 2 | 30 | 10 | 0 |

### prompt_attack_pib: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 300 | 0.826 | 0.937 | 0.878 |
| G prompt_attack | 200 | 0.964 | 0.665 | 0.787 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 281 | 3 | 2 | 3 | 6 | 0 | 5 |
| G | 59 | 0 | 0 | 0 | 2 | 6 | 133 |

### safeguard_test_secondary: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 0.979 | 0.930 | 0.954 |
| G prompt_attack | 100 | 0.990 | 0.960 | 0.975 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 93 | 1 | 3 | 0 | 1 | 1 | 1 |
| G | 2 | 0 | 0 | 1 | 0 | 1 | 96 |

Note: with ~100 rows a 95% Wilson interval is roughly +/- 10 points; treat differences inside the interval as noise.