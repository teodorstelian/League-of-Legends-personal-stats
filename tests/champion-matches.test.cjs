const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('champion saved matches follow the selected role, including unassigned and empty results', () => {
  const elements = new Map();
  function el(tag, text, className) {
    return {tag, textContent:text, className, children:[], append(...items){this.children.push(...items)}, replaceChildren(){this.children=[]}, addEventListener(){}};
  }
  for (const id of ['matches', 'matches-summary', 'matchup-role', 'queue']) elements.set(id, el('div'));
  const matches = ['MIDDLE', 'UTILITY', undefined].map((role, i) => ({id:String(i), role, queue:420, win:true, kills:1, deaths:2, assists:3, cs:50, duration:900, playedAt:0}));
  const context = vm.createContext({$:id=>elements.get(id), data:{name:'Lux',matches}, el, number:String, journey:new URLSearchParams(), championId:'99', view:null, URLSearchParams, Math, Date, matchBuildAndScore:()=>[]});
  const source = fs.readFileSync('static/champion.js','utf8');
  vm.runInContext(source.slice(source.indexOf('function renderMatches()'),source.indexOf('async function load()')),context);
  elements.get('queue').value = 'all';
  for (const [role,count] of [['all',3],['MIDDLE',1],['UTILITY',1],['TOP',0],['all',3]]) {
    elements.get('matchup-role').value = role;
    context.renderMatches();
    const rows = elements.get('matches').children;
    assert.equal(rows.filter(row=>row.tag==='a').length,count);
    assert.match(elements.get('matches-summary').textContent,new RegExp(`^${count} of 3`));
    if (!count) assert.match(rows[0].textContent,/Try another role or queue/);
    if (role==='MIDDLE') assert.equal(rows[0].children[2].children[2].textContent,'Role: Mid');
    if (role==='all') assert.equal(rows[2].children[2].children[2].textContent,'Role: Unassigned');
  }
  assert.equal(matches.length,3);
});
