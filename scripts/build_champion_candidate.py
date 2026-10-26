"""Frozen, offline champion-reference candidate. Never edits production model or DB."""
import hashlib
import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scoring import score_player, VERSION
from app.references import CATALOG, ELIGIBLE
from app.history_policy import eligible_info
from scripts.validate_scoring import auc

SOURCE = 'Other participants in selected local histories; configured players excluded; chronological training only; not a population reference'


def balanced_median(rows):
    groups = [[r['rate30'] for r in rows if r['win'] is outcome] for outcome in (True, False)]
    return statistics.mean(statistics.median(g) for g in groups) if all(groups) else None


def fit_catalog(observations):
    """Caller passes training-only, player-excluded observations. Parent excludes champion."""
    groups = defaultdict(list)
    for r in observations:
        if r['metric'] in ELIGIBLE and math.isfinite(r['rate30']) and r['rate30'] >= 0:
            groups[(r['champion'], r['role'], r['metric'])].append(r)
    records = []
    for (champion, role, metric), group in sorted(groups.items()):
        if len(group) < 30 or min(sum(r['win'] is b for r in group) for b in (True, False)) < 10:
            continue
        styles = {r['style'] for r in group}
        if len(styles) != 1:
            continue
        style = next(iter(styles))
        parent = [r for r in observations if r['champion'] != champion and r['role'] == role and r['metric'] == metric and r['style'] == style]
        scope = 'Archetype + role (excluding this champion)'
        if len(parent) < 60 or min(sum(r['win'] is b for r in parent) for b in (True, False)) < 20:
            parent = [r for r in observations if r['champion'] != champion and r['role'] == role and r['metric'] == metric]
            scope = 'Role (excluding this champion)'
        if len(parent) < 60 or min(sum(r['win'] is b for r in parent) for b in (True, False)) < 20:
            continue
        own_median, parent_median = balanced_median(group), balanced_median(parent)
        if own_median is None or parent_median is None or own_median <= 0 or parent_median <= 0:
            continue
        # Match relative champion output to its parent, retaining existing grade semantics.
        baseline = statistics.median(r['roleTarget'] for r in group)
        records.append({'champion': champion, 'role': role, 'metric': metric, 'samples': len(group),
            'rate': baseline * own_median / parent_median, 'source': SOURCE, 'independentOfRatedPlayers': True,
            'parentScope': scope, 'parentSamples': len(parent), 'championMedian30': own_median,
            'parentMedian30': parent_median, 'roleTarget': baseline, 'wins': sum(r['win'] for r in group)})
    return {'id': 'local-champion-candidate-1', 'enabled': True, 'source': SOURCE,
            'note': 'Experimental local reference candidate, not independently validated. Sample blend and +/-20% correction cap are applied by app.references.resolve_reference.', 'records': records}


def summarize(rows):
    if not rows:
        return {'count': 0, 'current': None, 'candidate': None, 'delta': None, 'affected': 0}
    return {'count': len(rows), 'current': round(statistics.mean(r['current'] for r in rows), 2),
            'candidate': round(statistics.mean(r['candidate'] for r in rows), 2),
            'delta': round(statistics.mean(r['candidate'] - r['current'] for r in rows), 2),
            'affected': sum(r['current'] != r['candidate'] for r in rows)}


def run():
    output = ROOT / 'reports/champion-candidate'
    if output.exists():
        raise SystemExit('Frozen experiment already exists. Preserve it; choose a new versioned output directory for a new experiment.')
    db = sqlite3.connect((ROOT / 'data/journal.sqlite3').as_uri() + '?mode=ro', uri=True)
    profiles = {o: json.loads(b) for o, b in db.execute('SELECT player,body FROM profiles')}
    details = db.execute('SELECT player,id,body FROM details ORDER BY player,id').fetchall()
    db.close()
    excluded = {json.loads(body)['puuid'] for _, _, body in details}
    games = {}
    for owner, mid, body in details:
        d = json.loads(body)
        if eligible_info(d['raw']['info']):
            games.setdefault(mid, (owner, d))
    ordered = sorted(games, key=lambda mid: (games[mid][1]['raw']['info'].get('gameStartTimestamp', 0), mid))
    if len(ordered) < 10:
        raise SystemExit('Not enough saved matches for a chronological experiment.')
    cut = int(len(ordered) * .6)
    cutoff = games[ordered[cut]][1]['raw']['info'].get('gameStartTimestamp', 0)
    train_ids = {mid for mid in ordered if games[mid][1]['raw']['info'].get('gameStartTimestamp', 0) < cutoff}
    test_ids = set(ordered) - train_ids
    assert train_ids.isdisjoint(test_ids)
    observations, scored = [], []
    for mid in ordered:
        owner, d = games[mid]; info = d['raw']['info']
        tags = {c['championId']: c.get('tags') for c in profiles.get(owner, {}).get('champions', [])}
        for p in info['participants']:
            current = score_player(info, p, tags.get(p['championId']))
            if current['value'] is None:
                continue
            row = {'match': mid, 'champion': p['championName'], 'role': p.get('teamPosition') or 'UNKNOWN',
                   'style': current['archetype'], 'win': bool(p['win']), 'minutes': info['gameDuration'] / 60,
                   'configuredPlayer': p['puuid'] in excluded, 'current': current['value'],
                   'split': 'training' if mid in train_ids else 'holdout'}
            scored.append((row, info, p, tags.get(p['championId']), current))
            if mid not in train_ids or p['puuid'] in excluded or not 10 <= row['minutes'] <= 50:
                continue
            for c in current['components']:
                if c['name'] in ELIGIBLE:
                    observations.append({**row, 'metric': c['name'], 'rate30': c['own'] / c['durationMultiplier'], 'roleTarget': c['roleTarget']})
    catalog = fit_catalog(observations)
    evaluated = []
    for row, info, p, tags, current in scored:
        candidate = score_player(info, p, tags, reference_catalog=catalog)
        applied = [{'metric': c['name'], 'samples': c['referenceSamples'], 'blend': c['referenceBlend'],
                    'reference': c['baseTarget'], 'roleReference': c['roleTarget']} for c in candidate['components'] if c['referenceSamples']]
        evaluated.append({**row, 'candidate': candidate['value'], 'delta': round(candidate['value'] - row['current'], 1), 'appliedReferences': applied})
    held = [r for r in evaluated if r['split'] == 'holdout']
    others = [r for r in held if not r['configuredPlayer']]
    own = [r for r in held if r['configuredPlayer']]
    styles = {s: summarize([r for r in others if r['style'] == s]) for s in sorted({r['style'] for r in others})}
    champion_groups = {}
    for r in own:
        champion_groups.setdefault((r['champion'], r['role']), []).append(r)
    own_groups = [{'champion': k[0], 'role': k[1], **summarize(rs)} for k, rs in sorted(champion_groups.items())]
    biggest = sorted(held, key=lambda r: (-abs(r['delta']), r['match'], r['champion']))[:20]
    report = {'baselineVersion': VERSION, 'trainingMatches': len(train_ids), 'holdoutMatches': len(test_ids),
        'cutoffTimestamp': cutoff, 'excludedConfiguredPlayers': len(excluded), 'trainingObservations': len(observations),
        'candidateRecords': len(catalog['records']), 'holdoutOtherPlayers': summarize(others), 'holdoutConfiguredPlayers': summarize(own),
        'otherPlayersAUC': {'current': auc([{'score': r['current'], 'win': r['win']} for r in others]),
                           'candidate': auc([{'score': r['candidate'], 'win': r['win']} for r in others])},
        'holdoutArchetypes': styles, 'configuredChampionGroups': own_groups, 'largestChanges': biggest}
    output.mkdir(parents=True)
    baseline_dir = output / 'baseline'; baseline_dir.mkdir()
    manifest = {}
    for name in ('scoring.py', 'references.py', 'champion_references.json', 'duration.py', 'duration_model.json', 'archetypes.py'):
        body = (ROOT / 'app' / name).read_bytes()
        (baseline_dir / name).write_bytes(body)
        manifest[name] = hashlib.sha256(body).hexdigest()
    (output / 'baseline-manifest.json').write_text(json.dumps({'version': VERSION, 'sha256': manifest}, indent=2), encoding='utf-8')
    (output / 'candidate-references.json').write_text(json.dumps(catalog, indent=2), encoding='utf-8')
    (output / 'split.json').write_text(json.dumps({'training': sorted(train_ids), 'holdout': sorted(test_ids)}, indent=2), encoding='utf-8')
    (output / 'evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (output / 'match-comparisons.json').write_text(json.dumps(evaluated, indent=2), encoding='utf-8')
    lines = ['# Champion/role reference candidate — frozen experiment 1', '',
        '**Active v6 is unchanged. This candidate is not a validated replacement.**', '',
        f"Training: {len(train_ids)} earlier matches. Holdout: {len(test_ids)} later matches. Both configured players ({len(excluded)} identities) are excluded from fitting, even when appearing in another profile’s history. Shared matches are deduplicated. Equal timestamps remain in the same split.", '',
        '## What changes', '',
        'Only champion/role references for damage, ally utility, CC and tower pressure. References are estimated from other players in training matches, using raw rates normalized by the frozen duration multiplier to 30-minute equivalents. Champion and parent rates each balance win/loss medians 50:50. The parent is archetype+role excluding that champion, falling back to role excluding that champion. Champion samples need at least 30 performances with 10 wins and 10 losses; parents need 60 with 20 of each. Sample shrinkage n/(n+100) and a ±20% correction bound remain. Curves, weights, duration model, bonus caps and survival are fixed.', '',
        'These observations exclude the rated accounts but remain selected through their histories. They are not a representative population or independent replay judgments. Champion fit changes reference difficulty; it must not be interpreted as measuring champion strength or player skill.', '',
        f"Qualified champion/role/metric records: {len(catalog['records'])}. Unsupported champion metrics retain their existing references.", '',
        '## Later-match comparison', '', '| Evaluation group | Performances | V6 mean | Candidate mean | Change | Changed scores |', '|---|---:|---:|---:|---:|---:|']
    for label, rs in [('Other participants', others), ('Configured players (never fitted)', own)]:
        s = summarize(rs); lines.append(f"| {label} | {s['count']} | {s['current']} | {s['candidate']} | {s['delta']} | {s['affected']} |")
    lines += ['', f"Retrospective win/outcome AUC among other held-out participants: {report['otherPlayersAUC']['current']} → {report['otherPlayersAUC']['candidate']}. Outcome association alone is not a measure of fair individual contribution.", '',
        '## Held-out archetypes (other participants)', '', '| Archetype | Performances | V6 | Candidate | Change | Changed scores |', '|---|---:|---:|---:|---:|---:|']
    for name, s in styles.items(): lines.append(f"| {name} | {s['count']} | {s['current']} | {s['candidate']} | {s['delta']} | {s['affected']} |")
    lines += ['', '## Held-out familiar-match review', '',
        'Review links reveal current scores and require the matching profile to be selected. Candidate scores are shown here for comparison; this is not a blind review. Prefer cases you remember or can replay. Statistical coverage does not establish whether a death, engage, or damage was useful.', '',
        '| Match | Champion / role | Result | V6 | Candidate | Change |', '|---|---|---|---:|---:|---:|']
    familiar = sorted([r for r in own if r['appliedReferences']], key=lambda r: (-abs(r['delta']), r['match']))[:12]
    for r in familiar:
        lines.append(f"| [{r['match']}](http://127.0.0.1:8000/matches/{r['match']}) | {r['champion']} / {r['role']} | {'Win' if r['win'] else 'Loss'} | {r['current']} | {r['candidate']} | {r['delta']} |")
    lines += ['', '## Artifacts and decision', '',
        '- baseline/: frozen scorer/configuration sources; baseline-manifest.json records hashes.',
        '- candidate-references.json: offline experimental references; not copied into app/.',
        '- split.json: exact training and holdout IDs.',
        '- match-comparisons.json: every comparison, with split and reference coverage.',
        '- evaluation.json: numerical summary.', '',
        'Do not activate automatically. Judge changed familiar games and compare held-out champion groups; lower archetype gaps or better win association alone cannot establish correctness. Future tuning must use a new experiment ID and a fresh evaluation set. The split protects against champion-reference fitting leakage; it does not undo prior v4/v6 design decisions informed by this history, nor prove the pre-existing duration model was trained on a disjoint history.', '']
    (output / 'review.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': run()
