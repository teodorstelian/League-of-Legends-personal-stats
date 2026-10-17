"""Rift Score v3: independent, provisional role and archetype benchmarks."""
import math
from .archetypes import archetype_for

VERSION = '3'
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


def score_player(info, player, champion_tags=None):
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
    archetype, style = archetype_for(player, champion_tags)
    if profile == 'ARAM':
        archetype, style = 'ARAM role baseline', 'baseline'
    weights = [20, 25, 20, 10, 20, 5] if support else [20, 20, 15, 15, 15, 15]
    if style == 'carry':
        weights = [30, 20, 15, 20, 5, 10]
    elif style == 'fighter':
        weights = [20, 20, 20, 15, 10, 15]
    elif style == 'tank':
        weights = [10, 25, 20, 5 if support else 10, 15 if support else 10, 10]
        damage *= .65
    elif style == 'split':
        weights = [10, 10, 20, 20, 10, 30]
        kp, objectives = 50, 600
    elif style == 'damage_support':
        weights = [30, 25, 15, 5, 20, 5]
        damage = 800
    use_ally_utility = support and style not in ('tank', 'damage_support')
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
        keys = ['totalDamageDealtToChampions'] + (['totalHealsOnTeammates', 'totalDamageShieldedOnTeammates'] if use_ally_utility else [])
        values = [metric(p, key) for key in keys]
        return sum(values) / minutes if all(v is not None for v in values) else None
    definitions = [
        ('Support impact' if use_ally_utility else 'Champion damage', weights[0], impact, damage, False, 'per minute', 'Damage + ally healing + ally shielding per minute' if use_ally_utility else 'Champion damage per minute'),
        ('Kill participation', weights[1], participation, kp, False, '%', '(Kills + assists) / team kills x 100'),
        ('Survival', weights[2], lambda p: per_minute(p, 'deaths'), .6 if profile == 'ARAM' else .4, True, 'deaths/min', '100 at zero deaths/min; falls linearly to 0 at the displayed zero-score threshold'),
        ('Economy', weights[3], lambda p: per_minute(p, 'goldEarned'), gold, False, 'gold/min', 'Gold earned per minute'),
    ]
    if profile != 'ARAM':
        definitions += [('Vision', weights[4], lambda p: per_minute(p, 'visionScore'), vision, False, 'vision/min', 'Vision score per minute'),
                        ('Tower pressure' if style == 'split' else 'Objective pressure', weights[5], lambda p: per_minute(p, 'damageDealtToTurrets' if style == 'split' else 'damageDealtToObjectives'), objectives, False, 'damage/min', 'Turret damage per minute' if style == 'split' else 'Objective damage per minute; does not measure setup or shotcalling')]
        if style == 'tank':
            definitions.append(('Crowd control', 15, lambda p: per_minute(p, 'timeCCingOthers'), 1.5, False, 'CC seconds/min', 'Time crowd controlling others; damage taken is not rewarded'))
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
        c['contribution'] = round(c['value'] * c['weight'] / 100, 1)
        c['missedPoints'] = round((100-c['value']) * c['weight'] / 100, 1)
    strengths = sorted(components, key=lambda c: -c['contribution'])[:2]
    gaps = sorted(components, key=lambda c: -c['missedPoints'])[:2]
    return {'value': value, 'version': VERSION, 'components': components, 'role': role or 'Unknown',
            'archetype': archetype, 'tags': champion_tags or [],
            'explanations': {'strengths': [f'{c["name"]}: {c["contribution"]} score points earned' for c in strengths], 'gaps': [f'{c["name"]}: {c["missedPoints"]} points below full target' for c in gaps]},
            'comparison': f'{archetype} · {profile.title()} benchmarks · provisional', 'reason': None,
            'coverage': f'{len(components)} of {len(definitions)} metrics available',
            'opponentContext': 'Same-role opponent' if len(peers) == 1 else 'Opposing team average',
            'method': 'Rift Score v3 uses provisional role and archetype targets chosen for this app, not population statistics. Archetypes use Riot primary tags plus app-defined split-pusher overrides in solo lanes. Positive metrics score min(100, own / target x 100); survival scores max(0, 100 x (1 - deaths/min / threshold)). Available weights are rescaled. Tanks emphasize CC and participation without rewarding damage taken; split-pushers emphasize turret damage; damage supports do not need healing/shielding. Missing champion tags use a role baseline. Opponent values are context only. No win bonus or adjustment for rank, patch, or game phase. The calibration page describes your saved sample, not proof of fairness.'}
