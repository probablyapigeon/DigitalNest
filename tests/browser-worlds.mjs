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
async function wait(expression){const end=Date.now()+12000;while(Date.now()<end){if(await evaluate(expression))return;await delay(100)}throw Error('Timeout: '+expression)}
async function shot(name){const r=await cdp('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('../.qa/'+name,import.meta.url),Buffer.from(r.data,'base64'))}
try {
  await cdp('Runtime.enable'); await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});
  await wait('typeof state !== "undefined" && state?.spaces && window.WorldRooms');
  await evaluate(`(async()=>{if(!state.paused)await act('pause');document.getElementById('worldMapButton').click()})()`);
  assert.equal(await evaluate(`document.querySelectorAll('#mapCards .world-card').length`),6);
  assert.equal(await evaluate(`document.querySelectorAll('#mapRoutes .portal-route').length`),7);
  await shot('world-map-desktop.png');
  for(const id of ['garden','roost','nursery','archive','commons','workshop']){
    await evaluate(`WorldRooms.open('${id}')`);
    await delay(90);
    assert.equal(await evaluate('WorldRooms.current'),id);
    assert.equal(await evaluate(`Object.keys(hitboxes).every(k=>state.birds[k].room===WorldRooms.current)`),true);
  }
  await evaluate(`WorldRooms.open('garden');document.getElementById('pinWorld').click();WorldRooms.open('archive');document.getElementById('pinWorld').click()`);
  assert.equal(await evaluate(`document.querySelectorAll('#pinnedWorlds .world-card').length`),2);
  await evaluate(`select('pip');document.getElementById('followBird').click()`);
  assert.equal(await evaluate('WorldRooms.current'),await evaluate('state.birds.pip.room'));
  await evaluate(`WorldRooms.open('garden');document.getElementById('inviteBird').click()`);
  await wait('!busy');
  // Already-present birds need no invitation; otherwise the saved destination must match.
  assert.equal(await evaluate(`state.birds.pip.room==='garden'||state.birds.pip.destination==='garden'`),true);
  await shot('garden-desktop.png');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await delay(150);assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
  await shot('garden-mobile.png');
  await evaluate(`document.getElementById('worldMapButton').click()`);await shot('world-map-mobile.png');
  assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
  assert.deepEqual(errors,[]);
  console.log('PASS: six illustrated rooms, seven portal links, accurate residents/hitboxes, pinning, follow, invitation, desktop/mobile, no browser exceptions.');
} finally { ws.close(); }
