const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function harness(profile='A#EU', store=new Map()) {
  const elements=new Map(), handlers={}, frames=[];
  class Element {
    constructor(id='',value='',choices=null){this.id=id;this.value=value;this.tagName=choices?'SELECT':'INPUT';this.options=(choices||[]).map(value=>({value}));this.children=[];this.events={};}
    append(...items){this.children.push(...items)}
    replaceChildren(...items){this.children=items}
    addEventListener(name,callback){this.events[name]=callback}
  }
  for(const [id,value,choices] of [['queue','all',['all','solo','flex']],['search','',null],['result','all',['all','win','loss']],['sort','recent',['recent','score']],['more','',null],['matches','',null],['status','',null],['summary','',null],['refresh','',null]])elements.set(id,new Element(id,value,choices));
  const context=vm.createContext({console,URLSearchParams,Intl,Date,Math,Promise,JSON,Number,Array,Object,
    journalProfileReady:Promise.resolve(profile),scrollY:0,history:{scrollRestoration:'auto'},
    document:{getElementById:id=>elements.get(id),createElement:()=>new Element()},
    sessionStorage:{getItem:key=>store.get(key)||null,setItem:(key,value)=>store.set(key,value)},
    addEventListener:(name,callback)=>handlers[name]=callback,
    requestAnimationFrame:callback=>frames.push(callback),scrollTo:(x,y)=>context.scrollY=y,
    matchBuildAndScore:()=>[],fetch:async()=>({ok:true,json:async()=>({matches:Array.from({length:90},(_,i)=>({id:String(i),name:'Teemo',win:true,queue:420,kills:1,deaths:1,assists:1,cs:100,duration:1800,playedAt:100,score:60}))})})});
  context.window=context;
  vm.runInContext(fs.readFileSync('static/view-state.js','utf8'),context);
  return {context,elements,handlers,frames,store};
}

test('restores profile-scoped controls, validates choices, and restores scroll once',async()=>{
  const h=harness();h.store.set('rift-journal:view:1:A%23EU:matches',JSON.stringify({queue:'solo',search:'Teemo',sort:'invalid',scroll:900,visible:75}));
  const view=await h.context.JournalViewState.create('matches',['queue','search','sort']);
  assert.equal(h.elements.get('queue').value,'solo');assert.equal(h.elements.get('search').value,'Teemo');assert.equal(h.elements.get('sort').value,'recent');
  view.restoreScroll();while(h.frames.length)h.frames.shift()();assert.equal(h.context.scrollY,900);
  h.context.scrollY=1200;view.restoreScroll();assert.equal(h.frames.length,0);
  h.handlers.pagehide();assert.equal(JSON.parse(h.store.get('rift-journal:view:1:A%23EU:matches')).scroll,1200);
  const other=harness('B#EU',h.store);await other.context.JournalViewState.create('matches',['queue','search']);assert.equal(other.elements.get('queue').value,'all');assert.equal(other.elements.get('search').value,'');
});

test('blocked or malformed storage falls back without blocking',async()=>{
  const h=harness();h.context.sessionStorage.getItem=()=>{throw Error('blocked')};h.context.sessionStorage.setItem=()=>{throw Error('blocked')};
  const view=await h.context.JournalViewState.create('matches',['queue']);assert.doesNotThrow(()=>view.save());
  const bad=harness();bad.store.set('rift-journal:view:1:A%23EU:matches','{broken');await bad.context.JournalViewState.create('matches',['queue']);assert.equal(bad.elements.get('queue').value,'all');
});

test('match list restores loaded rows and queue before fetching, then resets pagination for new filters',async()=>{
  const h=harness();h.store.set('rift-journal:view:1:A%23EU:matches',JSON.stringify({queue:'solo',search:'Teemo',result:'win',sort:'score',visible:75,scroll:850}));
  let request;const original=h.context.fetch;h.context.fetch=async url=>{request=url;return original(url)};
  vm.runInContext(fs.readFileSync('static/matches.js','utf8'),h.context);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(request,'/api/dashboard?queue=solo');assert.equal(h.elements.get('matches').children.length,75);
  assert.match(h.elements.get('matches').children[0].href,/from=matches&queue=solo/);
  while(h.frames.length)h.frames.shift()();assert.equal(h.context.scrollY,850);
  h.elements.get('search').events.input();assert.equal(h.elements.get('matches').children.length,25);
  h.elements.get('more').events.click();assert.equal(h.elements.get('matches').children.length,50);
  assert.equal(JSON.parse(h.store.get('rift-journal:view:1:A%23EU:matches')).visible,50);
});
