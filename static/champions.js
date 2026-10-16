const $ = id => document.getElementById(id);
let data, displayedQueue = 'all';
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function render() {
  if (!data) return;
  const groups = new Map();
  for (const m of data.matches) { if (!groups.has(m.championId)) groups.set(m.championId, []); groups.get(m.championId).push(m); }
  const mastery = new Map(data.mastery.map(m => [m.championId, m.points]));
  const query = $('search').value.trim().toLocaleLowerCase();
  const rows = data.champions.map(c => {
    const games = groups.get(c.championId) || [], wins = games.filter(m => m.win).length;
    return {...c, games, wins, winRate: games.length ? wins / games.length * 100 : null, points: mastery.get(c.championId) || 0};
  }).filter(c => c.name.toLocaleLowerCase().includes(query) && (!$('played').checked || c.games.length) && c.scoreStats.scored >= Number($('minimum').value));
  const sort = $('sort').value;
  rows.sort((a,b) => {
    let difference = 0;
    if (sort.startsWith('score')) {
      if (a.scoreStats.average === null || b.scoreStats.average === null) return a.scoreStats.average === b.scoreStats.average ? a.name.localeCompare(b.name) : a.scoreStats.average === null ? 1 : -1;
      difference = (a.scoreStats.average - b.scoreStats.average) * (sort === 'score-asc' ? 1 : -1);
    } else if (sort === 'games') difference = b.games.length - a.games.length;
    else if (sort === 'wins') difference = (b.winRate ?? -1) - (a.winRate ?? -1);
    else if (sort === 'mastery') difference = b.points - a.points;
    return difference || b.scoreStats.scored - a.scoreStats.scored || a.name.localeCompare(b.name);
  });
  if (sort === 'name') rows.sort((a,b) => a.name.localeCompare(b.name));
  $('count').textContent = `${rows.length} of ${data.champions.length} champions · ${data.matches.length} saved games · ${displayedQueue === 'all' ? 'All ranked' : displayedQueue === 'solo' ? 'Solo / Duo' : 'Flex'}`;
  $('champion-rows').replaceChildren();
  for (const c of rows) {
    const row = node('tr'), name = node('td'), link = node('a', undefined, 'directory-champion'); link.href = `/champions/${c.championId}`;
    if (c.icon) { const image = node('img'); image.src = c.icon; image.alt = ''; image.loading = 'lazy'; link.append(image); }
    link.append(node('span', c.name)); name.append(link); row.append(name);
    const score = node('td'); score.append(scoreGauge(c.scoreStats.average)); row.append(score);
    const sample = node('td', `${c.scoreStats.scored} / ${c.games.length}`);
    if (c.scoreStats.scored > 0 && c.scoreStats.scored < 5) sample.append(node('small','Small sample','small-sample')); row.append(sample);
    row.append(node('td', c.winRate === null ? '—' : `${c.winRate.toFixed(0)}%`), node('td', `${c.wins} / ${c.games.length - c.wins}`));
    row.append(node('td', c.games.length ? ['kills','deaths','assists'].map(k => (c.games.reduce((n,m) => n + m[k],0) / c.games.length).toFixed(1)).join(' / ') : '—'), node('td',new Intl.NumberFormat().format(c.points)));
    $('champion-rows').append(row);
  }
  if (!rows.length) { const row = node('tr'), cell = node('td','No champions match these filters.'); cell.colSpan = 7; row.append(cell); $('champion-rows').append(row); }
}
async function load() {
  $('refresh').disabled = true; $('queue').disabled = true; $('status').textContent = 'Loading champion stats…';
  const selected = $('queue').value;
  try {
    const response = await fetch(`/api/dashboard?queue=${encodeURIComponent(selected)}`), body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load champions.');
    data = body; displayedQueue = selected; render(); $('status').textContent = '';
  } catch(error) { $('status').textContent = error.message; $('queue').value = displayedQueue; }
  finally { $('refresh').disabled = false; $('queue').disabled = false; }
}
for (const id of ['search','sort','minimum','played']) $(id).addEventListener(id === 'search' ? 'input' : 'change', render);
$('queue').addEventListener('change', load); $('refresh').addEventListener('click', load);
load();
setInterval(() => { if (document.visibilityState === 'visible' && !$('refresh').disabled) load(); }, 30000);
