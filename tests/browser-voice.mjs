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
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});await wait('typeof state!=="undefined" && state?.objects && window.WorldLife');
 await evaluate(`(async()=>{if(state.paused)await act('pause');WorldRooms.open(state.birds.pip.room);})()`);
 await evaluate(`window.voiceCalls=[];window.voiceEnds=[];window.voiceCancelCount=0;const originalSpeak=speechSynthesis.speak.bind(speechSynthesis),originalCancel=speechSynthesis.cancel.bind(speechSynthesis);speechSynthesis.speak=u=>{voiceCalls.push({text:u.text,local:u.voice?.localService});u.addEventListener('end',()=>voiceEnds.push('end'));u.addEventListener('error',e=>voiceEnds.push(e.error));originalSpeak(u)};speechSynthesis.cancel=()=>{voiceCancelCount++;originalCancel()}`);
 const rect=await evaluate(`(()=>{const r=document.getElementById('voices').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...rect,button:'left',clickCount:1});await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...rect,button:'left',clickCount:1});
 await wait('voiceCalls.length>0');
 assert.equal(await evaluate('voiceCalls[0].local'),true);
 await wait('voiceEnds.length>0');
 console.log('Real speech service completion:',await evaluate('voiceEnds[0]'));
 assert.equal(await evaluate('voiceEnds[0]'),'end');
 // An active thought is visible, but never sent to the speech synthesizer.
 await evaluate(`window.beforeThought=voiceCalls.length;const n=structuredClone(state);n.voices.push({id:(n.voices.at(-1)?.id||0)+1000,tick:n.tick,bird:'pip',room:WorldRooms.current,kind:'thought',text:'TEST PRIVATE THOUGHT'});setState(n)`);
 assert.equal(await evaluate(`voiceCalls.some(v=>v.text==='TEST PRIVATE THOUGHT')`),false);
 await evaluate(`document.getElementById('voices').click()`);
 assert.equal(await evaluate(`document.getElementById('voices').getAttribute('aria-pressed')`),'false');
 assert(await evaluate('voiceCancelCount>0'));
 await evaluate(`(async()=>{if(!state.paused)await act('pause')})()`);
 assert.deepEqual(errors,[]);
 console.log('PASS: real local speech completed, thoughts never voiced, mute cancels speech.');
} finally {ws.close();}
