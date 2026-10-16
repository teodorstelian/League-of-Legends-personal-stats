const $=id=>document.getElementById(id);
let data,last={queue:'all',role:'all',period:'all',champion:'0',minimum:'3'};
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function championLink(id,name,icon){const link=el('a',undefined,'directory-champion');link.href=`/champions/${id}`;if(icon){const image=el('img');image.src=icon;image.alt='';image.loading='lazy';link.append(image);}link.append(name);return link;}
function pairs(){if(!data)return;const query=$('search').value.trim().toLocaleLowerCase(),sort=$('sort').value;
  const rows=data.rows.filter(r=>r.name.toLocaleLowerCase().includes(query));
  rows.sort((a,b)=>sort==='difficult'?a.winRate-b.winRate||b.games-a.games:sort==='score'?(b.scoreStats.average??-1)-(a.scoreStats.average??-1)||b.games-a.games:b.games-a.games||a.ownName.localeCompare(b.ownName));
  $('pairs').replaceChildren();
  for(const r of rows){const row=el('tr'),own=el('td'),opponent=el('td');own.append(championLink(r.ownId,r.ownName,r.ownIcon));opponent.append(championLink(r.championId,r.name,r.icon));row.append(own,opponent);
    for(const text of [r.roleName,`${r.games}${r.games<5?' · Small sample':''}`,`${r.winRate}%`,`${r.wins} / ${r.losses}`])row.append(el('td',text));
    const score=el('td');score.append(scoreGauge(r.scoreStats.average));row.append(score,el('td',r.kda.map(v=>v.toFixed(1)).join(' / ')));$('pairs').append(row);}
  if(!rows.length){const row=el('tr'),cell=el('td','No matchup pairs meet these filters. Try a lower minimum or more history.');cell.colSpan=8;row.append(cell);$('pairs').append(row);}
}
function render(){
  $('summary').textContent=`${data.matchedGames} matched games of ${data.totalGames} · ${data.rows.length} qualifying champion pairs · ${data.period==='30d'?'Last 30 days':'All saved history'}`;
  $('bans').replaceChildren();
  for(const [index,b] of data.bans.slice(0,5).entries()){
    const card=el('article',undefined,'ban-card');card.append(el('p',`BAN CANDIDATE ${index+1}`,'eyebrow'),championLink(b.championId,b.name,b.icon));
    const gauge=scoreGauge(b.priority,'gauge-medium','Ban priority');gauge.style.setProperty('--score-color',scoreColor(100-b.priority));
    const priority=el('div',undefined,'ban-priority');priority.append(gauge,el('span','Ban priority / 100','muted'));card.append(priority,
      el('p',`${b.losses} losses / ${b.games} games · ${b.winRate}% win rate`,'muted'),el('p',`Your average Rift Score: ${b.scoreStats.average}`,'muted'),
      el('p',`${b.roles.join(', ')} · ${b.yourChampions} of your champions`,'muted'),el('small',b.limited?'Limited evidence (<10 games)':'Larger sample; still observational',b.limited?'small-sample':'muted'));$('bans').append(card);}
  if(!data.bans.length)$('bans').append(el('p',`No supported ban suggestions for these filters. Opponents need at least ${data.banMinimum} games and an above-neutral priority.`,'muted'));
  pairs();
}
async function load(){const filters={};for(const id of Object.keys(last)){filters[id]=$(id).value;$(id).disabled=true;}$('refresh').disabled=true;$('status').textContent='Loading saved matchups…';
  try{const response=await fetch(`/api/matchups?${new URLSearchParams(filters)}`),body=await response.json();if(!response.ok)throw new Error(body.message||'Unable to load matchups.');
    if(!data)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=el('option',c.name);option.value=c.championId;$('champion').append(option);}data=body;last=filters;render();$('status').textContent='';
  }catch(error){$('status').textContent=error.message;for(const id of Object.keys(last))$(id).value=last[id];}
  finally{for(const id of [...Object.keys(last),'refresh'])$(id).disabled=false;}}
for(const id of Object.keys(last))$(id).addEventListener('change',load);$('search').addEventListener('input',pairs);$('sort').addEventListener('change',pairs);$('refresh').addEventListener('click',load);
setInterval(()=>{if(document.visibilityState==='visible'&&!$('refresh').disabled)load();},30000);load();
