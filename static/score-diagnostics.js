// Technical score detail is loaded only when Calibration is opened for a match.
(() => {
  const match=new URLSearchParams(location.search).get('match');
  if(!match)return;
  const get=id=>document.getElementById(id);
  const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const num=value=>typeof value==='number'?new Intl.NumberFormat(undefined,{maximumFractionDigits:3}).format(value):'—';
  const section=get('match-diagnostics');section.hidden=false;
  get('diagnostics-back').href=`/matches/${encodeURIComponent(match)}`;
  async function loadDetails(){
    get('diagnostics-status').textContent='Loading match scoring details…';get('diagnostics-retry').hidden=true;
    try{
      const response=await fetch(`/api/matches/${encodeURIComponent(match)}`),data=await response.json();
      if(!response.ok)throw Error(data.message||'Unable to load match scoring details.');
      const own=data.participants.find(p=>p.you);if(!own)throw Error('Your player was not found in this match.');
      get('match-diagnostics-title').textContent=`${own.name} · Match scoring details`;
      get('diagnostics-method').textContent=own.score.method||own.score.reason;
      get('diagnostics-components').replaceChildren();
      for(const c of own.score.components){
        const card=node('article');card.className='component';card.append(node('h3',c.name));
        for(const text of [
          `Score: ${num(c.value)} / ${c.maximum||100} · Weight: ${num(c.weight)}% · Contribution: ${num(c.contribution)} points`,
          `Your rate: ${num(c.own)} ${c.unit} · ${c.targetLabel}: ${num(c.target)} ${c.unit}`,
          c.description,
          `${own.score.opponentContext||'Opponent'}: ${num(c.opponent)} ${c.unit} (context only)`,
          `Reference source: ${c.referenceSource||'Role baseline'} · Champion samples: ${c.referenceSamples||0} · Champion blend: ${num((c.referenceBlend||0)*100)}%`,
          `Role reference: ${num(c.roleTarget??c.baseTarget)} · Base reference: ${num(c.baseTarget)} · Duration multiplier: ${num(c.durationMultiplier)}×`,
          `Exceptional bonus: ${num(c.bonus)} component points · ${num(c.bonusContribution)} weighted points before the overall cap`,
          `Benchmarks (${c.unit} → points): ${(c.benchmarks||[]).map(b=>`${num(b.own)} → ${num(b.value)}`).join(' · ')}`
        ]){if(text){const p=node('p',text);p.className='muted';card.append(p);}}
        get('diagnostics-components').append(card);
      }
      const economy=own.score.economyContext,checkpoints=data.economyCheckpoints||[];
      get('diagnostics-economy').textContent=economy?`Gold/min difference vs opponent context: ${num(economy.differencePerMinute)}. ${economy.note} ${checkpoints.length?`Recorded role-opponent gold leads: ${checkpoints.map(p=>`${num(p.timestamp/60000)} min: ${num(p.goldDifference)}`).join(' · ')}`:'Gold advantage checkpoints unavailable.'}`:'';
      get('diagnostics-status').textContent=own.score.components.length?'':own.score.reason;
    }catch(error){get('diagnostics-status').textContent=error.message;get('diagnostics-retry').hidden=false;}
  }
  get('diagnostics-retry').addEventListener('click',loadDetails);loadDetails();
})();
