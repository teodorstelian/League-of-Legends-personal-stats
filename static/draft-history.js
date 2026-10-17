(() => {
  const get = id => document.getElementById(id);
  const make = (tag, text) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; return n; };
  let history, generation=0;
  function message(text) {
    const row=make('tr'), cell=make('td',text); cell.colSpan=8; row.append(cell); get('evidence-pairs').replaceChildren(row);
  }
  function champion(id,name,icon) {
    const a=make('a'); a.className='directory-champion'; a.href=`/champions/${id}`;
    if(icon){const img=make('img');img.src=icon;img.alt='';img.loading='lazy';a.append(img);} a.append(document.createTextNode(name)); return a;
  }
  function render() {
    if(!history)return;
    const enemy=Number(get('enemy').value), sort=get('evidence-sort').value;
    const rows=history.rows.filter(r=>!enemy||r.championId===enemy);
    rows.sort((a,b)=>sort==='difficult'?a.winRate-b.winRate||b.games-a.games:sort==='score'?(b.scoreStats.average??-1)-(a.scoreStats.average??-1)||b.games-a.games:b.games-a.games||a.ownName.localeCompare(b.ownName));
    const selected=enemy?get('enemy').selectedOptions[0]?.textContent:'All enemies';
    get('evidence-summary').textContent=`${selected} · ${rows.reduce((n,r)=>n+r.games,0)} games in ${rows.length} pairs · ${history.period==='30d'?'Last 30 days':'All saved history'}`;
    get('evidence-pairs').replaceChildren();
    for(const r of rows){const row=make('tr'),own=make('td'),enemyCell=make('td');own.append(champion(r.ownId,r.ownName,r.ownIcon));enemyCell.append(champion(r.championId,r.name,r.icon));row.append(own,enemyCell);
      for(const text of [r.roleName,`${r.games}${r.games<5?' · Small sample':''}`,`${r.winRate}%`,`${r.wins} / ${r.losses}`])row.append(make('td',text));
      const score=make('td');score.append(scoreGauge(r.scoreStats.average));row.append(score,make('td',r.kda.map(n=>n.toFixed(1)).join(' / ')));get('evidence-pairs').append(row);
    }
    if(!rows.length)message(`No recorded pairs${enemy?` against ${selected}`:''} match the selected role, queue and period. Try a longer period or import more history.`);
  }
  async function load() {
    const request=++generation;get('evidence-status').textContent='Loading matchup history…';message('Loading matchup history…');
    const params=new URLSearchParams({queue:get('queue').value,role:get('role').value,period:get('period').value,minimum:'1',champion:get('evidence-champion').value});
    try{const response=await fetch(`/api/matchups?${params}`),body=await response.json();if(request!==generation)return;if(!response.ok)throw Error(body.message||'Unable to load matchup history.');
      if(get('evidence-champion').options.length===1)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=make('option',c.name);option.value=c.championId;get('evidence-champion').append(option);}
      history=body;render();get('evidence-status').textContent='';
    }catch(error){if(request!==generation)return;history=null;get('evidence-summary').textContent='';get('evidence-status').textContent=error.message;message('History could not load. Use Refresh to try again.');}
  }
  for(const id of ['queue','role','period','evidence-champion'])get(id).addEventListener('change',load);
  get('enemy').addEventListener('change',render);
  get('evidence-sort').addEventListener('change',render);
  get('refresh').addEventListener('click',load);
  window.draftRoleReady.then(load);
})();
