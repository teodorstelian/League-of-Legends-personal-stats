const $ = id => document.getElementById(id);
let data, displayedQueue = 'all', displayedRole = 'all';
const columns = [
  ['name','Champion', 'Champion name'], ['score','Avg Rift Score','Average Rift Score'],
  ['samples','Games','Games played'], ['winRate','Win rate','Win rate'],
  ['record','W / L','Wins, then fewer losses'], ['kda','Avg K / D / A','KDA ratio: (kills + assists) / max(1, deaths)'],
  ['mastery','Mastery points','Mastery points']
];
const sortSelect = $('sort'); sortSelect.replaceChildren();
for (const [key,label] of [...columns,['games','Games played']]) for(const direction of ['desc','asc']) {
  const option=document.createElement('option');option.value=`${key}-${direction}`;option.textContent=`${label}: ${direction==='asc'?'ascending':'descending'}`;sortSelect.append(option);
}
sortSelect.value='score-desc';
document.querySelectorAll('.champion-directory thead th').forEach((th,index)=>{
  const [key,label,description]=columns[index];
  const button=document.createElement('button');button.className='table-sort';button.type='button';button.dataset.column=key;button.title=`Sort by ${description}`;button.textContent=label;
  button.addEventListener('click',()=>{
    const [active,direction]=sortSelect.value.split('-');sortSelect.value=`${key}-${active===key?(direction==='asc'?'desc':'asc'):key==='name'?'asc':'desc'}`;render();
  });th.replaceChildren(button);
});
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function render() {
  if (!data) return;
  const selectedRole = $('role').value;
  const matches = data.matches.filter(m => selectedRole === 'all' || m.role === selectedRole);
  const groups = new Map();
  for (const m of matches) { if (!groups.has(m.championId)) groups.set(m.championId, []); groups.get(m.championId).push(m); }
  const mastery = new Map(data.mastery.map(m => [m.championId, m.points]));
  const query = $('search').value.trim().toLocaleLowerCase();
  const rows = data.champions.map(c => {
    const games = groups.get(c.championId) || [], wins = games.filter(m => m.win).length;
    const scores = games.map(m => m.score).filter(s => typeof s === 'number' && Number.isFinite(s) && s >= 0 && s <= 100);
    const scoreStats = {total: games.length, scored: scores.length, average: scores.length ? Math.round(scores.reduce((a,b) => a+b,0) / scores.length * 10) / 10 : null};
    return {...c, scoreStats, games, wins, winRate: games.length ? wins / games.length * 100 : null, points: mastery.get(c.championId) || 0};
  }).filter(c => c.name.toLocaleLowerCase().includes(query) && (!$('played').checked || c.games.length) && c.scoreStats.scored >= Number($('minimum').value));
  const [sort,direction] = $('sort').value.split('-');
  const multiplier=direction==='asc'?1:-1;
  const value=c=>{
    if(sort==='name')return c.name;
    if(sort==='score')return c.scoreStats.average;
    if(sort==='samples')return c.games.length;
    if(sort==='games')return c.games.length;
    if(sort==='winRate')return c.winRate;
    if(sort==='record')return c.games.length?c.wins:null;
    if(sort==='mastery')return c.points;
    if(sort==='kda')return c.games.length?c.games.reduce((n,m)=>n+m.kills+m.assists,0)/Math.max(1,c.games.reduce((n,m)=>n+m.deaths,0)):null;
  };
  rows.sort((a,b) => {
    const av=value(a),bv=value(b);
    if(av===null||bv===null)return av===bv?a.name.localeCompare(b.name):av===null?1:-1;
    const difference=typeof av==='string'?av.localeCompare(bv):av-bv;
    const tie=sort==='samples'?a.games.length-b.games.length:sort==='record'?(b.games.length-b.wins)-(a.games.length-a.wins):0;
    return multiplier*(difference||tie)||a.name.localeCompare(b.name);
  });
  document.querySelectorAll('.table-sort').forEach(button=>{
    const active=button.dataset.column===sort;
    button.parentElement.setAttribute('aria-sort',active?(direction==='asc'?'ascending':'descending'):'none');
    const label=columns.find(c=>c[0]===button.dataset.column)[1];button.textContent=`${label} ${active?(direction==='asc'?'↑':'↓'):'↕'}`;
  });
  $('count').textContent = `${rows.length} of ${data.champions.length} champions · ${matches.length} games · ${displayedQueue === 'all' ? 'All ranked' : displayedQueue === 'solo' ? 'Solo / Duo' : 'Flex'} · ${$('role').selectedOptions[0].textContent}`;
  $('champion-rows').replaceChildren();
  for (const c of rows) {
    const row = node('tr'), name = node('td'), link = node('a', undefined, 'directory-champion'); link.href = `/champions/${c.championId}`;
    if (c.icon) { const image = node('img'); image.src = c.icon; image.alt = ''; image.loading = 'lazy'; link.append(image); }
    link.append(node('span', c.name)); name.append(link); row.append(name);
    const score = node('td'); score.append(scoreGauge(c.scoreStats.average)); row.append(score);
    const sample = node('td', `${c.games.length}`);
    if (c.scoreStats.scored > 0 && c.scoreStats.scored < 5) sample.append(node('small','Small sample','small-sample')); row.append(sample);
    row.append(node('td', c.winRate === null ? '—' : `${c.winRate.toFixed(0)}%`), node('td', `${c.wins} / ${c.games.length - c.wins}`));
    row.append(node('td', c.games.length ? ['kills','deaths','assists'].map(k => (c.games.reduce((n,m) => n + m[k],0) / c.games.length).toFixed(1)).join(' / ') : '—'), node('td',new Intl.NumberFormat().format(c.points)));
    $('champion-rows').append(row);
  }
  if (!rows.length) { const row = node('tr'), cell = node('td','No champions match these filters.'); cell.colSpan = 7; row.append(cell); $('champion-rows').append(row); }
}
async function load() {
  $('refresh').disabled = true; $('queue').disabled = true; $('role').disabled = true; $('status').textContent = 'Loading champion stats…';
  const selected = $('queue').value;
  try {
    const selectedRole = $('role').value;
    const response = await fetch(`/api/champion-pool?${new URLSearchParams({queue:selected,role:selectedRole})}`, {cache:'no-store'}), body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load champions.');
    data = body; displayedQueue = selected; displayedRole = body.role; render(); $('status').textContent = '';
  } catch(error) { $('status').textContent = error.message; $('queue').value = displayedQueue; $('role').value = displayedRole; }
  finally { $('refresh').disabled = false; $('queue').disabled = false; $('role').disabled = false; }
}
for (const id of ['search','sort','minimum','played']) $(id).addEventListener(id === 'search' ? 'input' : 'change', render);
$('role').addEventListener('change', load);
$('queue').addEventListener('change', load); $('refresh').addEventListener('click', load);
load();
setInterval(() => { if (document.visibilityState === 'visible' && !$('refresh').disabled) load(); }, 30000);
