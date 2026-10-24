# Champion benchmarks and game-phase investigation

**Experimental, read-only analysis. Production v4 is unchanged.**

Earliest 445 matches train duration models; latest 297 matches are held out by whole match. Both configured players are excluded from fitting and the outcome table. Other participants still come from their selected histories; this is not population reference data.

## Duration-only candidate

Within role/archetype/metric, fit log(1 + raw rate) against log(duration / 30 minutes), with equal total weight for wins and losses. Require at least 20 wins and 20 losses, shrink slope by n/(n+100), limit slope to ±2 and reference multiplier to 0.7–1.3. Clamp model duration to 10–50 minutes. Keep existing 30-minute references, weights and curves; do not add a win bonus. Survival and participation are unchanged. Missing models retain current scoring. This functional choice is a sensitivity experiment, not proven normalization.

Fitted groups: 63. Held-out participants with an adjusted component: 2783.

| Held-out duration | Outcome | Participants | Current | Candidate |
|---|---|---:|---:|---:|
| Under 20 | Win | 21 | 58.11 | 66.31 |
| Under 20 | Loss | 19 | 25.51 | 29.57 |
| 20–30 | Win | 508 | 60.47 | 62.3 |
| 20–30 | Loss | 506 | 39.06 | 40.64 |
| 30–40 | Win | 599 | 61.1 | 59.14 |
| 30–40 | Loss | 620 | 49.19 | 47.19 |
| 40+ | Win | 107 | 62.1 | 56.85 |
| 40+ | Loss | 102 | 55.14 | 49.69 |

## Within-champion phase checks

Each row fixes champion, role and outcome; requires 10 observations in each adjacent duration band. Opponents, rank, patch and player ability are not held fixed. These checks use all saved dates and are descriptive, not holdout performance estimates.

| Champion / role | Outcome | Metric | n 20–30 / 30–40 | Raw rate 20–30 / 30–40 | Change |
|---|---|---|---|---|---:|
| Ahri / MIDDLE | Loss | Champion damage | 14 / 16 | 708.01 / 881.32 | 24.5% |
| Ahri / MIDDLE | Loss | Economy | 14 / 16 | 374.76 / 376.72 | 0.5% |
| Ahri / MIDDLE | Loss | Kill participation | 14 / 16 | 52.29 / 43.87 | -16.1% |
| Ahri / MIDDLE | Loss | Objective pressure | 14 / 16 | 170.28 / 224.5 | 31.8% |
| Ahri / MIDDLE | Loss | Survival | 14 / 16 | 0.29 / 0.27 | -8.9% |
| Ahri / MIDDLE | Loss | Vision | 14 / 16 | 0.73 / 0.71 | -3.4% |
| Amumu / JUNGLE | Win | Champion damage | 15 / 12 | 585.19 / 798.53 | 36.5% |
| Amumu / JUNGLE | Win | Crowd control | 15 / 12 | 1.35 / 1.52 | 12.9% |
| Amumu / JUNGLE | Win | Economy | 15 / 12 | 436.29 / 429.8 | -1.5% |
| Amumu / JUNGLE | Win | Kill participation | 15 / 12 | 45.48 / 48.0 | 5.5% |
| Amumu / JUNGLE | Win | Objective pressure | 15 / 12 | 1423.87 / 1141.16 | -19.9% |
| Amumu / JUNGLE | Win | Survival | 15 / 12 | 0.12 / 0.22 | 78.9% |
| Amumu / JUNGLE | Win | Vision | 15 / 12 | 0.85 / 0.91 | 6.8% |
| Ashe / BOTTOM | Win | Champion damage | 13 / 16 | 796.97 / 963.67 | 20.9% |
| Ashe / BOTTOM | Win | Economy | 13 / 16 | 477.59 / 463.0 | -3.1% |
| Ashe / BOTTOM | Win | Kill participation | 13 / 16 | 44.0 / 47.86 | 8.8% |
| Ashe / BOTTOM | Win | Objective pressure | 13 / 16 | 544.23 / 548.64 | 0.8% |
| Ashe / BOTTOM | Win | Survival | 13 / 16 | 0.18 / 0.22 | 25.0% |
| Ashe / BOTTOM | Win | Vision | 13 / 16 | 0.49 / 0.84 | 70.8% |
| Briar / JUNGLE | Win | Champion damage | 13 / 13 | 820.35 / 1139.21 | 38.9% |
| Briar / JUNGLE | Win | Economy | 13 / 13 | 504.62 / 528.33 | 4.7% |
| Briar / JUNGLE | Win | Kill participation | 13 / 13 | 43.27 / 52.94 | 22.3% |
| Briar / JUNGLE | Win | Objective pressure | 13 / 13 | 1287.58 / 1194.86 | -7.2% |
| Briar / JUNGLE | Win | Survival | 13 / 13 | 0.18 / 0.23 | 29.4% |
| Briar / JUNGLE | Win | Vision | 13 / 13 | 0.83 / 0.96 | 15.7% |
| Caitlyn / BOTTOM | Loss | Champion damage | 37 / 37 | 665.21 / 858.75 | 29.1% |
| Caitlyn / BOTTOM | Win | Champion damage | 26 / 35 | 946.73 / 1185.26 | 25.2% |
| Caitlyn / BOTTOM | Loss | Economy | 37 / 37 | 423.2 / 439.37 | 3.8% |
| Caitlyn / BOTTOM | Win | Economy | 26 / 35 | 502.33 / 532.23 | 6.0% |
| Caitlyn / BOTTOM | Loss | Kill participation | 37 / 37 | 43.22 / 41.87 | -3.1% |
| Caitlyn / BOTTOM | Win | Kill participation | 26 / 35 | 40.8 / 50.4 | 23.5% |
| Caitlyn / BOTTOM | Loss | Objective pressure | 37 / 37 | 234.95 / 271.7 | 15.6% |
| Caitlyn / BOTTOM | Win | Objective pressure | 26 / 35 | 615.71 / 760.31 | 23.5% |
| Caitlyn / BOTTOM | Loss | Survival | 37 / 37 | 0.28 / 0.27 | -3.8% |
| Caitlyn / BOTTOM | Win | Survival | 26 / 35 | 0.21 / 0.21 | 1.3% |
| Caitlyn / BOTTOM | Loss | Vision | 37 / 37 | 0.57 / 0.65 | 13.8% |
| Caitlyn / BOTTOM | Win | Vision | 26 / 35 | 0.61 / 0.79 | 30.1% |
| Diana / JUNGLE | Loss | Champion damage | 12 / 14 | 533.69 / 904.66 | 69.5% |
| Diana / JUNGLE | Loss | Economy | 12 / 14 | 354.89 / 459.81 | 29.6% |
| Diana / JUNGLE | Loss | Kill participation | 12 / 14 | 43.79 / 52.85 | 20.7% |
| Diana / JUNGLE | Loss | Objective pressure | 12 / 14 | 443.96 / 614.52 | 38.4% |
| Diana / JUNGLE | Loss | Survival | 12 / 14 | 0.33 / 0.26 | -22.4% |
| Diana / JUNGLE | Loss | Vision | 12 / 14 | 0.73 / 0.74 | 1.9% |
| Diana / MIDDLE | Loss | Champion damage | 10 / 11 | 828.32 / 1006.86 | 21.6% |
| Diana / MIDDLE | Loss | Economy | 10 / 11 | 412.35 / 415.91 | 0.9% |
| Diana / MIDDLE | Loss | Kill participation | 10 / 11 | 50.9 / 46.46 | -8.7% |
| Diana / MIDDLE | Loss | Objective pressure | 10 / 11 | 233.99 / 397.24 | 69.8% |
| Diana / MIDDLE | Loss | Survival | 10 / 11 | 0.37 / 0.25 | -33.2% |
| Diana / MIDDLE | Loss | Vision | 10 / 11 | 0.71 / 0.73 | 2.9% |
| Fizz / MIDDLE | Win | Champion damage | 15 / 15 | 988.95 / 1189.02 | 20.2% |
| Fizz / MIDDLE | Win | Economy | 15 / 15 | 488.58 / 483.7 | -1.0% |
| Fizz / MIDDLE | Win | Kill participation | 15 / 15 | 44.01 / 48.36 | 9.9% |
| Fizz / MIDDLE | Win | Objective pressure | 15 / 15 | 482.92 / 430.54 | -10.8% |
| Fizz / MIDDLE | Win | Survival | 15 / 15 | 0.16 / 0.21 | 32.6% |
| Fizz / MIDDLE | Win | Vision | 15 / 15 | 0.69 / 0.82 | 18.0% |
| Jhin / BOTTOM | Win | Champion damage | 22 / 27 | 857.77 / 976.1 | 13.8% |
| Jhin / BOTTOM | Win | Economy | 22 / 27 | 506.37 / 488.19 | -3.6% |
| Jhin / BOTTOM | Win | Kill participation | 22 / 27 | 47.94 / 51.78 | 8.0% |
| Jhin / BOTTOM | Win | Objective pressure | 22 / 27 | 454.43 / 600.58 | 32.2% |
| Jhin / BOTTOM | Win | Survival | 22 / 27 | 0.16 / 0.16 | -1.4% |
| Jhin / BOTTOM | Win | Vision | 22 / 27 | 0.64 / 0.66 | 3.1% |
| Jinx / BOTTOM | Loss | Champion damage | 16 / 24 | 505.48 / 799.88 | 58.2% |
| Jinx / BOTTOM | Win | Champion damage | 26 / 26 | 928.9 / 1168.49 | 25.8% |
| Jinx / BOTTOM | Loss | Economy | 16 / 24 | 384.17 / 436.46 | 13.6% |
| Jinx / BOTTOM | Win | Economy | 26 / 26 | 508.4 / 533.32 | 4.9% |
| Jinx / BOTTOM | Loss | Kill participation | 16 / 24 | 44.86 / 44.24 | -1.4% |
| Jinx / BOTTOM | Win | Kill participation | 26 / 26 | 48.08 / 54.59 | 13.6% |
| Jinx / BOTTOM | Loss | Objective pressure | 16 / 24 | 138.1 / 302.72 | 119.2% |
| Jinx / BOTTOM | Win | Objective pressure | 26 / 26 | 640.89 / 708.46 | 10.5% |
| Jinx / BOTTOM | Loss | Survival | 16 / 24 | 0.31 / 0.24 | -24.6% |
| Jinx / BOTTOM | Win | Survival | 26 / 26 | 0.16 / 0.19 | 14.8% |
| Jinx / BOTTOM | Loss | Vision | 16 / 24 | 0.5 / 0.71 | 40.4% |
| Jinx / BOTTOM | Win | Vision | 26 / 26 | 0.66 / 0.67 | 2.8% |
| Kaisa / BOTTOM | Loss | Champion damage | 13 / 13 | 554.41 / 803.06 | 44.8% |
| Kaisa / BOTTOM | Loss | Economy | 13 / 13 | 407.11 / 439.56 | 8.0% |
| Kaisa / BOTTOM | Loss | Kill participation | 13 / 13 | 47.48 / 44.86 | -5.5% |
| Kaisa / BOTTOM | Loss | Objective pressure | 13 / 13 | 159.32 / 271.59 | 70.5% |
| Kaisa / BOTTOM | Loss | Survival | 13 / 13 | 0.31 / 0.25 | -19.7% |
| Kaisa / BOTTOM | Loss | Vision | 13 / 13 | 0.56 / 0.62 | 12.0% |
| Katarina / MIDDLE | Loss | Champion damage | 10 / 23 | 760.1 / 865.99 | 13.9% |
| Katarina / MIDDLE | Loss | Economy | 10 / 23 | 407.69 / 394.87 | -3.1% |
| Katarina / MIDDLE | Loss | Kill participation | 10 / 23 | 46.92 / 48.4 | 3.1% |
| Katarina / MIDDLE | Loss | Objective pressure | 10 / 23 | 127.23 / 151.92 | 19.4% |
| Katarina / MIDDLE | Loss | Survival | 10 / 23 | 0.31 / 0.3 | -3.7% |
| Katarina / MIDDLE | Loss | Vision | 10 / 23 | 0.56 / 0.8 | 42.6% |
| Kayle / TOP | Win | Champion damage | 10 / 15 | 926.41 / 1163.79 | 25.6% |
| Kayle / TOP | Win | Economy | 10 / 15 | 472.21 / 483.99 | 2.5% |
| Kayle / TOP | Win | Kill participation | 10 / 15 | 34.37 / 41.72 | 21.4% |
| Kayle / TOP | Win | Objective pressure | 10 / 15 | 589.54 / 635.66 | 7.8% |
| Kayle / TOP | Win | Survival | 10 / 15 | 0.14 / 0.22 | 55.1% |
| Kayle / TOP | Win | Vision | 10 / 15 | 0.79 / 0.83 | 4.3% |
| Kayn / JUNGLE | Loss | Champion damage | 11 / 28 | 678.84 / 737.79 | 8.7% |
| Kayn / JUNGLE | Win | Champion damage | 13 / 20 | 793.9 / 980.73 | 23.5% |
| Kayn / JUNGLE | Loss | Economy | 11 / 28 | 405.49 / 420.23 | 3.6% |
| Kayn / JUNGLE | Win | Economy | 13 / 20 | 497.84 / 470.57 | -5.5% |
| Kayn / JUNGLE | Loss | Kill participation | 11 / 28 | 42.36 / 46.03 | 8.7% |
| Kayn / JUNGLE | Win | Kill participation | 13 / 20 | 48.59 / 43.32 | -10.8% |
| Kayn / JUNGLE | Loss | Objective pressure | 11 / 28 | 358.79 / 567.39 | 58.1% |
| Kayn / JUNGLE | Win | Objective pressure | 13 / 20 | 1477.83 / 988.68 | -33.1% |
| Kayn / JUNGLE | Loss | Survival | 11 / 28 | 0.31 / 0.28 | -8.7% |
| Kayn / JUNGLE | Win | Survival | 13 / 20 | 0.13 / 0.23 | 79.3% |
| Kayn / JUNGLE | Loss | Vision | 11 / 28 | 0.73 / 0.8 | 8.9% |
| Kayn / JUNGLE | Win | Vision | 13 / 20 | 0.79 / 0.93 | 17.0% |
| Khazix / JUNGLE | Loss | Champion damage | 10 / 10 | 441.17 / 730.9 | 65.7% |
| Khazix / JUNGLE | Win | Champion damage | 11 / 14 | 809.49 / 812.5 | 0.4% |
| Khazix / JUNGLE | Loss | Economy | 10 / 10 | 366.99 / 433.94 | 18.2% |
| Khazix / JUNGLE | Win | Economy | 11 / 14 | 514.19 / 493.44 | -4.0% |
| Khazix / JUNGLE | Loss | Kill participation | 10 / 10 | 37.25 / 38.59 | 3.6% |
| Khazix / JUNGLE | Win | Kill participation | 11 / 14 | 39.66 / 44.1 | 11.2% |
| Khazix / JUNGLE | Loss | Objective pressure | 10 / 10 | 291.43 / 660.14 | 126.5% |
| Khazix / JUNGLE | Win | Objective pressure | 11 / 14 | 1357.64 / 1151.05 | -15.2% |
| Khazix / JUNGLE | Loss | Survival | 10 / 10 | 0.27 / 0.29 | 7.5% |
| Khazix / JUNGLE | Win | Survival | 11 / 14 | 0.16 / 0.21 | 25.7% |
| Khazix / JUNGLE | Loss | Vision | 10 / 10 | 0.82 / 0.92 | 12.9% |
| Khazix / JUNGLE | Win | Vision | 11 / 14 | 1.03 / 1.02 | -0.9% |
| Lux / UTILITY | Loss | Champion damage | 15 / 15 | 631.34 / 696.19 | 10.3% |
| Lux / UTILITY | Win | Champion damage | 16 / 21 | 719.22 / 839.78 | 16.8% |
| Lux / UTILITY | Loss | Economy | 15 / 15 | 309.41 / 305.36 | -1.3% |
| Lux / UTILITY | Win | Economy | 16 / 21 | 360.44 / 367.97 | 2.1% |
| Lux / UTILITY | Loss | Kill participation | 15 / 15 | 47.5 / 41.57 | -12.5% |
| Lux / UTILITY | Win | Kill participation | 16 / 21 | 46.61 / 53.12 | 14.0% |
| Lux / UTILITY | Loss | Objective pressure | 15 / 15 | 65.35 / 83.71 | 28.1% |
| Lux / UTILITY | Win | Objective pressure | 16 / 21 | 177.67 / 176.03 | -0.9% |
| Lux / UTILITY | Loss | Survival | 15 / 15 | 0.33 / 0.28 | -15.3% |
| Lux / UTILITY | Win | Survival | 16 / 21 | 0.16 / 0.22 | 42.9% |
| Lux / UTILITY | Loss | Vision | 15 / 15 | 1.51 / 1.81 | 19.9% |
| Lux / UTILITY | Win | Vision | 16 / 21 | 2.18 / 2.21 | 1.1% |
| Malphite / TOP | Win | Champion damage | 13 / 12 | 740.76 / 823.26 | 11.1% |
| Malphite / TOP | Win | Crowd control | 13 / 12 | 1.07 / 1.13 | 5.8% |
| Malphite / TOP | Win | Economy | 13 / 12 | 394.02 / 390.46 | -0.9% |
| Malphite / TOP | Win | Kill participation | 13 / 12 | 35.47 / 35.32 | -0.4% |
| Malphite / TOP | Win | Objective pressure | 13 / 12 | 440.17 / 338.52 | -23.1% |
| Malphite / TOP | Win | Survival | 13 / 12 | 0.07 / 0.17 | 140.2% |
| Malphite / TOP | Win | Vision | 13 / 12 | 0.75 / 0.82 | 8.9% |
| Malzahar / MIDDLE | Loss | Champion damage | 12 / 13 | 697.32 / 1062.56 | 52.4% |
| Malzahar / MIDDLE | Win | Champion damage | 12 / 18 | 942.22 / 941.59 | -0.1% |
| Malzahar / MIDDLE | Loss | Economy | 12 / 13 | 369.7 / 419.76 | 13.5% |
| Malzahar / MIDDLE | Win | Economy | 12 / 18 | 473.1 / 443.74 | -6.2% |
| Malzahar / MIDDLE | Loss | Kill participation | 12 / 13 | 31.71 / 43.88 | 38.4% |
| Malzahar / MIDDLE | Win | Kill participation | 12 / 18 | 37.59 / 37.84 | 0.7% |
| Malzahar / MIDDLE | Loss | Objective pressure | 12 / 13 | 199.24 / 243.94 | 22.4% |
| Malzahar / MIDDLE | Win | Objective pressure | 12 / 18 | 546.8 / 426.6 | -22.0% |
| Malzahar / MIDDLE | Loss | Survival | 12 / 13 | 0.3 / 0.26 | -11.1% |
| Malzahar / MIDDLE | Win | Survival | 12 / 18 | 0.16 / 0.21 | 27.2% |
| Malzahar / MIDDLE | Loss | Vision | 12 / 13 | 0.67 / 0.64 | -4.2% |
| Malzahar / MIDDLE | Win | Vision | 12 / 18 | 0.62 / 0.7 | 13.2% |
| MissFortune / BOTTOM | Loss | Champion damage | 22 / 36 | 730.43 / 789.84 | 8.1% |
| MissFortune / BOTTOM | Win | Champion damage | 29 / 35 | 846.42 / 1034.34 | 22.2% |
| MissFortune / BOTTOM | Loss | Economy | 22 / 36 | 443.88 / 451.85 | 1.8% |
| MissFortune / BOTTOM | Win | Economy | 29 / 35 | 524.96 / 540.49 | 3.0% |
| MissFortune / BOTTOM | Loss | Kill participation | 22 / 36 | 45.86 / 46.25 | 0.8% |
| MissFortune / BOTTOM | Win | Kill participation | 29 / 35 | 45.37 / 49.54 | 9.2% |
| MissFortune / BOTTOM | Loss | Objective pressure | 22 / 36 | 208.7 / 266.72 | 27.8% |
| MissFortune / BOTTOM | Win | Objective pressure | 29 / 35 | 542.57 / 560.35 | 3.3% |
| MissFortune / BOTTOM | Loss | Survival | 22 / 36 | 0.32 / 0.28 | -10.0% |
| MissFortune / BOTTOM | Win | Survival | 29 / 35 | 0.14 / 0.2 | 40.8% |
| MissFortune / BOTTOM | Loss | Vision | 22 / 36 | 0.57 / 0.72 | 25.7% |
| MissFortune / BOTTOM | Win | Vision | 29 / 35 | 0.66 / 0.78 | 18.5% |
| Mordekaiser / TOP | Loss | Champion damage | 11 / 10 | 728.18 / 989.52 | 35.9% |
| Mordekaiser / TOP | Win | Champion damage | 10 / 21 | 1090.31 / 1109.12 | 1.7% |
| Mordekaiser / TOP | Loss | Economy | 11 / 10 | 387.41 / 423.92 | 9.4% |
| Mordekaiser / TOP | Win | Economy | 10 / 21 | 465.25 / 437.23 | -6.0% |
| Mordekaiser / TOP | Loss | Kill participation | 11 / 10 | 34.59 / 43.41 | 25.5% |
| Mordekaiser / TOP | Win | Kill participation | 10 / 21 | 38.18 / 34.94 | -8.5% |
| Mordekaiser / TOP | Loss | Objective pressure | 11 / 10 | 226.97 / 353.35 | 55.7% |
| Mordekaiser / TOP | Win | Objective pressure | 10 / 21 | 471.35 / 464.0 | -1.6% |
| Mordekaiser / TOP | Loss | Survival | 11 / 10 | 0.29 / 0.24 | -17.0% |
| Mordekaiser / TOP | Win | Survival | 10 / 21 | 0.2 / 0.18 | -9.8% |
| Mordekaiser / TOP | Loss | Vision | 11 / 10 | 0.71 / 0.73 | 2.2% |
| Mordekaiser / TOP | Win | Vision | 10 / 21 | 0.71 / 0.8 | 13.0% |
| Nautilus / UTILITY | Loss | Champion damage | 15 / 18 | 315.18 / 441.58 | 40.1% |
| Nautilus / UTILITY | Loss | Crowd control | 15 / 18 | 2.02 / 2.32 | 14.7% |
| Nautilus / UTILITY | Loss | Economy | 15 / 18 | 287.32 / 298.53 | 3.9% |
| Nautilus / UTILITY | Loss | Kill participation | 15 / 18 | 48.92 / 52.53 | 7.4% |
| Nautilus / UTILITY | Loss | Objective pressure | 15 / 18 | 35.35 / 50.57 | 43.1% |
| Nautilus / UTILITY | Loss | Survival | 15 / 18 | 0.28 / 0.29 | 3.2% |
| Nautilus / UTILITY | Loss | Vision | 15 / 18 | 1.58 / 1.98 | 25.0% |
| Nocturne / JUNGLE | Win | Champion damage | 11 / 10 | 577.02 / 791.1 | 37.1% |
| Nocturne / JUNGLE | Win | Economy | 11 / 10 | 453.82 / 468.08 | 3.1% |
| Nocturne / JUNGLE | Win | Kill participation | 11 / 10 | 39.27 / 53.07 | 35.1% |
| Nocturne / JUNGLE | Win | Objective pressure | 11 / 10 | 1053.96 / 1193.55 | 13.2% |
| Nocturne / JUNGLE | Win | Survival | 11 / 10 | 0.13 / 0.14 | 11.6% |
| Nocturne / JUNGLE | Win | Vision | 11 / 10 | 0.76 / 0.78 | 3.0% |
| Renekton / TOP | Loss | Champion damage | 11 / 12 | 717.01 / 825.38 | 15.1% |
| Renekton / TOP | Loss | Economy | 11 / 12 | 381.5 / 403.31 | 5.7% |
| Renekton / TOP | Loss | Kill participation | 11 / 12 | 32.21 / 38.77 | 20.4% |
| Renekton / TOP | Loss | Objective pressure | 11 / 12 | 274.5 / 288.14 | 5.0% |
| Renekton / TOP | Loss | Survival | 11 / 12 | 0.24 / 0.26 | 8.3% |
| Renekton / TOP | Loss | Vision | 11 / 12 | 0.65 / 0.77 | 18.3% |
| Samira / BOTTOM | Loss | Champion damage | 14 / 13 | 704.35 / 762.49 | 8.3% |
| Samira / BOTTOM | Win | Champion damage | 18 / 15 | 990.87 / 1136.15 | 14.7% |
| Samira / BOTTOM | Loss | Economy | 14 / 13 | 442.46 / 452.43 | 2.3% |
| Samira / BOTTOM | Win | Economy | 18 / 15 | 553.27 / 566.65 | 2.4% |
| Samira / BOTTOM | Loss | Kill participation | 14 / 13 | 52.64 / 42.07 | -20.1% |
| Samira / BOTTOM | Win | Kill participation | 18 / 15 | 49.33 / 52.27 | 6.0% |
| Samira / BOTTOM | Loss | Objective pressure | 14 / 13 | 124.41 / 229.17 | 84.2% |
| Samira / BOTTOM | Win | Objective pressure | 18 / 15 | 484.07 / 517.53 | 6.9% |
| Samira / BOTTOM | Loss | Survival | 14 / 13 | 0.34 / 0.29 | -13.3% |
| Samira / BOTTOM | Win | Survival | 18 / 15 | 0.2 / 0.22 | 10.7% |
| Samira / BOTTOM | Loss | Vision | 14 / 13 | 0.57 / 0.63 | 10.8% |
| Samira / BOTTOM | Win | Vision | 18 / 15 | 0.65 / 0.79 | 21.5% |
| Sett / TOP | Loss | Champion damage | 11 / 17 | 783.31 / 856.91 | 9.4% |
| Sett / TOP | Win | Champion damage | 16 / 15 | 950.83 / 1087.22 | 14.3% |
| Sett / TOP | Loss | Economy | 11 / 17 | 362.9 / 384.87 | 6.1% |
| Sett / TOP | Win | Economy | 16 / 15 | 455.16 / 436.65 | -4.1% |
| Sett / TOP | Loss | Kill participation | 11 / 17 | 33.2 / 33.82 | 1.9% |
| Sett / TOP | Win | Kill participation | 16 / 15 | 34.47 / 38.27 | 11.0% |
| Sett / TOP | Loss | Objective pressure | 11 / 17 | 286.72 / 372.9 | 30.1% |
| Sett / TOP | Win | Objective pressure | 16 / 15 | 697.77 / 566.25 | -18.8% |
| Sett / TOP | Loss | Survival | 11 / 17 | 0.29 / 0.28 | -4.1% |
| Sett / TOP | Win | Survival | 16 / 15 | 0.18 / 0.19 | 6.7% |
| Sett / TOP | Loss | Vision | 11 / 17 | 0.54 / 0.75 | 40.9% |
| Sett / TOP | Win | Vision | 16 / 15 | 0.68 / 0.7 | 2.3% |
| Smolder / BOTTOM | Loss | Champion damage | 15 / 18 | 599.09 / 971.15 | 62.1% |
| Smolder / BOTTOM | Win | Champion damage | 11 / 20 | 1202.37 / 1183.53 | -1.6% |
| Smolder / BOTTOM | Loss | Economy | 15 / 18 | 383.16 / 431.85 | 12.7% |
| Smolder / BOTTOM | Win | Economy | 11 / 20 | 544.53 / 504.92 | -7.3% |
| Smolder / BOTTOM | Loss | Kill participation | 15 / 18 | 39.46 / 43.56 | 10.4% |
| Smolder / BOTTOM | Win | Kill participation | 11 / 20 | 50.86 / 49.18 | -3.3% |
| Smolder / BOTTOM | Loss | Objective pressure | 15 / 18 | 128.18 / 218.99 | 70.8% |
| Smolder / BOTTOM | Win | Objective pressure | 11 / 20 | 409.67 / 449.03 | 9.6% |
| Smolder / BOTTOM | Loss | Survival | 15 / 18 | 0.26 / 0.29 | 11.6% |
| Smolder / BOTTOM | Win | Survival | 11 / 20 | 0.12 / 0.2 | 65.4% |
| Smolder / BOTTOM | Loss | Vision | 15 / 18 | 0.49 / 0.61 | 22.6% |
| Smolder / BOTTOM | Win | Vision | 11 / 20 | 0.62 / 0.71 | 15.1% |
| Teemo / TOP | Win | Champion damage | 11 / 10 | 978.78 / 1140.37 | 16.5% |
| Teemo / TOP | Win | Economy | 11 / 10 | 450.34 / 411.53 | -8.6% |
| Teemo / TOP | Win | Kill participation | 11 / 10 | 34.81 / 37.45 | 7.6% |
| Teemo / TOP | Win | Objective pressure | 11 / 10 | 528.2 / 469.16 | -11.2% |
| Teemo / TOP | Win | Survival | 11 / 10 | 0.16 / 0.22 | 32.5% |
| Teemo / TOP | Win | Vision | 11 / 10 | 0.69 / 0.84 | 22.8% |
| Veigar / MIDDLE | Win | Champion damage | 17 / 25 | 990.72 / 1181.82 | 19.3% |
| Veigar / MIDDLE | Win | Economy | 17 / 25 | 465.27 / 460.95 | -0.9% |
| Veigar / MIDDLE | Win | Kill participation | 17 / 25 | 41.64 / 46.54 | 11.7% |
| Veigar / MIDDLE | Win | Objective pressure | 17 / 25 | 529.77 / 490.12 | -7.5% |
| Veigar / MIDDLE | Win | Survival | 17 / 25 | 0.15 / 0.19 | 24.9% |
| Veigar / MIDDLE | Win | Vision | 17 / 25 | 0.61 / 0.79 | 29.3% |
| Viego / JUNGLE | Loss | Champion damage | 12 / 27 | 497.34 / 734.37 | 47.7% |
| Viego / JUNGLE | Win | Champion damage | 19 / 27 | 737.43 / 978.01 | 32.6% |
| Viego / JUNGLE | Loss | Economy | 12 / 27 | 409.59 / 439.91 | 7.4% |
| Viego / JUNGLE | Win | Economy | 19 / 27 | 503.49 / 514.0 | 2.1% |
| Viego / JUNGLE | Loss | Kill participation | 12 / 27 | 40.69 / 46.78 | 15.0% |
| Viego / JUNGLE | Win | Kill participation | 19 / 27 | 42.53 / 48.33 | 13.6% |
| Viego / JUNGLE | Loss | Objective pressure | 12 / 27 | 575.08 / 690.5 | 20.1% |
| Viego / JUNGLE | Win | Objective pressure | 19 / 27 | 1402.57 / 1315.8 | -6.2% |
| Viego / JUNGLE | Loss | Survival | 12 / 27 | 0.27 / 0.29 | 7.5% |
| Viego / JUNGLE | Win | Survival | 19 / 27 | 0.14 / 0.21 | 46.6% |
| Viego / JUNGLE | Loss | Vision | 12 / 27 | 0.86 / 0.96 | 12.7% |
| Viego / JUNGLE | Win | Vision | 19 / 27 | 0.84 / 0.87 | 2.8% |
| Volibear / JUNGLE | Loss | Champion damage | 11 / 11 | 524.89 / 838.94 | 59.8% |
| Volibear / JUNGLE | Loss | Economy | 11 / 11 | 396.2 / 438.72 | 10.7% |
| Volibear / JUNGLE | Loss | Kill participation | 11 / 11 | 46.7 / 57.02 | 22.1% |
| Volibear / JUNGLE | Loss | Objective pressure | 11 / 11 | 593.05 / 710.13 | 19.7% |
| Volibear / JUNGLE | Loss | Survival | 11 / 11 | 0.28 / 0.25 | -10.9% |
| Volibear / JUNGLE | Loss | Vision | 11 / 11 | 0.82 / 0.81 | -1.7% |
| Warwick / JUNGLE | Loss | Champion damage | 11 / 11 | 552.63 / 592.62 | 7.2% |
| Warwick / JUNGLE | Loss | Economy | 11 / 11 | 403.42 / 404.55 | 0.3% |
| Warwick / JUNGLE | Loss | Kill participation | 11 / 11 | 59.4 / 44.36 | -25.3% |
| Warwick / JUNGLE | Loss | Objective pressure | 11 / 11 | 531.38 / 700.49 | 31.8% |
| Warwick / JUNGLE | Loss | Survival | 11 / 11 | 0.34 / 0.33 | -3.7% |
| Warwick / JUNGLE | Loss | Vision | 11 / 11 | 0.69 / 0.8 | 15.9% |
| Yasuo / MIDDLE | Loss | Champion damage | 18 / 15 | 681.95 / 840.75 | 23.3% |
| Yasuo / MIDDLE | Win | Champion damage | 17 / 28 | 907.93 / 1051.85 | 15.9% |
| Yasuo / MIDDLE | Loss | Economy | 18 / 15 | 371.32 / 381.91 | 2.9% |
| Yasuo / MIDDLE | Win | Economy | 17 / 28 | 455.7 / 461.44 | 1.3% |
| Yasuo / MIDDLE | Loss | Kill participation | 18 / 15 | 39.31 / 36.91 | -6.1% |
| Yasuo / MIDDLE | Win | Kill participation | 17 / 28 | 40.33 / 41.04 | 1.8% |
| Yasuo / MIDDLE | Loss | Objective pressure | 18 / 15 | 209.9 / 292.04 | 39.1% |
| Yasuo / MIDDLE | Win | Objective pressure | 17 / 28 | 435.89 / 650.82 | 49.3% |
| Yasuo / MIDDLE | Loss | Survival | 18 / 15 | 0.29 / 0.35 | 23.0% |
| Yasuo / MIDDLE | Win | Survival | 17 / 28 | 0.21 / 0.26 | 27.8% |
| Yasuo / MIDDLE | Loss | Vision | 18 / 15 | 0.53 / 0.64 | 21.5% |
| Yasuo / MIDDLE | Win | Vision | 17 / 28 | 0.62 / 0.74 | 18.1% |
| Yone / MIDDLE | Loss | Champion damage | 15 / 14 | 669.77 / 1027.11 | 53.4% |
| Yone / MIDDLE | Loss | Economy | 15 / 14 | 370.06 / 399.36 | 7.9% |
| Yone / MIDDLE | Loss | Kill participation | 15 / 14 | 37.74 / 39.44 | 4.5% |
| Yone / MIDDLE | Loss | Objective pressure | 15 / 14 | 164.75 / 231.04 | 40.2% |
| Yone / MIDDLE | Loss | Survival | 15 / 14 | 0.35 / 0.32 | -9.0% |
| Yone / MIDDLE | Loss | Vision | 15 / 14 | 0.55 / 0.61 | 12.5% |
| Zed / MIDDLE | Win | Champion damage | 16 / 15 | 1010.01 / 867.08 | -14.2% |
| Zed / MIDDLE | Win | Economy | 16 / 15 | 448.28 / 423.99 | -5.4% |
| Zed / MIDDLE | Win | Kill participation | 16 / 15 | 41.01 / 40.51 | -1.2% |
| Zed / MIDDLE | Win | Objective pressure | 16 / 15 | 350.73 / 315.0 | -10.2% |
| Zed / MIDDLE | Win | Survival | 16 / 15 | 0.16 / 0.21 | 29.0% |
| Zed / MIDDLE | Win | Vision | 16 / 15 | 0.66 / 0.7 | 7.5% |

## Champion-specific targets

Champion-role diagnostics and raw medians are in the JSON companion (minimum 20 cases). They are NOT proposed targets: duration/outcome/player composition affects these medians. Do not fit full-score targets to them.

A future reference hierarchy should be champion + role → archetype + role → role, with sample-dependent shrinkage and explicit coverage. Use champion-specific damage/utility/CC references where functions differ; avoid unique champion survival or participation rules without evidence. Reference samples should be independent of the rated player, conditioned on duration and ideally rank/patch. Small or absent reference samples must fall back rather than inventing champion targets.

## Decision

Do not promote this duration candidate or champion medians automatically. Check whether within-champion shifts replicate in held-out role groups and independent replay judgments. Outcome/duration mean flattening alone cannot prove fairer ratings. Preserve the existing model until that evidence exists.
