import assert from 'node:assert/strict';
const tabs=await(await fetch('http://127.0.0.1:9334/json')).json();
const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise(resolve=>ws.addEventListener('open',resolve,{once:true}));
let serial=0;const pending=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result)}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params)};
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function wait(expression){const end=Date.now()+12000;while(Date.now()<end){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,100))}throw Error('Timeout: '+expression)}
try {
 await cdp('Runtime.enable');await cdp('Page.enable');
 await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});
 await wait('typeof state!=="undefined" && state?.habitat_open');
 await evaluate("window.replyReads=[];WorldLife.speakReply=(text)=>replyReads.push(text);select('pip')");
 for(let i=0;i<3;i++){
  await evaluate("document.getElementById('chatInput').value='Is my wing repaired?';document.getElementById('chatForm').requestSubmit()");
  await wait('!chatting && document.getElementById("chatInput").value===""');
 }
 assert.equal(await evaluate('replyReads.length'),2);
 assert.equal(await evaluate('new Set(replyReads).size'),2);
 assert.equal(await evaluate('document.getElementById("chatMode").textContent'),'LISTENING');
 assert.equal(await evaluate('state.chats.filter(e=>e.role==="assistant").length'),2);
 await cdp('Page.reload');await wait('typeof state!=="undefined" && state?.habitat_open');
 await evaluate("document.getElementById('chatInput').value='Is my wing repaired?';document.getElementById('chatForm').requestSubmit()");
 await wait('!chatting && document.getElementById("chatInput").value===""');
 assert.equal(await evaluate('document.getElementById("chatMode").textContent'),'LISTENING');
 assert.deepEqual(errors,[]);
 console.log('PASS: distinct replies, duplicate suppressed, no duplicate TTS, quiet UI, reload persistence.');
} finally {ws.close();}
