const timeLabel = ms => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;
const deltaLabel = n => `${n > 0 ? '+' : ''}${number(n)}`;
const deltaClass = n => n > 0 ? 'positive' : n < 0 ? 'negative' : '';
async function loadTimeline() {
 const status=$('timeline-status'),body=$('timeline-body'),retry=$('timeline-retry');
 status.textContent='Loading the story of this match…';retry.hidden=true;body.replaceChildren();
 try {
  const response=await fetch(`/api/matches/${encodeURIComponent(data.id)}/timeline`),report=await response.json();
  if(!response.ok)throw Error(report.message||'Timeline unavailable.');
  status.textContent=report.opponent?`YOUR LANE · vs ${report.opponent} · Positive values mean you are ahead`:'No unique role opponent was recorded. Key events are still available.';
  if(report.points.length){
   const panel=el('div',undefined,'timeline-chart-panel'),top=el('div',undefined,'timeline-chart-top'),title=el('div');
   title.append(el('p','THE BALANCE OF THE LANE','eyebrow'),el('h3','Every lead has a turning point'));
   const tabs=el('div',undefined,'timeline-tabs');tabs.setAttribute('aria-label','Chart metric');let metric='gold';const buttons=[];
   for(const [key,label]of [['gold','Gold'],['xp','XP'],['cs','CS']]){const b=el('button',label);b.type='button';b.addEventListener('click',()=>{metric=key;draw();});buttons.push([key,b]);tabs.append(b);}
   top.append(title,tabs);panel.append(top);
   const chart=el('div',undefined,'timeline-chart'),readout=el('div',undefined,'timeline-readout'),sliderLabel=el('label','Explore a recorded moment','timeline-slider-label'),slider=el('input');slider.type='range';slider.min=0;slider.max=report.points.length-1;slider.value=report.points.length-1;slider.step=1;slider.setAttribute('aria-label','Recorded timeline moment');sliderLabel.append(slider);panel.append(chart,readout,sliderLabel);body.append(panel);let marker;
   function update(){const p=report.points[Number(slider.value)];readout.replaceChildren(el('span',timeLabel(p.timestamp),'timeline-time'),el('strong',`${deltaLabel(p[metric])} ${metric==='xp'?'XP':metric.toUpperCase()}`,deltaClass(p[metric])),el('span',p[metric]>0?'Ahead of your role opponent':p[metric]<0?'Behind your role opponent':'Even with your role opponent','muted'));slider.setAttribute('aria-valuetext',`${timeLabel(p.timestamp)}, ${deltaLabel(p[metric])} ${metric}`);if(marker){const max=Math.max(1,...report.points.map(p=>Math.abs(p[metric])));marker.setAttribute('cx',56+p.timestamp/Math.max(1,report.points.at(-1).timestamp)*700);marker.setAttribute('cy',130-p[metric]/max*94);marker.setAttribute('fill',p[metric]>=0?'#6ed7cc':'#f08b87');}}
   function draw(){
    buttons.forEach(([key,b])=>b.setAttribute('aria-pressed',String(key===metric)));chart.replaceChildren();const points=report.points,max=Math.max(1,...points.map(p=>Math.abs(p[metric]))),end=Math.max(1,points.at(-1).timestamp),ns='http://www.w3.org/2000/svg';
    function sv(tag,attrs={},text){const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
    const svg=sv('svg',{viewBox:'0 0 800 280',role:'img','aria-label':`${metric} difference versus ${report.opponent}. Use the slider below to inspect recorded frames.`});svg.append(sv('title',{},'Teal above zero is ahead; coral below zero is behind.'));
    const defs=sv('defs');for(const[id,y,height]of [['lead-clip',20,110],['deficit-clip',130,110]]){const clip=sv('clipPath',{id});clip.append(sv('rect',{x:56,y,width:700,height}));defs.append(clip);}svg.append(defs);
    for(const[y,label]of [[36,`+${number(max)}`],[130,'0'],[224,`−${number(max)}`]])svg.append(sv('line',{x1:56,x2:756,y1:y,y2:y,stroke:'#31473f','stroke-dasharray':y===130?'0':'3 6'}),sv('text',{x:46,y:y+4,'text-anchor':'end',fill:'#9db4a9','font-size':11},label));
    for(let min=0;min<=end/60000;min+=5){const x=56+min*60000/end*700;svg.append(sv('line',{x1:x,x2:x,y1:28,y2:234,stroke:'#24392f','stroke-dasharray':'3 6'}),sv('text',{x,y:260,'text-anchor':'middle',fill:'#9db4a9','font-size':11},`${min}:00`));}
    const coords=points.map(p=>`${56+p.timestamp/end*700},${130-p[metric]/max*94}`),area=`M${56+points[0].timestamp/end*700},130 L${coords.join(' L')} L756,130 Z`;
    for(const[clip,color]of [['lead-clip','#6ed7cc'],['deficit-clip','#f08b87']])svg.append(sv('path',{d:area,fill:color,opacity:.12,'clip-path':`url(#${clip})`}),sv('polyline',{points:coords.join(' '),fill:'none',stroke:color,'stroke-width':3,'stroke-linejoin':'round','clip-path':`url(#${clip})`}));
    marker=sv('circle',{r:5,stroke:'#101b16','stroke-width':3});svg.append(marker);chart.append(svg);update();
   }
   slider.addEventListener('input',update);draw();const cards=el('div',undefined,'timeline-checkpoints');
   for(const c of report.checkpoints){const card=el('article',undefined,'timeline-checkpoint');card.append(el('p',`${c.minute} MINUTE CHECKPOINT`,'eyebrow'));if(c.point){const p=c.point;card.append(el('strong',`${deltaLabel(p.gold)} gold`,deltaClass(p.gold)));const metrics=el('div',undefined,'timeline-mini-metrics');metrics.append(el('span',`${deltaLabel(p.xp)} XP`,deltaClass(p.xp)),el('span',`${deltaLabel(p.cs)} CS`,deltaClass(p.cs)));card.append(metrics,el('small',`Recorded at ${timeLabel(p.timestamp)}`,'muted'));}else card.append(el('strong','—'),el('small','Game ended earlier or no nearby frame','muted'));cards.append(card);}body.append(cards,el('p','Checkpoints use the latest frame at or before the target, within 90 seconds. CS includes jungle monsters. Timeline differences do not change Rift Score.','sample-note'));
  }
  const eventPanel=el('div',undefined,'timeline-event-panel'),eventTop=el('div',undefined,'timeline-chart-top'),heading=el('div');heading.append(el('p','MOMENTS THAT MATTER','eyebrow'),el('h3','Kills, objectives & structures'));const filter=el('label',undefined,'timeline-event-filter'),checkbox=el('input');checkbox.type='checkbox';filter.append(checkbox,document.createTextNode(' Only my involvement'));eventTop.append(heading,filter);eventPanel.append(eventTop);const list=el('ol',undefined,'timeline-events');
  function renderEvents(){list.replaceChildren();const events=report.events.filter(e=>!checkbox.checked||e.involved);for(const e of events){const kind=e.type==='CHAMPION_KILL'?(e.death?'death':'kill'):e.type==='ELITE_MONSTER_KILL'?'objective':'structure';const row=el('li',undefined,`timeline-event event-${kind}`),icon=el('span',kind==='death'?'×':kind==='kill'?'⚔':kind==='objective'?'◆':'▥','timeline-event-icon');icon.setAttribute('aria-hidden','true');const text=el('div');text.append(el('small',`${e.death?'YOUR DEATH':kind.toUpperCase()}${e.involved&&!e.death?' · YOU INVOLVED':''}`),el('p',e.label.replaceAll('_',' ')));row.append(el('time',timeLabel(e.timestamp)),icon,text);list.append(row);}if(!events.length)list.append(el('li','No recorded events for this selection.','muted'));}
  checkbox.addEventListener('change',renderEvents);renderEvents();eventPanel.append(list);body.append(eventPanel);
 }catch(error){status.textContent=error.message;retry.hidden=false;}
}
$('timeline-retry').addEventListener('click',loadTimeline);
