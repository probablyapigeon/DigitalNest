window.WorldLife = (()=>{
  let latest=null, enabled=false, lastRoom='', signature='', bubbleEvents=[], queued=[], speaking=false, generation=0, activeEvent=null, readReplies=true;
  try{readReplies=localStorage.getItem('little-flock-read-replies')!=='off';}catch{}
  const synth=window.speechSynthesis;
  const localVoices=()=>synth?synth.getVoices().filter(v=>v.localService&&/^en\b/i.test(v.lang)):[];
  function stop(){generation++;queued=[];speaking=false;activeEvent=null;synth?.cancel();}
  function nextVoice(){
    if(speaking||document.hidden||!queued.length)return;
    queued=queued.filter(e=>e.kind==='reply'?(readReplies||e.force):(enabled&&!state?.paused));
    if(!queued.length)return;
    const voices=localVoices();if(!voices.length){queued=[];status();return;}
    const event=queued.shift(),u=new SpeechSynthesisUtterance(event.text),token=generation;
    const index=Math.max(0,keys.indexOf(event.bird));u.voice=voices[index%voices.length];u.rate=[.92,.85,1.08,.9][index%4];u.pitch=[1.05,1.1,1.3,.85][index%4];u.volume=.65;
    speaking=true;activeEvent=event;u.onend=()=>{if(token!==generation)return;speaking=false;activeEvent=null;nextVoice();};u.onerror=()=>{if(token!==generation)return;speaking=false;queued=[];$('voiceStatus').textContent='Voice playback unavailable. Their words are still shown here.';};synth.speak(u);
  }
  function status(){
    $('voices').textContent=enabled?'Voices on':'Voices off';$('voices').setAttribute('aria-pressed',String(enabled));
    $('voiceStatus').textContent=!synth?'This browser has no speech service; text and chirps still work.':enabled?(localVoices().length?'Ambient voices on. Chat replies have their own read-aloud setting.':'No local English voice is available in this browser. Text and chirps still work.'):'Chat replies are read aloud unless muted below the chat. Voices enables room chatter.';
  }
  function heading(e){const who=e.kind==='user'?'You':names[e.bird]||e.bird;const kind=e.kind==='thought'?'thinks':e.kind==='action'?'does':e.kind==='user'?'say':e.target?`to ${e.target==='user'?'you':names[e.target]||e.target}`:'says';return `${who} ${kind}`;}
  function update(){if(!state?.objects)return;const room=WorldRooms.current,b=state.birds[selected],events=state.voices||[];
    const changed=room!==lastRoom;
    if(changed){lastRoom=room;if(activeEvent?.kind!=='reply')stop();else queued=[];bubbleEvents=[];}
    if(document.hidden||(state.paused&&activeEvent?.kind!=='reply'))stop();
    const fresh=latest===null?[]:events.filter(e=>e.id>latest);latest=Math.max(latest||0,...events.map(e=>e.id));
    for(const event of fresh){if(event.room!==room)continue;bubbleEvents.push({...event,until:performance.now()+10000});
      if(enabled&&!state.paused&&event.kind==='speech'&&queued.length<3)queued.push(event);
    }
    bubbleEvents=bubbleEvents.filter(e=>e.until>performance.now()).slice(-8);nextVoice();
    $('partsTray').hidden=!state.habitat_open;$('roomLife').hidden=!state.habitat_open;
    $('partsCount').textContent=`${b.scrap}/8`;$('partsHint').textContent=`${b.toys||0} toys built. Open Build to turn parts into permanent world structures.`;
    $('tinker').disabled=busy||b.scrap<2;
    const friend=$('shareFriend').value;
    $('shareFriend').replaceChildren(...keys.filter(k=>k!==selected).map(k=>option(k,`${names[k]} (${state.birds[k].scrap}/8)`)));
    if(keys.includes(friend)&&friend!==selected)$('shareFriend').value=friend;
    $('sharePart').disabled=busy||b.scrap<1||state.birds[$('shareFriend').value]?.scrap>=8;
    $('partsSlots').replaceChildren(...Array.from({length:8},(_,i)=>{const el=document.createElement('span');el.className=i<b.scrap?'filled':'';el.textContent=i<b.scrap?'⚙':'·';return el;}));
    const sig=JSON.stringify([room,selected,busy,state.tick,state.objects[room],events.slice(-20),b.scrap]);if(sig===signature)return;signature=sig;
    $('objectsTitle').textContent=state.spaces[room].name;
    $('objectHotspots').replaceChildren();$('objectActions').replaceChildren();
    for(const item of state.objects[room]){
      const reason=item.reasons[selected],row=document.createElement('div');row.className='object-row';
      const button=document.createElement('button');button.className='secondary';button.textContent=`${item.name}: ${item.label}${item.cost?` · ${item.cost} parts`:''}`;button.disabled=busy;button.onclick=()=>WorldBuilder.inspect(room,item.id);
      const hint=document.createElement('p');hint.className='hint';hint.textContent=reason||`${item.uses} uses so far · Ready`;
      row.append(button,hint);$('objectActions').append(row);
      const spot=document.createElement('button');spot.className='object-hotspot';spot.dataset.object=item.id;spot.dataset.x=item.x;spot.dataset.y=item.y;spot.textContent=`✧ ${item.name}`;spot.title=reason||`${item.label}${item.cost?` (${item.cost} parts)`:''}`;spot.setAttribute('aria-label',`${item.name}: ${spot.title}`);spot.disabled=busy;spot.onclick=button.onclick;$('objectHotspots').append(spot);
    }
    const visible=events.filter(e=>e.room===room).slice(-12);
    $('roomTranscript').replaceChildren(...visible.map(e=>{const p=document.createElement('p');p.className='room-line '+e.kind;const strong=document.createElement('strong');strong.textContent=heading(e);p.append(strong,document.createTextNode(e.text));return p;}));
    if(!visible.length)$('roomTranscript').textContent='A quiet moment. Teach some words, arrange a visit, or let the flock explore.';
    $('roomTranscript').scrollTop=$('roomTranscript').scrollHeight;
  }
  function draw(g){
    for(const el of $('objectHotspots').children){el.style.left=(w/2+Number(el.dataset.x)*sceneScale)+'px';el.style.top=(sceneY+Number(el.dataset.y)*sceneScale)+'px';}
    if(!state?.habitat_open)return;
    const room=WorldRooms.current;
    WorldBuilder.drawStructures(g,room,false);
    const uses=state.room_objects?.[room]||{};
    const kind=state.spaces[room].kind;
    g.save();g.translate(w/2,sceneY);g.scale(sceneScale,sceneScale);
    if(kind==='garden'){for(let i=0;i<Math.min(8,uses.planter||0);i++){const x=-145+(i%5)*66,y=-122-Math.floor(i/5)*14;ellipse(g,x,y,7,7,'#e2be85');ellipse(g,x,y,3,3,'#f9e4a4');}}
    if(kind==='archive'){for(let i=0;i<Math.min(6,uses.press||0);i++)round(g,160+i*3,97-i*3,29,15,2,'#eee2b9','#a19877');}
    if(kind==='nursery'){for(let i=0;i<Math.min(5,uses.mobile||0);i++)ellipse(g,-95+i*45,150,9,7,['#deb882','#a7c69b','#b0a2c6'][i%3]);}
    if(kind==='workshop'){const toys=Object.values(state.birds).reduce((n,b)=>n+(b.toys||0),0);for(let i=0;i<Math.min(5,toys);i++){const x=-280+i*26;round(g,x,137,16,14,4,'#d6b374');ellipse(g,x+3,153,3,3,'#253e40');ellipse(g,x+13,153,3,3,'#253e40');}}
    g.restore();
    const recent=bubbleEvents.filter(e=>e.until>performance.now()&&e.room===room&&hitboxes[e.bird]);
    const chosen=[...new Map(recent.map(e=>[e.bird,e])).values()].slice(w<600?-1:-3),occupied=[];
    for(const e of chosen){const box=hitboxes[e.bird],width=Math.min(200,w-32);let x=Math.max(12,Math.min(w-width-12,box.x-width/2)),y=Math.max(210,box.y-125);
      for(const other of occupied)if(Math.abs(x-other.x)<width&&Math.abs(y-other.y)<83)y=other.y-86;
      y=Math.max(205,y);occupied.push({x,y});
      round(g,x,y,width,78,12,e.kind==='thought'?'#dce9e7f0':'#fff4dff2','#8a9a8655');
      g.fillStyle='#365851';g.textAlign='left';g.font='bold 11px Segoe UI';g.fillText((e.kind==='thought'?'○ ':e.kind==='user'?'':'♫ ')+heading(e),x+10,y+17);
      g.font='12px Segoe UI';const words=e.text.split(/\s+/);let lineText='',lines=[];
      for(const word of words){if(g.measureText(lineText+' '+word).width>width-20&&lineText){lines.push(lineText);lineText=word;}else lineText+=(lineText?' ':'')+word;}if(lineText)lines.push(lineText);
      for(let i=0;i<Math.min(3,lines.length);i++)g.fillText(lines[i].slice(0,65)+(i===2&&lines.length>3?'…':''),x+10,y+34+i*14);
    }
  }
  $('tinker').onclick=()=>act('tinker');$('sharePart').onclick=()=>act('share_part',$('shareFriend').value);$('shareFriend').onchange=()=>update();
  function speakReply(text,birdKey,force=false){
    if((!readReplies&&!force)||!synth||document.hidden)return;
    stop();queued.push({bird:birdKey,text,kind:'reply',force});nextVoice();
  }
  $('readReplies').checked=readReplies;
  $('readReplies').onchange=()=>{readReplies=$('readReplies').checked;try{localStorage.setItem('little-flock-read-replies',readReplies?'on':'off');}catch{}if(!readReplies&&activeEvent?.kind==='reply')stop();};
  $('replayReply').onclick=()=>{const reply=state?.chats.filter(e=>e.bird===selected&&e.role==='assistant').at(-1);if(reply){speakReply(reply.text,selected,true);}else toast('Send your bird a message first.');};
  $('voices').disabled=!synth;$('voices').onclick=()=>{enabled=!enabled;stop();status();if(enabled&&localVoices().length){queued.push({bird:selected,text:'Voice circuits online. Hello, technician.'});nextVoice();}};
  synth?.addEventListener('voiceschanged',status);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});window.addEventListener('pagehide',stop);
  status();update();return {update,draw,speakReply};
})();
