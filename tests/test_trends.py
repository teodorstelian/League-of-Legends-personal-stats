from app.trends import performance_trends, period_stats, DAY


def test_period_boundaries_filters_and_empty_weeks():
    now=2_000_000_000
    def match(age,score,role='TOP',champion=1):
        return {'playedAt':(now-age*DAY)*1000,'championId':champion,'role':role,'score':score,'win':True,'duration':1200,'deaths':4,'damage':12000,'vision':10}
    data={'matches':[match(0,80),match(30,60),match(30.001,40),match(60,20),match(61,100),match(1,0,'UTILITY',2)],'champions':[{'championId':1,'name':'Annie'}]}
    result=performance_trends(data,now,'TOP',1)
    assert result['current']['score']['value']==70
    assert result['previous']['score']['value']==30
    assert result['deltas']['score']==40
    assert result['current']['total']==2
    assert result['forms'][0]['form']=='insufficient'
    assert len(result['weeks'])==12
    assert any(w['score']['value'] is None for w in result['weeks'])


def test_rates_use_only_covered_minutes_and_zero_is_valid():
    stats=period_stats([{'score':0,'win':False,'duration':600,'damage':10000,'deaths':2},
                        {'score':100,'win':True,'duration':1200,'damage':10000,'vision':0,'deaths':0},
                        {'score':None,'win':True,'duration':600}])
    assert stats['score']=={'value':50,'count':2}
    assert stats['damage']=={'value':666.67,'count':2}
    assert stats['vision']=={'value':0,'count':1}
    assert stats['deaths']=={'value':1,'count':2}
    assert period_stats([])['score']['value'] is None


def test_champion_form_needs_three_samples_in_both_periods():
    now=2_000_000_000
    matches=[{'championId':1,'playedAt':(now-age*DAY)*1000,'score':score} for age,score in [(1,80)]*3+[(31,60)]*3]
    result=performance_trends({'matches':matches,'champions':[{'championId':1,'name':'Annie'}]},now)
    assert result['forms'][0]['form']=='improving'
    assert result['forms'][0]['delta']==20
