"""Sanitized timeline analysis using recorded timestamps, never frame indices."""


def timeline_report(raw, stored):
    players = stored['raw']['info']['participants']
    own = next(p for p in players if p.get('puuid') == stored['puuid'])
    roles = ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY')
    rivals = [p for p in players if own.get('teamPosition') in roles and p.get('teamPosition') == own['teamPosition'] and p['teamId'] != own['teamId']]
    rival = rivals[0] if len(rivals) == 1 else None
    names = {p['participantId']: p.get('championName', 'Unknown') for p in players}
    points, events, seen = [], [], set()
    for frame in sorted(raw.get('info', {}).get('frames', []), key=lambda f: f['timestamp']):
        frames = frame.get('participantFrames', {})
        a = frames.get(str(own['participantId']))
        b = frames.get(str(rival['participantId'])) if rival else None
        if a and b:
            points.append({'timestamp': frame['timestamp'], 'gold': a['totalGold'] - b['totalGold'], 'xp': a['xp'] - b['xp'], 'cs': a.get('minionsKilled', 0) + a.get('jungleMinionsKilled', 0) - b.get('minionsKilled', 0) - b.get('jungleMinionsKilled', 0)})
        for e in frame.get('events', []):
            kind = e.get('type')
            if kind not in ('CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'BUILDING_KILL'):
                continue
            key = repr(sorted(e.items()))
            if key in seen:
                continue
            seen.add(key)
            actor = names.get(e.get('killerId'), 'Environment')
            if kind == 'CHAMPION_KILL':
                label = f"{actor} killed {names.get(e.get('victimId'), 'Unknown')}"
            elif kind == 'ELITE_MONSTER_KILL':
                label = f"{actor}: {e.get('monsterSubType') or e.get('monsterType', 'Objective')}"
            else:
                label = f"{actor}: {e.get('laneType', '')} {e.get('towerType') or e.get('buildingType', 'Building')}"
            events.append({'timestamp': e.get('timestamp', 0), 'label': label, 'type': kind, 'death': kind == 'CHAMPION_KILL' and e.get('victimId') == own['participantId'], 'involved': own['participantId'] in [e.get('killerId'), e.get('victimId'), *e.get('assistingParticipantIds', [])]})
    checkpoints = []
    for minute in (10, 15, 20):
        # Do not invent an exact-minute sample when Riot's frames are irregular.
        candidates = [p for p in points if minute * 60000 - 90000 <= p['timestamp'] <= minute * 60000]
        checkpoints.append({'minute': minute, 'point': candidates[-1] if candidates and stored['raw']['info'].get('gameDuration', 0) >= minute * 60 else None})
    return {'opponent': rival.get('championName') if rival else None, 'points': points, 'checkpoints': checkpoints, 'events': sorted(events, key=lambda e: e['timestamp'])}


def economy_checkpoints(raw, stored):
    """Recorded same-role gold leads; context only, never substituted into scores."""
    if not raw or raw.get('unavailable'):
        return []
    report = timeline_report(raw, stored)
    return [{'minute': c['minute'], 'timestamp': c['point']['timestamp'], 'goldDifference': c['point']['gold']}
            for c in report['checkpoints'] if c['point'] is not None]
