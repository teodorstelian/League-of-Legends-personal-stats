"""Rift Score v2: independent, provisional role benchmarks."""
import math

VERSION = '2'
# Full-score targets: damage/min, gold/min, kill participation %, vision/min, objective damage/min.
TARGETS = {
    'TOP': (1000, 500, 65, 1.2, 1000),
    'JUNGLE': (850, 480, 80, 1.5, 1600),
    'MIDDLE': (1100, 500, 75, 1.2, 900),
    'BOTTOM': (1200, 550, 75, 1.2, 1200),
    'UTILITY': (1000, 350, 80, 3.0, 400),
    'GENERAL': (1000, 500, 75, 1.2, 900),
    'ARAM': (1500, 650, 80, 0, 0),
}


def score_player(info, player):
    participants = info.get('participants', [])
    def unavailable(reason, components=None):
        return {'value': None, 'reason': reason, 'version': VERSION, 'components': components or []}
    if info.get('gameDuration', 0) < 180 or any(p.get('gameEndedInEarlySurrender') for p in participants):
        return unavailable('Short game / remake: no score.')
    if info.get('gameMode') not in ('CLASSIC', 'ARAM') or len(participants) != 10:
        return unavailable('Scoring currently supports standard 5v5 and ARAM.')
    minutes = info['gameDuration'] / 60
    role = player.get('teamPosition', '')
    profile = 'ARAM' if info['gameMode'] == 'ARAM' else role if role in ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY') else 'GENERAL'
    support = profile == 'UTILITY'
    damage, gold, kp, vision, objectives = TARGETS[profile]
    def metric(p, key):
        value = p.get(key)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else None
    def per_minute(p, key):
        value = metric(p, key)
        return value / minutes if value is not None else None
    def participation(p):
        team = [q for q in participants if q.get('teamId') == p.get('teamId')]
        values = [metric(q, 'kills') for q in team]
        kills, assists = metric(p, 'kills'), metric(p, 'assists')
        if kills is None or assists is None or any(v is None for v in values):
            return None
        return min(100, (kills + assists) / max(1, sum(values)) * 100)
    def impact(p):
        keys = ['totalDamageDealtToChampions'] + (['totalHealsOnTeammates', 'totalDamageShieldedOnTeammates'] if support else [])
        values = [metric(p, key) for key in keys]
        return sum(values) / minutes if all(v is not None for v in values) else None
    definitions = [
        ('Support impact' if support else 'Champion damage', 20, impact, damage, False, 'per minute', 'Damage + ally healing + ally shielding per minute' if support else 'Champion damage per minute'),
        ('Kill participation', 25 if support else 20, participation, kp, False, '%', '(Kills + assists) / team kills x 100'),
        ('Survival', 20 if support else 15, lambda p: per_minute(p, 'deaths'), .6 if profile == 'ARAM' else .4, True, 'deaths/min', '100 at zero deaths/min; falls linearly to 0 at the displayed zero-score threshold'),
        ('Economy', 10 if support else 15, lambda p: per_minute(p, 'goldEarned'), gold, False, 'gold/min', 'Gold earned per minute'),
    ]
    if profile != 'ARAM':
        definitions += [('Vision', 20 if support else 15, lambda p: per_minute(p, 'visionScore'), vision, False, 'vision/min', 'Vision score per minute'),
                        ('Objective pressure', 5 if support else 15, lambda p: per_minute(p, 'damageDealtToObjectives'), objectives, False, 'damage/min', 'Objective damage per minute; does not measure setup or shotcalling')]
    enemies = [p for p in participants if p.get('teamId') != player.get('teamId')]
    same_role = [p for p in enemies if role and p.get('teamPosition') == role]
    peers = same_role if profile != 'ARAM' and len(same_role) == 1 else enemies
    components = []
    raw_total = 0
    for name, weight, getter, target, reverse, unit, description in definitions:
        own = getter(player)
        if own is None:
            continue
        value = max(0, min(100, (1 - own / target if reverse else own / target) * 100))
        raw_total += value * weight
        opponents = [getter(p) for p in peers]
        opponent = sum(opponents) / len(opponents) if opponents and all(v is not None for v in opponents) else None
        components.append({'name': name, 'weight': weight, 'value': round(value, 1), 'own': round(own, 2),
                           'target': target, 'targetLabel': 'Zero-score threshold' if reverse else '100-point target',
                           'opponent': round(opponent, 2) if opponent is not None else None, 'unit': unit, 'description': description})
    if len(components) < (3 if profile == 'ARAM' else 4):
        return unavailable('Insufficient data for a multi-metric score.', components)
    weight_total = sum(c['weight'] for c in components)
    value = round(raw_total / weight_total, 1)
    for c in components:
        c['weight'] = round(c['weight'] / weight_total * 100, 1)
    return {'value': value, 'version': VERSION, 'components': components, 'role': role or 'Unknown',
            'comparison': f'Independent {profile.title()} benchmarks - provisional', 'reason': None,
            'coverage': f'{len(components)} of {len(definitions)} metrics available',
            'opponentContext': 'Same-role opponent' if len(peers) == 1 else 'Opposing team average',
            'method': 'Rift Score v2 uses provisional targets chosen for this app, not population statistics. Positive metrics score min(100, own / target x 100). Survival scores max(0, 100 x (1 - deaths/min / threshold)). The final score is the weighted average of available metrics; missing weights are rescaled. Meeting every full target, including zero deaths, earns 100. Opponent values are context only and do not enter the formula. Kill participation still uses your own team kills. No win bonus. Benchmarks do not adjust for champion, rank, patch, or game phase yet.'}
