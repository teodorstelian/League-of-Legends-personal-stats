"""Explicit, frozen champion references; no fitting to the rated player's history."""
import json
import math
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name('champion_references.json').read_text(encoding='utf-8'))
ELIGIBLE = {'Champion damage', 'Support impact', 'Crowd control', 'Tower pressure'}


def resolve_reference(champion, role, metric, fallback, catalog=None):
    catalog = CATALOG if catalog is None else catalog
    result = {'rate': fallback, 'source': 'Archetype / role baseline', 'samples': 0,
              'blend': 0, 'status': 'Provisional app reference; no champion reference applied'}
    if not catalog.get('enabled') or metric not in ELIGIBLE:
        return result
    # Reject ambiguous entries rather than choosing whichever happens to occur first.
    rows = [r for r in catalog.get('records', []) if (r.get('champion'), r.get('role'), r.get('metric')) == (champion, role, metric)]
    if len(rows) != 1:
        return result
    row = rows[0]
    count, rate = row.get('samples'), row.get('rate')
    if (not isinstance(count, int) or isinstance(count, bool) or count < 30
        or not isinstance(rate, (int, float)) or isinstance(rate, bool) or not math.isfinite(rate) or rate <= 0
        or not row.get('source') or row.get('independentOfRatedPlayers') is not True):
        return result
    blend = count / (count + 100)
    # Conservative correction around the archetype baseline, not a new personal average.
    ratio = max(.8, min(1.2, 1 + (rate / fallback - 1) * blend))
    return {'rate': fallback * ratio, 'source': row['source'], 'samples': count,
            'blend': round(blend, 3), 'status': 'Champion + role reference, shrunk toward archetype / role baseline'}
