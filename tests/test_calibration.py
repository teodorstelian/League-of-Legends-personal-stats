from app.calibration import distribution, calibration_report


def test_distribution_includes_100_and_excludes_missing():
    stats=distribution([{'score':v} for v in [0,10,50,100,None]])
    assert stats['count']==4 and stats['total']==5
    assert stats['mean']==40 and stats['median']==30
    assert stats['histogram']==[1,1,0,0,0,1,0,0,0,1]
    assert stats['floor']==1 and stats['ceiling']==1
    assert distribution([])['mean'] is None


def test_review_flags_need_sample_and_do_not_change_scores():
    data={'matches':[{'score':80,'role':'TOP','archetype':'Tank','championId':1} for _ in range(10)]+[{'score':20,'role':'UTILITY','archetype':'Utility support','championId':2} for _ in range(10)],'champions':[{'championId':1,'name':'A'},{'championId':2,'name':'B'}]}
    result=calibration_report(data)
    assert result['overall']['mean']==50
    assert result['roles'][0]['review'] is True
    assert result['champions'][0]['count']==10
    assert data['matches'][0]['score']==80
