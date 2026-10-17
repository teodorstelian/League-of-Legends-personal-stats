const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let report,limit=20,request=0;
function champion(p){const a=el('a',undefined,'directory-champion');a.href=`/champions/${p.championId}`;if(p.icon){const img=el('img');img.src=p.icon;img.alt='';img.loading='lazy';a.append(img);}a.append(el('span',`${p.name} · ${p.role}`));return a;}
function renderMatches(){
 $('matches').replaceChildren();
 for(const m of report.matches.slice(0,limit)){
  const row=el('article',undefined,`duo-match ${m.win?'duo-win':'duo-loss'}`),result=el('div');result.append(el('strong',m.win?'VICTORY':'DEFEAT'),el('small',`${m.queue===420?'Solo / Duo':'Flex'} · ${Math.floor(m.duration/60)}m`, 'muted'));row.append(result);
  for(const p of m.players){const player=el('div',undefined,'duo-player'),stats=el('div');stats.append(champion(p),el('small',`${p.kills} / ${p.deaths} / ${p.assists}`,'muted'));player.append(stats,scoreGauge(p.score));row.append(player);}
  const details=el('div',undefined,'duo-match-date');details.append(el('small',new Date(m.playedAt).toLocaleDateString(),'muted'));
  const link=el('a','Match details →','back-link');link.href=`/matches/${encodeURIComponent(m.id)}`;
  if(m.owner!==0)link.addEventListener('click',async e=>{e.preventDefault();try{const r=await fetch('/api/profiles/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({riotId:report.profiles[m.owner]})});if(!r.ok)throw Error('Unable to open partner’s match.');location.assign(link.href);}catch(error){$('status').textContent=error.message;}});
  if(m.owner!==0)link.title='Switch to partner profile to inspect this saved match';details.append(link);row.append(details);$('matches').append(row);
 }
 if(!report.matches.length)$('matches').append(el('p','No matches together found for these filters. Import more history on both profiles, then refresh.','muted'));
 $('more').hidden=limit>=report.matches.length;$('match-count').textContent=`${report.matches.length} games`;
}
function render(){
 const s=report.summary;$('duo-names').textContent=report.profiles.join(' + ');
 $('coverage').textContent=report.profiles.map((p,i)=>`${p}: ${report.coverage[i].details}/${report.coverage[i].saved} games with details`).join(' · ')+' · Shared matches are found across both saved histories; coverage grows as imports finish.';
 $('summary').replaceChildren();const overview=el('article',undefined,'early-card');overview.append(el('p','ON THE SAME TEAM','eyebrow'),el('strong',s.games),el('p',`${s.winRate??'—'}${s.winRate===null?'':'%'} win rate`),el('small',`${s.wins} wins · ${s.losses} losses${s.games<5?' · Limited sample':''}`,'muted'));$('summary').append(overview);
 for(const [i,name]of report.profiles.entries()){const card=el('article',undefined,'early-card'),p=s.players[i];card.append(el('p',name,'eyebrow'),scoreGauge(p.score,'gauge-medium'),el('p','Average Rift Score together','muted'),el('small',`K / D / A: ${p.kda.map(v=>v??'—').join(' / ')} · ${p.scoreGames} scores`,'muted'));$('summary').append(card);}
 const table=el('table'),head=el('thead'),hr=el('tr');for(const title of [report.profiles[0],report.profiles[1],'Games','Win rate','W / L','Scores together'])hr.append(el('th',title));head.append(hr);table.append(head);const body=el('tbody');
 for(const c of report.combinations){const row=el('tr');for(const p of c.champions){const td=el('td');td.append(champion(p));row.append(td);}row.append(el('td',`${c.games}${c.games<5?' · Limited':''}`),el('td',`${c.winRate}%`),el('td',`${c.wins} / ${c.losses}`));const scores=el('td'),wrap=el('div',undefined,'duo-pair-scores');for(const p of c.players)wrap.append(scoreGauge(p.score));scores.append(wrap);row.append(scores);body.append(row);}
 if(!report.combinations.length){const row=el('tr'),td=el('td','No champion combinations found yet.');td.colSpan=6;row.append(td);body.append(row);}table.append(body);$('combinations').replaceChildren(table);renderMatches();
}
async function load(){const gen=++request;$('status').textContent='Finding your games together…';try{const q=new URLSearchParams(Object.fromEntries(['partner','queue','period'].map(id=>[id,$(id).value]))),r=await fetch(`/api/duo?${q}`),data=await r.json();if(gen!==request)return;if(!r.ok)throw Error(data.message||'Unable to load duo stats.');report=data;limit=20;render();$('status').textContent=data.ready?'':'Both profiles need at least one imported match with full details before we can identify shared games.';}catch(e){if(gen===request)$('status').textContent=e.message;}}
async function init(){try{const response=await fetch('/api/profiles');if(!response.ok)throw Error('Unable to load profiles.');const data=await response.json();for(const p of data.profiles.filter(p=>p.riotId!==data.active)){const o=el('option',p.riotId);o.value=p.riotId;$('partner').append(o);}if(!$('partner').options.length){$('status').textContent='Add a second profile using the header to see duo stats.';return;}load();}catch(e){$('status').textContent=e.message;}}
for(const id of ['partner','queue','period'])$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);$('more').addEventListener('click',()=>{limit+=20;renderMatches();});init();
