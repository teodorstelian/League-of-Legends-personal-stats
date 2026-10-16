const $ = id => document.getElementById(id);
let data, visible = 25, selectedQueue = 'all';
function el(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function render() {
  if (!data) return;
  const query = $('search').value.trim().toLocaleLowerCase(), result = $('result').value;
  const matches = data.matches.filter(m => m.name.toLocaleLowerCase().includes(query) && (result === 'all' || m.win === (result === 'win')));
  if ($('sort').value === 'score') matches.sort((a,b) => (b.score ?? -1) - (a.score ?? -1) || b.playedAt - a.playedAt);
  const wins = matches.filter(m => m.win).length, scored = matches.filter(m => typeof m.score === 'number');
  const average = scored.length ? (scored.reduce((n,m) => n + m.score,0) / scored.length).toFixed(1) : '—';
  $('summary').textContent = `${matches.length} matching games · ${wins} wins / ${matches.length - wins} losses · Average Rift Score ${average} (${scored.length} scored) · Showing ${Math.min(visible,matches.length)}`;
  $('matches').replaceChildren();
  for (const match of matches.slice(0,visible)) {
    const row = el('a', undefined, `match ${match.win ? 'win' : 'loss'}`); row.href = `/matches/${encodeURIComponent(match.id)}`;
    const image = el('img'); image.src = match.icon; image.alt = match.name; image.loading = 'lazy';
    const champion = el('div'); champion.append(el('strong',match.name),el('small',match.queue === 420 ? 'Ranked Solo / Duo' : 'Ranked Flex'));
    const kda = el('div',`${match.kills} / ${match.deaths} / ${match.assists}`,'score'); kda.append(el('small',`${new Intl.NumberFormat().format(match.cs)} CS`));
    const time = el('div',`${Math.floor(match.duration / 60)}m ${match.duration % 60}s`,'match-time'); time.append(el('small',new Date(match.playedAt).toLocaleDateString([], {month:'short',day:'numeric'})));
    row.append(el('span',match.win ? 'VICTORY' : 'DEFEAT','result'),image,champion,kda,...matchBuildAndScore(match),time); $('matches').append(row);
  }
  if (!matches.length) $('matches').append(el('p','No saved matches match these filters.','muted'));
  $('more').hidden = visible >= matches.length;
}
async function load() {
  $('queue').disabled = true; $('refresh').disabled = true; $('status').textContent = 'Loading saved matches…';
  const queue = $('queue').value;
  try {
    const response = await fetch(`/api/dashboard?queue=${encodeURIComponent(queue)}`), body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load saved matches.');
    if (queue !== selectedQueue) visible = 25;
    data = body; selectedQueue = queue; render(); $('status').textContent = '';
  } catch(error) { $('status').textContent = error.message; $('queue').value = selectedQueue; }
  finally { $('queue').disabled = false; $('refresh').disabled = false; }
}
for (const id of ['search','result','sort']) $(id).addEventListener(id === 'search' ? 'input' : 'change', () => { visible = 25; render(); });
$('queue').addEventListener('change',load); $('refresh').addEventListener('click',load);
$('more').addEventListener('click',() => { visible += 25; render(); });
load();
