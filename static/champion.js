const $ = id => document.getElementById(id);
const number = n => new Intl.NumberFormat().format(n);
const championId = location.pathname.split('/').filter(Boolean).pop();
const queueNames = {all: 'all ranked', solo: 'Ranked Solo / Duo', flex: 'Ranked Flex'};
let data;
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function render() {
  renderScoreSummary(data.scoreStats, data.lanes);
  document.title = `${data.name} · Rift Journal`;
  $('name').textContent = data.name;
  $('subtitle').textContent = `${data.title} · ${data.riotId}`;
  $('portrait').src = data.icon; $('portrait').alt = data.name; $('portrait').hidden = !data.icon;
  $('points').textContent = number(data.mastery.points);
  $('level').textContent = data.mastery.level;
  $('player').textContent = data.riotId;
  $('roles').textContent = data.tags.join(' / ') || '—';
  $('title').textContent = data.title;
  $('queue').value = data.queue;
  const matches = data.matches, wins = matches.filter(m => m.win).length;
  $('sample').textContent = `${matches.length} ${data.name} game${matches.length === 1 ? '' : 's'} found in your ${data.sampleSize} saved games in ${queueNames[data.queue]}. Stats cover imported history; more games appear as background sync progresses.`;
  $('win-rate').textContent = matches.length ? `${Math.round(wins / matches.length * 100)}%` : '—';
  const losses = matches.length - wins;
  $('record').textContent = `${wins} win${wins === 1 ? '' : 's'} · ${losses} loss${losses === 1 ? '' : 'es'}`;
  $('kda').textContent = matches.length ? ['kills', 'deaths', 'assists'].map(k => (matches.reduce((n, m) => n + m[k], 0) / matches.length).toFixed(1)).join(' / ') : '—';
  const seconds = matches.reduce((n, m) => n + m.duration, 0);
  $('cs').textContent = seconds ? (matches.reduce((n, m) => n + m.cs, 0) / (seconds / 60)).toFixed(1) : '—';
  $('updated').textContent = `Profile updated ${new Date(data.updatedAt * 1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})} · History updates automatically`;
  $('matches').replaceChildren();
  const queues = {420: 'Ranked Solo / Duo', 440: 'Ranked Flex', 450: 'ARAM', 400: 'Normal Draft', 490: 'Quickplay', 1700: 'Arena'};
  for (const match of matches) {
    const row = el('a', undefined, `match ${match.win ? 'win' : 'loss'}`);
    row.href = `/matches/${encodeURIComponent(match.id)}`;
    const image = el('img'); image.src = match.icon; image.alt = data.name;
    const champion = el('div'); champion.append(el('strong', data.name), el('small', queues[match.queue] || match.mode));
    const score = el('div', `${match.kills} / ${match.deaths} / ${match.assists}`, 'score'); score.append(el('small', `${number(match.cs)} CS`));
    const duration = el('div', `${Math.floor(match.duration / 60)}m ${match.duration % 60}s`, 'match-time');
    duration.append(el('small', new Date(match.playedAt).toLocaleDateString([], {month:'short',day:'numeric'})));
    row.append(el('span', match.win ? 'VICTORY' : 'DEFEAT', 'result'), image, champion, score, ...matchBuildAndScore(match), duration);
    $('matches').append(row);
  }
  if (!matches.length) $('matches').append(el('p', `No ${data.name} games in this sample. Try another queue.`, 'muted'));
}
async function load() {
  $('queue').disabled = true; $('refresh').disabled = true;
  $('status').hidden = false; $('status').className = ''; $('status').textContent = 'Loading champion stats…';
  try {
    const response = await fetch(`/api/champions/${encodeURIComponent(championId)}?queue=${encodeURIComponent($('queue').value)}`);
    const body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load this champion.');
    data = body; render(); $('content').hidden = false;
    loadMatchups();
    $('status').hidden = !data.warning;
    if (data.warning) { $('status').className = 'error'; $('status').textContent = `The recent match sample is incomplete: ${data.warning}`; }
  } catch (error) {
    $('status').className = 'error'; $('status').textContent = error.message;
    if (data) { $('queue').value = data.queue; $('status').append(el('p', 'Showing previously loaded stats below.')); }
  } finally { $('queue').disabled = false; $('refresh').disabled = false; }
}
$('queue').addEventListener('change', load);
$('refresh').addEventListener('click', load);
load();
