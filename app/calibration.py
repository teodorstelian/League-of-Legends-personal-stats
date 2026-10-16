import math
import statistics
from .statistics import LANES
from .scoring import VERSION


def distribution(matches):
    values = sorted(m['score'] for m in matches if isinstance(m.get('score'), (int,float)) and not isinstance(m['score'],bool) and math.isfinite(m['score']) and 0 <= m['score'] <= 100)
    def percentile(fraction):
        if not values:
            return None
        position = (len(values)-1)*fraction
        low = int(position)
        high = min(low+1,len(values)-1)
        return round(values[low]+(values[high]-values[low])*(position-low),1)
    histogram = [0]*10
    for value in values:
        histogram[min(9,int(value//10))] += 1
    return {'count':len(values),'total':len(matches),'mean':round(statistics.mean(values),1) if values else None,
            'median':percentile(.5),'p10':percentile(.1),'p90':percentile(.9),
            'stddev':round(statistics.pstdev(values),1) if values else None,
            'floor':sum(v<=5 for v in values),'ceiling':sum(v>=95 for v in values),'histogram':histogram}


def calibration_report(data, minimum=5):
    matches = data['matches']
    overall = distribution(matches)
    def row(name, group, **extra):
        stats=distribution(group)
        difference=round(stats['mean']-overall['mean'],1) if stats['mean'] is not None and overall['mean'] is not None else None
        return {'name':name,**stats,**extra,'difference':difference,
                'review':stats['count']>=10 and difference is not None and abs(difference)>=10}
    roles=[row(name,[m for m in matches if m.get('role')==role]) for role,name in LANES.items() if role not in ('ARAM','UNKNOWN')]
    styles=sorted({m.get('archetype','Role baseline') for m in matches})
    archetypes=[row(style,[m for m in matches if m.get('archetype','Role baseline')==style]) for style in styles]
    champions=[]
    for c in data.get('champions',[]):
        group=[m for m in matches if m['championId']==c['championId']]
        stats=row(c['name'],group,championId=c['championId'])
        if stats['count']>=minimum:
            champions.append(stats)
    champions.sort(key=lambda c: (not c['review'],-abs(c['difference'] or 0),c['name']))
    return {'version':VERSION,'queue':data.get('queue','all'),'overall':overall,'roles':roles,'archetypes':archetypes,'champions':champions,'minimum':minimum}
