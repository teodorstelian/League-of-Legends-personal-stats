let matchupRequest=0;
async function loadMatchups(){
  const request=++matchupRequest;
  const status=document.getElementById('matchup-status');status.textContent='Loading saved matchups…';
  const params=new URLSearchParams({queue:document.getElementById('queue').value,role:document.getElementById('matchup-role').value,period:document.getElementById('matchup-period').value});
  try{
    const response=await fetch(`/api/champions/${encodeURIComponent(championId)}/matchups?${params}`),body=await response.json();
    if(request!==matchupRequest)return;
    if(!response.ok)throw new Error(body.message||'Unable to load matchups.');
    const sort=document.getElementById('matchup-sort').value;
    body.rows.sort((a,b)=>sort==='score'?(b.scoreStats.average??-1)-(a.scoreStats.average??-1)||b.games-a.games:sort==='winRate'?b.winRate-a.winRate||b.games-a.games:b.games-a.games||a.name.localeCompare(b.name));
    status.textContent=`${body.matchedGames} matched games of ${body.totalGames} · ${body.period==='30d'?'Last 30 days':'All saved history'}${body.missingDetails?` · ${body.missingDetails} awaiting details`:''}${body.ambiguousGames?` · ${body.ambiguousGames} without a unique same-role opponent`:''}`;
    const root=document.getElementById('matchup-rows');root.replaceChildren();
    for(const m of body.rows){
      const row=document.createElement('tr'),name=document.createElement('td'),link=document.createElement('a');link.href=`/champions/${m.championId}`;link.className='directory-champion';
      if(m.icon){const image=document.createElement('img');image.src=m.icon;image.alt='';image.loading='lazy';link.append(image);}link.append(m.name);name.append(link);row.append(name);
      for(const value of [m.roleName,m.games,`${m.winRate}%`,`${m.wins} / ${m.losses}`]){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}
      const score=document.createElement('td');score.append(scoreGauge(m.scoreStats.average));row.append(score);
      const kda=document.createElement('td');kda.textContent=m.kda.map(v=>v.toFixed(1)).join(' / ');row.append(kda);
      const sample=document.createElement('td');sample.textContent=m.games<5?'Small sample':'—';if(m.games<5)sample.className='small-sample';row.append(sample);root.append(row);
    }
    if(!body.rows.length){const row=document.createElement('tr'),cell=document.createElement('td');cell.colSpan=8;cell.textContent='No clear same-role matchups for these filters.';row.append(cell);root.append(row);}
  }catch(error){if(request===matchupRequest){status.textContent=error.message;document.getElementById('matchup-rows').replaceChildren();}}
}
for(const id of ['matchup-role','matchup-period','matchup-sort'])document.getElementById(id).addEventListener('change',loadMatchups);
