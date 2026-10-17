from .timeline import timeline_report


def summarize(games):
    checkpoints = []
    for minute in (10, 15):
        covered = [(g, next(c['point'] for c in r['checkpoints'] if c['minute'] == minute)) for g, r in games]
        covered = [(g, p) for g, p in covered if p is not None]
        ahead = [(g, p) for g, p in covered if p['gold'] > 0]
        checkpoints.append({'minute': minute, 'count': len(covered),
            **{key: round(sum(p[key] for _, p in covered) / len(covered), 1) if covered else None for key in ('gold', 'xp', 'cs')},
            'leads': len(ahead), 'leadRate': round(len(ahead) / len(covered) * 100, 1) if covered else None,
            'leadWins': sum(bool(g.get('win')) for g, _ in ahead),
            'conversion': round(sum(bool(g.get('win')) for g, _ in ahead) / len(ahead) * 100, 1) if ahead else None})
    # Short games do not provide a complete ten-minute observation window.
    complete = [(g, r) for g, r in games if g.get('duration', 0) >= 600]
    deaths = sum(sum(e.get('death', False) and e['timestamp'] < 600000 for e in r['events']) for _, r in complete)
    return {'games': len(games), 'checkpoints': checkpoints, 'earlyDeaths': deaths,
            'deathGames': len(complete), 'deathsPerGame': round(deaths / len(complete), 2) if complete else None}


def early_game_report(rows, now, queue='all', role='all', champion=0, period='all'):
    normalized = []
    for m, d, t in rows:
        # Older summaries predate role storage. Full match details are authoritative.
        if d:
            own = next((p for p in d['raw']['info']['participants'] if p.get('puuid') == d['puuid']), {})
            recorded_role = own.get('teamPosition')
            m = {**m, 'role': recorded_role if recorded_role in ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY') else 'UNKNOWN'}
        normalized.append((m, d, t))
    rows = normalized
    filtered = [(m, d, t) for m, d, t in rows if (queue == 'all' or m['queue'] == {'solo': 420, 'flex': 440}[queue])
        and (role == 'all' or m.get('role') == role) and (not champion or m['championId'] == champion)
        and (period == 'all' or (now - 30 * 86400) * 1000 <= m.get('playedAt', 0) <= now * 1000)]
    games = [(m, timeline_report(t, d)) for m, d, t in filtered if d and t and not t.get('unavailable')]
    groups = []
    for key in sorted({(m['championId'], m.get('role', 'UNKNOWN')) for m, _ in games}):
        group = [(m, r) for m, r in games if (m['championId'], m.get('role', 'UNKNOWN')) == key]
        groups.append({'championId': key[0], 'role': key[1], **summarize(group)})
    roles = [{'role': r, **summarize([(m, t) for m, t in games if m.get('role', 'UNKNOWN') == r])} for r in sorted({m.get('role', 'UNKNOWN') for m, _ in games})]
    return {'total': len(filtered), 'cached': len(games), 'unavailable': sum(bool(t and t.get('unavailable')) for _, _, t in filtered),
        'summary': summarize(games), 'champions': groups, 'roles': roles}
