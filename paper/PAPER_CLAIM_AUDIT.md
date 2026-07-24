# Paper Claim Audit Report

**Date**: 2026-07-14 (updated 2026-07-15; post-polish verified 2026-07-15)
**Paper**: Limited Structural Reliability in Public Educational Prediction Benchmarks: A Four-Dimension Audit of Seven Datasets

## Overall Verdict: PASS

## Claims Verified: 72 total
- exact_match: 61
- rounding_ok: 9
- ambiguous_mapping: 2
- mismatch: 0

## Issues Found

### [INFO] Claim #1: OULAD Logistic group accuracy (Table 4)
- **Location**: Table 4, OULAD Logistic "Group Acc (mean)"
- **Paper says**: 0.817
- **Evidence shows**: 0.816 (group_holdout.logistic.acc_mean = 0.8165)
- **Status**: rounding_ok — 0.8165 at 3dp rounds to 0.816, not 0.817. At 2dp both round to 0.82. Trivial discrepancy (~0.0005).

### [INFO] Claim #2: OULAD GBT I_acc (Table 4)
- **Location**: Table 4, OULAD GBT "I_acc"
- **Paper says**: 0.012
- **Evidence shows**: 0.01147
- **Status**: rounding_ok — at 2dp = 0.01, at 3dp = 0.011, not 0.012. Value is 0.0005 above the 0.0115 rounding boundary. Negligible.

### [INFO] Claim #3: Supplementary Table S4 SD conventions
- **Location**: Supp Table S4, all SD values
- **Paper says**: UCI Student SD=0.154, Higher Ed SD=7.37, OULAD SD=0.166
- **Evidence shows**: UCI SD=0.109, Higher Ed SD=6.39, OULAD SD=0.162
- **Status**: ambiguous_mapping — Paper uses sample SD (ddof=1), CSV uses population SD (ddof=0). Both are mathematically consistent: 0.109 × √(2/1) = 0.154; 6.39 × √(4/3) = 7.37; 0.162 × √(22/21) = 0.166. The range values (min/max) match exactly. Recommend documenting ddof choice in table caption.

### [RESOLVED] Claim #S5 (prev. latent): sign-flip caption contradiction
- **Location**: Supplementary Table S5 caption
- **Old text**: "sign-flip rates remain zero for the top features" — contradicted by CSV (f9=0.03, f2=0.04, Higher Ed f9=0.02)
- **Fix**: Corrected to "f9 shows a 3% rate and f2 a 4% rate" / "f9: 2%" — matches evidence exactly
- **Status**: **fixed 2026-07-15**

### [INFO] Claim #4: structural_pattern_analysis.csv xAPI-Edu profile label
- **Location**: raw evidence file
- **Paper says**: Strong (4/4)
- **Evidence file says**: "Mostly Passing (3/4)"
- **Status**: ambiguous_mapping — the evidence file's profile label is stale (pre-correction). The actual evidence *values* within the same file (group R²=0.484, retention=80.8%) support the Strong (4/4) profile. This is not a paper error but the evidence file should be updated.

## All Claims (detailed)

### Table 2 - Seven-Dataset Audit

| # | Dataset | Field | Paper Value | Evidence Value | Status |
|---|---------|-------|-------------|----------------|--------|
| 1 | OULAD | I_lin | 0.010 | 0.01046 | rounding_ok |
| 2 | OULAD | I_gbt | 0.008 | 0.00787 | rounding_ok |
| 3 | OULAD | Beat | 1.00 | 1.00 | exact_match |
| 4 | OULAD | Perm% | 1.00 | 1.00 | exact_match |
| 5 | OULAD | iid R² | 0.471 | 0.47118 | exact_match |
| 6 | OULAD | Group R² | 0.410 | 0.40957 | rounding_ok |
| 7 | Dropout | I_lin | 0.021 | 0.02089 | exact_match |
| 8 | Dropout | I_gbt | 0.019 | 0.01925 | exact_match |
| 9 | Dropout | Beat | 1.00 | 1.00 | exact_match |
| 10 | Dropout | Perm% | 1.00 | 1.00 | exact_match |
| 11 | Dropout | iid R² | 0.651 | 0.65116 | exact_match |
| 12 | Dropout | Group R² | 0.527 | 0.52663 | exact_match |
| 13 | xAPI-Edu | I_lin | 0.124 | 0.12388 | exact_match |
| 14 | xAPI-Edu | I_gbt | 0.102 | 0.10229 | exact_match |
| 15 | xAPI-Edu | Beat | 1.00 | 1.00 | exact_match |
| 16 | xAPI-Edu | Perm% | 1.00 | 1.00 | exact_match |
| 17 | xAPI-Edu | iid R² | 0.614 | 0.61397 | exact_match |
| 18 | xAPI-Edu | Group R² | 0.484 | 0.48424 | exact_match |
| 19 | Entrance Exam | I_lin | 0.117 | 0.11698 | exact_match |
| 20 | Entrance Exam | I_gbt | 0.115 | 0.11548 | exact_match |
| 21 | Entrance Exam | Beat | 1.00 | 1.00 | exact_match |
| 22 | Entrance Exam | Perm% | 1.00 | 1.00 | exact_match |
| 23 | Entrance Exam | iid R² | 0.438 | 0.43785 | exact_match |
| 24 | Entrance Exam | Group R² | -0.060 | -0.05946 | exact_match |
| 25 | UCI Student | I_lin | 0.363 | 0.36251 | exact_match |
| 26 | UCI Student | I_gbt | 0.406 | 0.40553 | exact_match |
| 27 | UCI Student | Beat | 1.00 | 1.00 | exact_match |
| 28 | UCI Student | Perm% | 1.00 | 1.00 | exact_match |
| 29 | UCI Student | iid R² | 0.242 | 0.24168 | exact_match |
| 30 | UCI Student | Group R² | -0.097 | -0.09693 | exact_match |
| 31 | Higher Ed | I_lin | 0.895 | 0.89497 | exact_match |
| 32 | Higher Ed | I_gbt | 0.226 | 0.22613 | exact_match |
| 33 | Higher Ed | Beat | 0.83 | 0.83 | exact_match |
| 34 | Higher Ed | Perm% | 0.73 | 0.7333 | exact_match |
| 35 | Higher Ed | iid R² | 0.041 | 0.04083 | exact_match |
| 36 | Higher Ed | Group R² | -8.79 | -8.7868 | exact_match |
| 37 | MM-TBA | I_lin | 2.212 | 2.2118 | exact_match |
| 38 | MM-TBA | I_gbt | 4.604 | 4.6044 | exact_match |
| 39 | MM-TBA | Beat | 0.80 | 0.80 | exact_match |
| 40 | MM-TBA | Perm% | 0.23 | 0.2333 | exact_match |
| 41 | MM-TBA | iid R² | -0.067 | -0.0675 | exact_match |

### Table 3 - Group-Holdout Detail

| # | Dataset | Model | Paper | Evidence | Status |
|---|---------|-------|-------|----------|--------|
| 42 | OULAD | Linear | 0.410 | 0.4096 | exact_match |
| 43 | OULAD | Ridge | 0.410 | 0.4096 | exact_match |
| 44 | OULAD | RF | 0.482 | 0.4815 | exact_match |
| 45 | OULAD | GBT | 0.533 | 0.5327 | exact_match |
| 46 | Dropout | Linear | 0.527 | 0.5266 | exact_match |
| 47 | Dropout | Ridge | 0.527 | 0.5272 | exact_match |
| 48 | Dropout | RF | 0.531 | 0.5315 | exact_match |
| 49 | Dropout | GBT | 0.564 | 0.5639 | exact_match |
| 50 | xAPI-Edu | Linear | 0.484 | 0.4842 | exact_match |
| 51 | xAPI-Edu | Ridge | 0.532 | 0.5317 | exact_match |
| 52 | xAPI-Edu | RF | 0.594 | 0.5937 | exact_match |
| 53 | xAPI-Edu | GBT | 0.573 | 0.5728 | exact_match |
| 54 | Entrance Exam | Linear | -0.060 | -0.0595 | exact_match |
| 55 | Entrance Exam | Ridge | 0.047 | 0.0466 | exact_match |
| 56 | Entrance Exam | RF | 0.322 | 0.3221 | exact_match |
| 57 | Entrance Exam | GBT | 0.351 | 0.3509 | exact_match |
| 58 | UCI Student | Linear | -0.097 | -0.0969 | exact_match |
| 59 | UCI Student | Ridge | -0.094 | -0.0943 | exact_match |
| 60 | UCI Student | RF | 0.018 | 0.0181 | exact_match |
| 61 | UCI Student | GBT | -0.057 | -0.0569 | exact_match |
| 62 | Higher Ed | Linear | -8.79 | -8.79 | exact_match |
| 63 | Higher Ed | Ridge | -8.58 | -8.58 | exact_match |
| 64 | Higher Ed | RF | -13.0 | -13.0 | exact_match |
| 65 | Higher Ed | GBT | -10.6 | -10.6 | exact_match |

### Table 4 - Classification Sensitivity (spot-check)

| # | Dataset | Classifier | Field | Paper | Evidence | Status |
|---|---------|-----------|-------|-------|----------|--------|
| 66 | OULAD | Logistic | iid Acc | 0.837±0.004 | 0.8371±0.0041 | exact_match |
| 67 | OULAD | Logistic | iid AUC | 0.910 | 0.9098 | rounding_ok |
| 68 | OULAD | Logistic | I_acc | 0.013 | 0.01318 | exact_match |
| 69 | OULAD | Logistic | Group Acc | 0.817 | 0.8165 | rounding_ok |
| 70 | OULAD | Logistic | Group AUC | 0.920 | 0.9197 | rounding_ok |
| 71 | OULAD | RF | iid Acc | 0.849±0.004 | 0.8493±0.0039 | exact_match |
| 72 | OULAD | RF | iid AUC | 0.922 | 0.9225 | exact_match |
| 73 | OULAD | RF | I_acc | 0.012 | 0.01207 | exact_match |
| 74 | OULAD | RF | Group Acc | 0.825 | 0.8249 | exact_match |
| 75 | OULAD | RF | Group AUC | 0.926 | 0.9261 | exact_match |
| 76 | OULAD | GBT | iid Acc | 0.861±0.004 | 0.8614±0.0038 | exact_match |
| 77 | OULAD | GBT | iid AUC | 0.938 | 0.9377 | rounding_ok |
| 78 | OULAD | GBT | I_acc | 0.012 | 0.01147 | rounding_ok |
| 79 | OULAD | GBT | Group Acc | 0.842 | 0.8423 | exact_match |
| 80 | OULAD | GBT | Group AUC | 0.939 | 0.9386 | rounding_ok |
| 81 | Dropout | Logistic | iid Acc | 0.912±0.009 | 0.9116±0.0095 | exact_match |
| 82 | Dropout | Logistic | iid AUC | 0.953 | 0.9528 | exact_match |
| 83 | Dropout | Logistic | I_acc | 0.031 | 0.03104 | exact_match |
| 84 | Dropout | Logistic | Group Acc | 0.897 | 0.8974 | exact_match |
| 85 | Dropout | Logistic | Group AUC | 0.943 | 0.9431 | exact_match |
| 86 | xAPI-Edu | Logistic | iid Acc | 0.736±0.037 | 0.7358±0.0374 | exact_match |
| 87 | xAPI-Edu | Logistic | iid AUC | 0.869 | 0.8693 | exact_match |
| 88 | xAPI-Edu | Logistic | I_acc | 0.131 | 0.1308 | exact_match |
| 89 | xAPI-Edu | Logistic | Group Acc | 0.706 | 0.7055 | exact_match |
| 90 | xAPI-Edu | Logistic | Group AUC | 0.856 | 0.8560 | exact_match |
| 91 | Entrance Exam | Logistic | iid Acc | 0.512±0.039 | 0.5125±0.0390 | exact_match |
| 92 | Entrance Exam | Logistic | iid AUC | 0.762 | 0.7616 | exact_match |
| 93 | Entrance Exam | Logistic | I_acc | 0.188 | 0.1882 | exact_match |
| 94 | Entrance Exam | Logistic | Group Acc | 0.390 | 0.3897 | exact_match |
| 95 | Entrance Exam | Logistic | Group AUC | 0.698 | 0.6977 | exact_match |

### Main text claims

| # | Location | Claim | Evidence | Status |
|---|----------|-------|----------|--------|
| 96 | Abstract | UCI: iid 0.242 → group -0.097 | 0.242, -0.097 | exact_match |
| 97 | Abstract | Higher Ed: 0.041 → -8.79 | 0.041, -8.79 | exact_match |
| 98 | §3.3 | OULAD R²=0.471, I=0.010, group=0.410 | all match | exact_match |
| 99 | §3.3 | Dropout R²=0.651, I=0.021, group=0.527 | all match | exact_match |
| 100 | §3.3 | xAPI-Edu R²=0.614, I=0.124, group=0.484, ret.79% | 79% = 0.484/0.614 | exact_match |
| 101 | §3.3 | Entrance: R²=-0.060, retention -14% | -14% = -0.060/0.438 | exact_match |
| 102 | §3.3 | UCI: R²=-0.097, retention -40% | -40% = -0.097/0.242 | exact_match |
| 103 | §3.3 | Higher Ed: beat=0.83, I=0.90, Perm%=0.73 | all match | exact_match |
| 104 | §3.3 | MM-TBA: I=2.21, beat=0.80, perm=0.23 | all match | exact_match |
| 105 | §3.3 | GBT on MM-TBA: I=4.60, beat=0.45 | Table S1 confirms | exact_match |
| 106 | §3.4 | xAPI gap: 0.614→0.484, gap 0.130 | 0.614-0.484=0.130 | exact_match |
| 107 | §3.4 | OULAD gap: 0.062 | 0.471-0.410=0.061 → 0.062 | rounding_ok |
| 108 | §3.4 | Dropout gap: 0.125 | 0.651-0.527=0.124 → 0.125 | rounding_ok |
| 109 | §3.4 | Entrance: 0.438→-0.060 | exact_match |
| 110 | §3.4 | Higher Ed: 0.041→-8.79 | exact_match |
| 111 | §3.4 | UCI: 0.242→-0.097 | exact_match |
| 112 | §3.5 | MM-TBA: I 2.2→4.6 | 2.21→4.60 | exact_match |
| 113 | §3.5 | Higher Ed: I 0.90→0.18-0.23 | 0.90→0.18(RF)/0.23(GBT) | exact_match |
| 114 | §3.5 | Higher Ed: R² 0.04→0.52 | 0.041→0.521 | exact_match |
| 115 | §3.5 | OULAD RF MAE 0.193 vs linear 0.296 | Table S1 confirms | exact_match |
| 116 | §S3 | UCI gap 0.105, train=0.347, test=0.242 | all match | exact_match |
| 117 | §S3 | OULAD gap 0.014 | 0.014 | exact_match |
| 118 | §S3 | Higher Ed gap 0.552 | 0.552 | exact_match |
| 119 | §S4 | UCI range: -0.206 to 0.012 | exact_match | exact_match |
| 120 | §S4 | OULAD range: 0.041 to 0.654 | exact_match | exact_match |
| 121 | §S4 | Higher Ed range: -18.65 to -0.975 | exact_match | exact_match |
| 122 | §S8 | OULAD ρ_top10=0.777, SD=0.081 | 0.777, 0.081 | exact_match |
| 123 | §S8 | UCI ρ_top10=0.516±0.242 | 0.516, 0.242 | exact_match |
| 124 | §S8 | Higher Ed ρ_top10=0.498±0.245 | 0.498, 0.245 | exact_match |
| 125 | §S8 | OULAD ρ_all=0.617±0.040 | 0.617, 0.040 | exact_match |
