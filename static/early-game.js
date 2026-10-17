const $ = id => document.getElementById(id);
const make = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
const signed = n => n==null ? '—' : `${n>0?'+':''}${n.toLocaleString()}`;
const pct = n => n==null?'—':`${n}%`;
const roleName = role => ({TOP:'Top',JUNGLE:'Jungle',MIDDLE:'Mid',BOTTOM:'Bot',UTILITY:'Support'}[role] || 'Unassigned');
let report, generation=0, importWasActive=false;
function table(target, groups, champion=false) {
  const minute=Number($('checkpoint').value), t=make('table'), h=make('thead'), hr=make('tr');
  for(const title of [champion?'Champion / role':'Role', 'Samples', 'Gold Δ', 'XP Δ', 'CS Δ', 'Lead rate', 'Lead → win', 'Deaths <10 / game']) hr.append(make('th',title)); h.append(hr);t.append(h);
  const body=make('tbody');
  for(const g of groups) {
    const c=g.checkpoints.find(c=>c.minute===minute), row=make('tr'), name=make('td');
    if(champion){ const entry=report.catalog.find(c=>c.championId===g.championId), a=make('a',entry?.name||String(g.championId),'directory-champion');a.href=`/champions/${g.championId}`; if(entry?.icon){const img=make('img');img.src=entry.icon;img.alt='';a.prepend(img);} name.append(a,make('small',roleName(g.role))); } else name.textContent=roleName(g.role);
    row.append(name);
    for(const [i,value] of [`${c.count} games${c.count<5?' · Limited':''}`,signed(c.gold),signed(c.xp),signed(c.cs),`${pct(c.leadRate)} · ${c.leads}/${c.count}`,`${pct(c.conversion)} · ${c.leadWins}/${c.leads}`,`${g.deathsPerGame??'—'} · ${g.deathGames} games`].entries())row.append(make('td',value,i>=1&&i<=3?(c[['gold','xp','cs'][i-1]]>0?'positive':c[['gold','xp','cs'][i-1]]<0?'negative':''):''));body.append(row);
  }
  if(!groups.length){const row=make('tr'),cell=make('td','No cached timelines match these filters yet. Import timelines above to build this report.');cell.colSpan=8;row.append(cell);body.append(row);}
  t.append(body);$(target).replaceChildren(t);
}
function render(){
  $('report-status').textContent=`${report.cached} of ${report.total} filtered games have timelines · ${report.unavailable} unavailable from Riot. Checkpoint samples may be smaller.`;
  $('early-summary').replaceChildren();
  for(const c of report.summary.checkpoints){const card=make('article',undefined,'early-card');card.append(make('p',`AT ${c.minute} MINUTES`,'eyebrow'),make('strong',signed(c.gold),c.gold>0?'positive':c.gold<0?'negative':''),make('p','average gold difference','muted'),make('p',`${signed(c.xp)} XP · ${signed(c.cs)} CS`),make('p',`${pct(c.leadRate)} ahead · ${pct(c.conversion)} win from a lead`,'muted'),make('small',`${c.count} checkpoint samples · ${c.leads} leads${c.count<5?' · Limited sample':''}`,'muted'));$('early-summary').append(card);}
  const s=report.summary, deaths=make('article',undefined,'early-card');deaths.append(make('p','BEFORE 10 MINUTES','eyebrow'),make('strong',String(s.deathsPerGame??'—')),make('p','deaths per game','muted'),make('p',`${s.earlyDeaths} deaths across ${s.deathGames} complete windows`,'muted'));$('early-summary').append(deaths);
  table('role-table',report.roles);table('champion-table',report.champions,true);
}
async function load(){const gen=++generation;try{const q=new URLSearchParams(Object.fromEntries(['queue','role','champion','period'].map(id=>[id,$(id).value])));const res=await fetch(`/api/early-game?${q}`);if(!res.ok)throw Error('Unable to load early-game report.');const data=await res.json();if(gen!==generation)return;report=data;if($('champion').options.length===1)for(const c of [...report.catalog].sort((a,b)=>a.name.localeCompare(b.name))){const o=make('option',c.name);o.value=c.championId;$('champion').append(o);}render();}catch(e){$('report-status').textContent=e.message;}}
async function importStatus(){try{const res=await fetch('/api/timeline-import');if(!res.ok)throw Error('Unable to load timeline import status.');const s=await res.json();$('import-status').textContent=`${s.cached} / ${s.total} cached · ${s.unavailable} unavailable · ${s.remaining} pending. ${s.active?'Import running. ':''}${s.message}`;$('import-progress').max=Math.max(1,s.total);$('import-progress').value=s.cached+s.unavailable;$('import-start').disabled=s.active;$('import-pause').disabled=!s.active;if(s.active||importWasActive)await load();importWasActive=s.active;}catch(e){$('import-status').textContent=e.message;}}
for(const action of ['start','pause'])$(`import-${action}`).addEventListener('click',async()=>{try{const res=await fetch(`/api/timeline-import/${action}`,{method:'POST'});if(!res.ok)throw Error('Unable to change import status.');await importStatus();}catch(e){$('import-status').textContent=e.message;}});
for(const id of ['queue','role','champion','period'])$(id).addEventListener('change',load);
$('checkpoint').addEventListener('change',()=>{if(report)render();});$('refresh').addEventListener('click',()=>{load();importStatus();});
load();importStatus();setInterval(importStatus,4000);
