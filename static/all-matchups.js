(() => {
const $=id=>document.getElementById(['queue','role','period','minimum','refresh','enemy'].includes(id)?id:'evidence-'+id);
let request=0;
let data,last={queue:'all',role:'TOP',period:'all',champion:'0',minimum:'5'};
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function championLink(id,name,icon){const link=el('a',undefined,'directory-champion');link.href=`/champions/${id}`;if(icon){const image=el('img');image.src=icon;image.alt='';image.loading='lazy';link.append(image);}link.append(name);return link;}
function pairs(){if(!data)return;const query=$('search').value.trim().toLocaleLowerCase(),sort=$('sort').value;
  const enemy=Number($('enemy').value);const rows=data.rows.filter(r=>(!enemy||r.championId===enemy)&&r.name.toLocaleLowerCase().includes(query));
  rows.sort((a,b)=>sort==='difficult'?a.winRate-b.winRate||b.games-a.games:sort==='score'?(b.scoreStats.average??-1)-(a.scoreStats.average??-1)||b.games-a.games:b.games-a.games||a.ownName.localeCompare(b.ownName));
  $('pairs').replaceChildren();
  for(const r of rows){const row=el('tr'),own=el('td'),opponent=el('td');own.append(championLink(r.ownId,r.ownName,r.ownIcon));opponent.append(championLink(r.championId,r.name,r.icon));row.append(own,opponent);
    for(const text of [r.roleName,`${r.games}${r.games<5?' · Small sample':''}`,`${r.winRate}%`,`${r.wins} / ${r.losses}`])row.append(el('td',text));
    const score=el('td');score.append(scoreGauge(r.scoreStats.average));row.append(score,el('td',r.kda.map(v=>v.toFixed(1)).join(' / ')));$('pairs').append(row);}
  if(!rows.length){const row=el('tr'),cell=el('td','No matchup pairs meet these filters. Try a lower minimum or more history.');cell.colSpan=8;row.append(cell);$('pairs').append(row);}
}
function render(){
  $('summary').textContent=`${data.matchedGames} matched games of ${data.totalGames} · ${data.rows.length} qualifying champion pairs · ${data.period==='30d'?'Last 30 days':'All saved history'}`;
  pairs();
}
async function load(){const generation=++request;const filters={};for(const id of Object.keys(last)){filters[id]=$(id).value;}$('status').textContent='Loading saved matchups…';
  try{const response=await fetch(`/api/matchups?${new URLSearchParams(filters)}`),body=await response.json();if(generation!==request)return;if(!response.ok)throw new Error(body.message||'Unable to load matchups.');
    if(!data)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=el('option',c.name);option.value=c.championId;$('champion').append(option);}data=body;last=filters;render();$('status').textContent='';
  }catch(error){if(generation===request)$('status').textContent=error.message;}
}
for(const id of Object.keys(last))$(id).addEventListener('change',load);$('search').addEventListener('input',pairs);$('sort').addEventListener('change',pairs);$('refresh').addEventListener('click',load);$('enemy').addEventListener('change',pairs);
load();

})();
