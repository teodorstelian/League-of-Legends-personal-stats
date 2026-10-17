from app.draft import draft_report


NOW=2_000_000_000
CATALOG=[{'championId':i,'name':str(i)} for i in (1,2,3,99)]


def game(champion=1,opponent=99,score=70,role='TOP',age=0,win=True):
    return {'championId':champion,'opponentId':opponent,'score':score,'role':role,'win':win,'playedAt':(NOW-age*86400)*1000}


def test_comfort_requires_role_samples_and_excludes_mirror_pick():
    data={'champions':CATALOG,'matches':[game() for _ in range(5)]+[game(2,score=100)]+[game(3,role='UTILITY') for _ in range(10)]+[game(99) for _ in range(5)]}
    report=draft_report(data,NOW,enemy=99,minimum=3)
    assert [c['championId'] for c in report['comfort']]==[1]
    assert report['matchup'][0]['championId']==1
    assert all(b['championId']!=99 for b in report['bans'])


def test_sparse_matchups_fall_back_without_counter_claim():
    data={'champions':CATALOG,'matches':[game(opponent=2) for _ in range(5)]+[game()]}
    report=draft_report(data,NOW,enemy=99,minimum=3)
    assert report['fallback'] is True and report['matchup']==[]
    assert report['comfort'][0]['matchup']['total']==1
    assert not report['comfort'][0]['matchupEligible']


def test_shrinkage_prevents_small_sample_outranking_same_average():
    data={'champions':CATALOG,'matches':[game(1,score=80) for _ in range(3)]+[game(2,score=80) for _ in range(10)]}
    report=draft_report(data,NOW)
    assert report['comfort'][0]['championId']==2
    assert report['comfort'][0]['comfort']['average']==report['comfort'][1]['comfort']['average']


def test_period_and_role_filters_apply_to_entire_pool():
    data={'champions':CATALOG,'matches':[game(age=31) for _ in range(5)]+[game(2,role='UTILITY') for _ in range(5)]}
    report=draft_report(data,NOW,period='30d')
    assert report['totalGames']==0 and report['comfort']==[] and report['bans']==[]


def test_bans_use_only_qualifying_champion_pool():
    data={'champions':CATALOG,'matches':[game(1,opponent=2,score=30,win=False) for _ in range(5)]+[game(3,opponent=99,score=0,win=False)]}
    report=draft_report(data,NOW)
    assert [b['championId'] for b in report['bans']]==[2]
