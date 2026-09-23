import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const tabs=await (await fetch('http://127.0.0.1:9334/json')).json();
const target=tabs.find(t=>t.type==='page');
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
let serial=0;const pending=new Map(),errors=[];
ws.addEventListener('message',e=>{const data=JSON.parse(e.data);if(data.id){const p=pending.get(data.id);pending.delete(data.id);if(data.error)p.reject(Error(data.error.message));else p.resolve(data.result)}else if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text+': '+JSON.stringify(data.params.exceptionDetails.exception))});
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const result=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function wait(expression){const end=Date.now()+12000;while(Date.now()<end){if(await evaluate(expression))return;await delay(100)}throw Error('Timeout: '+expression)}
async function clickAction(action,flag){await evaluate(`document.querySelector('[data-action="${action}"]').click()`);await wait(`state && state.${flag} && !busy`)}
async function screenshot(name){const shot=await cdp('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('../.qa/'+name,import.meta.url),Buffer.from(shot.data,'base64'))}
try{
  await cdp('Runtime.enable');await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:'http://127.0.0.1:8878/'});
  await wait('typeof state !== "undefined" && state !== null');await delay(300);
  if(!await evaluate('state.awake')){
    await screenshot('first-light.png');
    for(const [action,flag] of [['wake','awake'],['inspect','inspected'],['salvage','salvaged'],['repair','wing_fixed'],['hatch','habitat_open'],['cassette','cassette'],['reassure','reassured'],['listen','listened']])await clickAction(action,flag);
    await evaluate(`document.getElementById('note1').value='2';document.getElementById('note2').value='4';document.getElementById('note3').value='3';document.getElementById('decode').click()`);
    await wait('state.decoded && !busy');await clickAction('teach','taught');await clickAction('heater','heater');
  }
  await evaluate(`document.getElementById('latticeToggle').click();document.getElementById('bubble').hidden=true`);
  await wait('state.habitat_open');await delay(1500);await screenshot('habitat-desktop.png');
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'),true,'desktop horizontal overflow');
  await evaluate(`document.querySelector('[aria-label="Select Moss"]').click()`);assert.equal(await evaluate('selected'),'moss');
  await evaluate(`document.getElementById('journalButton').click()`);assert.equal(await evaluate(`document.getElementById('journal').open`),true);await evaluate(`document.getElementById('closeJournal').click()`);
  await evaluate(`document.querySelector('[aria-label="Select Pip"]').click();document.getElementById('chatInput').value='Is my wing repaired?';document.getElementById('chatForm').requestSubmit()`);
  await wait('!chatting && state.chats.length>0');assert.equal(await evaluate(`state.chats.at(-1).renderer`),'authored');
  const flags=await evaluate('JSON.stringify([state.wing_fixed,state.decoded,state.servo,state.habitat_open])');
  await cdp('Page.reload');await wait('typeof state !== "undefined" && state !== null');
  assert.equal(await evaluate('JSON.stringify([state.wing_fixed,state.decoded,state.servo,state.habitat_open])'),flags,'saved progress after reload');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(400);
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'),true,'mobile horizontal overflow');await screenshot('habitat-mobile.png');
  assert.deepEqual(errors,[],'browser errors');
  console.log('PASS: complete opening, cassette, flock, journal, selection, grounded chat, save/reload, desktop/mobile layouts; no JS exceptions.');
}finally{ws.close()}
