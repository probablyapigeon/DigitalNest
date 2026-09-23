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
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});await delay(350);await wait('typeof state!=="undefined" && state?.building && window.WorldLife');
 await evaluate(`localStorage.removeItem('little-flock-read-replies')`);await cdp('Page.reload');await delay(350);await wait('typeof state!=="undefined" && state?.building && window.WorldLife');
 await evaluate(`(async()=>{if(!state.paused)await act('pause');select('pip');WorldRooms.open('garden')})()`);
 assert(await evaluate(`document.getElementById('readReplies').checked`));
 await evaluate(`window.voiceCalls=[];window.voiceEnds=[];const speakOriginal=speechSynthesis.speak.bind(speechSynthesis);speechSynthesis.speak=u=>{voiceCalls.push(u.text);u.addEventListener('end',()=>voiceEnds.push('end'));u.addEventListener('error',e=>voiceEnds.push(e.error));speakOriginal(u)};document.getElementById('chatInput').value='Is my wing repaired?'`);
 await realClick('send');await wait('!chatting && voiceCalls.length>0');await wait('voiceEnds.length>0');
 assert.equal(await evaluate('voiceEnds[0]'),'end');assert.equal(await evaluate('voiceCalls[0]'),await evaluate('state.chats.at(-1).text'));
 assert.equal(await evaluate('state.paused'),true);
 console.log('PASS: typed chat response spoken to completion while paused and viewing another room.');
 await realClick('readReplies');const count=await evaluate('voiceCalls.length');
 await evaluate(`document.getElementById('chatInput').value='Is my wing repaired?'`);await realClick('send');await wait('!chatting');
 assert.equal(await evaluate('voiceCalls.length'),count);
 await evaluate(`WorldRooms.open('garden');document.querySelector('[data-object="pond"]').click()`);
 assert(await evaluate(`document.getElementById('objectInspector').open`));assert.equal(await evaluate(`getComputedStyle(document.querySelector('[data-object="pond"]')).cursor`),'pointer');
 await evaluate(`document.getElementById('useObjectSelf').click()`);await wait('!busy');assert(await evaluate('state.room_charge.garden>0'));
 await evaluate(`document.getElementById('objectInspector').close();document.getElementById('newWorld').click();document.getElementById('newWorldName').value='Moonberry Meadow';document.getElementById('newWorldKind').value='garden';document.getElementById('newWorldLink').value='garden';document.getElementById('newWorldForm').requestSubmit()`);
 await wait(`!busy && state.last_created_world && WorldRooms.current===state.last_created_world`);
 const room=await evaluate('state.last_created_world');assert.equal(await evaluate('state.spaces[WorldRooms.current].name'),'Moonberry Meadow');
 assert(await evaluate(`state.spaces.garden.links.includes('${room}')`));assert.equal(await evaluate('state.building.supplies'),16);
 await evaluate(`document.getElementById('buildWorld').click()`);
 await evaluate(`document.querySelector('#blueprintCards .blueprint-card button').click()`);await wait('!busy');
 assert.equal(await evaluate(`state.building.structures['${room}'][0].type`),'solar');assert.equal(await evaluate('state.building.supplies'),12);
 await evaluate(`document.getElementById('buildDialog').close();document.getElementById('worldMapButton').click()`);await shot('builder-map.png');
 assert.equal(await evaluate(`document.querySelectorAll('#mapCards .world-card').length`),7);
 await evaluate(`document.getElementById('worldMap').close();document.getElementById('bubble').hidden=true;scrollTo(0,0)`);await shot('built-world.png');
 await cdp('Page.reload');await delay(350);await wait('typeof state!=="undefined" && state?.building');
 assert.equal(await evaluate(`state.building.structures['${room}'][0].type`),'solar');assert.equal(await evaluate(`document.getElementById('readReplies').checked`),false);
 await evaluate(`WorldRooms.open('${room}');document.getElementById('buildWorld').click()`);
 await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(100);await shot('builder-mobile.png');
 assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'));assert.deepEqual(errors,[]);
 console.log('PASS: mute persists, empty-room object usable, no help cursor, new named world, reciprocal portal, paid visible solar canopy, save/reload and mobile builder.');
} finally {ws.close();}
