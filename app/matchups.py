from .statistics import score_average, LANES


def champion_matchups(data, champion_id, now, role='all', period='all'):
    matches = [m for m in data['matches'] if m['championId']==champion_id and (role=='all' or m.get('role')==role)
               and (period=='all' or (now-30*86400)*1000 <= m.get('playedAt',0) <= now*1000)]
    catalog={c['championId']:c for c in data.get('champions',[])}
    groups={}
    missing=ambiguous=0
    for m in matches:
        if m.get('opponentId') is None:
            if m.get('matchupStatus')=='ambiguous': ambiguous+=1
            else: missing+=1
            continue
        groups.setdefault((m['opponentId'],m.get('role')),[]).append(m)
    rows=[]
    for (opponent_id,lane),games in groups.items():
        c=catalog.get(opponent_id,{'championId':opponent_id,'name':f'Champion {opponent_id}','icon':None})
        wins=sum(bool(m.get('win')) for m in games)
        rows.append({'championId':opponent_id,'name':c['name'],'icon':c.get('icon'),'role':lane,'roleName':LANES.get(lane,'Unknown'),
                     'games':len(games),'wins':wins,'losses':len(games)-wins,'winRate':round(wins/len(games)*100,1),
                     'scoreStats':score_average(games),'kda':[round(sum(m.get(k,0) for m in games)/len(games),1) for k in ('kills','deaths','assists')]})
    rows.sort(key=lambda r:(-r['games'],r['name'],r['role']))
    return {'rows':rows,'totalGames':len(matches),'matchedGames':sum(r['games'] for r in rows),'missingDetails':missing,'ambiguousGames':ambiguous,
            'queue':data.get('queue','all'),'role':role,'period':period}


def all_matchups(data, now, role='all', period='all', minimum=3, champion=0):
    matches=[m for m in data['matches'] if (role=='all' or m.get('role')==role)
             and (not champion or m['championId']==champion)
             and (period=='all' or (now-30*86400)*1000<=m.get('playedAt',0)<=now*1000)]
    catalog={c['championId']:c for c in data.get('champions',[])}
    filtered={**data,'matches':matches}
    rows=[]
    for own_id in sorted({m['championId'] for m in matches}):
        result=champion_matchups(filtered,own_id,now)
        own=catalog.get(own_id,{'championId':own_id,'name':f'Champion {own_id}','icon':None})
        rows.extend({**r,'ownId':own_id,'ownName':own['name'],'ownIcon':own.get('icon')} for r in result['rows'] if r['games']>=minimum)
    rows.sort(key=lambda r:(-r['games'],r['ownName'],r['name'],r['role']))
    groups={}
    for m in matches:
        if m.get('opponentId') is not None:
            groups.setdefault(m['opponentId'],[]).append(m)
    bans=[]
    required=max(3,minimum)
    for opponent_id,games in groups.items():
        if len(games)<required:
            continue
        stats=score_average(games)
        if stats['average'] is None or stats['scored']<required:
            continue
        wins=sum(bool(m.get('win')) for m in games)
        loss_rate=(len(games)-wins)/len(games)*100
        # Shrink toward neutral 50: one-off bad games must not dominate the list.
        raw=.7*loss_rate+.3*(100-stats['average'])
        priority=50+(raw-50)*len(games)/(len(games)+5)
        if priority<=50:
            continue
        c=catalog.get(opponent_id,{'name':f'Champion {opponent_id}','icon':None})
        bans.append({'championId':opponent_id,'name':c['name'],'icon':c.get('icon'),'games':len(games),'wins':wins,'losses':len(games)-wins,
                     'winRate':round(wins/len(games)*100,1),'scoreStats':stats,'priority':round(priority,1),
                     'roles':sorted({LANES.get(m.get('role'),'Unknown') for m in games}),
                     'yourChampions':len({m['championId'] for m in games}), 'limited':len(games)<10})
    bans.sort(key=lambda b:(-b['priority'],-b['games'],b['name']))
    return {'rows':rows,'bans':bans,'totalGames':len(matches),'matchedGames':sum(len(g) for g in groups.values()),'minimum':minimum,'banMinimum':required,
            'queue':data.get('queue','all'),'role':role,'period':period,'champion':champion,'champions':data.get('champions',[])}
