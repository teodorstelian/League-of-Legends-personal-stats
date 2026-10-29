from datetime import datetime, timedelta, timezone
from .statistics import score_average

DAY = 86400


def period_stats(matches):
    scores = score_average(matches)
    def average(key):
        values = [m[key] for m in matches if isinstance(m.get(key), (int, float))]
        return {'value': round(sum(values) / len(values), 1) if values else None, 'count': len(values)}
    def rate(key):
        covered = [m for m in matches if isinstance(m.get(key), (int, float)) and m.get('duration', 0) > 0]
        minutes = sum(m['duration'] for m in covered) / 60
        return {'value': round(sum(m[key] for m in covered) / minutes, 2) if minutes else None, 'count': len(covered)}
    return {'total': len(matches), 'score': {'value': scores['average'], 'count': scores['scored']},
            'winRate': {'value': round(sum(bool(m.get('win')) for m in matches) / len(matches) * 100, 1) if matches else None, 'count': len(matches)},
            'deaths': average('deaths'), 'damage': rate('damage'), 'vision': rate('vision')}


def performance_trends(data, now, role='all', champion=0, comparison='days', size=30):
    if comparison not in ('days', 'games'):
        raise ValueError('Unknown trend comparison')
    if type(size) is not int or size not in (30, 50, 100):
        raise ValueError('Comparison size must be 30, 50 or 100')
    matches = [m for m in data['matches'] if 0 < m.get('playedAt', 0) <= now * 1000
               and (role == 'all' or m.get('role') == role) and (not champion or m['championId'] == champion)]
    if comparison == 'games':
        ordered = sorted(matches, key=lambda m: (-m['playedAt'], str(m.get('id', ''))))
        recent, previous = ordered[:size], ordered[size:2 * size]
    else:
        recent = [m for m in matches if m['playedAt'] >= (now - size * DAY) * 1000]
        previous = [m for m in matches if (now - 2 * size * DAY) * 1000 <= m['playedAt'] < (now - size * DAY) * 1000]
    current_stats, previous_stats = period_stats(recent), period_stats(previous)
    deltas = {key: round(current_stats[key]['value'] - previous_stats[key]['value'], 2)
              if current_stats[key]['value'] is not None and previous_stats[key]['value'] is not None else None
              for key in ('score', 'winRate', 'deaths', 'damage', 'vision')}
    today = datetime.fromtimestamp(now, timezone.utc)
    monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    weeks = []
    for index in range(12):
        start = monday - timedelta(weeks=11-index)
        end = start + timedelta(days=7)
        group = [m for m in matches if start.timestamp() * 1000 <= m['playedAt'] < end.timestamp() * 1000]
        weeks.append({'start': int(start.timestamp()*1000), 'end': int(end.timestamp()*1000), 'partial': end.timestamp() > now, **period_stats(group)})
    forms = []
    for c in data.get('champions', []):
        before = score_average([m for m in previous if m['championId'] == c['championId']])
        after = score_average([m for m in recent if m['championId'] == c['championId']])
        if not before['total'] and not after['total']:
            continue
        enough = before['scored'] >= 3 and after['scored'] >= 3
        delta = round(after['average'] - before['average'], 1) if enough else None
        forms.append({**c, 'current': after, 'previous': before, 'delta': delta,
                      'form': 'insufficient' if not enough else 'improving' if delta >= 3 else 'declining' if delta <= -3 else 'steady'})
    forms.sort(key=lambda c: (c['delta'] is None, -abs(c['delta'] or 0), c['name']))
    return {'size': size, 'comparison': comparison, 'queue': data.get('queue', 'all'), 'role': role, 'champion': champion, 'asOf': int(now*1000),
            'current': current_stats, 'previous': previous_stats, 'deltas': deltas, 'weeks': weeks, 'forms': forms,
            'champions': data.get('champions', []), 'filteredGames': len(matches)}
