const $=id=>document.getElementById(id);
let data,last={role:'TOP',queue:'all',enemy:'0',period:'all'};
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function link(c){const a=el('a',undefined,'directory-champion');a.href=`/champions/${c.championId}`;if(c.icon){const img=el('img');img.src=c.icon;img.alt='';img.loading='lazy';a.append(img);}a.append(c.name);return a;}
function pick(c,matchup=false){
  const card=el('article',undefined,'ban-card'),stats=matchup?c.matchup:c.comfort;
  card.append(el('p',!c.supported?'LIMITED DATA':matchup?'MATCHUP + COMFORT':'COMFORT','eyebrow'),link(c));const score=el('div',undefined,'ban-priority');score.append(scoreGauge(stats.average,'gauge-medium'),el('span',`${matchup?'Vs selected enemy':'Role average'} Rift Score`,'muted'));card.append(score);
  card.append(el('p',`${stats.total} games · ${stats.winRate}% WR`,'muted'));
  if(c.form!==null)card.append(el('small',`Form ${c.form>0?'+':''}${c.form} points`,'muted'));
  if(!c.supported)card.append(el('small',`Limited data · ${c.comfort.scored} games`,'small-sample'));
  else if(stats.scored<10)card.append(el('small','Limited sample','small-sample'));
  if(matchup)card.title=`Comfort: ${c.comfort.average} Rift Score across ${c.comfort.total} role games. Ranking blends matchup and comfort evidence.`;
  return card;
}
function render(){
  $('summary').textContent=`${data.roleName} · ${data.totalGames} role games · ${data.eligibleChampions} qualifying champions · ${data.period==='30d'?'Last 30 days':'All saved history'}`;
  $('suggested-picks').replaceChildren(...data.picks.map(c=>pick(c,c.matchupEligible)));
  $('picks-note').textContent=data.enemy?`Against ${data.enemy.name} · Comfort fills gaps in matchup history.`:'Comfort ranked first · Limited-data picks fill remaining places.';
  if(!data.picks.length)$('suggested-picks').append(el('p',`No recorded picks in this role. Try a longer period or import more history.`,'muted'));
  renderBans();
  $('general-ban-coverage').textContent=`${data.generalCovered} of ${data.generalGames} games with enemy-team data.`;
}
async function load(){const selection={};for(const id of Object.keys(last)){selection[id]=$(id).value;$(id).disabled=true;}$('refresh').disabled=true;$('status').textContent='Building your shortlist…';
  try{const response=await fetch(`/api/draft?${new URLSearchParams(selection)}`),body=await response.json();if(!response.ok)throw new Error(body.message||'Unable to build draft suggestions.');
    if(!data)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=el('option',c.name);option.value=c.championId;$('enemy').append(option);}data=body;last=selection;render();$('status').textContent='';
  }catch(error){$('status').textContent=error.message;for(const id of Object.keys(last))$(id).value=last[id];}
  finally{for(const id of [...Object.keys(last),'refresh'])$(id).disabled=false;}}
for(const id of Object.keys(last))$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);
$('role').disabled=true;
window.draftRoleReady=fetch('/api/draft/defaults').then(async response=>{if(!response.ok)throw Error();const defaults=await response.json();$('role').value=defaults.role;last.role=defaults.role;}).catch(()=>{});
window.draftRoleReady.then(load);

function renderBans(){
 const root=$('bans');root.replaceChildren();
 for(const b of data.bans){const card=el('article',undefined,'ban-card');card.append(el('p',`${b.scope==='lane'?'LANE · '+data.roleName:'GENERAL · ALL ROLES'}${b.supported?'':' · LIMITED DATA'}`,'eyebrow'),link(b));const gauge=scoreGauge(b.priority,'gauge-medium','Ban priority');gauge.style.setProperty('--score-color',scoreColor(100-b.priority));const score=el('div',undefined,'ban-priority');score.append(gauge,el('span','Ban priority / 100','muted'));card.append(score,el('p',`${b.games} games · ${b.winRate}% WR`,'muted'),el('small',`Your Rift Score ${b.scoreStats.average}`,'muted'));
 if(!b.supported)card.append(el('small',`Limited data · ${b.scoreStats.scored} games`,'small-sample'));else if(b.limited)card.append(el('small','Limited sample','small-sample'));root.append(card);}
 if(!data.bans.length)root.append(el('p','No above-neutral ban candidates in this history. Try a longer period or import more matches.','muted'));
}
