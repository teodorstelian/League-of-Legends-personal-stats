from .statistics import score_average, LANES
from .matchups import all_matchups


def draft_report(data, now, role='TOP', enemy=0, minimum=3, period='all'):
    matches=[m for m in data['matches'] if m.get('role')==role and (period=='all' or (now-30*86400)*1000<=m.get('playedAt',0)<=now*1000)]
    catalog={c['championId']:c for c in data.get('champions',[])}
    def evidence(games):
        stats=score_average(games)
        wins=sum(bool(m.get('win')) for m in games)
        rate=wins/len(games)*100 if games else None
        score_adj=50+(stats['average']-50)*stats['scored']/(stats['scored']+5) if stats['average'] is not None else 50
        win_adj=50+(rate-50)*len(games)/(len(games)+5) if games else 50
        return {**stats,'wins':wins,'winRate':round(rate,1) if rate is not None else None,'index':round(.8*score_adj+.2*win_adj,1)}
    comfort=[]
    for own_id in sorted({m['championId'] for m in matches}):
        if own_id==enemy:
            continue
        games=[m for m in matches if m['championId']==own_id]
        stats=evidence(games)
        if stats['scored']<minimum:
            continue
        c=catalog.get(own_id,{'championId':own_id,'name':f'Champion {own_id}','icon':None})
        recent=score_average([m for m in games if (now-30*86400)*1000<=m.get('playedAt',0)<=now*1000])
        previous=score_average([m for m in data['matches'] if m['championId']==own_id and m.get('role')==role and (now-60*86400)*1000<=m.get('playedAt',0)<(now-30*86400)*1000])
        form=round(recent['average']-previous['average'],1) if recent['scored']>=3 and previous['scored']>=3 else None
        versus=evidence([m for m in games if m.get('opponentId')==enemy]) if enemy else None
        reliable=versus is not None and versus['scored']>=minimum
        comfort.append({'championId':own_id,'name':c['name'],'icon':c.get('icon'),'comfort':stats,'matchup':versus,
                        'form':form,'formCurrent':recent['total'],'formPrevious':previous['total'],
                        'matchupEligible':reliable,'recommendationIndex':round(.6*stats['index']+.4*versus['index'],1) if reliable else stats['index'],
                        'confidence':'More history' if stats['scored']>=10 else 'Limited sample'})
    comfort.sort(key=lambda c:(-c['comfort']['index'],-c['comfort']['scored'],c['name']))
    matchup=sorted([c for c in comfort if c['matchupEligible']],key=lambda c:(-c['recommendationIndex'],-c['matchup']['scored'],c['name']))
    eligible={c['championId'] for c in comfort}
    pool={**data,'matches':[m for m in matches if m['championId'] in eligible]}
    bans=[b for b in all_matchups(pool,now,role,period,minimum)['bans'] if b['championId']!=enemy]
    return {'role':role,'roleName':LANES[role],'queue':data.get('queue','all'),'enemy':catalog.get(enemy) if enemy else None,
            'period':period,'minimum':minimum,'comfort':comfort[:5],'matchup':matchup[:5],'fallback':bool(enemy and not matchup),
            'bans':bans[:3],'eligibleChampions':len(comfort),'totalGames':len(matches),'champions':data.get('champions',[])}
