from app.duo import duo_report


NOW=2_000_000_000


def game(mid='shared', owner='a', enemy=False, queue=420, duration=1200, age=0, win=True):
    participants=[{'puuid':'a','teamId':100,'championId':17,'championName':'Teemo','teamPosition':'TOP','kills':3,'deaths':2,'assists':4,'win':win},
        {'puuid':'b','teamId':200 if enemy else 100,'championId':143,'championName':'Zyra','teamPosition':'UTILITY','kills':1,'deaths':4,'assists':8,'win':win}]
    return ({'id':mid,'playedAt':(NOW-age*86400)*1000}, {'puuid':owner,'raw':{'info':{'participants':participants,'queueId':queue,'gameDuration':duration,'gameStartTimestamp':(NOW-age*86400)*1000}}})


def test_deduplicates_shared_games_and_preserves_player_order():
    r=duo_report([game()],[game(owner='b')],[{},{}],now=NOW)
    assert r['ready'] and r['summary']['games']==1
    assert r['summary']['winRate']==100
    assert r['matches'][0]['players'][0]['name']=='Teemo'
    assert r['matches'][0]['players'][1]['role']=='Support'
    assert r['summary']['players'][0]['kda']==[3,2,4]
    assert 'puuid' not in str(r)


def test_union_counts_shared_game_saved_only_by_partner():
    r=duo_report([game('a-only')],[game('b-only',owner='b')],[{},{}],now=NOW)
    assert r['summary']['games']==2
    assert r['combinations'][0]['games']==2
    assert {m['owner'] for m in r['matches']}=={0,1}


def test_excludes_opponents_nonranked_remakes_and_filters():
    first=[game('valid'),game('opponents',enemy=True),game('normal',queue=400),game('short',duration=179),game('old',age=31),game('flex',queue=440)]
    r=duo_report(first,[game('valid',owner='b')],[{},{}],queue='solo',period='30d',now=NOW)
    assert [m['id'] for m in r['matches']]==['valid']


def test_empty_or_same_identity_is_not_a_duo():
    for second in ([],[game()]):
        r=duo_report([game()],second,[{},{}],now=NOW)
        assert not r['ready'] and r['summary']['games']==0
        assert r['summary']['players'][0]['score'] is None


def test_absent_partner_not_inferred_from_names():
    a=game();a[1]['raw']['info']['participants'].pop()
    r=duo_report([a],[game('opponents',owner='b',enemy=True)],[{},{}],now=NOW)
    assert r['ready'] and r['summary']['games']==0
