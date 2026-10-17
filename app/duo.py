from .history_policy import eligible_info
from .scoring import score_player
from .statistics import LANES


def duo_report(first, second, profiles, queue='all', period='all', now=0):
    """Identify teammates by private PUUID, across the union of saved histories."""
    identities = [next((d['puuid'] for _, d in rows if d), None) for rows in (first, second)]
    ready = all(identities) and identities[0] != identities[1]
    catalog = {c['championId']: c for profile in profiles for c in profile.get('champions', [])}
    games = []
    union = {}
    for owner, rows in reversed(list(enumerate((first, second)))):
        for m, d in rows:
            if d:
                union[m['id']] = (m, d, owner)
    if ready:
        for mid, (m, d, owner) in union.items():
            info = d['raw']['info']
            if not eligible_info(info) or (queue != 'all' and info['queueId'] != {'solo':420,'flex':440}[queue]):
                continue
            played = info.get('gameStartTimestamp', m.get('playedAt', 0))
            if period == '30d' and not (now - 30*86400)*1000 <= played <= now*1000:
                continue
            players = [next((p for p in info['participants'] if p.get('puuid') == identity), None) for identity in identities]
            if not all(players) or players[0].get('teamId') not in (100, 200) or players[0]['teamId'] != players[1].get('teamId'):
                continue
            entries = []
            for p in players:
                champion = catalog.get(p['championId'], {})
                role = p.get('teamPosition') or 'UNKNOWN'
                entries.append({'championId':p['championId'], 'name':champion.get('name', p.get('championName', 'Unknown')), 'icon':champion.get('icon'),
                    'role':LANES.get(role,'Unassigned'), 'kills':p.get('kills',0), 'deaths':p.get('deaths',0), 'assists':p.get('assists',0),
                    'score':score_player(info,p,champion.get('tags'))['value']})
            games.append({'id':mid,'playedAt':played,'duration':info['gameDuration'],'queue':info['queueId'],'win':bool(players[0].get('win')),'players':entries,'owner':owner})
    games.sort(key=lambda m: (m['playedAt'],m['id']), reverse=True)

    def stats(group):
        wins = sum(m['win'] for m in group)
        players = []
        for index in (0,1):
            ps = [m['players'][index] for m in group]
            scores = [p['score'] for p in ps if p['score'] is not None]
            players.append({'score':round(sum(scores)/len(scores),1) if scores else None, 'scoreGames':len(scores),
                'kda':[round(sum(p[key] for p in ps)/len(ps),1) if ps else None for key in ('kills','deaths','assists')]})
        return {'games':len(group),'wins':wins,'losses':len(group)-wins,'winRate':round(wins/len(group)*100,1) if group else None,'players':players}
    pairs = {}
    for game in games:
        key = tuple((p['championId'],p['role']) for p in game['players'])
        pairs.setdefault(key,[]).append(game)
    combinations = [{'champions':[{'name':p['name'],'championId':p['championId'],'icon':p['icon'],'role':p['role']} for p in group[0]['players']], **stats(group)} for group in pairs.values()]
    combinations.sort(key=lambda g:(-g['games'],-g['winRate']))
    return {'ready':bool(ready), 'coverage':[{'saved':len(rows),'details':sum(d is not None for _,d in rows)} for rows in (first,second)],
        'summary':stats(games),'combinations':combinations,'matches':games}
