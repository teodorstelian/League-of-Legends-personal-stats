"""Prepare a reproducible blinded review worksheet from saved data, without DB writes."""
import hashlib
import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scoring import VERSION, score_player
from app.history_policy import eligible_info


def prepare():
    db = sqlite3.connect((ROOT / 'data/journal.sqlite3').as_uri() + '?mode=ro', uri=True)
    profiles = {owner: json.loads(body) for owner, body in db.execute('SELECT player,body FROM profiles')}
    rows = db.execute('SELECT d.player,d.id,d.body,EXISTS(SELECT 1 FROM timelines t WHERE t.id=d.id) FROM details d JOIN matches m ON m.player=d.player AND m.id=d.id').fetchall()
    db.close()
    candidates = []
    for owner, match_id, body, timeline in rows:
        if match_id == 'EUN1_4017526326':
            continue  # Previously inspected development example.
        detail = json.loads(body)
        info = detail['raw']['info']
        if not eligible_info(info):
            continue
        p = next((p for p in info['participants'] if p.get('puuid') == detail['puuid']), None)
        if not p:
            continue
        tags = next((c.get('tags') for c in profiles.get(owner, {}).get('champions', []) if c['championId'] == p['championId']), None)
        score = score_player(info, p, tags)
        if score['value'] is None:
            continue
        style = score['archetype']
        pool = 'Tank' if style in ('Tank', 'Tank support') else 'Damage support' if style == 'Damage support' else 'Other'
        candidates.append({'profile': owner, 'match': match_id, 'champion': p['championName'], 'role': p.get('teamPosition') or 'Unknown',
            'win': bool(p['win']), 'duration': info['gameDuration'], 'playedAt': info.get('gameStartTimestamp', 0),
            'timelineCached': bool(timeline), 'pool': pool, 'score': score['value'], 'archetype': style, 'components': score['components']})
    selected, used = [], set()
    for pool in ('Tank', 'Damage support', 'Other'):
        for win in (True, False):
            group = sorted([c for c in candidates if c['pool'] == pool and c['win'] == win], key=lambda c: (c['score'], c['match'], c['profile']))
            width = max(1, len(group) // 3)
            for label, band in [('lower third', group[:width]), ('upper third', group[-width:])]:
                available = [c for c in band if c['match'] not in used]
                if not available:
                    raise ValueError(f'Insufficient distinct matches for {pool}, win={win}, {label}')
                # Stable sample within each tail, rather than picking the most extreme match.
                chosen = min(available, key=lambda c: hashlib.sha256(f"review-v1:{c['profile']}:{c['match']}".encode()).hexdigest())
                selected.append({**chosen, 'selectionBand': label})
                used.add(chosen['match'])
    random.Random(20261020).shuffle(selected)
    for i, case in enumerate(selected, 1):
        case['case'] = f'R{i:02d}'
    output = ROOT / 'reports' / 'blind-review'
    output.mkdir(exist_ok=True)
    key = {'version': VERSION, 'method': 'Development-only purposive sample: lower and upper score thirds in each of tank/damage-support/other × win/loss. Includes both saved profiles; one performance per match. Known inspected Skarner match excluded. This selection is score-stratified, not random population validation, and reviewer may recognize prior games. Do not use for estimating population accuracy. Freeze reviews before opening this key. Timeline cache is not proof a replay or usable timeline exists.', 'cases': selected}
    (output / 'score-key.json').write_text(json.dumps(key, indent=2), encoding='utf-8')
    lines = ['# Blind Rift Score review — 12 matches', '',
        'Review the specified player in each match. Do not open score-key.json, calibration rankings, or the app’s match page until judgments are frozen: those reveal scores. Cases are shuffled and the worksheet contains no formula scores or strength labels.', '',
        'This is a development review, not an independent population study. It includes two saved profiles. Some games may be familiar. A cached timeline does not contain the full replay; these historical games may no longer have playable replays. Mark unavailable cases rather than inventing judgments.', '',
        '## How to review', '',
        'Use an available replay or your own direct recollection, and state which. If using only memory, mark confidence low. Recorded statistics alone cannot establish positioning, decision quality, or whether a death was justified.', '',
        'For each criterion use 1 = repeatedly harmful/ineffective, 2 = below ordinary, 3 = mixed/ordinary, 4 = strong, 5 = exceptional. Use N/A when evidence is missing. These are reviewer categories, not measured population standards. Assess contribution in the player’s role; avoid grading solely on win/loss, KDA, or total damage.', '',
        '- Early game/resource use: farming, pressure, resource efficiency, and role duties.',
        '- Deaths/risk: avoidable deaths versus justified risks or useful sacrifices.',
        '- Fights/utility: useful damage, engages, protection, CC, and participation.',
        '- Objectives/map: setup, rotations, towers, neutral objectives, and pressure.', '',
        'Record two timestamped examples where possible, an overall category, confidence, and optional 0–100 grade. Leave the numerical grade blank if you cannot justify it. Do not average N/A criteria as zero.', '',
        'After all cases, name 3–5 pairs where one performance clearly contributed more, with reasons. Save your completed judgments before consulting the separate key. Compare ordering first and numerical grades second; do not tune on every case and then call those cases independent validation.', '',
        '## Review cases', '']
    for c in selected:
        date = datetime.fromtimestamp(c['playedAt'] / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if c['playedAt'] else 'Unknown'
        lines += [f"### {c['case']} — {c['champion']} · {c['role']}", '',
            f"Player: **{c['profile']}** · Match: **{c['match']}**", '',
            f"Played: {date} · Duration: {c['duration']//60}:{c['duration']%60:02d} · Result: {'Win' if c['win'] else 'Loss'} · Timeline row cached: {'Yes' if c['timelineCached'] else 'No'}", '',
            '- Evidence source (replay / direct recollection / unavailable):',
            '- Familiar case or remembered score? (yes/no):',
            '- Early game/resources (1–5 or N/A):', '- Deaths/risk (1–5 or N/A):',
            '- Fights/utility (1–5 or N/A):', '- Objectives/map (1–5 or N/A):',
            '- Example 1 — timestamp, decision, consequence:', '- Example 2 — timestamp, decision, consequence:',
            '- Overall category (poor / below ordinary / mixed / strong / exceptional / cannot judge):',
            '- Optional independent grade (0–100):', '- Confidence (low/medium/high):', '- Main improvement:', '']
    lines += ['## Pairwise judgments', '', '| Better case | Weaker case | Evidence / reason | Confidence |', '|---|---|---|---|', '| | | | |', '| | | | |', '| | | | |', '', 'Review completed at: ____', '', 'Judgments frozen before opening key: yes / no', '']
    (output / 'review-sheet.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'README.md').write_text('# Review pack\n\nStart with **review-sheet.md**. Keep **score-key.json** closed until your judgments are complete. Match pages show scores, so avoid them during the blind pass. No replays are included or fetched. If replay evidence is unavailable, say so; a worksheet cannot replace gameplay review.\n', encoding='utf-8')
    assert len(selected) == 12 and len({c['match'] for c in selected}) == 12
    assert sum(c['win'] for c in selected) == 6
    for pool in ('Tank', 'Damage support', 'Other'):
        assert sum(c['pool'] == pool for c in selected) == 4
    # Ensure formula scores and selection labels never enter the review sheet.
    assert 'selectionBand' not in '\n'.join(lines) and '"score"' not in '\n'.join(lines)
    print('Prepared 12 distinct matches: 6 wins / 6 losses; 4 tanks, 4 damage supports, 4 other styles.')
    print('Timeline rows cached:', sum(c['timelineCached'] for c in selected))
    print(output / 'review-sheet.md')


if __name__ == '__main__':
    prepare()
