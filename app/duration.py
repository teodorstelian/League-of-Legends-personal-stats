"""Frozen experimental duration adjustment. Disable and restart to restore v4."""
import json
from pathlib import Path

DURATION_ENABLED = True
MODEL = json.loads(Path(__file__).with_name('duration_model.json').read_text(encoding='utf-8'))
SLOPES = {(r['role'], r['style'], r['metric']): r['slope'] for r in MODEL['models']}


def reference_multiplier(role, archetype, metric, minutes):
    slope = SLOPES.get((role, archetype, metric))
    if slope is None:
        return 1.0
    duration = max(10, min(50, minutes))
    return max(.7, min(1.3, (duration / 30) ** slope))
