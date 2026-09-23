import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const tabs=await(await fetch('http://127.0.0.1:9334/json')).json();
const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
let serial=0;const pending=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result)}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params)};
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function wait(expression,timeout=12000){const end=Date.now()+timeout;while(Date.now()<end){if(await evaluate(expression))return;await delay(100)}throw Error('Timeout: '+expression)}
async function shot(name){const r=await cdp('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('../.qa/'+name,import.meta.url),Buffer.from(r.data,'base64'))}
try{
  await cdp('Runtime.enable');await cdp('Page.enable');await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});await wait('typeof state !== "undefined" && state?.habitat_open');
  await evaluate(`document.getElementById('societyButton').click()`);
  assert(await evaluate(`document.getElementById('societyDialog').open`));
  for(let i=0;i<6;i++){
    const before=await evaluate('state.birds.pip.culture.conversations');
    await evaluate(`document.getElementById('teachEveryone').checked=true;document.getElementById('teachInput').value='beep boop moonberry moss garden warm nest friend song shiny feather home';document.getElementById('teachForm').requestSubmit()`);
    await wait(`!busy && state.birds.pip.culture.conversations>${before}`);
  }
  assert.equal(await evaluate('state.birds.pip.culture.stage'),'graduate');
  assert(await evaluate(`state.birds.pip.culture.vocabulary.includes('moonberry')`));
  for(let i=0;i<14;i++){
    const before=await evaluate('state.birds.pip.culture.conversations');
    await evaluate(`document.getElementById('visitFriend').value='moss';document.getElementById('visit').click()`);
    await wait(`!busy && state.birds.pip.culture.conversations>${before}`);
  }
  assert(await evaluate(`state.birds.pip.culture.partners.includes('moss')`));
  assert(await evaluate(`state.birds.moss.culture.partners.includes('pip')`));
  assert(await evaluate('state.society.colonies.length>0'));
  // Prepare a second perch explicitly; do not assume earlier tests left one built.
  await evaluate(`document.getElementById('closeSociety').click()`);
  if(await evaluate('state.birds.pip.nest<2')){
    if(!await evaluate('state.paused')){await evaluate(`document.getElementById('pause').click()`);await wait('state.paused && !busy');}
    for(let i=0;i<6;i++){if(await evaluate('state.birds.pip.scrap>=6'))break;await evaluate(`document.getElementById('gift').click()`);await wait('!busy');}
    await evaluate(`WorldRooms.open('roost');document.getElementById('inviteBird').click()`);await wait('!busy');
    await evaluate(`document.getElementById('pause').click()`);await wait('!state.paused && !busy');
    await wait(`state.birds.pip.room==='roost'`,25000);
    await evaluate(`document.getElementById('pause').click()`);await wait('state.paused && !busy');
    if(await evaluate('state.birds.pip.nest<2')){await evaluate(`document.querySelector('[data-object="perch"]').click();document.getElementById('useObjectBird').click()`);await wait('!busy && state.birds.pip.nest>=2');await evaluate(`document.getElementById('objectInspector').close()`);}
  }
  // Supply the nursery through the normal gift control.
  await evaluate(`document.getElementById('closeSociety').click()`);
  // Freeze autonomous construction before checking nursery resources, as a player can.
  if(!await evaluate('state.paused')){await evaluate(`document.getElementById('pause').click()`);await wait('state.paused && !busy')}
  for(let i=0;i<3;i++){
    if(await evaluate('state.birds.pip.scrap>=3'))break;
    const before=await evaluate('state.birds.pip.scrap');
    await evaluate(`document.getElementById('gift').click()`);await wait(`!busy && state.birds.pip.scrap>${before}`);
  }
  await wait('state.birds.pip.nest>=2');
  await evaluate(`document.getElementById('societyButton').click()`);
  const before=await evaluate('state.society.population');
  assert.equal(await evaluate(`document.getElementById('nursery').disabled`),false);
  await evaluate(`document.getElementById('nursery').click()`);await wait(`!busy && state.society.population>${before}`);
  const baby=await evaluate(`Object.keys(state.birds).find(k=>k.startsWith('chick-'))`);
  assert(baby);assert(await evaluate(`state.birds[${JSON.stringify(baby)}].culture.vocabulary.includes('moonberry')`));
  assert.equal(await evaluate(`state.birds[${JSON.stringify(baby)}].culture.generation`),2);
  await evaluate(`document.getElementById('cultureBird').value=${JSON.stringify(baby)};document.getElementById('cultureBird').dispatchEvent(new Event('change'))`);
  assert.equal(await evaluate('selected'),baby);await shot('society-desktop.png');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(300);
  assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'));
  assert(await evaluate(`document.getElementById('societyDialog').scrollWidth<=document.getElementById('societyDialog').clientWidth`));await shot('society-mobile.png');
  await cdp('Page.reload');await wait(`typeof state!=='undefined' && state?.birds[${JSON.stringify(baby)}]`);
  assert(await evaluate(`state.birds[${JSON.stringify(baby)}].culture.parents.includes('pip')`));
  assert.deepEqual(errors,[]);
  console.log('PASS: UI teaching, word learning, graduation, reciprocal partners, colony, nursery, descendant selection, inheritance, reload, mobile layout; no JS exceptions.');
}finally{ws.close()}
