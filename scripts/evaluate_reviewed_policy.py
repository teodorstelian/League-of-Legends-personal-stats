"""Read-only comparison of metric-cap policy against prior v5 scoring."""
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.scoring import score_player, VERSION
from app.history_policy import eligible_info


def run():
    db=sqlite3.connect((ROOT/'data/journal.sqlite3').as_uri()+'?mode=ro',uri=True)
    profiles={o:json.loads(b) for o,b in db.execute('SELECT player,body FROM profiles')}
    rows=db.execute('SELECT player,id,body FROM details ORDER BY player,id').fetchall();db.close()
    groups=defaultdict(list);seen=set();monotonic_failures=0
    for owner,mid,body in rows:
        d=json.loads(body);info=d['raw']['info']
        if not eligible_info(info):continue
        catalog={c['championId']:c.get('tags') for c in profiles.get(owner,{}).get('champions',[])}
        for p in info['participants']:
            if (mid,p['puuid']) in seen:continue
            seen.add((mid,p['puuid']))
            tags=catalog.get(p['championId'])
            old=score_player(info,p,tags,reviewed_policy=False)
            new=score_player(info,p,tags)
            if new['value'] is None or old['value'] is None:continue
            groups[new['archetype']].append((old['value'],new['value']))
            for field in ('goldEarned','visionScore','totalDamageDealtToChampions'):
                if not isinstance(p.get(field),(int,float)):continue
                raised=score_player(info,{**p,field:p[field]+1000},tags)['value']
                monotonic_failures+=raised is None or raised<new['value']
    output=[]
    for name,values in sorted(groups.items()):
        output.append({'archetype':name,'count':len(values),'before':round(statistics.mean(a for a,b in values),2),'after':round(statistics.mean(b for a,b in values),2),'delta':round(statistics.mean(b-a for a,b in values),2)})
    lines=['# Reviewed scoring policy comparison','',f'Active version: `{VERSION}`. No database writes or imports. The same recorded performances are compared under previous blanket bonuses and reviewed metric caps. This is a sensitivity check, not independent replay validation. No champion-specific data is activated because no independent dataset was supplied.','',
        '| Archetype | Games | Previous | Reviewed | Change |','|---|---:|---:|---:|---:|']
    for r in output:lines.append(f"| {r['archetype']} | {r['count']} | {r['before']} | {r['after']} | {r['delta']} |")
    lines+=['',f'Monotonicity failures when raising damage, gold or vision: {monotonic_failures}.','',
        'Duration remains a frozen experimental adjustment. Survival weights remain unchanged: no data supports a specific alternative, and recorded deaths do not establish engage quality. Gold-lead context is descriptive; total gold still determines the Economy component. Source-qualified champion references can be supplied in app/champion_references.json, but small samples, ambiguous records, or missing independence declarations fall back to archetype/role rates.','']
    (ROOT/'reports/reviewed-policy-comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'participants':sum(len(v) for v in groups.values()),'monotonicFailures':monotonic_failures,'comparisons':output},indent=2))


if __name__=='__main__':run()
