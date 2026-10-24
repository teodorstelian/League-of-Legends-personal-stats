import math
import statistics
from .statistics import LANES
from .scoring import VERSION, score_player


def distribution(matches):
    values = sorted(m['score'] for m in matches if isinstance(m.get('score'), (int,float)) and not isinstance(m['score'],bool) and math.isfinite(m['score']) and 0 <= m['score'] <= 100)
    def percentile(fraction):
        if not values:
            return None
        position = (len(values)-1)*fraction
        low = int(position)
        high = min(low+1,len(values)-1)
        return round(values[low]+(values[high]-values[low])*(position-low),1)
    histogram = [0]*10
    for value in values:
        histogram[min(9,int(value//10))] += 1
    return {'count':len(values),'total':len(matches),'mean':round(statistics.mean(values),1) if values else None,
            'median':percentile(.5),'p10':percentile(.1),'p90':percentile(.9),
            'stddev':round(statistics.pstdev(values),1) if values else None,
            'floor':sum(v<=5 for v in values),'ceiling':sum(v>=95 for v in values),'histogram':histogram}


def calibration_report(data, minimum=5, details=None):
    matches = data['matches']
    overall = distribution(matches)
    def row(name, group, **extra):
        stats=distribution(group)
        difference=round(stats['mean']-overall['mean'],1) if stats['mean'] is not None and overall['mean'] is not None else None
        return {'name':name,**stats,**extra,'difference':difference,
                'review':stats['count']>=10 and difference is not None and abs(difference)>=10}
    roles=[row(name,[m for m in matches if m.get('role')==role]) for role,name in LANES.items() if role not in ('ARAM','UNKNOWN')]
    styles=sorted({m.get('archetype','Role baseline') for m in matches})
    archetypes=[row(style,[m for m in matches if m.get('archetype','Role baseline')==style]) for style in styles]
    role_means = {r: distribution([m for m in matches if m.get('role') == r])['mean'] for r in LANES if r not in ('ARAM', 'UNKNOWN')}
    champions=[]
    for c in data.get('champions',[]):
        group=[m for m in matches if m['championId']==c['championId']]
        stats=row(c['name'],group,championId=c['championId'])
        comparable = [m for m in group if distribution([m])['count'] and role_means.get(m.get('role')) is not None]
        expected = statistics.mean(role_means[m['role']] for m in comparable) if comparable else None
        stats['roleReference'] = round(expected, 1) if expected is not None else None
        stats['roleDifference'] = round(statistics.mean(m['score'] for m in comparable) - expected, 1) if comparable else None
        stats['roleComparedGames'] = len(comparable)
        if stats['count']>=minimum:
            champions.append(stats)
    champions.sort(key=lambda c: (not c['review'],-abs(c['difference'] or 0),c['name']))
    durations = []
    for name, low, high in DURATION_BANDS:
        durations.append(row(name, [m for m in matches if isinstance(m.get('duration'), (int, float)) and not isinstance(m['duration'], bool) and math.isfinite(m['duration']) and m['duration'] > 0 and low <= m['duration'] < high]))
    catalog = {c['championId']: c.get('tags') for c in data.get('champions', [])}
    component_groups = {}
    detailed_games = 0
    evidence = []
    short_games = []
    for match in matches:
        detail = (details or {}).get(match.get('id'))
        if not detail:
            continue
        info = detail['raw']['info']
        player = next((p for p in info['participants'] if p.get('puuid') == detail['puuid']), None)
        if player is None:
            continue
        score = score_player(info, player, catalog.get(player['championId']))
        if info.get('gameDuration', 0) < 600:
            def flags(key):
                values = [p.get(key) for p in info['participants']]
                return 'Yes' if any(v is True for v in values) else 'No' if values and all(v is False for v in values) else 'Unknown'
            short_games.append({**match, 'earlySurrender': flags('gameEndedInEarlySurrender'),
                                'surrender': flags('gameEndedInSurrender'), 'scoreReason': score.get('reason')})
        if score['value'] is None:
            continue
        candidate = score_player(info, player, catalog.get(player['championId']), cc_target=3.0)
        evidence.append({'match': match, 'current': score, 'candidate': candidate})
        detailed_games += 1
        for scope, group in [('Overall', 'All scored details'), ('Role', LANES.get(match.get('role'), 'Unknown lane')), ('Archetype', score['archetype'])]:
            for component in score['components']:
                component_groups.setdefault((scope, group, component['name']), []).append(component)
    components = []
    for (scope, group, name), values in sorted(component_groups.items()):
        count = len(values)
        components.append({'scope': scope, 'group': group, 'name': name, 'count': count,
            'mean': round(statistics.mean(v['value'] for v in values), 1),
            'rawMean': round(statistics.mean(v['own'] for v in values), 2),
            'unit': values[0]['unit'],
            'targetMin': min(v['target'] for v in values), 'targetMax': max(v['target'] for v in values),
            'contribution': round(statistics.mean(v['contribution'] for v in values), 1),
            'zeroPercent': round(sum(v['value'] == 0 for v in values) / count * 100, 1),
            'hundredPercent': round(sum(v['value'] >= 100 for v in values) / count * 100, 1)})
    scored = [m for m in matches if distribution([m])['count'] and m.get('id')]
    def extremes(reverse):
        ordered = sorted(scored, key=lambda m: (-(m['score']) if reverse else m['score'], -m.get('playedAt', 0), m['id']))[:5]
        return [{k: m.get(k) for k in ('id', 'champion', 'championId', 'role', 'score', 'playedAt', 'duration', 'win')} for m in ordered]
    investigation = investigate(evidence)
    return {'investigation': investigation, 'shortGames': short_games, 'components': components, 'componentGames': detailed_games, 'durations': durations,
            'extremes': {'highest': extremes(True), 'lowest': extremes(False)}, 'version':VERSION,'queue':data.get('queue','all'),'overall':overall,'roles':roles,'archetypes':archetypes,'champions':champions,'minimum':minimum}


DURATION_BANDS = [('Under 20 min', 0, 1200), ('20–29:59 min', 1200, 1800),
                  ('30–39:59 min', 1800, 2400), ('40+ min', 2400, math.inf)]


def investigate(evidence):
    """Paired, read-only sensitivity analysis; never changes persisted scores."""
    def summary(name, group):
        current = [e['current']['value'] for e in group]
        candidate = [e['candidate']['value'] for e in group]
        deltas = [b - a for a, b in zip(current, candidate)]
        return {'name': name, 'count': len(group),
                'current': round(statistics.mean(current), 1) if group else None,
                'candidate': round(statistics.mean(candidate), 1) if group else None,
                'delta': round(statistics.mean(deltas), 1) if group else None}
    duration_results = []
    duration_components = []
    for band, low, high in DURATION_BANDS:
        for outcome, label in [(True, 'Win'), (False, 'Loss'), (None, 'Unknown result')]:
            group = [e for e in evidence if isinstance(e['match'].get('duration'), (int, float))
                     and not isinstance(e['match']['duration'], bool) and low <= e['match']['duration'] < high
                     and e['match']['duration'] > 0 and e['match'].get('win') is outcome]
            if outcome is None and not group:
                continue
            duration_results.append({**summary(f'{band} · {label}', group), 'band': band, 'outcome': label})
            names = sorted({c['name'] for e in group for c in e['current']['components']})
            for name in names:
                values = [c for e in group for c in e['current']['components'] if c['name'] == name]
                duration_components.append({'group': f'{band} · {label}', 'name': name, 'count': len(values),
                    'mean': round(statistics.mean(c['value'] for c in values), 1),
                    'rawMean': round(statistics.mean(c['own'] for c in values), 2), 'unit': values[0]['unit']})
    comparisons = [summary('All paired games', evidence)]
    for style in sorted({e['current']['archetype'] for e in evidence}):
        comparisons.append(summary(style, [e for e in evidence if e['current']['archetype'] == style]))
    changes = sorted(evidence, key=lambda e: (-abs(e['candidate']['value'] - e['current']['value']),
                     -e['match'].get('playedAt', 0), e['match'].get('id', '')))
    examples = [{**e['match'], 'current': e['current']['value'], 'candidate': e['candidate']['value'],
                 'delta': round(e['candidate']['value'] - e['current']['value'], 1)}
                for e in changes if e['candidate']['value'] != e['current']['value']][:10]
    cc = []
    for style in ('Tank', 'Tank support'):
        pairs = [(a, b) for e in evidence if e['current']['archetype'] == style
                 for a in e['current']['components'] if a['name'] == 'Crowd control'
                 for b in e['candidate']['components'] if b['name'] == 'Crowd control']
        cc.append({'name': style, 'count': len(pairs),
            'currentCap': round(100 * sum(a['value'] >= 100 for a, b in pairs) / len(pairs), 1) if pairs else None,
            'candidateCap': round(100 * sum(b['value'] >= 100 for a, b in pairs) / len(pairs), 1) if pairs else None})
    return {'durationResults': duration_results, 'durationComponents': duration_components,
            'comparisons': comparisons, 'examples': examples, 'cc': cc}
