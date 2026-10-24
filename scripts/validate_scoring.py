"""Read-only audit of saved Rift Scores; no Riot calls or benchmark fitting."""
import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scoring import VERSION, score_player
from app.history_policy import eligible_info


def mean(values):
    return round(statistics.mean(values), 2) if values else None


def auc(rows):
    """Mann–Whitney AUC with half credit for tied scores; association, not prediction."""
    ordered = sorted(rows, key=lambda r: r['score'])
    positives = sum(r['win'] for r in ordered)
    negatives = len(ordered) - positives
    if not positives or not negatives:
        return None
    rank_sum = 0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end]['score'] == ordered[index]['score']:
            end += 1
        rank_sum += (index + 1 + end) / 2 * sum(r['win'] for r in ordered[index:end])
        index = end
    return round((rank_sum - positives * (positives + 1) / 2) / (positives * negatives), 3)


def describe(rows):
    return {'games': len(rows), 'mean': mean([r['score'] for r in rows]),
            'wins': sum(r['win'] for r in rows),
            'winMean': mean([r['score'] for r in rows if r['win']]),
            'lossMean': mean([r['score'] for r in rows if not r['win']]),
            'outcomeAUC': auc(rows)}


def audit(database):
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    profiles = {owner: json.loads(body) for owner, body in db.execute('SELECT player,body FROM profiles')}
    rows = db.execute('SELECT m.player,m.id,m.body,d.body FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id').fetchall()
    db.close()
    own_rows = defaultdict(list)
    participants = {}
    checks = defaultdict(int, {key: 0 for key in ('invalidScores', 'savedScoreMismatches', 'staleVersions', 'monotonicFailures', 'missingDetails')})
    examples = []
    for owner, match_id, body, detail_body in rows:
        summary = json.loads(body)
        if not detail_body:
            checks['missingDetails'] += 1
            continue
        detail = json.loads(detail_body)
        info = detail['raw']['info']
        if not eligible_info(info):
            continue
        catalog = {c['championId']: c.get('tags') for c in profiles.get(owner, {}).get('champions', [])}
        for p in info['participants']:
            result = score_player(info, p, catalog.get(p['championId']))
            own = p.get('puuid') == detail['puuid']
            value = result['value']
            if value is None:
                checks['unscoredParticipantEvaluations'] += 1
                continue
            if not math.isfinite(value) or not 0 <= value <= 100:
                checks['invalidScores'] += 1
            row = {'score': value, 'win': bool(p['win']), 'role': p.get('teamPosition', 'UNKNOWN'),
                   'style': result['archetype'], 'duration': info['gameDuration'], 'match': match_id,
                   'champion': p['championName'], 'team': p['teamId']}
            participants.setdefault((match_id, p['puuid']), row)
            if own:
                own_rows[owner].append(row)
                checks['ownScoresChecked'] += 1
                if summary.get('scoreVersion') != VERSION:
                    checks['staleVersions'] += 1
                if summary.get('score') != value:
                    checks['savedScoreMismatches'] += 1
                for field, increment, improves in [('totalDamageDealtToChampions', 1000, True), ('goldEarned', 1000, True), ('deaths', 1, False)]:
                    if field not in p:
                        continue
                    modified = {**p, field: p[field] + increment}
                    changed = score_player(info, modified, catalog.get(p['championId']))['value']
                    checks['monotonicChecks'] += 1
                    if changed is None or (changed < value if improves else changed > value):
                        checks['monotonicFailures'] += 1
            if match_id == 'EUN1_4017526326' and p['championName'] in ('Skarner', 'Urgot', 'Lux') and not any(e['champion'] == p['championName'] for e in examples):
                examples.append({**row, 'components': result['components']})
    all_rows = list(participants.values())
    groups = defaultdict(list)
    for r in all_rows:
        groups[r['match']].append(r)
    top_winner = 0
    for game in groups.values():
        best = max(r['score'] for r in game)
        winners = [r for r in game if r['score'] == best]
        top_winner += sum(r['win'] for r in winners) / len(winners)
    def breakdown(rows, key):
        return {name: describe([r for r in rows if r[key] == name]) for name in sorted({r[key] for r in rows})}
    outcome_duration = []
    for label, low, high in [('Under 20', 0, 1200), ('20–30', 1200, 1800), ('30–40', 1800, 2400), ('40+', 2400, math.inf)]:
        outcome_duration.append({'band': label, **describe([r for r in all_rows if low <= r['duration'] < high])})
    return {'version': VERSION, 'checks': dict(checks), 'profiles': {owner: {'overall': describe(rs), 'roles': breakdown(rs, 'role'), 'archetypes': breakdown(rs, 'style')} for owner, rs in own_rows.items()},
            'allParticipants': describe(all_rows), 'uniqueMatches': len(groups),
            'topScoreOnWinningTeamPercent': round(100 * top_winner / len(groups), 1) if groups else None,
            'roles': breakdown(all_rows, 'role'), 'archetypes': breakdown(all_rows, 'style'),
            'duration': outcome_duration, 'examples': examples}


def markdown(report):
    lines = [f'# Rift Score v{report["version"]}: saved-data validation', '',
        '**Verdict: mechanically consistent where checks pass; not validated as a player-skill grade or a population percentile.**', '',
        'This audit reads the local database without modifying it or fetching Riot data. It uses all saved profiles, deduplicates shared match participants, and recalculates scores using current cached champion tags. Outcome association is retrospective: the score uses end-of-game data and cannot predict these outcomes before the match. These matches were selected through two saved profile histories and are not representative of the ranked population. Participants in the same match are correlated; no significance or causal claim is made.', '',
        '## Mechanical checks', '', '```json', json.dumps(report['checks'], indent=2), '```', '',
        '## Individual profiles', '', '| Profile | Games | Mean | Win mean | Loss mean | Outcome AUC |', '|---|---:|---:|---:|---:|---:|']
    for name, profile in report['profiles'].items():
        r = profile['overall']
        lines.append(f"| {name} | {r['games']} | {r['mean']} | {r['winMean']} | {r['lossMean']} | {r['outcomeAUC']} |")
    lines += ['', '## All unique participants', '', f"{report['uniqueMatches']} unique matches; {report['allParticipants']['games']} participants. Highest score belongs to the winning team in {report['topScoreOnWinningTeamPercent']}% of matches (ties split). This is a descriptive check, not ground truth for individual contribution.", '',
        'AUC here is the probability that a randomly selected winning participant scores above a randomly selected losing participant, with half credit for ties. 0.5 is no separation. A high value can also reflect team advantage already embedded in gold, damage, and objectives.', '']
    for title, rows in [('Roles', report['roles']), ('Archetypes', report['archetypes']), ('Duration bands (minutes)', {r['band']: r for r in report['duration']})]:
        lines += [f'## {title}', '', '| Group | Games | Mean | Win mean | Loss mean | Outcome AUC |', '|---|---:|---:|---:|---:|---:|']
        for name, r in rows.items():
            lines.append(f"| {name} | {r['games']} | {r['mean']} | {r['winMean']} | {r['lossMean']} | {r['outcomeAUC']} |")
        lines.append('')
    lines += ['## Interpretation limits and next validation', '',
        '- Curves and role references are product choices. No representative rank/patch/champion reference population establishes that 50 is average or 90 is exceptional.',
        '- Differences between profiles conflate champion pool, role, duration, opponents, and performance. They are not estimates of relative skill.',
        '- Mechanical monotonicity and outcome association are necessary sanity checks, not proof that rankings or numerical grades are fair.',
        '- The previously discussed Skarner game informed the curve design. It is a development example, not an independent validation case.',
        '- Independent validation needs replay judgments made without seeing the scores, including strong losses, weak wins, tanks, damage supports, and short games. Assess pairwise ordering and numerical anchors separately on cases not used for tuning.',
        '- Do not add a win bonus or fit each profile to a desired average based on this report.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    result = audit(ROOT / 'data/journal.sqlite3')
    output = ROOT / 'reports'
    output.mkdir(exist_ok=True)
    (output / 'scoring-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (output / 'scoring-validation.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('checks', 'allParticipants', 'uniqueMatches', 'topScoreOnWinningTeamPercent', 'roles', 'archetypes', 'duration')}, indent=2))
