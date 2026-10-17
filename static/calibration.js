const $=id=>document.getElementById(id);
let lastQueue='all',lastMinimum='5';
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
const format=value=>value===null?'—':String(value);
function table(id,rows){
  const table=el('table'),head=el('thead'),heading=el('tr');
  for(const label of ['Group','Games','Mean','Median','P10 / P90','Spread','Vs overall','Review'])heading.append(el('th',label));head.append(heading);table.append(head);
  const body=el('tbody');
  for(const r of rows){
    const row=el('tr'),name=el('td');
    if(r.championId){const link=el('a',r.name,'back-link');link.href=`/champions/${r.championId}`;name.append(link);}else name.textContent=r.name;
    row.append(name,el('td',`${r.total}`));
    const mean=el('td');mean.append(scoreGauge(r.mean));row.append(mean);
    for(const value of [format(r.median),`${format(r.p10)} / ${format(r.p90)}`,format(r.stddev),r.difference===null?'—':`${r.difference>0?'+':''}${r.difference}`])row.append(el('td',value));
    const flag=el('td',r.count<5?'Small sample':r.review?'Review group difference':'No large mean difference');if(r.review)flag.style.color='#efb56c';row.append(flag);body.append(row);
  }
  if(!rows.length){const row=el('tr'),cell=el('td','No groups meet this sample requirement.');cell.colSpan=8;row.append(cell);body.append(row);}
  table.append(body);$(id).replaceChildren(table);
}
function render(data){
  const stats=data.overall;$('overall').replaceChildren();
  for(const [label,value,note] of [['Scored games',stats.count,`${stats.total} saved games`],['Average score',stats.mean,`Median ${format(stats.median)}`],['Near floor / ceiling',`${stats.floor} / ${stats.ceiling}`,'Scores ≤5 / ≥95']]){
    const card=el('article');card.append(el('p',label));if(label==='Average score')card.append(scoreGauge(value,'gauge-medium'));else card.append(el('strong',format(value)));card.append(el('small',note));$('overall').append(card);
  }
  const maximum=Math.max(1,...stats.histogram);$('histogram').replaceChildren();
  stats.histogram.forEach((count,index)=>{const cell=el('div',undefined,'calibration-bin'),track=el('div',undefined,'calibration-track'),bar=el('div');bar.style.height=`${count/maximum*100}%`;bar.style.background=scoreColor(index*10+5);track.append(bar);cell.append(el('strong',count),track,el('small',`${index*10}–${index===9?100:index*10+9.9}`));$('histogram').append(cell);});
  table('roles',data.roles);table('archetypes',data.archetypes);table('champions',data.champions);
}
async function load(){
  const queue=$('queue').value,minimum=$('minimum').value;for(const id of ['queue','minimum','refresh'])$(id).disabled=true;$('status').textContent='Loading calibration…';
  try{const response=await fetch(`/api/calibration?queue=${queue}&minimum=${minimum}`),data=await response.json();if(!response.ok)throw new Error(data.message||'Unable to load calibration.');render(data);lastQueue=queue;lastMinimum=minimum;$('content').hidden=false;$('status').textContent='';}
  catch(error){$('status').textContent=error.message;$('queue').value=lastQueue;$('minimum').value=lastMinimum;}
  finally{for(const id of ['queue','minimum','refresh'])$(id).disabled=false;}
}
for(const id of ['queue','minimum'])$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);
setInterval(()=>{if(document.visibilityState==='visible'&&!$('refresh').disabled)load();},30000);load();
