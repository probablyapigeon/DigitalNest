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
 await cdp('Runtime.enable');await cdp('Page.enable');
 await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});await wait('typeof state!=="undefined" && state?.objects && window.WorldLife');
 await evaluate(`(async()=>{if(!state.paused)await act('pause');select('pip');while(state.birds.pip.scrap<4)await act('gift');})()`);
 const before=await evaluate('state.birds.pip.scrap');
 await evaluate(`document.getElementById('tinker').click()`);await wait('!busy');
 assert.equal(await evaluate('state.birds.pip.scrap'),before-2);
 assert(await evaluate('state.birds.pip.toys>0'));
 await evaluate(`document.getElementById('shareFriend').value='moss';document.getElementById('shareFriend').dispatchEvent(new Event('change'));document.getElementById('sharePart').click()`);await wait('!busy');
 assert.equal(await evaluate('state.birds.pip.scrap'),before-3);
 await evaluate(`(async()=>{await act('teach_words',{text:'moonberry little friends sing shiny songs in the garden',everyone:true});WorldRooms.open(state.birds.pip.room);await act('visit','moss');})()`);
 assert(await evaluate(`state.voices.some(e=>e.kind==='speech'&&e.bird==='pip'&&e.target==='moss')`));
 assert(await evaluate(`document.getElementById('roomTranscript').textContent.includes('Pip to Moss')`));
 assert.equal(await evaluate(`document.querySelectorAll('#objectHotspots button').length`),2);
 assert.equal(await evaluate(`document.getElementById('voices').getAttribute('aria-pressed')`),'false');
 const voiceInfo=await evaluate(`({available:!!window.speechSynthesis,local:window.speechSynthesis?.getVoices().filter(v=>v.localService).map(v=>v.name)})`);
 console.log('Actual browser voice availability:',JSON.stringify(voiceInfo));
 await evaluate(`document.getElementById('bubble').hidden=true`);await delay(100);await shot('life-desktop.png');
 await evaluate(`document.getElementById('roomLife').scrollIntoView()`);await shot('life-transcript.png');
 // Exercise an actual enabled world object through its rendered button.
 const available=await evaluate(`state.objects[WorldRooms.current].find(o=>!o.reasons[selected])?.id`);
 if(available){await evaluate(`document.querySelector('[data-object="${available}"]').click();document.getElementById('useObjectBird').click()`);await wait('!busy');assert(await evaluate(`state.room_objects[WorldRooms.current]['${available}']>0`));}
 await evaluate(`document.getElementById('objectInspector').close()`);
 await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await evaluate('scrollTo(0,0)');await delay(100);assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'));await shot('life-mobile.png');
 assert.deepEqual(errors,[]);
 console.log('PASS: tray spend/share, real spoken text, room transcript, object hotspot activation, desktop/mobile layout, voices opt-in.');
} finally {ws.close();}
