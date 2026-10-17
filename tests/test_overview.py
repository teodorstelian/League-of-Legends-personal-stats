from app.overview import overview_stats


def game(i, win=True, **kw):
    return {'id':str(i),'playedAt':i*1000,'win':win,'championId':17,'kills':4,'deaths':0,'assists':6,'score':70,'duration':1200,'cs':150,**kw}


def test_streaks_use_chronological_order_and_current_result():
    stats=overview_stats([game(3),game(1),game(6,False),game(4,False),game(2),game(5,False)])
    assert stats['currentStreak']=={'games':3,'win':False}
    assert stats['longestWinStreak']==3 and stats['longestLossStreak']==3
    assert [m['id'] for m in stats['results']]==['1','2','3','4','5','6']


def test_records_ties_missing_metrics_and_deathless_kda():
    stats=overview_stats([game(1,score=100),game(2,score=100),game(3,score=None,cs=None)])
    records={r['key']:r for r in stats['records']}
    assert records['score']['match']['id']=='2'
    assert records['score']['sample']==2
    assert records['kda']['value']==10
    assert records['cs']['value']==7.5 and records['cs']['sample']==2
    assert records['damage']['value'] is None
    assert stats['deathless']==3 and stats['hours']==1


def test_recent_windows_and_empty_history():
    stats=overview_stats([game(i,win=i>=20) for i in range(40)])
    assert stats['recent']['games']==20 and stats['recent']['winRate']==100
    assert stats['previous']['games']==20 and stats['previous']['winRate']==0
    empty=overview_stats([])
    assert empty['currentStreak']['games']==0 and empty['recent']['score'] is None
    assert all(r['match'] is None for r in empty['records'])
