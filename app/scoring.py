"""Rift Score v6 experimental: independent, provisional role and archetype benchmarks."""
import math
from .archetypes import archetype_for
from .duration import DURATION_ENABLED, MODEL, reference_multiplier
from .references import CATALOG, resolve_reference

VERSION = f"6-duration-{MODEL['id']}-caps125-{CATALOG['id']}" if DURATION_ENABLED else '4'
# Role reference rates (curve anchors define the score): damage/min, gold/min, kill participation %, vision/min, objective damage/min.
TARGETS = {
    'TOP': (1000, 500, 65, 1.2, 1000),
    'JUNGLE': (850, 480, 80, 1.5, 1600),
    'MIDDLE': (1100, 500, 75, 1.2, 900),
    'BOTTOM': (1200, 550, 75, 1.2, 1200),
    'UTILITY': (1000, 350, 80, 3.0, 400),
    'GENERAL': (1000, 500, 75, 1.2, 900),
    'ARAM': (1500, 650, 80, 0, 0),
}


# Provisional design anchors, not population percentiles. X is own/reference.
# Each metric has its own low, ordinary, strong and exceptional benchmarks.
CURVES = {
    'Champion damage': ((0, 0), (.25, 0), (.5, 20), (.75, 50), (1, 80), (1.25, 100)),
    'Support impact': ((0, 0), (.25, 0), (.5, 20), (.75, 50), (1, 80), (1.25, 100)),
    'Kill participation': ((0, 0), (.15, 0), (.4, 20), (.65, 50), (.9, 80), (1.1, 100)),
    'Economy': ((0, 0), (.4, 0), (.6, 20), (.8, 50), (1, 90), (1.1, 100)),
    'Vision': ((0, 0), (.15, 0), (.4, 20), (.65, 50), (1, 80), (1.3, 100)),
    'Objective pressure': ((0, 0), (.1, 20), (.3, 50), (.6, 80), (1, 100)),
    'Tower pressure': ((0, 0), (.1, 20), (.3, 50), (.6, 80), (1, 100)),
    'Crowd control': ((0, 0), (.4, 20), (.8, 50), (1.3, 80), (2, 100)),
    'Survival': ((0, 100), (.125, 100), (.3, 80), (.5, 50), (.75, 20), (1, 0)),
}


def curve_score(ratio, anchors):
    """Bounded continuous piecewise-linear interpolation between explicit anchors."""
    if ratio <= anchors[0][0]:
        return anchors[0][1]
    for (left, low), (right, high) in zip(anchors, anchors[1:]):
        if ratio <= right:
            return low + (high - low) * (ratio - left) / (right - left)
    return anchors[-1][1]


# All positive metrics may earn bounded exceptional credit; survival stays at 100.
EXCEPTIONAL_CAPS = {name: 125 for name in CURVES if name != 'Survival'}

EXCEPTIONAL_CURVE = ((0, 0), (.25, 10), (.5, 16), (1, 20))


def exceptional_score(ratio, anchors):
    """Positive components: diminishing bonus above the 100-point anchor, up to 120."""
    normal = curve_score(ratio, anchors)
    full_reference = anchors[-1][0]
    if ratio <= full_reference:
        return normal
    return min(120, normal + curve_score(ratio / full_reference - 1, EXCEPTIONAL_CURVE))


def score_player(info, player, champion_tags=None, *, cc_target=1.5, duration_adjustment=None, exceptional_output=None, reviewed_policy=None, reference_catalog=None):
    duration_enabled = DURATION_ENABLED if duration_adjustment is None else duration_adjustment
    reviewed_policy = duration_enabled if reviewed_policy is None else reviewed_policy
    exceptional_enabled = duration_enabled if exceptional_output is None else exceptional_output
    version = (f"5-{MODEL['id']}" if duration_enabled else '4') + ('-extra120' if exceptional_enabled else '')
    selected_catalog = CATALOG if reference_catalog is None else reference_catalog
    if reviewed_policy:
        version = f"6-{'duration' if duration_enabled else 'fixed'}-{MODEL['id']}-caps125-{selected_catalog['id']}"
    participants = info.get('participants', [])
    def unavailable(reason, components=None):
        return {'value': None, 'reason': reason, 'version': version, 'components': components or []}
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
        ('Survival', weights[2], lambda p: per_minute(p, 'deaths'), .6 if profile == 'ARAM' else .4, True, 'deaths/min', 'Low death rates can earn full credit; benchmark curve falls to zero at the reference rate'),
        ('Economy', weights[3], lambda p: per_minute(p, 'goldEarned'), gold, False, 'gold/min', 'Total gold per minute, including passive income; not earned advantage. Opponent comparison is context only'),
    ]
    if profile != 'ARAM':
        definitions += [('Vision', weights[4], lambda p: per_minute(p, 'visionScore'), vision, False, 'vision/min', 'Vision score per minute'),
                        ('Tower pressure' if style == 'split' else 'Objective pressure', weights[5], lambda p: per_minute(p, 'damageDealtToTurrets' if style == 'split' else 'damageDealtToObjectives'), objectives, False, 'damage/min', 'Turret damage per minute' if style == 'split' else 'Objective damage per minute; does not measure setup or shotcalling')]
        if style == 'tank':
            definitions.append(('Crowd control', 15, lambda p: per_minute(p, 'timeCCingOthers'), cc_target, False, 'CC seconds/min', 'Time crowd controlling others; damage taken is not rewarded'))
    enemies = [p for p in participants if p.get('teamId') != player.get('teamId')]
    same_role = [p for p in enemies if role and p.get('teamPosition') == role]
    peers = same_role if profile != 'ARAM' and len(same_role) == 1 else enemies
    components = []
    raw_total = 0
    baseline_total = 0
    ordinary_total = 0
    for name, weight, getter, target, reverse, unit, description in definitions:
        own = getter(player)
        if own is None:
            continue
        role_target = target
        reference = resolve_reference(player.get('championName'), profile, name, target, catalog=selected_catalog) if reviewed_policy else {'rate': target, 'source': 'Archetype / role baseline', 'samples': 0, 'blend': 0}
        base_target = reference['rate']
        target = base_target
        multiplier = reference_multiplier(profile, archetype, name, minutes) if duration_enabled else 1.0
        target *= multiplier
        anchors = CURVES[name]
        baseline_total += curve_score(own / role_target, anchors) * weight
        ordinary = curve_score(own / target, anchors)
        ordinary_total += ordinary * weight
        maximum = (EXCEPTIONAL_CAPS.get(name, 100) if reviewed_policy else 120) if exceptional_enabled and not reverse else 100
        extended = exceptional_score(own / target, anchors) if maximum > 100 else ordinary
        value = ordinary + (extended - ordinary) * (maximum - 100) / 20 if maximum > 100 else ordinary
        raw_total += value * weight
        opponents = [getter(p) for p in peers]
        opponent = sum(opponents) / len(opponents) if opponents and all(v is not None for v in opponents) else None
        components.append({'name': name, 'weight': weight, 'maximum': maximum, 'bonus': round(value - ordinary, 1), 'value': round(value, 1), 'own': round(own, 2),
                           'roleTarget': role_target, 'referenceSource': reference['source'], 'referenceSamples': reference['samples'], 'referenceBlend': reference['blend'], 'baseTarget': base_target, 'durationMultiplier': round(multiplier, 4), 'target': round(target, 4), 'targetLabel': 'Zero-score threshold' if reverse else 'Role reference rate',
                           'benchmarks': [{'own': round(ratio * target, 3), 'value': points} for ratio, points in anchors] + ([{'own': round(anchors[-1][0] * target * (1 + extra), 3), 'value': 100 + bonus * (maximum - 100) / 20} for extra, bonus in EXCEPTIONAL_CURVE[1:]] if maximum > 100 else []),
                           'opponent': round(opponent, 2) if opponent is not None else None, 'unit': unit, 'description': description})
    if len(components) < (3 if profile == 'ARAM' else 4):
        return unavailable('Insufficient data for a multi-metric score.', components)
    weight_total = sum(c['weight'] for c in components)
    value = round(min(100, raw_total / weight_total), 1)
    for c in components:
        c['weight'] = round(c['weight'] / weight_total * 100, 1)
        c['contribution'] = round(c['value'] * c['weight'] / 100, 1)
        c['bonusContribution'] = round(c['bonus'] * c['weight'] / 100, 1)
        c['missedPoints'] = round(max(0, 100-c['value']) * c['weight'] / 100, 1)
    strengths = sorted(components, key=lambda c: -c['contribution'])[:2]
    gaps = sorted(components, key=lambda c: -c['missedPoints'])[:2]
    economy = next((c for c in components if c['name'] == 'Economy'), None)
    economy_context = {'goldPerMinute': economy['own'], 'opponentGoldPerMinute': economy['opponent'], 'differencePerMinute': round(economy['own'] - economy['opponent'], 2) if economy['opponent'] is not None else None, 'affectsScore': False, 'note': 'Context only; total gold includes passive income. This does not measure earned advantage or decision quality.'} if economy else None
    return {'economyContext': economy_context, 'value': value, 'baselineValue': round(baseline_total / weight_total, 1), 'withoutExceptional': round(ordinary_total / weight_total, 1), 'exceptionalBonus': round(value - round(ordinary_total / weight_total, 1), 1), 'version': version, 'components': components, 'role': role or 'Unknown',
            'archetype': archetype, 'tags': champion_tags or [],
            'explanations': {'strengths': [f'{c["name"]}: {c["contribution"]} score points earned' for c in strengths], 'gaps': [f'{c["name"]}: {c["missedPoints"]} points below full component score' for c in gaps]},
            'summary': {'strength': strengths[0] if strengths else None, 'improvement': gaps[0] if gaps and gaps[0]['missedPoints'] > 0 else None},
            'comparison': f'{archetype} · {profile.title()} benchmarks', 'reason': None,
            'coverage': f'{len(components)} of {len(definitions)} metrics available',
            'opponentContext': 'Same-role opponent' if len(peers) == 1 else 'Opposing team average',
            'durationModel': MODEL['id'] if duration_enabled else None,
            'method': ('Reviewed policy: all positive components allow exceptional credit up to 125; survival stays capped at 100. Champion references require explicit independent provenance and sample-based shrinkage; missing references use archetype/role defaults. Survival measures recorded deaths and cannot judge whether an engage death was justified. ' if reviewed_policy else '') + ('Eligible components allow diminishing extra credit to their displayed maximum; intermediate tail anchors appear below. Survival remains capped at 100; weights are unchanged and the final score is capped at 100. ' if exceptional_enabled else '') + ('Duration adjustment: frozen role/archetype/metric references vary with match duration, clamped to 10–50 minutes and 0.7–1.3 times the 30-minute reference. Unmodeled groups, survival and participation retain their baseline. No runtime fitting. ' if duration_enabled else 'Duration adjustment is disabled. ') + 'Rift Score uses explicit per-metric benchmark curves, interpolating between low, ordinary, strong and exceptional reference points. Benchmarks are defined for this app, not population averages or percentiles. Rates use total match minutes; references do not adjust for rank or patch. Role and archetype weights remain unchanged. Low positive output can earn zero; exceptional output earns 100; survival permits full credit at low nonzero death rates. Available weights are rescaled and components are averaged. Opponents are context only; there is no win bonus. See each component for its exact raw-rate anchors.'}
