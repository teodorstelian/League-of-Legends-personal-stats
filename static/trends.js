const $ = id => document.getElementById(id);
let data, last = {queue:'all',role:'all',champion:'0',comparison:'days',size:'30'};
const metrics = [['score','Rift Score','points'],['winRate','Win rate','pp'],['deaths','Deaths per game',''],['damage','Champion damage / min',''],['vision','Vision / min','']];
function el(tag,text,cls) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; }
function format(value) { return value === null ? '—' : new Intl.NumberFormat(undefined,{maximumFractionDigits:2}).format(value); }
function render() {
  const games=data.comparison==='games',size=data.size||30,currentLabel=`Last ${size} ${games?'games':'days'}`,previousLabel=`Previous ${size} ${games?'games':'days'}`;
  $('comparison-title').textContent=`${currentLabel} vs ${previousLabel.toLowerCase()}`;
  $('form-period').textContent=$('comparison-title').textContent;
  $('current-period-heading').textContent=currentLabel;$('previous-period-heading').textContent=previousLabel;
  $('comparison-help').textContent=games?`The newest ${size} matching imported games versus the preceding ${size}, after queue, role and champion filters. Unscored games occupy slots but are excluded from score averages. Champion form uses these same two windows. Fewer than ${size*2} games leaves a partial or empty window. Weekly bars stay calendar-based.`:`Rolling ${size}-day periods, using only imported ranked games.`;
  $('as-of').textContent=`As of ${new Date(data.asOf).toLocaleDateString()} · ${data.current.total} vs ${data.previous.total} games`;
  $('comparison-cards').replaceChildren();
  for(const [key,name,unit] of metrics) {
    const card=el('article',undefined,'trend-metric'), current=data.current[key], previous=data.previous[key],delta=data.deltas[key];
    card.append(el('p',name,'eyebrow'));
    if(key==='score')card.append(scoreGauge(current.value,'gauge-medium',`${currentLabel} average Rift Score`));
    else card.append(el('strong',`${format(current.value)}${key==='winRate' && current.value!==null ? '%' : ''}`));
    card.append(el('p',`Previous: ${format(previous.value)}${key==='winRate' && previous.value!==null ? '%' : ''}`,'muted'));
    const change=el('p',delta===null ? 'No comparable data' : `${delta>0?'+':''}${format(delta)} ${unit}`,'trend-change');
    if(delta!==null)change.style.color=delta===0?'var(--muted)':(key==='deaths' ? delta<0 : delta>0)?'#9cda9a':'#f08b87';
    card.append(change,el('small',`${current.count} current / ${previous.count} previous games${Math.min(current.count,previous.count)<5?' · Small sample':''}`)); $('comparison-cards').append(card);
  }
  $('weekly').replaceChildren();
  for(const week of data.weeks) {
    const button=el('button',undefined,'week-button'), score=week.score.value;
    const label=new Date(week.start).toLocaleDateString(undefined,{month:'short',day:'numeric',timeZone:'UTC'});
    button.setAttribute('aria-label',`Week of ${label}: ${score===null?'no score':score+' out of 100'}, ${week.score.count} scored games${week.partial?', partial week':''}`);
    button.title=button.getAttribute('aria-label');
    const area=el('span',undefined,'week-track'), bar=el('span',undefined,'week-bar'); bar.style.height=score===null?'0%':`${score}%`; bar.style.background=scoreColor(score); area.append(bar);
    button.append(el('span',format(score),'week-value'),area,el('span',label),el('small',`${week.score.count} scored${week.partial?' *':''}`));
    button.addEventListener('click',()=>{
      $('weekly').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed','false')); button.setAttribute('aria-pressed','true');
      $('week-detail').textContent=`Week of ${label} (UTC)${week.partial?' · Partial week':''}: ${week.total} saved games, ${week.score.count} scored. Average score ${format(score)}, win rate ${format(week.winRate.value)}${week.winRate.value===null?'':'%'}. ${week.score.count<5?'Small sample.':''}`;
    }); $('weekly').append(button);
  }
  $('week-detail').textContent='Select a week for its sample details. Empty weeks have no score.';
  $('forms').replaceChildren();
  for(const c of data.forms) {
    const row=el('tr'),name=el('td'),link=el('a',c.name,'directory-champion'); link.href=`/champions/${c.championId}`; name.append(link); row.append(name);
    for(const period of [c.current,c.previous]) { const cell=el('td'); cell.append(scoreGauge(period.average),el('small',riftScoreSample(period)));row.append(cell); }
    row.append(el('td',c.delta===null?'—':`${c.delta>0?'+':''}${format(c.delta)}`));
    const label=el('td',c.form==='insufficient'?'Not enough scored games':c.form[0].toUpperCase()+c.form.slice(1));
    if(c.form==='improving')label.style.color='#9cda9a';if(c.form==='declining')label.style.color='#f08b87';row.append(label);$('forms').append(row);
  }
  if(!data.forms.length) {const row=el('tr'),cell=el('td',games?'No imported games for these filters.':`No games for these filters in the last ${size*2} days.`);cell.colSpan=5;row.append(cell);$('forms').append(row);}
}
async function load() {
  const selection={queue:$('queue').value,role:$('role').value,champion:$('champion').value,comparison:$('comparison').value,size:$('size').value};
  for(const id of ['refresh','queue','role','champion','comparison','size'])$(id).disabled=true;
  $('status').textContent='Loading trends…';
  try {
    const response=await fetch(`/api/trends?${new URLSearchParams(selection)}`),body=await response.json();if(!response.ok)throw new Error(body.message||'Unable to load trends.');
    if(!data)for(const c of [...body.champions].sort((a,b)=>a.name.localeCompare(b.name))){const option=el('option',c.name);option.value=c.championId;$('champion').append(option);}
    data=body;last=selection;render();$('content').hidden=false;$('status').textContent='';
  } catch(error){$('status').textContent=error.message;for(const id of ['queue','role','champion','comparison','size'])$(id).value=last[id];}
  finally{for(const id of ['refresh','queue','role','champion','comparison','size'])$(id).disabled=false;}
}
for(const id of ['queue','role','champion','comparison','size'])$(id).addEventListener('change',load);$('refresh').addEventListener('click',load);
setInterval(()=>{if(document.visibilityState==='visible'&&!$('refresh').disabled)load();},30000);
load();
