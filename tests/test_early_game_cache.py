from copy import deepcopy
from app import storage
from app.early_game import early_game_report
from test_early_game import row, NOW


def save(owner, item, timeline=True):
    m,d,t=item
    storage.save_match(owner,m);storage.detail(owner,m['id'],d)
    if timeline:storage.timeline(m['id'],t)


def test_compact_report_matches_original_and_warm_reads_skip_raw_payloads(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'cache.sqlite3')
    for item in (row(),row('loss',gold=-100,win=False),row('short',duration=500),row('unknown',role='UNKNOWN')):save('me',item)
    missing=row('missing');save('me',missing,False)
    unavailable=row('unavailable');save('me',unavailable,False);storage.timeline('unavailable',{'unavailable':True})
    expected=early_game_report(storage.timeline_rows('me'),NOW)
    actual=early_game_report(storage.early_game_rows('me',NOW),NOW)
    assert actual==expected
    import app.early_game as early
    monkeypatch.setattr(early,'compact_timeline',lambda *args:(_ for _ in ()).throw(AssertionError('Raw timeline recomputed')))
    assert early_game_report(storage.early_game_rows('me',NOW),NOW)==expected
    inventory=storage.timeline_inventory('me')
    assert inventory=={'total':6,'cached':4,'unavailable':1,'pending':['missing']}


def test_filters_precede_timeline_parsing_and_details_role_is_authoritative(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'filters.sqlite3')
    save('me',row('a',role='UTILITY'));save('me',row('other',champion=2));save('me',row('old',age=31));save('other',row('foreign'))
    expected=early_game_report(storage.timeline_rows('me'),NOW,role='UTILITY',champion=17,period='30d')
    filtered=storage.early_game_rows('me',NOW,role='UTILITY',champion=17,period='30d')
    assert early_game_report(filtered,NOW,role='UTILITY',champion=17,period='30d')==expected
    with storage.connect() as db:
        assert [r[0] for r in db.execute('SELECT id FROM early_game_cache')]==['a']
    # A previous role-filtered request must not poison a later unfiltered report.
    assert early_game_report(storage.early_game_rows('me',NOW),NOW)==early_game_report(storage.timeline_rows('me'),NOW)


def test_timeline_and_details_updates_invalidate_compact_results_across_profiles(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'invalidate.sqlite3')
    original=row();save('me',original);save('other',original)
    storage.early_game_rows('me',NOW);storage.early_game_rows('other',NOW)
    changed=deepcopy(original);changed[2]['info']['frames'][0]['participantFrames']['1']['totalGold']=8000
    storage.timeline('a',changed[2])
    with storage.connect() as db:assert db.execute('SELECT COUNT(*) FROM early_game_cache').fetchone()[0]==0
    actual=early_game_report(storage.early_game_rows('me',NOW),NOW)
    assert actual['summary']['checkpoints'][0]['gold']==3000
    changed[1]['raw']['info']['participants'][0]['teamPosition']='JUNGLE'
    storage.detail('me','a',changed[1])
    assert early_game_report(storage.early_game_rows('me',NOW),NOW)['roles'][0]['role']=='JUNGLE'
    storage.timeline('a',{'unavailable':True})
    assert storage.timeline_inventory('me')['unavailable']==1
    assert early_game_report(storage.early_game_rows('me',NOW),NOW)['cached']==0


def test_legacy_metadata_backfill_and_stale_cache_version(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'legacy.sqlite3')
    save('me',row())
    storage.early_game_rows('me',NOW)
    import json
    with storage.connect() as db:
        body=json.loads(db.execute('SELECT body FROM early_game_cache').fetchone()[0]);body['report']['version']=-1
        db.execute('UPDATE early_game_cache SET body=?',(json.dumps(body),))
        db.execute('DELETE FROM timeline_meta')
    assert storage.timeline_inventory('me')['cached']==1
    assert early_game_report(storage.early_game_rows('me',NOW),NOW)==early_game_report(storage.timeline_rows('me'),NOW)
