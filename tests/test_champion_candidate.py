from copy import deepcopy
import pytest
from scripts.build_champion_candidate import fit_catalog, balanced_median
from app.scoring import score_player, VERSION
from app.references import CATALOG
from test_scoring import game


def observations(champion, rate, count=40):
    return [{'champion': champion, 'role': 'TOP', 'metric': 'Champion damage',
             'style': 'Mage carry', 'rate30': rate, 'roleTarget': 1000, 'win': i % 2 == 0}
            for i in range(count)]


def test_fit_balances_outcomes_and_excludes_champion_from_parent():
    rows = observations('Annie', 900) + observations('Other1', 600) + observations('Other2', 600)
    catalog = fit_catalog(rows)
    a = next(r for r in catalog['records'] if r['champion'] == 'Annie')
    assert a['parentSamples'] == 80
    assert a['samples'] == 40
    assert a['championMedian30'] == 900
    assert a['parentMedian30'] == 600
    assert a['rate'] == 1500
    assert balanced_median([{'rate30': 100, 'win': True}] * 10 + [{'rate30': 300, 'win': False}]) == 200


def test_sparse_or_one_sided_champion_reference_falls_back():
    rows = observations('Annie', 900, 20) + observations('Other1', 600) + observations('Other2', 600)
    assert all(r['champion'] != 'Annie' for r in fit_catalog(rows)['records'])
    assert fit_catalog(observations('Annie', 900))['records'] == []
    assert fit_catalog([])['records'] == []


def test_candidate_catalog_injection_never_changes_default_catalog_or_version():
    before = deepcopy(CATALOG)
    info = game(); p = info['participants'][0]
    baseline = score_player(info, p, ['Mage'])
    catalog = fit_catalog(observations('Annie', 900) + observations('Other1', 600) + observations('Other2', 600))
    candidate = score_player(info, p, ['Mage'], reference_catalog=catalog)
    component = next(c for c in candidate['components'] if c['name'] == 'Champion damage')
    assert component['referenceSamples'] == 40
    assert component['referenceBlend'] == pytest.approx(40 / 140, abs=.001)
    assert candidate['version'] != baseline['version']
    assert baseline['version'] == VERSION
    assert CATALOG == before
    assert score_player(info, p, ['Mage']) == baseline
