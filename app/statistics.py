import math

LANES = {'TOP': 'Top', 'JUNGLE': 'Jungle', 'MIDDLE': 'Mid', 'BOTTOM': 'Bot', 'UTILITY': 'Support', 'ARAM': 'ARAM (no lane)', 'UNKNOWN': 'Unknown lane'}


def score_average(matches):
    values = [m['score'] for m in matches if isinstance(m.get('score'), (int, float)) and not isinstance(m['score'], bool) and math.isfinite(m['score']) and 0 <= m['score'] <= 100]
    return {'average': round(sum(values) / len(values), 1) if values else None,
            'scored': len(values), 'total': len(matches)}


def lane_averages(matches):
    groups = {lane: [] for lane in LANES}
    for match in matches:
        lane = 'ARAM' if match.get('mode') == 'ARAM' else match.get('role', 'UNKNOWN')
        groups[lane if lane in LANES else 'UNKNOWN'].append(match)
    return [{'lane': lane, 'name': name, **score_average(groups[lane])} for lane, name in LANES.items()
            if lane not in ('ARAM', 'UNKNOWN') or groups[lane]]


def enrich_dashboard(data):
    from .overview import overview_stats
    data = dict(data)
    matches = data['matches']
    data['overview'] = overview_stats(matches)
    groups = {}
    for match in matches:
        groups.setdefault(match['championId'], []).append(match)
    data['scoreStats'] = score_average(matches)
    data['lanes'] = lane_averages(matches)
    for field in ('champions', 'mastery'):
        data[field] = [{**c, 'scoreStats': score_average(groups.get(c['championId'], []))} for c in data.get(field, [])]
    return data


TIERS = [('S', 75), ('A', 60), ('B', 50), ('C', 40), ('D', 0)]


def champion_tiers(data, minimum=3):
    catalog = {c['championId']: c for c in data.get('champions', [])}
    roles = []
    for role in ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'):
        groups = {}
        for match in data['matches']:
            if match.get('role') == role:
                groups.setdefault(match['championId'], []).append(match)
        tiers = {tier: [] for tier, _ in TIERS}
        provisional = []
        for champion_id, matches in groups.items():
            champion = catalog.get(champion_id, {'championId': champion_id, 'name': f'Champion {champion_id}', 'icon': None})
            stats = score_average(matches)
            value = {**champion, 'scoreStats': stats, 'wins': sum(bool(m.get('win')) for m in matches)}
            if stats['scored'] < minimum or stats['average'] is None:
                provisional.append(value)
            else:
                tier = next(t for t, threshold in TIERS if stats['average'] >= threshold)
                tiers[tier].append(value)
        def order(c):
            return (-(c['scoreStats']['average'] if c['scoreStats']['average'] is not None else -1), -c['scoreStats']['scored'], c['name'])
        roles.append({'role': role, 'name': LANES[role], 'tiers': [{'tier': tier, 'minimum': threshold, 'champions': sorted(tiers[tier], key=order)} for tier, threshold in TIERS], 'provisional': sorted(provisional, key=order)})
    return {'queue': data.get('queue', 'all'), 'minimumGames': minimum, 'roles': roles,
            'unknownRoleGames': sum(m.get('role') not in ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY') for m in data['matches']),
            'totalGames': len(data['matches'])}
