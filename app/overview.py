import math


def overview_stats(matches):
    games = sorted(matches, key=lambda m: (m.get('playedAt', 0), m.get('id', '')), reverse=True)
    def valid(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    def score(m):
        value = m.get('score')
        return value if valid(value) and 0 <= value <= 100 else None
    def mean(values):
        values = [v for v in values if v is not None]
        return round(sum(values)/len(values), 1) if values else None
    def form(group):
        return {'games':len(group),'wins':sum(bool(m.get('win')) for m in group),
            'winRate':round(sum(bool(m.get('win')) for m in group)/len(group)*100,1) if group else None,
            'score':mean([score(m) for m in group]), 'scoreGames':sum(score(m) is not None for m in group)}
    current = 0
    if games:
        for m in games:
            if bool(m.get('win')) != bool(games[0].get('win')): break
            current += 1
    longest_win = longest_loss = run = 0
    last = None
    for m in reversed(games):
        win = bool(m.get('win')); run = run+1 if win == last else 1; last = win
        if win: longest_win = max(longest_win,run)
        else: longest_loss = max(longest_loss,run)
    definitions = [('score','Highest Rift Score',score,''),
        ('kills','Most kills',lambda m:m.get('kills'),'kills'),
        ('assists','Most assists',lambda m:m.get('assists'),'assists'),
        ('kda','Best KDA ratio',lambda m:(m['kills']+m['assists'])/max(1,m['deaths']) if all(valid(m.get(k)) for k in ('kills','assists','deaths')) else None,'KDA'),
        ('cs','Best CS / minute',lambda m:m['cs']/(m['duration']/60) if valid(m.get('cs')) and m.get('duration',0)>0 else None,'CS/min'),
        ('damage','Highest damage / minute',lambda m:m['damage']/(m['duration']/60) if valid(m.get('damage')) and m.get('duration',0)>0 else None,'damage/min')]
    records = []
    for key,label,metric,unit in definitions:
        candidates = [(m,metric(m)) for m in games]
        candidates = [(m,v) for m,v in candidates if valid(v)]
        best = max(candidates,key=lambda pair:pair[1]) if candidates else None
        records.append({'key':key,'label':label,'unit':unit,'sample':len(candidates),'value':round(best[1],1) if best else None,
            'match':{k:best[0].get(k) for k in ('id','championId','name','champion','icon','playedAt','kills','deaths','assists','win')} if best else None})
    return {'currentStreak':{'games':current,'win':bool(games[0].get('win')) if games else None},
        'longestWinStreak':longest_win,'longestLossStreak':longest_loss,'recent':form(games[:20]),'previous':form(games[20:40]),
        'results':[{'id':m.get('id'),'win':bool(m.get('win')),'champion':m.get('name') or m.get('champion'),'playedAt':m.get('playedAt')} for m in reversed(games[:20])],
        'hours':round(sum(m.get('duration',0) for m in games)/3600,1),
        'deathless':sum(m.get('deaths')==0 for m in games),'champions':len({m['championId'] for m in games}), 'records':records}
