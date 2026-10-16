"""Rift Score v1: explainable, within-match comparison, not a rank estimate."""


def score_player(info, player):
    participants = info.get('participants', [])
    if info.get('gameDuration', 0) < 180 or any(p.get('gameEndedInEarlySurrender') for p in participants):
        return {'value': None, 'reason': 'Short game / remake: no score.', 'version': '1', 'components': []}
    if info.get('gameMode') not in ('CLASSIC', 'ARAM') or len(participants) != 10:
        return {'value': None, 'reason': 'Scoring currently supports standard 5v5 and ARAM.', 'version': '1', 'components': []}
    enemies = [p for p in participants if p.get('teamId') != player.get('teamId')]
    role = player.get('teamPosition', '')
    same_role = [p for p in enemies if role and p.get('teamPosition') == role]
    peers = same_role if info['gameMode'] == 'CLASSIC' and len(same_role) == 1 else enemies
    support = role == 'UTILITY' and info['gameMode'] == 'CLASSIC'
    def metric(p, key):
        return p.get(key)
    def participation(p):
        if 'kills' not in p or 'assists' not in p:
            return None
        team = [q for q in participants if q.get('teamId') == p.get('teamId')]
        if any('kills' not in q for q in team):
            return None
        return (p['kills'] + p['assists']) / max(1, sum(q['kills'] for q in team)) * 100
    def impact(p):
        keys = ['totalDamageDealtToChampions'] + (['totalHealsOnTeammates', 'totalDamageShieldedOnTeammates'] if support else [])
        if any(k not in p for k in keys):
            return None
        return sum(p[k] for k in keys)
    definitions = [
        ('Teamfight impact' if support else 'Champion damage', 20, impact, False, 'Damage + ally healing + ally shielding' if support else 'Damage dealt to champions'),
        ('Kill participation', 20, participation, False, '(Kills + assists) / team kills × 100'),
        ('Survival', 15, lambda p: metric(p, 'deaths'), True, 'Fewer deaths earns a higher comparison score'),
        ('Economy', 15, lambda p: metric(p, 'goldEarned'), False, 'Total gold earned'),
    ]
    if info['gameMode'] == 'CLASSIC':
        definitions += [('Vision', 15, lambda p: metric(p, 'visionScore'), False, 'Vision score'),
                        ('Objective pressure', 15, lambda p: metric(p, 'damageDealtToObjectives'), False, 'Damage to objectives; does not measure shotcalling or objective setup')]
    components = []
    for name, weight, getter, reverse, description in definitions:
        own = getter(player)
        values = [getter(p) for p in peers]
        if own is None or not values or any(v is None for v in values):
            continue
        opponent = sum(values) / len(values)
        fraction = own / (own + opponent) if own + opponent else .5
        value = (1 - fraction if reverse else fraction) * 100
        components.append({'name': name, 'weight': weight, 'value': round(value, 1), 'own': round(own, 1), 'comparison': round(opponent, 1), 'description': description})
    total_weight = sum(c['weight'] for c in components)
    value = round(sum(c['value'] * c['weight'] for c in components) / total_weight, 1) if total_weight else None
    for c in components:
        c['weight'] = round(c['weight'] / total_weight * 100, 1)
    return {'value': value, 'version': '1', 'components': components,
            'comparison': 'Opposing player in the same role' if len(peers) == 1 else 'Average of the opposing team',
            'role': role or 'Unknown', 'reason': None if value is not None else 'Insufficient data.',
            'coverage': f'{len(components)} metrics available',
            'method': 'Each metric = your value / (your value + comparison) × 100; survival is inverted. Both zero = 50. Weighted average; missing metrics are excluded and weights rescaled. ARAM excludes vision and objectives. No win bonus. 50 means equal on these metrics, not a population percentile.'}
