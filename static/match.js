const $ = id => document.getElementById(id);
const number = n => n === null || n === undefined ? '—' : new Intl.NumberFormat().format(n);
let data;
const journey = new URLSearchParams(location.search);
const journeyQueue = ['all','solo','flex'].includes(journey.get('queue')) ? journey.get('queue') : 'all';
if(journey.get('from')==='champion' && /^\d+$/.test(journey.get('champion')||'')){
  for(const link of document.querySelectorAll('a.back-link[href="/matches"]')){link.href=`/champions/${journey.get('champion')}?${new URLSearchParams({queue:journeyQueue})}`;link.textContent='← Back to champion';}
}
function el(tag, text, className) {
  const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n;
}
function assets(id, list) {
  $(id).replaceChildren();
  for (const item of list) {
    const cell = el('div', undefined, 'asset');
    if (item?.icon) { const img = el('img'); img.src = item.icon; img.alt = item.name; img.loading = 'lazy'; img.addEventListener('error', () => img.hidden = true); cell.append(img); }
    cell.append(el('small', item?.name || 'Empty slot'));
    $(id).append(cell);
  }
}
function inspect(p) {
  $('player-name').textContent = `${p.riotId} · ${p.name}${p.you ? ' · You' : ''}`;
  $('champion-link').href = `/champions/${p.championId}?${new URLSearchParams({queue:journeyQueue,...(journey.get('from')==='matches'?{from:'matches'}:{})})}`;
  assets('items', p.items); assets('spells', p.spells); assets('runes', p.runes);
  const minutes = data.duration / 60;
  const stats = [
    ['Champion damage', p.totalDamageDealtToChampions], ['Physical / Magic / True damage', [p.physicalDamageDealtToChampions, p.magicDamageDealtToChampions, p.trueDamageDealtToChampions].map(number).join(' / ')],
    ['Damage per minute', minutes && p.totalDamageDealtToChampions != null ? Math.round(p.totalDamageDealtToChampions / minutes) : null], ['Damage taken', p.totalDamageTaken], ['Damage mitigated', p.damageSelfMitigated],
    ['Gold earned', p.goldEarned], ['CS / minute', minutes ? (p.cs / minutes).toFixed(1) : null], ['Kill participation', `${p.kp}%`],
    ['Vision score', p.visionScore], ['Wards placed / killed', `${number(p.wardsPlaced)} / ${number(p.wardsKilled)}`], ['Control wards placed', p.detectorWardsPlaced],
    ['Objective damage', p.damageDealtToObjectives], ['Turret damage', p.damageDealtToTurrets], ['Turret takedowns', p.turretTakedowns],
    ['Ally healing', p.totalHealsOnTeammates], ['Ally shielding', p.totalDamageShieldedOnTeammates], ['Crowd control seconds', p.timeCCingOthers], ['Time dead (seconds)', p.totalTimeSpentDead]
  ];
  $('stats').replaceChildren();
  for (const [name, value] of stats) { const card = el('article'); card.append(el('p', name, 'muted'), el('strong', typeof value === 'string' ? value : number(value))); $('stats').append(card); }
  document.querySelectorAll('.player-select').forEach(b => b.setAttribute('aria-pressed', b.dataset.player === p.riotId ? 'true' : 'false'));
}
function render() {
  const own = data.participants.find(p => p.you);
  if (!own) throw new Error('Your player data is missing from this match.');
  document.title = `${own.name} ${own.win ? 'Victory' : 'Defeat'} · Rift Journal`;
  $('heading').textContent = `${own.win ? 'Victory' : 'Defeat'} · ${own.name}`;
  const queues = {420:'Ranked Solo / Duo',440:'Ranked Flex',450:'ARAM',400:'Normal Draft'};
  $('subtitle').textContent = `${queues[data.queue] || data.mode} · ${Math.floor(data.duration / 60)}m ${data.duration % 60}s · ${new Date(data.playedAt).toLocaleString()} · Patch ${data.patch} · ${data.id}`;
  $('rift-score').replaceChildren(scoreGauge(own.score.value, 'gauge-hero'));
  $('comparison').textContent = `${own.score.comparison || own.score.reason}${own.score.coverage ? ` · ${own.score.coverage}` : ''}`;
  const equation=$('score-equation');
  equation.replaceChildren();
  if(typeof own.score.value==='number'&&typeof own.score.withoutExceptional==='number'){
    equation.append(el('p', `${own.score.withoutExceptional.toFixed(1)} base score + ${own.score.exceptionalBonus.toFixed(1)} exceptional bonus = ${own.score.value.toFixed(1)} final score`, 'score-equation-value'));

  }
  $('score-diagnostics-link').href = `/calibration?${new URLSearchParams({match:data.id})}`;
  let explanation=$('score-explanation');
  if(!explanation){explanation=el('div',undefined,'score-explanation');explanation.id='score-explanation';$('components').before(explanation);}
  explanation.replaceChildren();
  if(own.score.summary){
    const {strength,improvement}=own.score.summary;
    if(strength){const panel=el('article');panel.append(el('h3','Biggest strength'),el('p',`${strength.name} · ${strength.contribution.toFixed(1)} points earned`,'muted'));explanation.append(panel);}
    const panel=el('article');panel.append(el('h3','Improvement area'),el('p',improvement?`${improvement.name} · ${improvement.value.toFixed(1)} / 100`:'All benchmarks met','muted'));explanation.append(panel);
  }
  $('components').replaceChildren();
  for (const c of own.score.components) {
    const card = el('article', undefined, 'component');
    const unit=c.unit==='per minute'?(c.name==='Support impact'?'impact/min':'damage/min'):c.unit;
    card.append(el('h3',c.name),scoreGauge(c.value,'gauge-medium',c.name,c.maximum||100),el('p',`${number(c.own)} ${unit}`,'muted'),el('small',`${c.weight}% weight${c.bonus>0?` · +${c.bonusContribution.toFixed(1)} bonus`:''}`,'muted'));
    $('components').append(card);
  }
  if (!own.score.components.length) $('components').append(el('p', own.score.reason, 'muted'));
  $('teams').replaceChildren();
  for (const teamId of [...new Set(data.participants.map(p => p.teamId))]) {
    const players = data.participants.filter(p => p.teamId === teamId);
    const team = data.teams.find(t => t.teamId === teamId);
    const section = el('section', undefined, 'team-section');
    section.append(el('h3', `${teamId === 100 ? 'Blue' : teamId === 200 ? 'Red' : `Team ${teamId}`} · ${players[0].win ? 'Victory' : 'Defeat'} · ${players.reduce((n,p) => n + p.kills, 0)} kills · ${number(players.reduce((n,p) => n + p.goldEarned, 0))} gold`));
    const objectiveNames = {baron:'Barons', champion:'Kills', dragon:'Dragons', horde:'Void grubs', inhibitor:'Inhibitors', riftHerald:'Rift Heralds', tower:'Towers'};
    if (team?.objectives) section.append(el('p', Object.entries(team.objectives).filter(([key]) => key in objectiveNames).map(([key,value]) => `${objectiveNames[key]}: ${value.kills}`).join(' · '), 'muted'));
    const wrap = el('div', undefined, 'table-scroll'), table = el('table');
    const thead = el('thead'), headrow = el('tr');
    for (const text of ['Player / champion', 'Role', 'K / D / A', 'Damage', 'Gold', 'CS', 'Vision', 'KP', 'Rift Score']) headrow.append(el('th', text));
    thead.append(headrow); table.append(thead);
    const tbody = el('tbody');
    for (const p of players) {
      const row = el('tr', undefined, p.you ? 'you-row' : '');
      const name = el('td'), button = el('button', `${p.riotId}${p.you ? ' · You' : ''}`, 'player-select'); button.dataset.player = p.riotId; button.addEventListener('click', () => inspect(p));
      name.append(button, el('small', `${p.name} · Lv ${number(p.champLevel)}`)); row.append(name);
      for (const text of [p.role, `${p.kills} / ${p.deaths} / ${p.assists}`, number(p.totalDamageDealtToChampions), number(p.goldEarned), number(p.cs), number(p.visionScore), `${p.kp}%`]) row.append(el('td', text));
      const scoreCell = el('td'); scoreCell.append(scoreGauge(p.score.value)); row.append(scoreCell);
      tbody.append(row);
    }
    table.append(tbody); wrap.append(table); section.append(wrap); $('teams').append(section);
  }
  inspect(own);
}
async function load() {
  $('status').hidden = false; $('status').textContent = 'Loading advanced details…'; $('retry').hidden = true;
  try {
    const id = location.pathname.split('/').filter(Boolean).pop();
    const response = await fetch(`/api/matches/${encodeURIComponent(id)}`), body = await response.json();
    if (!response.ok) throw new Error(body.message || 'Unable to load match.');
    data = body; render(); loadTimeline(); $('content').hidden = false; $('status').hidden = !data.warning;
    if (data.warning) $('status').textContent = data.warning;
  } catch(error) { $('status').textContent = error.message; $('retry').hidden = false; }
}
$('retry').addEventListener('click', load);
load();
