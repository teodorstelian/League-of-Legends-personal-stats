import pytest
from app import storage

@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB', tmp_path / 'lp.sqlite3')

def rank(lp=80, wins=10, losses=5, tier='GOLD', division='II'):
    return dict(leaguePoints=lp, wins=wins, losses=losses, tier=tier, rank=division)

def observe(entry, ids, player='A', queue=420):
    storage.observe_rank(player, queue, entry, ids)

def delta(match='new', player='A'):
    with storage.connect() as db:
        row = db.execute('SELECT delta FROM lp_changes WHERE player=? AND id=?', (player, match)).fetchone()
    return row[0] if row else None

def test_single_game_promotion_and_repeat():
    observe(rank(), ['old', 'older'])
    observe(rank(5, 11, division='I'), ['new', 'old'])
    assert delta() == 25
    observe(rank(5, 11, division='I'), ['new', 'old'])
    assert delta() == 25
    storage.save_match('A', dict(id='new', queue=420, duration=900, playedAt=1))
    assert storage.matches('A')[0]['lpChange'] == 25

def test_loss_and_queue_player_isolation():
    observe(rank(), ['old', 'older'])
    observe(rank(60, losses=6), ['new', 'old'])
    assert delta() == -20
    assert delta(player='B') is None
    observe(rank(90, 11), ['flex', 'old'], queue=440)
    assert delta('flex') is None

@pytest.mark.parametrize('entry,ids', [
    (rank(30, 12), ['new', 'middle']),
    (rank(60), ['old', 'older']),
    (rank(0, 0, 0), ['new', 'old']),
    (None, ['new', 'old']),
    (rank(5, 11, tier='IRON'), ['new', 'old']),
])
def test_ambiguous_gaps_and_resets_are_unknown(entry, ids):
    observe(rank(), ['old', 'older'])
    observe(entry, ids)
    assert delta() is None

def test_unknown_is_not_zero():
    storage.save_match('A', dict(id='old', queue=420, duration=900, playedAt=1))
    assert storage.matches('A')[0]['lpChange'] is None
    observe(rank(), ['old', 'older'])
    observe(rank(wins=11), ['new', 'old'])
    assert delta() == 0


def test_import_lp_validates_matches_and_preserves_sources():
    storage.save_match('A', dict(id='EUN1_123', queue=420, duration=900, playedAt=1, win=True))
    record = dict(id='EUN1_123', delta=19, queue=420, source='https://www.leagueofgraphs.com/match/eune/123')
    assert storage.import_lp_records('A', [record])['imported'] == 1
    assert storage.import_lp_records('A', [record])['unchanged'] == 1
    match = storage.matches('A')[0]
    assert match['lpChange'] == 19
    assert match['lpSource']['url'] == record['source']
    assert storage.import_lp_records('B', [record])['missing'] == 1
    assert storage.import_lp_records('A', [{**record, 'delta': 20}])['conflicts'] == 1
    assert storage.matches('A')[0]['lpChange'] == 19


@pytest.mark.parametrize('changes', [
    {'delta': -20}, {'queue': 440}, {'delta': True},
    {'source': 'https://www.leagueofgraphs.com/match/eune/999'},
    {'source': 'https://example.com/match/eune/123'},
])
def test_import_rejects_inconsistent_records(changes):
    storage.save_match('A', dict(id='EUN1_123', queue=420, duration=900, playedAt=1, win=True))
    record = dict(id='EUN1_123', delta=19, queue=420, source='https://www.leagueofgraphs.com/match/eune/123')
    assert storage.import_lp_records('A', [{**record, **changes}])['invalid'] == 1
    assert storage.matches('A')[0]['lpChange'] is None
