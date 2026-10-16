const $ = id => document.getElementById(id);
const number = n => new Intl.NumberFormat().format(n);
let data, expanded = false;
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function icon(src, name) {
  const image = element('img'); image.alt = name; image.src = src; image.loading = 'lazy';
  image.addEventListener('error', () => image.hidden = true);
  return image;
}
function renderChampions() {
  const query = $('search').value.trim().toLocaleLowerCase();
  const champions = data.mastery.filter(c => c.name.toLocaleLowerCase().includes(query));
  $('champions').replaceChildren();
  for (const [index, champion] of champions.slice(0, expanded || query ? undefined : 8).entries()) {
    const card = element('article', undefined, 'champion');
    if (champion.icon) card.append(icon(champion.icon, champion.name));
    card.append(element('span', String(index + 1).padStart(2, '0'), 'rank'), element('h3', champion.name), element('p', `Mastery level ${champion.level}`), element('strong', number(champion.points)), element('small', 'MASTERY POINTS'));
    $('champions').append(card);
  }
  if (!champions.length) $('champions').append(element('p', 'No champions found.', 'muted'));
  $('show-all').hidden = !!query || data.mastery.length <= 8;
  $('show-all').textContent = expanded ? 'Show top champions' : `Show all ${data.mastery.length} champions`;
}
function render() {
  $('riot-id').textContent = data.riotId;
  $('profile-detail').textContent = `Europe Nordic & East · Level ${number(data.level)}`;
  $('profile-icon').src = data.icon; $('profile-icon').hidden = false;
  const matches = data.matches, wins = matches.filter(m => m.win).length;
  $('win-rate').textContent = matches.length ? `${Math.round(wins / matches.length * 100)}%` : '—';
  $('record').textContent = `${wins} wins · ${matches.length - wins} losses in ${matches.length} loaded games`;
  $('kda').textContent = matches.length ? ['kills', 'deaths', 'assists'].map(k => (matches.reduce((n, m) => n + m[k], 0) / matches.length).toFixed(1)).join(' / ') : '—';
  $('total-mastery').textContent = number(data.mastery.reduce((n, c) => n + c.points, 0));
  $('champion-count').textContent = `${data.mastery.length} champions played`;
  $('updated').textContent = `Updated ${new Date(data.updatedAt * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})} · Cached for 2 minutes`;
  renderChampions(); $('matches').replaceChildren();
  const queues = {420: 'Ranked Solo / Duo', 440: 'Ranked Flex', 450: 'ARAM', 400: 'Normal Draft', 490: 'Quickplay', 1700: 'Arena'};
  for (const match of matches) {
    const row = element('article', undefined, `match ${match.win ? 'win' : 'loss'}`);
    const champion = element('div'); champion.append(element('strong', match.name), element('small', queues[match.queue] || match.mode));
    const score = element('div', `${match.kills} / ${match.deaths} / ${match.assists}`, 'score'); score.append(element('small', `${number(match.cs)} CS`));
    const duration = element('div', `${Math.floor(match.duration / 60)}m ${match.duration % 60}s`, 'match-time');
    duration.append(element('small', new Date(match.playedAt).toLocaleDateString([], {month: 'short', day: 'numeric'})));
    row.append(element('span', match.win ? 'VICTORY' : 'DEFEAT', 'result'), match.icon ? icon(match.icon, match.name) : element('span'), champion, score, duration);
    $('matches').append(row);
  }
  if (!matches.length) $('matches').append(element('p', 'No recent matches available.', 'muted'));
}
async function load() {
  $('refresh').disabled = true; $('refresh').textContent = 'Loading…';
  $('status').hidden = false; $('status').className = ''; $('status').textContent = 'Fetching your latest stats from Riot…';
  try {
    const response = await fetch('/api/dashboard'); const body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load stats. Please try again.');
    data = body; render(); $('content').hidden = false;
    $('status').hidden = !data.warning;
    if (data.warning) { $('status').textContent = `Some recent matches could not be loaded: ${data.warning}`; $('status').className = 'error'; }
  } catch (error) {
    $('status').className = 'error'; $('status').textContent = error.message;
    if (data) $('status').append(element('p', 'Showing the previously loaded stats below.'));
  } finally { $('refresh').disabled = false; $('refresh').textContent = '↻ Refresh stats'; }
}
$('refresh').addEventListener('click', load);
$('search').addEventListener('input', renderChampions);
$('show-all').addEventListener('click', () => { expanded = !expanded; renderChampions(); });
load();
