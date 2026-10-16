// Shared presentation for every aggregate: unscored games never count as zero.
function scoreColor(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '#96a49b';
  return value < 40 ? '#f08b87' : value < 50 ? '#efb56c' : value < 60 ? '#dfcf77' : value < 75 ? '#9cda9a' : '#6ed7cc';
}
function scoreGauge(score, size = '', label = 'Rift Score') {
  const gauge = document.createElement('div'); gauge.className = `match-gauge ${size}`;
  const scored = typeof score === 'number' && Number.isFinite(score);
  const value = scored ? Math.min(100, Math.max(0, score)) : 0;
  gauge.style.setProperty('--score-angle', `${value * 3.6}deg`);
  gauge.style.setProperty('--score-color', scoreColor(score));
  gauge.setAttribute('role', 'img'); gauge.setAttribute('aria-label', scored ? `${label} ${value.toFixed(1)} out of 100` : `${label} unavailable`);
  gauge.title = gauge.getAttribute('aria-label');
  const number = document.createElement('span'); number.textContent = scored ? value.toFixed(1) : '—'; gauge.append(number);
  return gauge;
}
function riftScoreText(stats) {
  return stats?.average === null || stats?.average === undefined ? '—' : `${stats.average.toFixed(1)} / 100`;
}
function riftScoreSample(stats) {
  return `${stats.scored} scored / ${stats.total} saved game${stats.total === 1 ? '' : 's'}${stats.scored > 0 && stats.scored < 5 ? ' · Small sample' : ''}`;
}
function renderScoreSummary(stats, lanes) {
  document.getElementById('average-score').replaceChildren(scoreGauge(stats.average, 'gauge-large', 'Average Rift Score'));
  document.getElementById('score-sample').textContent = riftScoreSample(stats);
  const root = document.getElementById('lane-scores'); root.replaceChildren();
  for (const lane of lanes) {
    const card = document.createElement('article'); card.className = 'lane-score';
    const name = document.createElement('h3'); name.textContent = lane.name;
    const value = scoreGauge(lane.average, 'gauge-medium', `${lane.name} average Rift Score`);
    const sample = document.createElement('p'); sample.className = 'muted'; sample.textContent = riftScoreSample(lane);
    card.append(name, value, sample); root.append(card);
  }
  const legend = document.createElement('p'); legend.className = 'score-legend';
  for (const [value, text] of [[20,'0–39'],[45,'40–49'],[55,'50–59'],[65,'60–74'],[85,'75–100']]) {
    const item = document.createElement('span'); const dot = document.createElement('i'); dot.style.background = scoreColor(value); item.append(dot, text); legend.append(item);
  }
  root.append(legend);
}

const itemCatalogs = new Map();
let itemVersions;
async function matchItemCatalog(patch) {
  if (!itemCatalogs.has(patch)) itemCatalogs.set(patch, (async () => {
    itemVersions ??= fetch('https://ddragon.leagueoflegends.com/api/versions.json').then(r => { if (!r.ok) throw new Error(); return r.json(); });
    const versions = await itemVersions;
    const version = versions.find(v => v.startsWith(`${patch}.`)) || versions[0];
    const base = `https://ddragon.leagueoflegends.com/cdn/${version}`;
    const response = await fetch(`${base}/data/en_US/item.json`);
    if (!response.ok) throw new Error();
    return {base, items: (await response.json()).data};
  })().catch(() => null));
  return itemCatalogs.get(patch);
}

function matchBuildAndScore(match) {
  const build = document.createElement('div'); build.className = 'match-build';
  build.setAttribute('aria-label', match.items ? 'Final item build' : 'Item details pending');
  if (match.items) {
    for (const [slot, id] of match.items.entries()) {
      const item = document.createElement('span'); item.className = `match-item${slot === 6 ? ' trinket' : ''}`;
      item.title = id ? `Item ${id}` : 'Empty item slot';
      if (id) {
        item.textContent = '?';
        matchItemCatalog(match.itemPatch).then(catalog => {
          if (!catalog || !item.isConnected) return;
          const entry = catalog.items[id];
          if (!entry) return;
          const image = document.createElement('img'); image.src = `${catalog.base}/img/item/${entry.image.full}`;
          image.alt = entry.name; image.loading = 'lazy'; item.title = entry.name;
          image.addEventListener('error', () => { image.remove(); item.textContent = '?'; });
          item.replaceChildren(image);
        });
      }
      build.append(item);
    }
  } else {
    const pending = document.createElement('small'); pending.textContent = 'Items pending'; build.append(pending);
  }
  return [build, scoreGauge(match.score)];
}
