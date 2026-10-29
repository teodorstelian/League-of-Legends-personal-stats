const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');

test('status polling does not rebuild an unchanged report and skips overlapping polls',async()=>{
 class Element{constructor(){this.children=[];this.events={};this.options=[{}];this.value='all'}append(...xs){this.children.push(...xs)}replaceChildren(...xs){this.children=xs}addEventListener(name,callback){this.events[name]=callback}}
 const elements=new Map();const element=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)};
 let reports=0,statuses=0,cached=1,pending;
 const context=vm.createContext({URLSearchParams,Intl,console,setInterval:()=>{},document:{visibilityState:'visible',getElementById:element,createElement:()=>new Element()},fetch:async url=>{
   if(url.startsWith('/api/early-game')){reports++;return {ok:true,json:async()=>({cached,total:2,unavailable:0,catalog:[],champions:[],roles:[],summary:{checkpoints:[],earlyDeaths:0,deathGames:1,deathsPerGame:0}})}}
   statuses++;if(pending)await pending;
   return {ok:true,json:async()=>({cached,total:2,unavailable:0,remaining:0,active:true,message:''})};
 }});
 vm.runInContext(fs.readFileSync('static/early-game.js','utf8'),context);
 await new Promise(resolve=>setImmediate(resolve));assert.equal(reports,1);
 await vm.runInContext('importStatus()',context);assert.equal(reports,1);
 cached=2;await vm.runInContext('importStatus()',context);assert.equal(reports,2);
 let release;pending=new Promise(resolve=>release=resolve);const before=statuses;
 const first=vm.runInContext('importStatus()',context);await vm.runInContext('importStatus()',context);assert.equal(statuses,before+1);release();await first;
});
