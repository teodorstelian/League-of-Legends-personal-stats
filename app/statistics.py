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
    data = dict(data)
    matches = data['matches']
    groups = {}
    for match in matches:
        groups.setdefault(match['championId'], []).append(match)
    data['scoreStats'] = score_average(matches)
    data['lanes'] = lane_averages(matches)
    for field in ('champions', 'mastery'):
        data[field] = [{**c, 'scoreStats': score_average(groups.get(c['championId'], []))} for c in data.get(field, [])]
    return data
