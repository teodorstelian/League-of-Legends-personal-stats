const $=id=>document.getElementById(id);
let data,last={role:'TOP',queue:'all',enemy:'0',period:'all',minimum:'5'};
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function link(c){const a=el('a',undefined,'directory-champion');a.href=`/champions/${c.championId}`;if(c.icon){const img=el('img');img.src=c.icon;img.alt='';img.loading='lazy';a.append(img);}a.append(c.name);return a;}
function pick(c,matchup=false){
  const card=el('article',undefined,'ban-card'),stats=matchup?c.matchup:c.comfort;
  card.append(link(c));const score=el('div',undefined,'ban-priority');score.append(scoreGauge(stats.average,'gauge-medium'),el('span',`${matchup?'Vs selected enemy':'Role average'} Rift Score`,'muted'));card.append(score);
  card.append(el('p',`${stats.total} games · ${stats.winRate}% win rate · ${stats.wins} wins`,'muted'),el('p',matchup?`Qualified matchup evidence; comfort average ${c.comfort.average} across ${c.comfort.total} role games.`:`Qualified on ${c.comfort.total} games in this role. Small samples are adjusted toward neutral for ranking.`,'muted'));
  card.append(el('p',c.form===null?'Recent form: not enough games in both 30-day periods':`Recent form: ${c.form>0?'+':''}${c.form} score points (${c.formCurrent} vs ${c.formPrevious} games)`,'muted'));
  const count=stats.scored;card.append(el('small',count<10?'Limited sample (<10 games)':'More history; not a prediction',count<10?'small-sample':'muted'));return card;
}
function render(){
  $('summary').textContent=`${data.roleName} · ${data.totalGames} role games · ${data.eligibleChampions} qualifying champions · ${data.period==='30d'?'Last 30 days':'All saved history'}`;
  $('comfort-picks').replaceChildren(...data.comfort.map(c=>pick(c)));
  if(!data.comfort.length)$('comfort-picks').append(el('p',`No picks have ${data.minimum} scored games for these filters. Try a longer period or another role.`,'muted'));
  $('matchup-picks').replaceChildren();
  $('matchup-heading').textContent=data.enemy?`Picks against ${data.enemy.name}`:'Matchup picks';
  if(!data.enemy)$('matchup-note').textContent='Select an enemy champion to check same-role matchup history. Start with your comfort picks below.';
  else if(data.fallback){$('matchup-note').textContent=`No qualified picks have ${data.minimum} same-role games against ${data.enemy.name}. Falling back to comfort picks; no counter claim is made.`;for(const c of data.comfort.slice(0,3))$('matchup-picks').append(pick(c));}
  else{$('matchup-note').textContent='Qualified same-role evidence blended with your role comfort. These are personal results, not verified counters.';for(const c of data.matchup)$('matchup-picks').append(pick(c,true));}
  $('bans').replaceChildren();
  for(const b of data.bans){const card=el('article',undefined,'ban-card');card.append(link(b));const gauge=scoreGauge(b.priority,'gauge-medium','Ban priority');gauge.style.setProperty('--score-color',scoreColor(100-b.priority));const score=el('div',undefined,'ban-priority');score.append(gauge,el('span','Ban priority / 100','muted'));card.append(score,el('p',`${b.losses} losses in ${b.games} games · ${b.winRate}% win rate`,'muted'),el('p',`Your average Rift Score: ${b.scoreStats.average}`,'muted'),el('small',b.limited?'Limited evidence (<10 games)':'More history; still observational',b.limited?'small-sample':'muted'));$('bans').append(card);}
  if(!data.bans.length)$('bans').append(el('p','No supported ban suggestions for this qualifying champion pool.','muted'));
}
async function load(){const selection={};for(const id of Object.keys(last)){selection[id]=$(id).value;$(id).disabled=true;}$('refresh').disabled=true;$('status').textContent='Building your shortlist…';
  try{const response=await fetch(`/api/draft?${new URLSearchParams(selection)}`),body=await response.json();if(!response.ok)throw new Error(body.message||'Unable to build draft suggestions.');
    if(!data)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=el('option',c.name);option.value=c.championId;$('enemy').append(option);}data=body;last=selection;render();$('status').textContent='';
  }catch(error){$('status').textContent=error.message;for(const id of Object.keys(last))$(id).value=last[id];}
  finally{for(const id of [...Object.keys(last),'refresh'])$(id).disabled=false;}}
for(const id of Object.keys(last))$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);load();
