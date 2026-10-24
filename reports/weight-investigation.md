# Weight, curve and duration investigation

Read-only analysis of unique support performances in saved matches. No formula or saved scores changed. This is a selected history, not a representative population. Rounded component rates are used for sensitivity recombinations, so small rounding differences are possible.

## Baseline component contributions

### Damage support: 713 games, mean 59.759

| Component | Games | Mean component | Mean final points |
|---|---:|---:|---:|
| Champion damage | 713 | 78.134 | 23.441 |
| Economy | 713 | 83.017 | 4.151 |
| Kill participation | 713 | 45.659 | 11.417 |
| Objective pressure | 713 | 55.918 | 2.796 |
| Survival | 713 | 32.088 | 4.815 |
| Vision | 713 | 65.722 | 13.145 |

Most frequent champions: Zyra (437), Lux (80), Mel (27), Neeko (20), Velkoz (20)

### Tank support: 232 games, mean 47.363

| Component | Games | Mean component | Mean final points |
|---|---:|---:|---:|
| Champion damage | 232 | 40.943 | 4.095 |
| Crowd control | 232 | 67.383 | 10.109 |
| Economy | 232 | 67.046 | 3.352 |
| Kill participation | 232 | 47.467 | 11.866 |
| Objective pressure | 232 | 33.582 | 3.359 |
| Survival | 232 | 37.975 | 7.595 |
| Vision | 232 | 46.622 | 6.991 |

Most frequent champions: Nautilus (63), Leona (41), TahmKench (26), Braum (24), Blitzcrank (23)

### Utility support: 538 games, mean 51.107

| Component | Games | Mean component | Mean final points |
|---|---:|---:|---:|
| Economy | 538 | 67.971 | 6.796 |
| Kill participation | 538 | 52.11 | 13.029 |
| Objective pressure | 538 | 39.862 | 1.993 |
| Support impact | 538 | 47.941 | 9.588 |
| Survival | 538 | 45.442 | 9.088 |
| Vision | 538 | 53.061 | 10.612 |

Most frequent champions: Morgana (88), Nami (67), Senna (52), Lulu (45), Milio (44)

## Controlled sensitivity comparisons

All comparisons below use the same complete six-component support cases. CC is omitted from both groups and remaining weights rescaled; consequently these are diagnostic ablations, not proposed replacement scores. The final row also equalizes damage references. Different roles/functions cannot be made equivalent merely by equal weights.

| Experiment | Damage support | Tank support | Gap |
|---|---:|---:|---:|
| Six components: original weights / v4 curves | 59.764 | 43.837 | 15.927 |
| Six components: equal weights / v4 curves | 60.095 | 45.607 | 14.488 |
| Six components: original weights / linear curves | 70.544 | 53.996 | 16.548 |
| Six components: equal weights / linear curves | 66.916 | 56.511 | 10.405 |
| Six components: equal weights / common damage reference 800 / v4 | 60.095 | 43.486 | 16.609 |

## Duration within archetype and outcome

| Duration | Outcome | Archetype | Games | Mean |
|---|---|---|---:|---:|
| Under 20 | Win | Damage support | 13 | 46.346 |
| Under 20 | Win | Tank support | 4 | 54.825 |
| Under 20 | Win | Utility support | 7 | 45.2 |
| Under 20 | Loss | Damage support | 11 | 26.018 |
| Under 20 | Loss | Tank support | 3 | 21.1 |
| Under 20 | Loss | Utility support | 10 | 29.95 |
| 20–30 | Win | Damage support | 130 | 62.705 |
| 20–30 | Win | Tank support | 39 | 52.074 |
| 20–30 | Win | Utility support | 99 | 55.252 |
| 20–30 | Loss | Damage support | 115 | 48.965 |
| 20–30 | Loss | Tank support | 42 | 39.0 |
| 20–30 | Loss | Utility support | 111 | 41.417 |
| 30–40 | Win | Damage support | 183 | 66.502 |
| 30–40 | Win | Tank support | 51 | 54.686 |
| 30–40 | Win | Utility support | 138 | 58.401 |
| 30–40 | Loss | Damage support | 178 | 57.393 |
| 30–40 | Loss | Tank support | 70 | 43.983 |
| 30–40 | Loss | Utility support | 123 | 48.493 |
| 40+ | Win | Damage support | 40 | 67.897 |
| 40+ | Win | Tank support | 11 | 54.291 |
| 40+ | Win | Utility support | 27 | 59.93 |
| 40+ | Loss | Damage support | 43 | 65.928 |
| 40+ | Loss | Tank support | 12 | 47.65 |
| 40+ | Loss | Utility support | 23 | 50.87 |

Shared outcome/duration stratum gap: **11.743 points**. Each cell is weighted by the smaller group count, restricting comparisons to overlap; this does not control for champion, player, patch, or match difficulty.

## Same-match opposing support pairs

Pairs share exact duration, but necessarily have opposite outcomes. Separate by damage-support outcome:

```json
{
  "True": {
    "matches": 70,
    "gap": 25.764
  },
  "False": {
    "matches": 57,
    "gap": 3.226
  }
}
```

## Excluding both configured players

Other players remain drawn from the same selected matches; this reduces direct main-champion influence without providing an independent population sample.

```json
{
  "Damage support": {
    "count": 278,
    "mean": 53.337
  },
  "Tank support": {
    "count": 200,
    "mean": 47.625
  },
  "Utility support": {
    "count": 375,
    "mean": 50.883
  }
}
```

## Limits

These experiments isolate arithmetic effects on this sample, not causal fairness. Linear curves are an ablation, not an endorsed return to v3. Duration trends can reflect game phase, match selection, champion mix and performance; small short-game cells are noisy. Do not equalize archetype means automatically or fit a duration correction from these averages alone.

## Findings

- The observed damage-support/tank-support gap is 12.396 points. Matching the duration/outcome mix in overlapping cells leaves an 11.743-point gap. Duration mix alone does not explain it.
- In the six-component comparison (CC omitted consistently), equal weights reduce the gap only from 15.927 to 14.488 points. The present weight schedule is not the whole explanation; CC currently helps tanks rather than driving their disadvantage.
- On shared components, damage supports earn much higher damage, economy, and vision component scores; tank supports actually have higher survival and participation component means. It would be incorrect to attribute the gap simply to poor tank survival.
- Excluding both configured players reduces the native gap to 5.712 points. Main-champion/player selection therefore materially affects the pooled comparison. It does not prove the residual gap is unfair.
- Damage supports in losses score higher than opposing winning tank supports by 3.226 points on average across 57 same-match pairs. This is a useful review set, not proof that the winner should always score higher.
- Short games are both shorter opportunities and small subgroups: under-20 tank supports have only four wins and three losses. Their mean is unstable; the duration trend is also present in the much larger 20–30 and 30–40 damage-support groups, so it cannot be dismissed entirely as a small-sample effect.
- Do not adopt equal weights or a flat short-game bonus from this audit. Review benchmark suitability for damage/utility and game phase using independent match evidence; keep role-specific functional differences visible.
