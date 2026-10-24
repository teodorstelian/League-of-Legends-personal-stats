# Rift Score v4: saved-data validation

**Verdict: mechanically consistent where checks pass; not validated as a player-skill grade or a population percentile.**

This audit reads the local database without modifying it or fetching Riot data. It uses all saved profiles, deduplicates shared match participants, and recalculates scores using current cached champion tags. Outcome association is retrospective: the score uses end-of-game data and cannot predict these outcomes before the match. These matches were selected through two saved profile histories and are not representative of the ranked population. Participants in the same match are correlated; no significance or causal claim is made.

## Mechanical checks

```json
{
  "invalidScores": 0,
  "savedScoreMismatches": 0,
  "staleVersions": 0,
  "monotonicFailures": 0,
  "missingDetails": 0,
  "ownScoresChecked": 1074,
  "monotonicChecks": 3222
}
```

## Individual profiles

| Profile | Games | Mean | Win mean | Loss mean | Outcome AUC |
|---|---:|---:|---:|---:|---:|
| Bagabondu#1909 | 676 | 45.31 | 52.08 | 38.62 | 0.744 |
| Bagaboanda#6969 | 398 | 62.07 | 66.75 | 57.0 | 0.721 |

## All unique participants

742 unique matches; 7420 participants. Highest score belongs to the winning team in 87.7% of matches (ties split). This is a descriptive check, not ground truth for individual contribution.

AUC here is the probability that a randomly selected winning participant scores above a randomly selected losing participant, with half credit for ties. 0.5 is no separation. A high value can also reflect team advantage already embedded in gold, damage, and objectives.

## Roles

| Group | Games | Mean | Win mean | Loss mean | Outcome AUC |
|---|---:|---:|---:|---:|---:|
|  | 1 | 23.2 | None | 23.2 | None |
| BOTTOM | 1484 | 47.45 | 56.39 | 38.52 | 0.768 |
| JUNGLE | 1484 | 53.96 | 62.28 | 45.64 | 0.801 |
| MIDDLE | 1484 | 51.02 | 58.84 | 43.19 | 0.743 |
| TOP | 1484 | 51.97 | 59.1 | 44.84 | 0.734 |
| UTILITY | 1483 | 54.68 | 60.3 | 49.06 | 0.721 |

## Archetypes

| Group | Games | Mean | Win mean | Loss mean | Outcome AUC |
|---|---:|---:|---:|---:|---:|
| Assassin carry | 593 | 53.08 | 60.63 | 45.81 | 0.736 |
| Damage support | 713 | 59.76 | 64.59 | 54.66 | 0.708 |
| Fighter | 1752 | 50.99 | 59.44 | 42.88 | 0.774 |
| Mage carry | 1014 | 51.2 | 59.13 | 43.2 | 0.743 |
| Marksman carry | 1724 | 49.1 | 57.68 | 40.37 | 0.759 |
| Role baseline (unmapped tags) | 1 | 46.1 | 46.1 | None | None |
| Split-pusher | 243 | 58.88 | 67.05 | 50.23 | 0.791 |
| Tank | 610 | 51.83 | 58.02 | 45.27 | 0.784 |
| Tank support | 232 | 47.36 | 53.68 | 42.14 | 0.781 |
| Utility support | 538 | 51.11 | 57.06 | 45.06 | 0.74 |

## Duration bands (minutes)

| Group | Games | Mean | Win mean | Loss mean | Outcome AUC |
|---|---:|---:|---:|---:|---:|
| Under 20 | 240 | 37.37 | 49.87 | 24.87 | 0.899 |
| 20–30 | 2680 | 48.49 | 59.07 | 37.92 | 0.836 |
| 30–40 | 3720 | 53.96 | 59.89 | 48.03 | 0.713 |
| 40+ | 780 | 57.39 | 60.96 | 53.83 | 0.636 |

## Interpretation limits and next validation

- Curves and role references are product choices. No representative rank/patch/champion reference population establishes that 50 is average or 90 is exceptional.
- Differences between profiles conflate champion pool, role, duration, opponents, and performance. They are not estimates of relative skill.
- Mechanical monotonicity and outcome association are necessary sanity checks, not proof that rankings or numerical grades are fair.
- The previously discussed Skarner game informed the curve design. It is a development example, not an independent validation case.
- Independent validation needs replay judgments made without seeing the scores, including strong losses, weak wins, tanks, damage supports, and short games. Assess pairwise ordering and numerical anchors separately on cases not used for tuning.
- Do not add a win bonus or fit each profile to a desired average based on this report.
