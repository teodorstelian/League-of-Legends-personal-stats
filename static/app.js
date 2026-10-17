const $ = id => document.getElementById(id);
const number = n => new Intl.NumberFormat().format(n);
let data, expanded = false;
const queueNames = {all: 'All ranked', solo: 'Ranked Solo / Duo', flex: 'Ranked Flex'};
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
  const collection = expanded || query ? data.champions.map(c => ({...c, ...(data.mastery.find(m => m.championId === c.championId) || {points: 0, level: 0})})).sort((a, b) => b.points - a.points || a.name.localeCompare(b.name)) : data.mastery;
  const champions = collection.filter(c => c.name.toLocaleLowerCase().includes(query));
  $('champions').replaceChildren();
  for (const [index, champion] of champions.slice(0, expanded || query ? undefined : 8).entries()) {
    const card = element('a', undefined, 'champion');
    card.href = `/champions/${champion.championId}`;
    if (champion.icon) card.append(icon(champion.icon, champion.name));
    card.append(element('span', String(index + 1).padStart(2, '0'), 'rank'), element('h3', champion.name), element('p', `Mastery level ${champion.level}`), element('strong', number(champion.points)), element('small', 'MASTERY POINTS'));
    const average = element('div', undefined, 'champion-score');
    average.append(element('span', 'Average Rift Score'), scoreGauge(champion.scoreStats.average));
    card.append(average, element('p', riftScoreSample(champion.scoreStats)));
    $('champions').append(card);
  }
  if (!champions.length) $('champions').append(element('p', 'No champions found.', 'muted'));
  $('show-all').hidden = !!query || data.mastery.length <= 8;
  $('show-all').textContent = expanded ? 'Show top champions' : `Browse all ${data.champions.length} champions`;
}
function render() {
  renderScoreSummary(data.scoreStats, data.lanes);
  renderOverview();
  $('queue').value = data.queue;
  const context = `${data.matches.length} saved games · ${queueNames[data.queue]}`;
  $('queue-context').textContent = context;
  $('match-context').textContent = `Latest ${Math.min(5,data.matches.length)} · ${queueNames[data.queue]}`;
  $('ranked').replaceChildren();
  if (data.ranked === null) {
    $('ranked').append(element('p', `Ranked standings unavailable: ${data.rankWarning}`, 'muted'));
  } else for (const rank of data.ranked) {
    const card = element('article', undefined, 'rank-card');
    card.append(element('p', `RANKED ${rank.queue.toUpperCase()}`, 'eyebrow'));
    if (rank.tier) {
      const tier = rank.tier.charAt(0) + rank.tier.slice(1).toLowerCase();
      const apex = ['MASTER', 'GRANDMASTER', 'CHALLENGER'].includes(rank.tier);
      card.append(element('h3', `${tier}${apex ? '' : ` ${rank.division}`}`), element('strong', `${number(rank.lp)} LP`));
      const total = rank.wins + rank.losses;
      card.append(element('p', `${number(rank.wins)}W · ${number(rank.losses)}L · ${total ? Math.round(rank.wins / total * 100) : 0}% win rate`, 'muted'));
    } else card.append(element('h3', 'Unranked'), element('p', 'No current ranked entry for this queue.', 'muted'));
    $('ranked').append(card);
  }
  $('riot-id').textContent = data.riotId;
  $('profile-detail').textContent = `Europe Nordic & East · Level ${number(data.level)}`;
  $('profile-icon').src = data.icon; $('profile-icon').hidden = false;
  const matches = data.matches, wins = matches.filter(m => m.win).length;
  $('win-rate').textContent = matches.length ? `${Math.round(wins / matches.length * 100)}%` : '—';
  $('record').textContent = `${wins} wins · ${matches.length - wins} losses in ${matches.length} loaded games`;
  $('kda').textContent = matches.length ? ['kills', 'deaths', 'assists'].map(k => (matches.reduce((n, m) => n + m[k], 0) / matches.length).toFixed(1)).join(' / ') : '—';
  $('total-mastery').textContent = number(data.mastery.reduce((n, c) => n + c.points, 0));
  $('champion-count').textContent = `${data.mastery.length} champions played`;
  $('updated').textContent = `Profile updated ${new Date(data.updatedAt * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})} · Use Check new games to update history`;
  renderChampions(); $('matches').replaceChildren();
  const queues = {420: 'Ranked Solo / Duo', 440: 'Ranked Flex', 450: 'ARAM', 400: 'Normal Draft', 490: 'Quickplay', 1700: 'Arena'};
  for (const match of matches.slice(0, 5)) {
    const row = element('a', undefined, `match ${match.win ? 'win' : 'loss'}`);
    row.href = `/matches/${encodeURIComponent(match.id)}`;
    const champion = element('div'); champion.append(element('strong', match.name), element('small', queues[match.queue] || match.mode));
    const score = element('div', `${match.kills} / ${match.deaths} / ${match.assists}`, 'score'); score.append(element('small', `${number(match.cs)} CS`));
    const duration = element('div', `${Math.floor(match.duration / 60)}m ${match.duration % 60}s`, 'match-time');
    duration.append(element('small', new Date(match.playedAt).toLocaleDateString([], {month: 'short', day: 'numeric'})));
    row.append(element('span', match.win ? 'VICTORY' : 'DEFEAT', 'result'), match.icon ? icon(match.icon, match.name) : element('span'), champion, score, ...matchBuildAndScore(match), duration);
    $('matches').append(row);
  }
  if (!matches.length) $('matches').append(element('p', 'No recent matches available.', 'muted'));
}
async function load() {
  const selectedQueue = $('queue').value;
  $('queue').disabled = true;
  $('refresh').disabled = true; $('refresh').textContent = 'Loading…';
  $('status').hidden = false; $('status').className = ''; $('status').textContent = 'Fetching your latest stats from Riot…';
  try {
    const response = await fetch(`/api/dashboard?queue=${encodeURIComponent(selectedQueue)}`); const body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load stats. Please try again.');
    data = body; render(); $('content').hidden = false;
    $('status').hidden = !data.warning;
    if (data.warning) { $('status').textContent = `Some recent matches could not be loaded: ${data.warning}`; $('status').className = 'error'; }
  } catch (error) {
    if (data) $('queue').value = data.queue;
    $('status').className = 'error'; $('status').textContent = error.message;
    if (data) $('status').append(element('p', 'Showing the previously loaded stats below.'));
  } finally { $('queue').disabled = false; $('refresh').disabled = false; $('refresh').textContent = '↻ Refresh stats'; }
}
$('queue').addEventListener('change', load);
$('refresh').addEventListener('click', load);
$('search').addEventListener('input', renderChampions);
$('show-all').addEventListener('click', () => { expanded = !expanded; renderChampions(); });
load();
function renderOverview(){
 const o=data.overview;
 $('overview-momentum').replaceChildren();
 const r=o.recent,p=o.previous;
 function card(label,value,note,cls=''){const n=element('article',undefined,'overview-stat');n.append(element('p',label,'eyebrow'),element('strong',value,cls),element('small',note,'muted'));$('overview-momentum').append(n);}
 card('CURRENT STREAK',o.currentStreak.games?`${o.currentStreak.games}${o.currentStreak.win?'W':'L'}`:'—',`Longest: ${o.longestWinStreak} wins · ${o.longestLossStreak} losses`,o.currentStreak.win===true?'positive':o.currentStreak.win===false?'negative':'');
 card(`LAST ${r.games} GAMES`,r.winRate===null?'—':`${r.winRate}%`,`${r.wins}W / ${r.games-r.wins}L${p.games?` · Previous ${p.games}: ${p.winRate}%`:''}`);
 const score=element('article',undefined,'overview-stat');score.append(element('p','RECENT RIFT SCORE','eyebrow'),scoreGauge(r.score,'gauge-medium'),element('small',`${r.scoreGames} games${p.score!==null?` · Previous ${p.games}: ${p.score}`:''}`,'muted'));$('overview-momentum').append(score);
 card('TIME ON THE RIFT',`${o.hours}h`,`${o.champions} champions · ${o.deathless} deathless games`);
 $('overview-results').replaceChildren();
 for(const m of o.results){const a=element('a',m.win?'W':'L',`overview-result ${m.win?'result-win':'result-loss'}`);a.href=`/matches/${encodeURIComponent(m.id)}`;a.title=`${m.champion||'Match'} · ${m.win?'Victory':'Defeat'} · ${new Date(m.playedAt).toLocaleDateString()}`;a.setAttribute('aria-label',a.title);$('overview-results').append(a);}
 if(!o.results.length)$('overview-results').append(element('span','Import ranked games to build your form.','muted'));
 $('overview-records').replaceChildren();
 for(const record of o.records){const m=record.match,card=element(m?'a':'article',undefined,'overview-record');if(m)card.href=`/matches/${encodeURIComponent(m.id)}`;card.append(element('p',record.label.toUpperCase(),'eyebrow'));
 if(record.key==='score')card.append(scoreGauge(record.value,'gauge-medium'));else{const value=element('div',undefined,'record-value');value.append(element('strong',record.value===null?'—':number(record.value)),element('span',record.unit,'muted'));card.append(value);}
 if(m){const player=element('div',undefined,'record-player');if(m.icon)player.append(icon(m.icon,''));const text=element('div');text.append(element('strong',m.name||m.champion||'Champion'),element('small',`${m.kills??0} / ${m.deaths??0} / ${m.assists??0} · ${m.win?'Victory':'Defeat'}`,'muted'));player.append(text);card.append(player,element('small',`${new Date(m.playedAt).toLocaleDateString()} · ${record.sample} eligible games →`,'muted'));}else card.append(element('p','No recorded data yet.','muted'));
 $('overview-records').append(card);}
}
