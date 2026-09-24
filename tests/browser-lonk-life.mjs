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
async function realClick(id){await evaluate(`document.getElementById('${id}').scrollIntoView({block:'center'})`);const r=await evaluate(`(()=>{const r=document.getElementById('${id}').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...r,button:'left',clickCount:1});await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...r,button:'left',clickCount:1});}
try {
 await cdp('Runtime.enable');await cdp('Page.enable');await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});
 await wait('typeof state!=="undefined" && state?.habitat_open && document.getElementById("lonkLife")');
 await evaluate(`select('moss');WorldRooms.open('garden')`);
 const before=await evaluate('state.birds.moss.inner_life.inventory.length');
 await evaluate(`Array.from(document.querySelectorAll('#lonkLife button')).find(b=>b.textContent==='Find a keepsake').click()`);
 await wait('!busy && !!state.birds.moss.inner_life.treasure');
 assert.equal(await evaluate('state.birds.moss.inner_life.inventory.length'),before+1);
 assert(await evaluate(`document.getElementById('lonkLife').textContent.includes(state.birds.moss.inner_life.treasure)`));
 await evaluate(`select('pip')`);
 await evaluate(`Array.from(document.querySelectorAll('#lonkLife button')).find(b=>b.textContent==='Leaf duel').click()`);
 await wait('!busy && !!state.birds.pip.inner_life.rival');
 assert.equal(await evaluate('state.birds.pip.inner_life.rival'),'moss');
 await cdp('Page.reload');await wait('typeof state!=="undefined" && !!state?.birds?.moss?.inner_life?.treasure');
 await evaluate(`select('moss');WorldRooms.open('garden')`);await evaluate(`document.getElementById('lonkLife').scrollIntoView({block:'center'})`);await shot('lonk-life-desktop.png');
 await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(200);
 assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'));await shot('lonk-life-mobile.png');
 assert.deepEqual(errors,[]);
 console.log('PASS: selected bird collects, visible keepsakes, local duel, reload persistence, mobile layout, no browser exceptions');
} finally {ws.close();}
