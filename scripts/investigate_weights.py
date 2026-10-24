"""Read-only weight/curve/duration sensitivity audit; no production changes."""
import json
import math
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scoring import score_player, curve_score, CURVES
from app.history_policy import eligible_info

BANDS = [('Under 20', 0, 1200), ('20–30', 1200, 1800), ('30–40', 1800, 2400), ('40+', 2400, math.inf)]
COMMON = ['Champion damage', 'Kill participation', 'Survival', 'Economy', 'Vision', 'Objective pressure']


def average(values):
    return round(statistics.mean(values), 3) if values else None


def recombine(components, equal=False, linear=False, common_damage=None):
    """Compare identical six components; remove CC from both sides explicitly."""
    total = weight = 0
    for name in COMMON:
        c = components[name]
        reference = common_damage if name == 'Champion damage' and common_damage is not None else c['target']
        ratio = c['own'] / reference
        value = max(0, min(100, (1-ratio if name == 'Survival' else ratio) * 100)) if linear else curve_score(ratio, CURVES[name])
        w = 1 if equal else c['weight']
        total += value * w
        weight += w
    return total / weight


def run():
    db = sqlite3.connect((ROOT / 'data/journal.sqlite3').as_uri() + '?mode=ro', uri=True)
    profiles = {o: json.loads(b) for o, b in db.execute('SELECT player,body FROM profiles')}
    rows = db.execute('SELECT player,id,body FROM details ORDER BY player,id').fetchall()
    db.close()
    configured_players = {json.loads(b)['puuid'] for _, _, b in rows}
    seen, supports, paired = set(), [], defaultdict(list)
    for owner, mid, body in rows:
        d = json.loads(body); info = d['raw']['info']
        if not eligible_info(info): continue
        catalog = {c['championId']: c.get('tags') for c in profiles.get(owner, {}).get('champions', [])}
        for p in info['participants']:
            key = mid, p['puuid']
            if key in seen or p.get('teamPosition') != 'UTILITY': continue
            seen.add(key)
            score = score_player(info, p, catalog.get(p['championId']), duration_adjustment=False)
            if score['value'] is None: continue
            components = {c['name']: c for c in score['components']}
            row = {'match': mid, 'team': p['teamId'], 'style': score['archetype'], 'champion': p['championName'],
                   'win': bool(p['win']), 'duration': info['gameDuration'], 'score': score['value'],
                   'configuredPlayer': p['puuid'] in configured_players, 'components': components,
                   'band': next(n for n, lo, hi in BANDS if lo <= info['gameDuration'] < hi)}
            if all(n in components for n in COMMON):
                row['experiments'] = {
                    'Six components: original weights / v4 curves': recombine(components),
                    'Six components: equal weights / v4 curves': recombine(components, equal=True),
                    'Six components: original weights / linear curves': recombine(components, linear=True),
                    'Six components: equal weights / linear curves': recombine(components, equal=True, linear=True),
                    'Six components: equal weights / common damage reference 800 / v4': recombine(components, equal=True, common_damage=800),
                }
            supports.append(row); paired[mid].append(row)
    styles = ('Damage support', 'Tank support', 'Utility support')
    contributions = {}
    for style in styles:
        rs = [r for r in supports if r['style'] == style]
        names = sorted({n for r in rs for n in r['components']})
        contributions[style] = {'count': len(rs), 'mean': average([r['score'] for r in rs]),
            'champions': Counter(r['champion'] for r in rs).most_common(5),
            'components': {n: {'count': sum(n in r['components'] for r in rs),
                'mean': average([r['components'][n]['value'] for r in rs if n in r['components']]),
                'points': average([r['components'][n]['contribution'] for r in rs if n in r['components']])} for n in names}}
    experiments = []
    eligible = [r for r in supports if 'experiments' in r and r['style'] in styles[:2]]
    for name in next((r['experiments'].keys() for r in eligible), []):
        means = {s: average([r['experiments'][name] for r in eligible if r['style'] == s]) for s in styles[:2]}
        experiments.append({'name': name, **means, 'gap': round(means[styles[0]] - means[styles[1]], 3)})
    duration = []
    strata = []
    for band, _, _ in BANDS:
        for win in (True, False):
            cells = {}
            for style in styles:
                rs = [r for r in supports if r['style'] == style and r['band'] == band and r['win'] == win]
                cells[style] = {'count': len(rs), 'mean': average([r['score'] for r in rs])}
                duration.append({'band': band, 'win': win, 'style': style, **cells[style]})
            if all(cells[s]['count'] for s in styles[:2]):
                strata.append({'band': band, 'win': win, 'weight': min(cells[s]['count'] for s in styles[:2]),
                    'gap': cells[styles[0]]['mean'] - cells[styles[1]]['mean']})
    standardized_gap = sum(s['weight'] * s['gap'] for s in strata) / sum(s['weight'] for s in strata) if strata else None
    pair_results = []
    for rs in paired.values():
        if len(rs) != 2 or rs[0]['team'] == rs[1]['team']: continue
        damage = next((r for r in rs if r['style'] == styles[0]), None)
        tank = next((r for r in rs if r['style'] == styles[1]), None)
        if damage and tank: pair_results.append({'damageWin': damage['win'], 'gap': damage['score'] - tank['score']})
    pair_summary = {str(win): {'matches': sum(r['damageWin'] == win for r in pair_results),
                              'gap': average([r['gap'] for r in pair_results if r['damageWin'] == win])} for win in (True, False)}
    others = {s: {'count': sum(r['style'] == s and not r['configuredPlayer'] for r in supports),
                  'mean': average([r['score'] for r in supports if r['style'] == s and not r['configuredPlayer']])} for s in styles}
    report = {'contributions': contributions, 'experiments': experiments, 'duration': duration,
              'outcomeDurationStandardizedGap': round(standardized_gap, 3) if standardized_gap is not None else None,
              'standardizationStrata': strata, 'sameMatchOpposingSupportPairs': pair_summary,
              'excludingConfiguredPlayers': others}
    out = ROOT / 'reports'
    (out / 'weight-investigation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# Weight, curve and duration investigation', '',
        'Read-only analysis of unique support performances in saved matches. No formula or saved scores changed. This is a selected history, not a representative population. Rounded component rates are used for sensitivity recombinations, so small rounding differences are possible.', '',
        '## Baseline component contributions', '']
    for style, summary in contributions.items():
        lines += [f"### {style}: {summary['count']} games, mean {summary['mean']}", '',
            '| Component | Games | Mean component | Mean final points |', '|---|---:|---:|---:|']
        for name, c in summary['components'].items(): lines.append(f"| {name} | {c['count']} | {c['mean']} | {c['points']} |")
        lines += ['', 'Most frequent champions: ' + ', '.join(f'{n} ({c})' for n, c in summary['champions']), '']
    lines += ['## Controlled sensitivity comparisons', '',
        'All comparisons below use the same complete six-component support cases. CC is omitted from both groups and remaining weights rescaled; consequently these are diagnostic ablations, not proposed replacement scores. The final row also equalizes damage references. Different roles/functions cannot be made equivalent merely by equal weights.', '',
        '| Experiment | Damage support | Tank support | Gap |', '|---|---:|---:|---:|']
    for r in experiments: lines.append(f"| {r['name']} | {r[styles[0]]} | {r[styles[1]]} | {r['gap']} |")
    lines += ['', '## Duration within archetype and outcome', '', '| Duration | Outcome | Archetype | Games | Mean |', '|---|---|---|---:|---:|']
    for r in duration: lines.append(f"| {r['band']} | {'Win' if r['win'] else 'Loss'} | {r['style']} | {r['count']} | {r['mean']} |")
    lines += ['', f'Shared outcome/duration stratum gap: **{report["outcomeDurationStandardizedGap"]} points**. Each cell is weighted by the smaller group count, restricting comparisons to overlap; this does not control for champion, player, patch, or match difficulty.', '',
        '## Same-match opposing support pairs', '', 'Pairs share exact duration, but necessarily have opposite outcomes. Separate by damage-support outcome:', '', '```json', json.dumps(pair_summary, indent=2), '```', '',
        '## Excluding both configured players', '', 'Other players remain drawn from the same selected matches; this reduces direct main-champion influence without providing an independent population sample.', '', '```json', json.dumps(others, indent=2), '```', '',
        '## Limits', '', 'These experiments isolate arithmetic effects on this sample, not causal fairness. Linear curves are an ablation, not an endorsed return to v3. Duration trends can reflect game phase, match selection, champion mix and performance; small short-game cells are noisy. Do not equalize archetype means automatically or fit a duration correction from these averages alone.', '']
    (out / 'weight-investigation.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('duration', 'standardizationStrata')}, indent=2))
    print('DURATION', json.dumps(duration))


if __name__ == '__main__': run()
