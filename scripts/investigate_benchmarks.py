"""Champion/role benchmark and game-phase audit with a chronological holdout."""
import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scoring import score_player, curve_score, CURVES
from app.history_policy import eligible_info

METRICS = ('Champion damage', 'Support impact', 'Economy', 'Vision', 'Objective pressure', 'Tower pressure', 'Crowd control')
BANDS = [('Under 20', 0, 20), ('20–30', 20, 30), ('30–40', 30, 40), ('40+', 40, math.inf)]


def avg(xs): return round(statistics.mean(xs), 2) if xs else None


def fit_slope(rows):
    # Equal weight to wins and losses; this is a diagnostic local fit, not causal correction.
    groups = [[r for r in rows if r['win'] is outcome] for outcome in (True, False)]
    if any(len(g) < 20 for g in groups): return None
    points = [(math.log(r['minutes']/30), math.log1p(r['raw']), .5/len(g)) for g in groups for r in g]
    mx = sum(x*w for x,y,w in points); my = sum(y*w for x,y,w in points)
    variance = sum(w*(x-mx)**2 for x,y,w in points)
    if variance < .01: return None
    slope = sum(w*(x-mx)*(y-my) for x,y,w in points)/variance
    return max(-2, min(2, slope)) * len(rows)/(len(rows)+100)


def run():
    db = sqlite3.connect((ROOT/'data/journal.sqlite3').as_uri()+'?mode=ro', uri=True)
    profiles = {o:json.loads(b) for o,b in db.execute('SELECT player,body FROM profiles')}
    details = db.execute('SELECT player,id,body FROM details ORDER BY player,id').fetchall(); db.close()
    own_ids = {json.loads(b)['puuid'] for _,_,b in details}
    seen=set(); records=[]
    for owner, mid, body in details:
        d=json.loads(body);info=d['raw']['info']
        if not eligible_info(info):continue
        tags={c['championId']:c.get('tags') for c in profiles.get(owner,{}).get('champions',[])}
        for p in info['participants']:
            key=(mid,p['puuid'])
            if key in seen:continue
            seen.add(key)
            score=score_player(info,p,tags.get(p['championId']), duration_adjustment=False)
            if score['value'] is None:continue
            records.append({'match':mid,'played':info.get('gameStartTimestamp',0),'minutes':info['gameDuration']/60,
                'champion':p['championName'],'role':p.get('teamPosition') or 'UNKNOWN','style':score['archetype'],
                'win':bool(p['win']),'own':p['puuid'] in own_ids,'score':score['value'],'components':score['components']})
    matches=sorted({(r['played'],r['match']) for r in records});cut=max(1,int(len(matches)*.6));train_ids={mid for _,mid in matches[:cut]}
    training=defaultdict(list)
    for r in records:
        if r['match'] not in train_ids or r['own'] or not 10<=r['minutes']<=50:continue
        for c in r['components']:
            if c['name'] in METRICS:
                training[(r['role'],r['style'],c['name'])].append({'win':r['win'],'minutes':r['minutes'],'raw':c['own']})
    models={key:s for key,rows in training.items() if (s:=fit_slope(rows)) is not None}
    held=[]
    for r in records:
        if r['match'] in train_ids:continue
        total=weight=0;changed=0
        for c in r['components']:
            slope=models.get((r['role'],r['style'],c['name']))
            if slope is None:value=c['value']
            else:
                # Keep existing 30-minute reference. No fitting to desired score means.
                multiplier=max(.7,min(1.3,(max(10,min(50,r['minutes']))/30)**slope))
                value=curve_score(c['own']/(c['target']*multiplier),CURVES[c['name']]);changed+=1
            total+=c['weight']*value;weight+=c['weight']
        held.append({**r,'candidate':round(total/weight,1) if changed else r['score'],'adjusted':changed>0})
    duration=[]
    for label,lo,hi in BANDS:
        for win in (True,False):
            rs=[r for r in held if not r['own'] and lo<=r['minutes']<hi and r['win']==win]
            duration.append({'band':label,'win':win,'games':len(rs),'current':avg([r['score'] for r in rs]),'candidate':avg([r['candidate'] for r in rs])})
    # Within champion/role/outcome, compare adjacent well-covered duration bands.
    cells=defaultdict(lambda:defaultdict(list))
    for r in records:
        if r['own']:continue
        band='20–30' if 20<=r['minutes']<30 else '30–40' if 30<=r['minutes']<40 else None
        if band:
            for c in r['components']:
                cells[(r['champion'],r['role'],r['win'],c['name'])][band].append(c['own'])
    within=[]
    for (champ,role,win,metric),bins in cells.items():
        a,b=bins['20–30'],bins['30–40']
        if min(len(a),len(b))<10:continue
        before,after=statistics.mean(a),statistics.mean(b)
        within.append({'champion':champ,'role':role,'win':win,'metric':metric,'earlyGames':len(a),'lateGames':len(b),'earlyRate':round(before,2),'lateRate':round(after,2),'changePercent':round(100*(after/before-1),1) if before else None})
    champion_groups=defaultdict(list)
    for r in records:
        if not r['own']:champion_groups[(r['champion'],r['role'],r['style'])].append(r)
    benchmarks=[]
    for (champ,role,style),rs in champion_groups.items():
        if len(rs)<20:continue
        medians={name:round(statistics.median([c['own'] for r in rs for c in r['components'] if c['name']==name]),2) for name in METRICS if any(c['name']==name for r in rs for c in r['components'])}
        benchmarks.append({'champion':champ,'role':role,'style':style,'games':len(rs),'wins':sum(r['win'] for r in rs),'rawMedians':medians})
    report={'trainingMatches':cut,'holdoutMatches':len(matches)-cut,'fittedGroups':len(models),'holdoutAdjustedParticipants':sum(r['adjusted'] for r in held),'duration':duration,'withinChampion':within,'championDiagnostics':benchmarks,
        'models':[{'role':k[0],'style':k[1],'metric':k[2],'slope':s,'games':len(training[k])} for k,s in sorted(models.items())]}
    out=ROOT/'reports';(out/'benchmark-investigation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# Champion benchmarks and game-phase investigation','',
        '**Experimental, read-only analysis. Production v4 is unchanged.**','',
        f"Earliest {cut} matches train duration models; latest {len(matches)-cut} matches are held out by whole match. Both configured players are excluded from fitting and the outcome table. Other participants still come from their selected histories; this is not population reference data.",'',
        '## Duration-only candidate','',
        'Within role/archetype/metric, fit log(1 + raw rate) against log(duration / 30 minutes), with equal total weight for wins and losses. Require at least 20 wins and 20 losses, shrink slope by n/(n+100), limit slope to ±2 and reference multiplier to 0.7–1.3. Clamp model duration to 10–50 minutes. Keep existing 30-minute references, weights and curves; do not add a win bonus. Survival and participation are unchanged. Missing models retain current scoring. This functional choice is a sensitivity experiment, not proven normalization.','',
        f"Fitted groups: {len(models)}. Held-out participants with an adjusted component: {report['holdoutAdjustedParticipants']}.",'',
        '| Held-out duration | Outcome | Participants | Current | Candidate |','|---|---|---:|---:|---:|']
    for r in duration:lines.append(f"| {r['band']} | {'Win' if r['win'] else 'Loss'} | {r['games']} | {r['current']} | {r['candidate']} |")
    lines+=['','## Within-champion phase checks','','Each row fixes champion, role and outcome; requires 10 observations in each adjacent duration band. Opponents, rank, patch and player ability are not held fixed. These checks use all saved dates and are descriptive, not holdout performance estimates.','',
        '| Champion / role | Outcome | Metric | n 20–30 / 30–40 | Raw rate 20–30 / 30–40 | Change |','|---|---|---|---|---|---:|']
    for r in sorted(within,key=lambda r:(r['champion'],r['role'],r['metric'],r['win'])):
        lines.append(f"| {r['champion']} / {r['role']} | {'Win' if r['win'] else 'Loss'} | {r['metric']} | {r['earlyGames']} / {r['lateGames']} | {r['earlyRate']} / {r['lateRate']} | {r['changePercent']}% |")
    lines+=['','## Champion-specific targets','','Champion-role diagnostics and raw medians are in the JSON companion (minimum 20 cases). They are NOT proposed targets: duration/outcome/player composition affects these medians. Do not fit full-score targets to them.','',
        'A future reference hierarchy should be champion + role → archetype + role → role, with sample-dependent shrinkage and explicit coverage. Use champion-specific damage/utility/CC references where functions differ; avoid unique champion survival or participation rules without evidence. Reference samples should be independent of the rated player, conditioned on duration and ideally rank/patch. Small or absent reference samples must fall back rather than inventing champion targets.','',
        '## Decision','','Do not promote this duration candidate or champion medians automatically. Check whether within-champion shifts replicate in held-out role groups and independent replay judgments. Outcome/duration mean flattening alone cannot prove fairer ratings. Preserve the existing model until that evidence exists.','']
    (out/'benchmark-investigation.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('trainingMatches','holdoutMatches','fittedGroups','holdoutAdjustedParticipants','duration')},indent=2))
    print('Within-champion comparisons:',len(within),'Champion-role diagnostic groups:',len(benchmarks))


if __name__=='__main__':run()
