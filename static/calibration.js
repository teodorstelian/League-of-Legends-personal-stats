const $=id=>document.getElementById(id);
let lastQueue='all',lastMinimum='5';
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
const format=value=>value===null||value===undefined?'—':String(value);
const signed=value=>value===null||value===undefined?'—':`${value>0?'+':''}${value}`;
function table(id,rows){
  const championTable=id==='champions';
  const table=el('table'),head=el('thead'),heading=el('tr');
  for(const label of ['Group','Games','Mean','Median','P10 / P90','Spread','Vs overall',...(championTable?['Role baseline','Vs role baseline','Compared games']:[]),'Review'])heading.append(el('th',label));head.append(heading);table.append(head);
  const body=el('tbody');
  for(const r of rows){
    const row=el('tr'),name=el('td');
    if(r.championId){const link=el('a',r.name,'back-link');link.href=`/champions/${r.championId}`;name.append(link);}else name.textContent=r.name;
    row.append(name,el('td',`${r.total}`));
    const mean=el('td');mean.append(scoreGauge(r.mean));row.append(mean);
    for(const value of [format(r.median),`${format(r.p10)} / ${format(r.p90)}`,format(r.stddev),r.difference===null?'—':`${r.difference>0?'+':''}${r.difference}`])row.append(el('td',value));
    if(championTable)row.append(el('td',format(r.roleReference)),el('td',signed(r.roleDifference)),el('td',r.roleComparedGames));
    const flag=el('td',r.count<10?'Limited sample (<10)':r.review?'Difference ≥10; inspect':'Below 10-point review threshold');if(r.review)flag.style.color='#efb56c';row.append(flag);body.append(row);
  }
  if(!rows.length){const row=el('tr'),cell=el('td','No groups meet this sample requirement.');cell.colSpan=championTable?11:8;row.append(cell);body.append(row);}
  table.append(body);$(id).replaceChildren(table);
}
function render(data){
  const stats=data.overall;$('overall').replaceChildren();
  for(const [label,value,note] of [['Scored games',stats.count,`${stats.total} saved games`],['Average score',stats.mean,`Median ${format(stats.median)}`],['Near floor / ceiling',`${stats.floor} / ${stats.ceiling}`,'Scores ≤5 / ≥95']]){
    const card=el('article');card.append(el('p',label));if(label==='Average score')card.append(scoreGauge(value,'gauge-medium'));else card.append(el('strong',format(value)));card.append(el('small',note));$('overall').append(card);
  }
  const maximum=Math.max(1,...stats.histogram);$('histogram').replaceChildren();
  stats.histogram.forEach((count,index)=>{const cell=el('div',undefined,'calibration-bin'),track=el('div',undefined,'calibration-track'),bar=el('div');bar.style.height=`${count/maximum*100}%`;bar.style.background=scoreColor(index*10+5);track.append(bar);cell.append(el('strong',count),track,el('small',`${index*10}–${index===9?100:index*10+9.9}`));$('histogram').append(cell);});
  table('durations',data.durations);
  $('component-coverage').textContent=`${data.componentGames} of ${stats.count} scored games have usable saved details. Component counts exclude missing metrics. Zero/100 rates use component scores rounded to one decimal. Contributions use each game's rescaled weights.`;
  const scope=$('component-scope').value;
  simpleTable('components',['Group','Component','Games','Mean / 100','Mean score points','At 0','At least 100'],data.components.filter(r=>r.scope===scope).map(r=>[r.group,r.name,r.count,r.mean,r.contribution,`${r.zeroPercent}%`,`${r.hundredPercent}%`]));
  for(const kind of ['highest','lowest']){
    const rows=data.extremes[kind].map(m=>{
      const link=el('a',m.champion||`Champion ${m.championId}`,'back-link');link.href=`/matches/${encodeURIComponent(m.id)}`;
      return [link,m.role||'Unknown',m.score,m.win===true?'Win':m.win===false?'Loss':'—',m.duration?`${Math.floor(m.duration/60)}:${String(m.duration%60).padStart(2,'0')}`:'—',m.playedAt?new Date(m.playedAt).toLocaleDateString():'—'];
    });
    simpleTable(kind,['Champion / match','Role','Score','Result','Duration','Played'],rows);
  }
  const investigation=data.investigation;
  const matchLink=m=>{const link=el('a',`${m.champion||`Champion ${m.championId}`} · ${m.id}`,'back-link');link.href=`/matches/${encodeURIComponent(m.id)}`;return link;};
  simpleTable('duration-results',['Duration / result','Scored games','Mean active score'],investigation.durationResults.map(r=>[r.name,r.count,r.current]));
  simpleTable('duration-components',['Duration / result','Component','Games','Mean / 100','Raw rate','Unit'],investigation.durationComponents.map(r=>[r.group,r.name,r.count,r.mean,r.rawMean,r.unit]));
  simpleTable('target-review',['Scope','Group','Component','Games','Raw rate','Unit','Reference range','Mean / 100','At least 100'],data.components.filter(r=>r.scope!=='Overall'&&['Crowd control','Objective pressure','Tower pressure'].includes(r.name)).map(r=>[r.scope,r.group,r.name,r.count,r.rawMean,r.unit,r.targetMin===r.targetMax?r.targetMin:`${r.targetMin}–${r.targetMax}`,r.mean,`${r.hundredPercent}%`]));
  simpleTable('candidate-summary',['Group','Paired games','Current active score','Comparison','Change'],investigation.comparisons.map(r=>[r.name,r.count,r.current,r.candidate,signed(r.delta)]));
  simpleTable('candidate-cc',['Archetype','CC games','At least 100: current','At least 100: comparison'],investigation.cc.map(r=>[r.name,r.count,r.currentCap===null?'—':`${r.currentCap}%`,r.candidateCap===null?'—':`${r.candidateCap}%`]));
  simpleTable('candidate-examples',['Champion / match','Role','Current active score','Comparison','Change'],investigation.examples.map(r=>[matchLink(r),r.role,r.current,r.candidate,signed(r.delta)]));
  simpleTable('short-games',['Champion / match','Duration (seconds)','Result','Saved score','Early surrender','Surrender','Recalculation'],data.shortGames.map(r=>[matchLink(r),r.duration,r.win===true?'Win':r.win===false?'Loss':'—',r.score,r.earlySurrender,r.surrender,r.scoreReason||'Scored under current rules']));
  table('roles',data.roles);table('archetypes',data.archetypes);table('champions',data.champions);
}
function simpleTable(id,labels,rows){
  const t=el('table'),head=el('thead'),heading=el('tr'),body=el('tbody');
  for(const label of labels)heading.append(el('th',label));head.append(heading);t.append(head);
  for(const values of rows){const row=el('tr');for(const value of values){const cell=el('td');if(value instanceof Node)cell.append(value);else cell.textContent=format(value);row.append(cell);}body.append(row);}
  if(!rows.length){const row=el('tr'),cell=el('td','No saved data available.');cell.colSpan=labels.length;row.append(cell);body.append(row);}
  t.append(body);$(id).replaceChildren(t);
}
let report;
$('component-scope').addEventListener('change',()=>{if(report)render(report);});
async function load(){
  const queue=$('queue').value,minimum=$('minimum').value;for(const id of ['queue','minimum','refresh'])$(id).disabled=true;$('status').textContent='Loading calibration…';
  try{const response=await fetch(`/api/calibration?queue=${queue}&minimum=${minimum}`),data=await response.json();if(!response.ok)throw new Error(data.message||'Unable to load calibration.');report=data;render(data);lastQueue=queue;lastMinimum=minimum;$('content').hidden=false;$('status').textContent='';}
  catch(error){$('status').textContent=error.message;$('queue').value=lastQueue;$('minimum').value=lastMinimum;}
  finally{for(const id of ['queue','minimum','refresh'])$(id).disabled=false;}
}
for(const id of ['queue','minimum'])$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);
setInterval(()=>{if(document.visibilityState==='visible'&&!$('refresh').disabled)load();},30000);load();

for(const [id,open] of [['expand-diagnostics',true],['collapse-diagnostics',false]])$(id).addEventListener('click',()=>{for(const section of document.querySelectorAll('.calibration-details'))section.open=open;});
