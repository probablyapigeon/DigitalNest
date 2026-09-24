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
 await cdp('Runtime.enable');await cdp('Page.enable');
 await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});
 await wait('typeof state!=="undefined" && state?.spaces?.["world-2"] && document.getElementById("lonkLife")');
 const render=`(key)=>{const c=document.createElement('canvas');c.width=1000;c.height=600;const g=c.getContext('2d');g.translate(500,260);const r=state.spaces[key];SpaceArt.draw(g,r.kind,0,{},r.name,r.design);return c.toDataURL()}`;
 const first=await evaluate(`(${render})('world-1')`),second=await evaluate(`(${render})('world-2')`);
 assert.notEqual(first,second);
 assert.equal(first,await evaluate(`(${render})('world-1')`));
 await fs.writeFile(new URL('../.qa/evolving-pip-garden.png',import.meta.url),Buffer.from(first.split(',')[1],'base64'));
 await fs.writeFile(new URL('../.qa/evolving-moss-garden.png',import.meta.url),Buffer.from(second.split(',')[1],'base64'));
 await evaluate(`select('moss');WorldRooms.open('world-2')`);
 await evaluate(`Array.from(document.querySelectorAll('#lonkLife button')).find(b=>b.textContent==='Design your own world').click()`);
 await wait('!busy && !!state.birds.moss.world_project');
 assert.equal(await evaluate('!!state.birds.pip.world_project'),false);
 await evaluate(`Array.from(document.querySelectorAll('#lonkLife button')).find(b=>b.textContent.startsWith('Natural conversations:')).click()`);
 await wait('!busy && state.natural_conversations===false');
 await evaluate(`document.getElementById('lonkLife').scrollIntoView({block:'center'})`);
 await shot('evolving-desktop.png');
 await cdp('Page.reload');await wait('typeof state!=="undefined" && !!state?.birds?.moss?.world_project');
 assert.equal(first,await evaluate(`(${render})('world-1')`));
 await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(250);
 assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'));
 await shot('evolving-mobile.png');
 assert.deepEqual(errors,[]);
 console.log('PASS: distinct reproducible garden pixels, selected-bird project, natural conversation toggle, reload persistence, mobile layout, no JS exceptions');
} finally {ws.close();}
