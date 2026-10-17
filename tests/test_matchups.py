from app.matchups import champion_matchups, all_matchups


def test_matchups_group_by_opponent_and_role_and_filter_dates():
    now=2_000_000_000
    def game(role,score,age=0):
        return {'championId':17,'role':role,'opponentId':1,'score':score,'win':score>50,'kills':4,'deaths':2,'assists':6,'playedAt':(now-age*86400)*1000}
    data={'champions':[{'championId':1,'name':'Annie'}],'matches':[game('TOP',80),game('TOP',40),game('MIDDLE',90),game('TOP',100,31)]}
    result=champion_matchups(data,17,now,period='30d')
    assert result['matchedGames']==3
    top=next(r for r in result['rows'] if r['role']=='TOP')
    assert top['games']==2 and top['scoreStats']['average']==60 and top['winRate']==50
    assert top['kda']==[4,2,6]
    assert champion_matchups(data,17,now,role='TOP')['matchedGames']==3


def test_unmatched_games_do_not_get_guessed_opponents():
    data={'champions':[],'matches':[{'championId':17,'matchupStatus':'ambiguous'}, {'championId':17}]}
    result=champion_matchups(data,17,2_000_000_000)
    assert result['rows']==[]
    assert result['ambiguousGames']==1 and result['missingDetails']==1


def test_general_pairs_keep_own_champion_and_role_separate_and_pool_bans():
    now=2_000_000_000
    matches=[{'championId':own,'opponentId':2,'role':role,'score':30,'win':False,'playedAt':now*1000}
             for own,role in [(1,'TOP')]*3+[(3,'TOP')]*2+[(1,'MIDDLE')]*3]
    data={'matches':matches,'champions':[{'championId':1,'name':'One'},{'championId':2,'name':'Enemy'},{'championId':3,'name':'Three'}]}
    result=all_matchups(data,now,minimum=1)
    assert len(result['rows'])==3
    assert result['bans'][0]['games']==8
    assert result['bans'][0]['yourChampions']==2
    filtered=all_matchups(data,now,role='TOP',champion=1,minimum=3)
    assert filtered['bans'][0]['games']==3
    assert len(filtered['rows'])==1


def test_bans_require_repeated_struggles_and_shrink_small_samples():
    now=2_000_000_000
    def game(opponent,win=False):return {'championId':1,'opponentId':opponent,'role':'TOP','score':30 if not win else 80,'win':win,'playedAt':now*1000}
    data={'champions':[],'matches':[game(2) for _ in range(3)]+[game(3) for _ in range(10)]+[game(4)]+[game(5,True) for _ in range(10)]}
    bans=all_matchups(data,now,minimum=1)['bans']
    assert [b['championId'] for b in bans]==[3,2]
    assert bans[0]['priority']>bans[1]['priority']
    assert bans[1]['priority']<91


def test_general_period_filter_excludes_old_ban_evidence():
    now=2_000_000_000
    data={'champions':[],'matches':[{'championId':1,'opponentId':2,'role':'TOP','score':20,'win':False,'playedAt':(now-31*86400)*1000} for _ in range(3)]}
    assert all_matchups(data,now)['bans']
    assert all_matchups(data,now,period='30d')['bans']==[]
