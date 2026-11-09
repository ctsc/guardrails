## fine-tuned Qwen3.5-2B (LoRA r=16)  (523.4s)

| test set | n | accuracy [95% CI] | macro-F1 | flagged-FPR [95% CI] |
|---|---|---|---|---|
| aegis_test | 399 | 74.7% [70.2, 78.7] (n=399) | 0.734 | 16.9% [10.5, 26.0] (n=89) |
| openai_moderation | 1511 | 63.1% [60.7, 65.5] (n=1511) | 0.534 | 47.0% [44.0, 50.0] (n=1054) |
| overblock_jbb | 100 | 62.0% [52.2, 70.9] (n=100) | 0.765 | 38.0% [29.1, 47.8] (n=100) |
| overblock_xstest | 250 | 60.4% [54.2, 66.3] (n=250) | 0.753 | 39.6% [33.7, 45.8] (n=250) |
| prompt_attack_pib | 500 | 80.4% [76.7, 83.6] (n=500) | 0.814 | 10.0% [7.1, 13.9] (n=300) |
| safeguard_test_secondary | 200 | 94.0% [89.8, 96.5] (n=200) | 0.959 | 7.0% [3.4, 13.7] (n=100) |
| all_input_rows | 2826 | 69.3% [67.6, 71.0] (n=2826) | 0.582 | 36.4% [34.3, 38.6] (n=1867) |
| all_output_rows | 134 | 72.4% [64.3, 79.3] (n=134) | 0.703 | 15.4% [6.1, 33.5] (n=26) |
| overblocking_xstest+jbb | 350 | 60.9% [55.7, 65.8] (n=350) | 0.757 | 39.1% [34.2, 44.3] (n=350) |

### aegis_test: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 89 | 0.661 | 0.831 | 0.736 |
| B hate | 67 | 0.866 | 0.866 | 0.866 |
| C insults | 66 | 0.703 | 0.394 | 0.505 |
| D sexual | 66 | 0.923 | 0.909 | 0.916 |
| E violence | 42 | 0.525 | 0.762 | 0.621 |
| F misconduct | 69 | 0.842 | 0.696 | 0.762 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 74 | 3 | 4 | 2 | 2 | 4 | 0 |
| B | 6 | 58 | 1 | 0 | 2 | 0 | 0 |
| C | 17 | 6 | 26 | 3 | 11 | 3 | 0 |
| D | 2 | 0 | 1 | 60 | 3 | 0 | 0 |
| E | 3 | 0 | 5 | 0 | 32 | 2 | 0 |
| F | 10 | 0 | 0 | 0 | 11 | 48 | 0 |

### openai_moderation: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 1054 | 0.981 | 0.530 | 0.688 |
| B hate | 159 | 0.357 | 0.635 | 0.457 |
| C insults | 32 | 0.130 | 0.656 | 0.218 |
| D sexual | 175 | 0.600 | 0.960 | 0.738 |
| E violence | 91 | 0.442 | 0.802 | 0.570 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 559 | 174 | 118 | 96 | 88 | 14 | 5 |
| B | 2 | 101 | 33 | 12 | 11 | 0 | 0 |
| C | 2 | 4 | 21 | 5 | 0 | 0 | 0 |
| D | 0 | 1 | 3 | 168 | 3 | 0 | 0 |
| E | 7 | 3 | 6 | 1 | 73 | 1 | 0 |

### overblock_jbb: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 1.000 | 0.620 | 0.765 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 62 | 5 | 0 | 9 | 5 | 19 | 0 |

### overblock_xstest: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 250 | 1.000 | 0.604 | 0.753 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 151 | 34 | 1 | 7 | 47 | 10 | 0 |

### prompt_attack_pib: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 300 | 0.821 | 0.900 | 0.859 |
| G prompt_attack | 200 | 0.923 | 0.660 | 0.770 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 270 | 7 | 0 | 5 | 5 | 2 | 11 |
| G | 59 | 0 | 0 | 0 | 2 | 7 | 132 |

### safeguard_test_secondary: per class

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| A safe | 100 | 0.959 | 0.930 | 0.944 |
| G prompt_attack | 100 | 1.000 | 0.950 | 0.974 |

confusion (rows = gold, cols = predicted):

| gold \ pred | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| A | 93 | 2 | 2 | 0 | 3 | 0 | 0 |
| G | 4 | 0 | 0 | 0 | 0 | 1 | 95 |

Note: with ~100 rows a 95% Wilson interval is roughly +/- 10 points; treat differences inside the interval as noise.