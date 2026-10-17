from app.draft import draft_report


NOW=2_000_000_000
CATALOG=[{'championId':i,'name':str(i)} for i in (1,2,3,99)]


def test_default_role_uses_most_played_known_role():
    from app.draft import most_played_role
    assert most_played_role([{'role':'UTILITY'}]*8+[{'role':'TOP'}]*2+[{'role':'UNKNOWN'}]*20)=='UTILITY'
    assert most_played_role([])=='TOP'
    assert most_played_role([{'role':'TOP'},{'role':'MIDDLE'}])=='TOP'


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


def test_bans_keep_all_champion_evidence_and_separate_small_samples():
    data={'champions':CATALOG,'matches':[game(1,opponent=2,score=30,win=False) for _ in range(5)]+[game(3,opponent=99,score=0,win=False)]}
    report=draft_report(data,NOW)
    assert [b['championId'] for b in report['laneBans']['qualified']]==[2]
    assert report['laneBans']['limited'][0]['championId']==99


def test_minimum_changes_eligibility_not_ban_score_or_samples():
    matches=[game(1,opponent=99,score=30,win=False) for _ in range(4)]+[game(3,opponent=99,score=10,win=False) for _ in range(2)]
    data={'champions':CATALOG,'matches':matches}
    three=draft_report(data,NOW,minimum=3)['laneBans']['qualified'][0]
    five=draft_report(data,NOW,minimum=5)['laneBans']['qualified'][0]
    assert three['priority']==five['priority']
    assert three['games']==five['games']==6
    ten=draft_report(data,NOW,minimum=10)['laneBans']
    assert not ten['qualified'] and ten['limited'][0]['priority']==three['priority']


def test_general_bans_include_other_enemy_roles_once_per_match():
    matches=[{**game(opponent=99,score=20,win=False),'enemyChampionIds':[99,2,2]} for _ in range(5)]
    matches += [{**game(role='UTILITY',opponent=3,score=20,win=False),'enemyChampionIds':[2,3]} for _ in range(3)]
    report=draft_report({'champions':CATALOG,'matches':matches},NOW,minimum=3)
    assert [b['championId'] for b in report['laneBans']['qualified']]==[99]
    general={b['championId']:b for b in report['generalBans']['qualified']}
    assert general[2]['games']==8
    assert general[99]['games']==5
    assert report['generalCovered']==8
    selected=draft_report({'champions':CATALOG,'matches':matches},NOW,enemy=2)
    assert all(b['championId']!=2 for g in ('laneBans','generalBans') for kind in ('qualified','limited') for b in selected[g][kind])


def test_combined_bans_cap_deduplicate_and_prioritize_qualified():
    from app.bans import combined_bans
    def candidate(i,priority=60,supported=True):
        return {'championId':i,'name':str(i),'priority':priority,'games':5,'supported':supported}
    lane={'qualified':[candidate(i) for i in range(1,5)],'limited':[candidate(10,90,False)]}
    general={'qualified':[candidate(1,70),candidate(5),candidate(6)],'limited':[candidate(11,95,False)]}
    result=combined_bans(lane,general)
    assert len(result)==6 and len({b['championId'] for b in result})==6
    assert all(b['supported'] for b in result)
    assert result[0]['championId']==1 and result[0]['scope']=='general'
    sparse=combined_bans({'qualified':[candidate(1)],'limited':[candidate(2,90,False)]},{'qualified':[],'limited':[]})
    assert len(sparse)==2 and sparse[0]['supported'] and not sparse[1]['supported']


def test_combined_picks_limit_and_mix_evidence_without_duplicates():
    matches=[game(champion=i,opponent=99 if i%2 else 98,score=70+i) for i in range(1,9) for _ in range(5)]
    report=draft_report({'champions':CATALOG,'matches':matches},NOW,enemy=99)
    picks=report['picks']
    assert len(picks)==6 and len({c['championId'] for c in picks})==6
    assert any(c['matchupEligible'] for c in picks)
    assert any(not c['matchupEligible'] for c in picks)
    assert [c['recommendationIndex'] for c in picks]==sorted([c['recommendationIndex'] for c in picks],reverse=True)
    sparse=draft_report({'champions':CATALOG,'matches':[game()]},NOW)['picks']
    assert len(sparse)==1 and not sparse[0]['supported']


def test_low_sample_picks_fill_spaces_after_qualified_picks():
    data={'champions':CATALOG,'matches':[game(1,score=40) for _ in range(5)]+[game(2,score=100)]}
    picks=draft_report(data,NOW,minimum=5)['picks']
    assert [p['championId'] for p in picks]==[1,2]
    assert picks[0]['supported'] and not picks[1]['supported']
