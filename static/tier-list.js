const $ = id => document.getElementById(id);
let data, lastQueue = 'all', lastMinimum = '3', lastPeriod = 'all';
function el(tag,text,className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function championCard(c) {
  const card = el('a',undefined,'tier-champion'); card.href = `/champions/${c.championId}`;
  if(c.icon) { const image = el('img'); image.src=c.icon; image.alt=''; image.loading='lazy'; card.append(image); }
  const text=el('div'); text.append(el('strong',c.name),el('small',riftScoreSample(c.scoreStats)));
  if(c.scoreStats.scored > 0 && c.scoreStats.scored < 5) text.title='Small sample: fewer than five scored games';
  card.append(text,scoreGauge(c.scoreStats.average)); return card;
}
function render() {
  if(!data) return;
  $('tier-lists').replaceChildren();
  let ranked=0, provisional=0;
  for(const role of data.roles.filter(r => $('role').value === 'all' || r.role === $('role').value)) {
    const section=el('section',undefined,'role-tier-list');
    section.append(el('h2',role.name));
    for(const tier of role.tiers) {
      const row=el('div',undefined,'tier-row'); row.style.setProperty('--tier-color',scoreColor(tier.minimum));
      const label=el('div',tier.tier,'tier-label'); label.setAttribute('aria-label',`${tier.tier} tier`);
      const picks=el('div',undefined,'tier-picks');
      for(const c of tier.champions) picks.append(championCard(c));
      ranked+=tier.champions.length;
      if(!tier.champions.length) picks.append(el('span','No qualifying champions','muted'));
      row.append(label,picks); section.append(row);
    }
    if(role.provisional.length) {
      const details=el('details',undefined,'tier-provisional');
      details.append(el('summary',`Not yet ranked · ${role.provisional.length} picks need ${data.minimumGames} scored games in ${role.name}`));
      const picks=el('div',undefined,'tier-picks'); for(const c of role.provisional) picks.append(championCard(c)); details.append(picks); section.append(details);
    }
    provisional+=role.provisional.length;
    $('tier-lists').append(section);
  }
  $('summary').textContent=`${ranked} qualified champion/role picks · ${provisional} under-sampled · ${data.totalGames} saved games in ${data.queue === 'all' ? 'all ranked' : data.queue === 'solo' ? 'Solo / Duo' : 'Flex'} · ${data.period === '30d' ? 'Last 30 days' : 'All saved history'}${data.unknownRoleGames ? ` · ${data.unknownRoleGames} games without a known role excluded` : ''}`;
}
async function load() {
  $('refresh').disabled=true; $('queue').disabled=true; $('minimum').disabled=true; $('status').textContent='Building your tier list…';
  $('period').disabled=true;
  const queue=$('queue').value, minimum=$('minimum').value, period=$('period').value;
  try {
    const response=await fetch(`/api/tier-list?queue=${encodeURIComponent(queue)}&minimum=${minimum}&period=${period}`),body=await response.json();
    if(!response.ok) throw new Error(body.message || 'Unable to build the tier list.');
    data=body; lastQueue=queue; lastMinimum=minimum; lastPeriod=period; render(); $('status').textContent='';
  } catch(error) { $('status').textContent=error.message; $('queue').value=lastQueue; $('minimum').value=lastMinimum; $('period').value=lastPeriod; }
  finally { $('refresh').disabled=false; $('queue').disabled=false; $('minimum').disabled=false; $('period').disabled=false; }
}
$('role').addEventListener('change',render);
for(const id of ['queue','minimum','period']) $(id).addEventListener('change',load);
$('refresh').addEventListener('click',load);
setInterval(() => { if(document.visibilityState==='visible' && !$('refresh').disabled) load(); },30000);
load();
