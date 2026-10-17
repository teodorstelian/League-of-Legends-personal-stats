from .statistics import score_average


def ban_candidates(matches, catalog, minimum, enemy=0, general=False):
    groups = {}
    for m in matches:
        opponents = set(m.get('enemyChampionIds', [])) if general else {m.get('opponentId')}
        for opponent in opponents - {None, 0, enemy}:
            groups.setdefault(opponent, []).append(m)
    qualified, limited = [], []
    required = max(3, minimum)
    for opponent, games in groups.items():
        stats = score_average(games)
        if stats['average'] is None:
            continue
        wins = sum(bool(m.get('win')) for m in games)
        losses = len(games) - wins
        raw = .7 * losses / len(games) * 100 + .3 * (100 - stats['average'])
        priority = 50 + (raw - 50) * len(games) / (len(games) + 5)
        if priority <= 50:
            continue
        c = catalog.get(opponent, {'name':f'Champion {opponent}', 'icon':None})
        supported = len(games) >= required and stats['scored'] >= required
        candidate = {'championId':opponent,'name':c['name'],'icon':c.get('icon'),'games':len(games),'wins':wins,'losses':losses,
            'winRate':round(wins/len(games)*100,1),'scoreStats':stats,'priority':round(priority,1),
            'limited':len(games)<10,'supported':supported,'required':required}
        (qualified if supported else limited).append(candidate)
    for group in (qualified, limited):
        group.sort(key=lambda b:(-b['priority'],-b['games'],b['name']))
    return {'qualified':qualified,'limited':limited,'required':required}


def combined_bans(lane, general, limit=6):
    candidates = [{**b, 'scope':scope} for scope,group in [('lane',lane),('general',general)] for kind in ('qualified','limited') for b in group[kind]]
    candidates.sort(key=lambda b:(not b['supported'],-b['priority'],-b['games'],b['scope']!='lane',b['name']))
    result, seen = [], set()
    for b in candidates:
        if b['championId'] not in seen:
            result.append(b)
            seen.add(b['championId'])
        if len(result) == limit:
            break
    return result
