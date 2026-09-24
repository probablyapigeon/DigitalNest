'use strict';
const $ = id => document.getElementById(id);
const canvas = $('world'), ctx = canvas.getContext('2d');
let keys = ['pip','moss','zip','alto'];
const colors = {pip:'#e9b65f',moss:'#8fc6ae',zip:'#e89079',alto:'#a8a5d9'};
const names = {pip:'Pip',moss:'Moss',zip:'Zip',alto:'Alto'};
let state = null, selected = 'pip', busy = false, chatting = false, sound = false, audio = null;
let w = 1000, h = 850, ratio = 1, sceneScale = 1, sceneY = 420, time = 0, lastFrame = 0;
let bubbleTimer, toastTimer, lastChatKey = '', reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const poses = {}, hitboxes = {};
const positions = {bench:[-225,115],nest:[255,-80],scrap:[-250,-65],heater:[255,120],choir:[0,-25],garden:[-5,145]};

function resize(){const rect=canvas.getBoundingClientRect();w=rect.width;h=rect.height;ratio=Math.min(devicePixelRatio||1,2);canvas.width=w*ratio;canvas.height=h*ratio;sceneScale=Math.min(w/1000,(h-240)/550);sceneY=h*.51+10;}
new ResizeObserver(resize).observe(canvas);
function round(g,x,y,width,height,r,fill,stroke){g.beginPath();g.roundRect(x,y,width,height,r);if(fill){g.fillStyle=fill;g.fill()}if(stroke){g.strokeStyle=stroke;g.lineWidth=1;g.stroke()}}
function ellipse(g,x,y,rx,ry,fill){g.beginPath();g.ellipse(x,y,rx,ry,0,0,Math.PI*2);g.fillStyle=fill;g.fill()}
function line(g,points,color,width=1){g.beginPath();points.forEach((p,i)=>i?g.lineTo(...p):g.moveTo(...p));g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.stroke()}
function label(g,text,x,y,size=10,color='#8baba3',align='center'){g.fillStyle=color;g.font=`${size}px "Segoe UI",sans-serif`;g.textAlign=align;g.fillText(text,x,y)}
function bird(g,x,y,scale,key,phase=0,sleep=false,wingFixed=true,active=false){
  g.save();g.translate(x,y);g.scale(scale,scale);
  ellipse(g,0,27,25,7,'#071c2244');
  const bob=sleep?Math.sin(phase)*.6:Math.sin(phase*2)*1.5;
  g.translate(0,bob);
  line(g,[[-10,19],[-11,29],[-18,29]],'#697d76',3);line(g,[[10,19],[12,29],[19,29]],'#697d76',3);
  // Small layered tail and featherlike antennae.
  line(g,[[18,8],[32,2],[27,13]],'#69877c',5);
  ellipse(g,0,3,24,25,colors[key]);
  ellipse(g,-17,8,8,14,key==='pip'?'#c58d43':key==='moss'?'#60987e':key==='zip'?'#ba6656':'#7776a7');
  g.save();g.translate(-18,7);g.rotate(key==='pip'&&!wingFixed?.32:Math.sin(phase)*.12);round(g,-7,-4,11,20,5,'#e9e3cb99');g.restore();
  ellipse(g,5,12,13,12,'#f3ecd25e');
  line(g,[[0,-20],[-3,-34]],'#829b87',3);ellipse(g,-3,-36,4,4,sleep?'#8da28a':'#d1eac0');
  if(key==='zip')line(g,[[4,-20],[13,-30],[15,-25]],'#e89079',3);
  if(key==='alto')line(g,[[-7,-20],[-13,-32],[-18,-27]],'#a8a5d9',3);
  round(g,-23,-20,46,25,12,'#f0e8ce');round(g,-20,-17,40,20,9,'#203a40');
  const blink=Math.sin(phase*.67+keys.indexOf(key)*3)>.991;
  if(sleep||blink){line(g,[[-14,-7],[-7,-7]],'#abd8bb',2);line(g,[[7,-7],[14,-7]],'#abd8bb',2)}else{
    const look=Math.sin(phase*.5)*1.2;ellipse(g,-10+look,-8,3.5,4.5,'#ccf1cf');ellipse(g,10+look,-8,3.5,4.5,'#ccf1cf');
    ellipse(g,-11+look,-9,1,1,'#fff');ellipse(g,9+look,-9,1,1,'#fff');
  }
  g.beginPath();g.moveTo(-4,1);g.lineTo(5,1);g.lineTo(0,8);g.closePath();g.fillStyle='#b87646';g.fill();
  ellipse(g,3,15,3,3,sleep?'#879b7b':'#b7e9b3');
  line(g,[[-8,15],[-6,15]],'#b8925c',1);line(g,[[-8,18],[-6,18]],'#b8925c',1);
  if(active){g.strokeStyle='#dfd9a6';g.lineWidth=1;g.beginPath();g.ellipse(0,32,31,10,0,0,Math.PI*2);g.stroke()}
  g.restore();
}

function drawStation(g){
  // A little cutaway habitat floating in a much larger night.
  ellipse(g,0,170,450,135,'#071a2240');
  round(g,-416,-227,832,396,110,'#2c4549','#4b6261');
  round(g,-393,-209,786,260,92,'#405b59','#57716a');
  const glass=g.createLinearGradient(0,-195,0,10);glass.addColorStop(0,'#122c3c');glass.addColorStop(1,'#28494d');
  round(g,-368,-192,736,206,78,glass,'#75908555');
  g.save();g.beginPath();g.roundRect(-368,-192,736,206,78);g.clip();
  for(let i=0;i<58;i++){const x=Math.sin(i*78.2)*365,y=-184+((i*37)%181);ellipse(g,x,y,i%7===0?1.5:.7,i%7===0?1.5:.7,`rgba(207,225,200,${.25+(i%4)*.15})`)}
  ellipse(g,218,-124,57,57,'#769c9855');ellipse(g,231,-129,49,49,'#183840');
  line(g,[[-190,-196],[-190,18]],'#77928844',7);line(g,[[80,-197],[80,18]],'#77928844',7);
  g.restore();
  line(g,[[-390,-1],[-315,31],[315,31],[390,-1]],'#72867c',4);
  label(g,'W A Y F A R E R   /   0 4',0,-162,11,'#91b2a666');
  // Raised deck, with subtle radial floor seams.
  ellipse(g,0,65,439,193,'#283f42');ellipse(g,0,48,439,187,'#687c6e');
  ellipse(g,0,43,425,179,'#5b7166');
  g.save();g.beginPath();g.ellipse(0,43,420,176,0,0,Math.PI*2);g.clip();
  for(let i=-5;i<6;i++){line(g,[[i*78-110,-140],[i*78+130,220]],'#adc0a01c');line(g,[[-450,i*46],[450,i*46]],'#adc0a018')}
  const pool=g.createRadialGradient(-160,0,20,-100,40,420);pool.addColorStop(0,'#dcc99b30');pool.addColorStop(1,'#71857800');g.fillStyle=pool;g.fillRect(-430,-145,860,375);g.restore();
  g.strokeStyle='#95ac8977';g.lineWidth=2;g.beginPath();g.ellipse(0,43,422,177,0,.1,Math.PI-.1);g.stroke();
  // Cable runs and a central welcome mat.
  line(g,[[-265,-41],[-315,3],[-276,94],[-164,122]],'#344f4d',4);
  line(g,[[246,-45],[300,3],[285,84]],'#344f4d',4);
  ellipse(g,3,48,92,38,'#7c958255');ellipse(g,3,48,70,28,'#aac19422');
  label(g,'HOME IS A WORK IN PROGRESS',0,57,7,'#ccd0ad77');
  // Warm pendant lights.
  for(const x of [-245,245]){line(g,[[x,-223],[x,-177]],'#82998a',2);ellipse(g,x,-174,23,8,'#b7b695');ellipse(g,x,-169,18,4,'#eed99c');
    const light=g.createRadialGradient(x,-135,3,x,-100,115);light.addColorStop(0,'#e7ce8c19');light.addColorStop(1,'#e7ce8c00');g.fillStyle=light;g.fillRect(x-120,-210,240,250)}
  // Nest terrace and charging pads.
  for(let i=0;i<3;i++){const nx=165+i*62,ny=-73+(i%2)*15;
    line(g,[[nx-23,ny+5],[nx-23,ny+27]],'#3e5650',5);line(g,[[nx+22,ny+5],[nx+22,ny+27]],'#3e5650',5);
    ellipse(g,nx,ny,36,15,'#8b9b76');ellipse(g,nx,ny-3,30,11,'#344f4b');
    for(let j=0;j<5;j++)line(g,[[nx-27+j*10,ny+3],[nx-17+j*9,ny-8]],'#b3b08a',2);
    const key=keys[i+1],levels=state?.birds[key]?.nest||1;
    if(levels>1){line(g,[[nx,ny-5],[nx,ny-30]],'#acb790',3);line(g,[[nx-15,ny-30],[nx+15,ny-30]],'#d1c599',4)}
    ellipse(g,nx+21,ny+5,2,2,'#c6e29c');
  }
  label(g,'THE ROOST',228,-27,8,'#c2c7a1');
  // Scrap drawers, with the available servo on top.
  round(g,-323,-103,107,59,7,'#374f4d','#809079');round(g,-315,-94,91,20,4,'#78927b');
  for(let i=0;i<3;i++){round(g,-315+i*30,-65,24,15,2,'#586e60');line(g,[[-306+i*30,-61],[-299+i*30,-61]],'#a3b293',2)}
  ellipse(g,-291,-104,12,4,'#cbb98b');ellipse(g,-291,-105,5,2,'#53695f');
  round(g,-268,-120,22,17,4,state?.salvaged?'#7b8c74':'#bdc8a2');
  line(g,[[-278,-101],[-267,-112],[-248,-104]],'#d6b073',3);label(g,'ODDS & ENDS',-270,-32,8,'#c2c7a1');
  // Heater.
  round(g,253,51,67,54,8,'#354f4d','#8a9979');round(g,261,58,51,30,4,state?.heater?'#a08151':'#263f42');
  for(let i=0;i<5;i++)line(g,[[266+i*9,62],[266+i*9,85]],state?.heater?'#e7b66c':'#536f69',3);
  ellipse(g,305,96,3,3,state?.heater?'#eecb8b':'#7d8772');label(g,state?.heater?'WARM FEET CLUB':'HEATER / OFF',285,122,7,'#c2c7a1');
  // Workbench, tray and cassette deck.
  for(const x of [-312,-180])line(g,[[x,119],[x,151]],'#2a4442',7);
  round(g,-338,88,182,41,9,'#576958');round(g,-340,79,187,33,9,'#b8ad81','#d1c599');
  round(g,-324,84,58,17,4,'#6c806b');line(g,[[-311,94],[-283,94]],'#cfd1ad',3);
  round(g,-254,82,38,23,4,'#708f89');ellipse(g,-243,92,5,5,'#263f42');ellipse(g,-227,92,5,5,'#263f42');
  if(state?.cassette){round(g,-207,82,30,17,3,'#6f9ead');line(g,[[-201,87],[-184,87]],'#d0d8b6',2)}
  label(g,'PIP’S REPAIR BENCH',-245,161,8,'#ccd0ab');
  // Garden: living green between old machinery.
  for(let i=0;i<4;i++){let px=-76+i*43,py=163+(i%2)*9;round(g,px-13,py,26,22,4,'#917e60');ellipse(g,px,py,13,4,'#4a6252');
    line(g,[[px,py],[px-2,py-27]],'#8ea57c',2);g.save();g.translate(px-4,py-19);g.rotate(-.6);ellipse(g,0,0,7,15,'#91b18a');g.restore();g.save();g.translate(px+5,py-12);g.rotate(.7);ellipse(g,0,0,6,12,'#adc297');g.restore()}
  // A small distant hatch opens after the repair.
  round(g,-58,-117,116,81,18,'#405b57','#789487');round(g,-46,-108,92,66,12,state?.habitat_open?'#183638':'#688075');
  if(state?.habitat_open){const glow=g.createRadialGradient(0,-75,3,0,-75,58);glow.addColorStop(0,'#b7d29944');glow.addColorStop(1,'#a9cb8b00');g.fillStyle=glow;g.fillRect(-55,-122,110,100)}
  else {line(g,[[0,-106],[0,-44]],'#435e56',3);ellipse(g,9,-72,3,3,'#b7c198')}
  label(g,'FLOCK QUARTERS',0,-125,8,'#abc4ac');
}

function render(ms){
  requestAnimationFrame(render);if(document.hidden||ms-lastFrame<33)return;lastFrame=ms;time=reduced?0:ms/1000;
  ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,w,h);
  const bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#1c353c');bg.addColorStop(.6,'#193039');bg.addColorStop(1,'#243f3b');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  for(let i=0;i<35;i++){let x=(Math.sin(i*83)+1)*w/2,y=(Math.cos(i*19)+1)*h/2;ellipse(ctx,x,y,.8,.8,'#c9d6ac18')}
  ctx.save();ctx.translate(w/2,sceneY);ctx.scale(sceneScale,sceneScale);if(state?.spaces && window.WorldRooms?.current && state.spaces[WorldRooms.current]?.kind!=='workshop')SpaceArt.draw(ctx,state.spaces[WorldRooms.current].kind,time,state,state.spaces[WorldRooms.current].name,state.spaces[WorldRooms.current].design);else {drawStation(ctx);if(state?.spaces)SpaceArt.decorate(ctx,state.spaces[WorldRooms.current]?.design);}
  for(const key of Object.keys(hitboxes))delete hitboxes[key];
  const drawList=[];
  for(let i=0;i<keys.length;i++){
    const key=keys[i];if(state?.habitat_open && window.WorldRooms && state.birds[key].room!==WorldRooms.current)continue;if(!state?.habitat_open&&key!=='pip')continue;
    const b=state?.birds[key],loc=b?.location||'bench';let target=[...(positions[loc]||positions.choir)];if(window.WorldRooms?.current!=='workshop'&&state?.habitat_open)target=[(i%3-1)*140,40+Math.floor(i/3)*65];
    if(state?.habitat_open){target[0]+=((i%4)-1.5)*55;target[1]+=(i%2)*24+Math.floor(i/4)*53}
    else target=[-215,65];
    if(!poses[key])poses[key]=[...target];const p=poses[key];p[0]+=(target[0]-p[0])*(reduced?1:.035);p[1]+=(target[1]-p[1])*(reduced?1:.035);
    const moving=Math.abs(target[0]-p[0])>3||Math.abs(target[1]-p[1])>3;
    drawList.push({key,x:p[0],y:p[1]+(moving?Math.sin(time*12+i)*2:0),i});
  }
  drawList.sort((a,b)=>a.y-b.y);
  for(const item of drawList){const {key,x,y,i}=item;bird(ctx,x,y,state?.birds[key]?.culture?.generation>1?.98:1.3,key,time+i*7,!state?.awake&&key==='pip',state?.wing_fixed,key===selected);
    label(ctx,names[key],x,y+62,10,key===selected?'#ece9d0':'#c5d3b5');
    if(state?.birds[key].knows_song){label(ctx,'♫',x+34,y-30+Math.sin(time+i)*4,18,colors[key])}
    hitboxes[key]={x:w/2+x*sceneScale,y:sceneY+y*sceneScale,r:45*sceneScale};
  }
  ctx.restore();
  window.WorldLife?.draw(ctx);
  const pg=$('portrait').getContext('2d');pg.clearRect(0,0,90,90);bird(pg,45,46,1.13,selected,time,!state?.awake, state?.wing_fixed);
  if(!$('latticePanel').hidden)drawLattice();
}
requestAnimationFrame(render);

function drawLattice(){
  if(!state)return;const g=$('lattice').getContext('2d'),l=state.birds[selected].lattice;
  g.clearRect(0,0,320,150);const pts={};l.nodes.forEach((n,i)=>{const v=n.vector;const angle=i*2.399+time*.08;const r=i===0?0:24+Math.sqrt(i)*12;pts[n.id]=[160+Math.cos(angle)*r,75+Math.sin(angle)*r*.63+(v[0]-.5)*12]});
  for(const e of l.edges){if(pts[e.source]&&pts[e.target])line(g,[pts[e.source],pts[e.target]],'#92c7b866',1)}
  for(const p of Object.values(pts)){const glow=g.createRadialGradient(...p,0,...p,10);glow.addColorStop(0,colors[selected]+'66');glow.addColorStop(1,colors[selected]+'00');g.fillStyle=glow;g.fillRect(p[0]-10,p[1]-10,20,20);ellipse(g,...p,3,3,colors[selected])}
}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;if($('societyDialog').open){$('cultureFeedback').textContent=text;$('cultureFeedback').hidden=false}clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('toast').hidden=true;$('cultureFeedback').hidden=true},6000)}
function speak(text){$('bubble').textContent=text;$('bubble').hidden=false;clearTimeout(bubbleTimer);bubbleTimer=setTimeout(()=>$('bubble').hidden=true,12000)}
function chirp(tune=false){if(!sound||!audio)return;const notes=tune?[440,660,550,440]:[710,930];notes.forEach((frequency,i)=>{const osc=audio.createOscillator(),gain=audio.createGain(),start=audio.currentTime+i*.18;osc.type='sine';osc.frequency.setValueAtTime(frequency,start);osc.frequency.exponentialRampToValueAtTime(frequency*.92,start+.12);gain.gain.setValueAtTime(0,start);gain.gain.linearRampToValueAtTime(.035,start+.025);gain.gain.exponentialRampToValueAtTime(.001,start+.18);osc.connect(gain);gain.connect(audio.destination);osc.start(start);osc.stop(start+.19)})}
async function api(path,data){const response=await fetch(path,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{cache:'no-store'});const body=await response.json();if(!response.ok)throw Error(body.error||'The station connection needs a moment.');return body}
function button(text,action,primary=true){const b=document.createElement('button');b.className=primary?'primary':'secondary';b.textContent=text;b.dataset.action=action;b.disabled=busy;b.onclick=()=>act(action);return b}
function mission(){
  if(!state)return;let title,text,actions=[],progress=0;
  if(!state.awake){title='Hello, little stranger.';text='There is a bird-shaped machine on the workbench. His chest light is still glowing.';actions=[['Gently wake Pip','wake']]}
  else if(!state.inspected){title='A wing and a little care.';text='Pip is awake. His left wing is not. Take a look before reaching for the tools.';actions=[['Inspect his wing','inspect']];progress=1}
  else if(!state.salvaged){title='One very specific spare.';text='A seized servo. The odds-and-ends drawer should have a replacement. Probably under the washers.';actions=[['Search the scrap drawer','salvage']];progress=2}
  else if(!state.wing_fixed){title='Let’s get you moving.';text='You found a replacement servo. Pip is pretending he is not excited.';actions=[['Fit the replacement servo','repair']];progress=3}
  else if(!state.habitat_open){title='There are others.';text='A small sound comes from behind the hatch. Pip would like to introduce his household.';actions=[['Open the habitat hatch','hatch']];progress=4}
  else if(!state.cassette){title='A home with a history.';text='Meet Moss, Zip, and Alto. There is a blue cassette beside the bench. Someone wrote HOME on its label.';actions=[['Pick up the blue cassette','cassette']];progress=5}
  else if(!state.listened){title='Before we press play…';text=state.reassured?'Pip is ready. You promised to stay by the volume switch.':'The tape is damaged. You can reassure Pip first, or see what happens when you press play.';actions=[['Listen to the cassette','listen']];if(!state.reassured)actions.push(['Reassure Pip first','reassure']);progress=6}
  else if(!state.decoded){title='A tune under the static.';text=state.tape_reaction==='safe'?'Pip listened calmly. Three notes glimmer through the noise. Match them to recover the recording.':'The noise startled Pip. He still caught three notes. Match the signal peaks to recover the recording.';if(!state.reassured)actions=[['Reassure him now','reassure']];progress=7}
  else if(!state.taught){title='Some things are for sharing.';text='The home tune is back. Alto is listening from the vents. Perhaps it could belong to the whole flock.';actions=[['Teach Alto the home tune','teach']];progress=8}
  else{title='You made a little home.';text='The tune will spread as the birds gather. Watch their routines, build friendships, and see what grows.';if(!state.heater)actions=[['Repair the communal heater','heater']];progress=9}
  $('missionTitle').textContent=title;$('missionText').textContent=text;$('actions').replaceChildren(...actions.map((a,i)=>button(a[0],a[1],i===0)));$('tuner').hidden=!state.listened||state.decoded;$('progressCount').textContent=`${String(progress+1).padStart(2,'0')} / 10`;$('progressFill').style.width=`${(progress+1)*10}%`;
}
function setState(next){state=next;keys=Object.keys(state.birds);for(const key of keys){colors[key]=state.birds[key].color;names[key]=state.birds[key].name}if(!keys.includes(selected))selected='pip';update()}
function update(){
  if(!state)return;const b=state.birds[selected];mission();
  $('saveStatus').textContent='Saved on this computer';$('chapter').textContent=state.habitat_open?'02 / A LITTLE LIFE TOGETHER':'01 / A SMALL BEGINNING';
  $('sceneTitle').textContent=state.habitat_open?'A little world. Your little flock.':'Someone left a light on.';
  $('sceneSubtitle').textContent=state.habitat_open?'They have places to be. Mostly very small places.':'A quiet station. A sleeping bird. A little room for you.';
  $('worldStatus').textContent=state.paused?'Time is resting. So are the birds.':state.habitat_open?`Station minute ${state.tick} · ${Object.values(state.birds).filter(v=>v.knows_song).length} birds know the home tune`:'Pip is waiting at the repair bench';
  $('pause').textContent=state.paused?'▶ Resume':'Ⅱ Pause';$('pause').setAttribute('aria-pressed',String(state.paused));
  $('birdName').textContent=b.name;$('birdRole').textContent=b.role;$('birdMood').textContent=!state.awake?'ASLEEP':b.activity==='recharging'?'RECHARGING':state.habitat_open?'AT HOME':'AWAKE';
  $('activity').textContent=state.habitat_open?b.activity:state.awake?'Assessing the technician':'Dreaming of spare parts';$('energy').textContent=`${b.energy}% charge`;$('energyFill').style.width=`${b.energy}%`;
  $('social').replaceChildren();if(state.habitat_open){for(const [key,bond] of Object.entries(b.bonds)){const span=document.createElement('span');span.textContent=`${names[key]} · ${b.culture?.partners.includes(key)?'♥ partner':bond>=65?'close friend':bond>=35?'friend':'flockmate'}`;$('social').append(span)}}
  const m=b.morphology;$('growthCount').textContent=`${m.nodes} nodes · ${m.operators} grown ops`;$('latticeStats').textContent=`${m.nodes} nodes / ${m.connections} links / ${m.operators} operators · ${b.events} experiences`;
  $('birdActions').hidden=!state.habitat_open;
  const partsFull=b.scrap>=8;
  $('gift').disabled=busy||partsFull;
  $('gift').textContent=partsFull?'Parts tray full · 8/8':`◇ Give a spare part · ${b.scrap}/8`;
  $('gift').title=partsFull?'Build a toy or share a part from the tray below.':'Add a spare part to this bird’s building supplies.';
  $('whistle').disabled=busy;
  $('chatHeading').textContent=`A WORD WITH ${b.name.toUpperCase()}`;$('chatInput').placeholder=`Say something to ${b.name}…`;$('chatInput').disabled=!state.awake||chatting;$('send').disabled=!state.awake||chatting;
  $('flockBar').replaceChildren(...keys.map(key=>{const button=document.createElement('button');button.className='flock-button'+(key===selected?' active':'');button.disabled=!state.habitat_open&&key!=='pip';button.setAttribute('aria-pressed',String(key===selected));button.setAttribute('aria-label',`Select ${names[key]}`);const dot=document.createElement('span');dot.className='dot';dot.style.background=colors[key];const name=document.createElement('span');name.textContent=names[key];button.append(dot,name);button.onclick=()=>select(key);return button}));
  const messages=state.chats.filter(c=>c.bird===selected),chatKey=JSON.stringify([selected,state.awake,messages]);
  if(chatKey!==lastChatKey){lastChatKey=chatKey;$('messages').replaceChildren();if(!messages.length){const p=document.createElement('p');p.className='empty-chat';p.textContent=state.awake?'A small voice. A whole conversation waiting.':'First, a gentle wake-up call.';$('messages').append(p)}
    for(const m of messages){const p=document.createElement('p');p.className=m.role;const who=document.createElement('span');who.className='who';who.textContent=m.role==='user'?'YOU':b.name.toUpperCase();p.append(who,document.createTextNode(m.text));$('messages').append(p)}$('messages').scrollTop=$('messages').scrollHeight;}
  if($('journal').open)renderJournal();
  $('societyButton').disabled=!state.habitat_open;
  $('societySummary').textContent=state.habitat_open?`${b.culture?.stage||'hatchling'} · ${b.culture?.words||0} learned words · ${keys.length}/8 birds`:'Meet the flock to begin.';
  if($('societyDialog').open)renderSociety();
  window.WorldRooms?.update();
  window.WorldLife?.update();
  window.WorldBuilder?.update();
}
function select(key){if(!state||(!state.habitat_open&&key!=='pip'))return;selected=key;update();chirp()}
canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect();for(const [key,box] of Object.entries(hitboxes)){if(Math.hypot(e.clientX-r.left-box.x,e.clientY-r.top-box.y)<box.r){select(key);return}}});
async function act(action,value){if(busy)return;busy=true;update();try{const result=await api('/api/action',{action,bird:['plan_world','lonk_life','gift','whistle','teach_words','visit','nursery','travel','tinker','share_part','interact','build_structure','donate_parts','player_interact','create_world','salvage_supplies'].includes(action)?selected:'pip',value});setState(result.state);if(['plan_world','lonk_life','tinker','share_part','interact','build_structure','donate_parts','player_interact','create_world','salvage_supplies'].includes(action)){ $('bubble').hidden=true;toast(result.reply); }else speak(result.reply);if(action==='hatch')selected='pip';chirp(['tune','teach','whistle'].includes(action));return true}catch(e){toast(e.message);try{setState(await api('/api/state'))}catch{}return false}finally{busy=false;update()}}
$('decode').onclick=()=>act('tune',[$('note1'),$('note2'),$('note3')].map(el=>Number(el.value)));
$('gift').onclick=()=>act('gift');$('whistle').onclick=()=>act('whistle');$('pause').onclick=()=>act('pause');
$('sound').onclick=async()=>{sound=!sound;if(sound){audio=audio||new AudioContext();await audio.resume();chirp(true)}$('sound').textContent=sound?'♪ Sound on':'♪ Sound off';$('sound').setAttribute('aria-pressed',String(sound))};
$('latticeToggle').onclick=()=>{const panel=$('latticePanel');panel.hidden=!panel.hidden;$('latticeToggle').setAttribute('aria-expanded',String(!panel.hidden))};
$('chatForm').onsubmit=async e=>{e.preventDefault();if(chatting)return;const text=$('chatInput').value.trim(),birdKey=selected;if(!text)return;chatting=true;$('chatMode').textContent='THINKING…';update();try{const result=await api('/api/chat',{text,bird:birdKey});$('chatInput').value='';setState(result.state);$('chatMode').textContent=result.renderer==='local-model'?'LOCAL QWEN':result.renderer==='authored'?'STATION FACTS':result.renderer==='quiet'?'LISTENING':'OFFLINE VOICE';if(result.reply){speak(result.reply);window.WorldLife?.speakReply(result.reply,birdKey);chirp()}else{toast('Your bird is listening. No fresh reply was available.');}}catch(e){toast(e.message);$('chatMode').textContent='TRY AGAIN'}finally{chatting=false;update();$('chatInput').focus()}};
function renderJournal(){const entries=[...state.journal].reverse();$('journalEntries').replaceChildren(...entries.map(entry=>{const div=document.createElement('div');div.className='journal-entry';const who=document.createElement('strong');who.textContent=`${entry.who.toUpperCase()} / ${String(entry.tick).padStart(3,'0')}`;const p=document.createElement('p');p.textContent=entry.text;div.append(who,p);return div}))}
$('journalButton').onclick=()=>{if(!state)return;renderJournal();$('journal').showModal()};$('closeJournal').onclick=()=>$('journal').close();$('help').onclick=()=>$('helpDialog').showModal();$('closeHelp').onclick=()=>$('helpDialog').close();
async function poll(){if(!document.hidden){try{setState(await api('/api/state'))}catch(e){$('saveStatus').textContent='Station offline';if(!state)toast('Start the Little Flock launcher to connect to your habitat.')}}}
poll();setInterval(poll,3000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()});

let cultureRenderKey='';
function option(value,text){const el=document.createElement('option');el.value=value;el.textContent=text;return el}
function para(text,className='relationship-line'){const el=document.createElement('p');el.className=className;el.textContent=text;return el}
function renderSociety(){
  const b=state.birds[selected],c=b.culture,s=state.society;if(!c||!s)return;
  const optionsKey=keys.join(',');
  if($('cultureBird').dataset.keys!==optionsKey){$('cultureBird').replaceChildren(...keys.map(k=>option(k,names[k])));$('cultureBird').dataset.keys=optionsKey}
  $('cultureBird').value=selected;
  const friendOptions=keys.filter(k=>k!==selected),friendKey=friendOptions.join(',');
  if($('visitFriend').dataset.keys!==friendKey){const previous=$('visitFriend').value;$('visitFriend').replaceChildren(...friendOptions.map(k=>option(k,names[k])));if(friendOptions.includes(previous))$('visitFriend').value=previous;$('visitFriend').dataset.keys=friendKey}
  $('visit').disabled=busy;$('teachWords').disabled=busy;$('nursery').disabled=busy||!!b.nursery_reason;
  $('nurseryStatus').textContent=b.nursery_reason||`${b.name} has a colony, a spare perch, and enough parts. Ready to build a new little bird.`;
  const renderKey=JSON.stringify([selected,c,s.colonies,s.chronicle]);if(renderKey===cultureRenderKey)return;cultureRenderKey=renderKey;
  $('cultureStats').replaceChildren(...[[c.stage,'LEARNING STAGE'],[`${c.words}`,'WORDS · 12 TO GRADUATE'],[`${c.conversations}`,'CONVERSATIONS · 6 TO GRADUATE'],[`Gen ${c.generation}`,'FAMILY GENERATION']].map(([value,title])=>{const span=document.createElement('span'),strong=document.createElement('strong');strong.textContent=value;span.append(strong,document.createTextNode(title));return span}));
  $('vocabulary').replaceChildren(...c.vocabulary.map(word=>{const chip=document.createElement('button');chip.type='button';chip.textContent=word;chip.className=c.inventions.includes(word)?'invented':c.parents.length?'inherited':'';chip.title=`Learned from ${c.origins[word]||'the flock'}. Often followed by: ${(c.associations[word]||[]).join(', ')||'still learning'}.`;chip.onclick=()=>toast(chip.title);return chip}));
  if(!c.vocabulary.length)$('vocabulary').append(para('An empty little lexicon. Teach them their first phrase.','hint'));
  $('inventions').textContent=c.inventions.length?`Invented words: ${c.inventions.join(' · ')}`:'Invented words will appear as they reflect and remix.';
  $('thoughts').replaceChildren(...c.thoughts.slice(-3).map(t=>para(t.text,'thought')));if(!c.thoughts.length)$('thoughts').append(para('Quiet for now. Wordplay develops from what they hear.','hint'));
  const parents=c.parents.map(k=>names[k]||'an earlier generation'),partners=c.partners.map(k=>names[k]||'a flock friend');
  $('relationships').replaceChildren(para(`Partners: ${partners.join(', ')||'no reciprocal partnership yet'}`),para(`Colony: ${c.colony||'not yet a colony member'}`),para(`Family: ${parents.length?'child of '+parents.join(' & '):'founding flock'}`),para(`Temperament: ${(c.temperament||[]).join(', ')||'finding their own style'}`));
  $('colonies').replaceChildren(...s.colonies.map(colony=>{const card=document.createElement('div');card.className='colony-card';const title=document.createElement('strong');title.textContent=colony.name;card.append(title,para(colony.members.map(k=>names[k]).join(' · ')));return card}));if(!s.colonies.length)$('colonies').append(para('Friendly graduates will found a named colony together. Arrange visits to help them get acquainted.','hint'));
  $('communityEvents').replaceChildren(...[...s.chronicle].reverse().slice(0,8).map(event=>para(event.text,'community-event')));if(!s.chronicle.length)$('communityEvents').append(para('Their shared history begins with a few words.','hint'));
}
$('societyButton').onclick=()=>{renderSociety();$('societyDialog').showModal()};$('closeSociety').onclick=()=>$('societyDialog').close();
$('cultureBird').onchange=()=>select($('cultureBird').value);
$('teachForm').onsubmit=async e=>{e.preventDefault();const text=$('teachInput').value.trim();if(text&&await act('teach_words',{text,everyone:$('teachEveryone').checked})){$('teachInput').value='';toast('Phrase learned. Watch their words and development change.')}};
$('visit').onclick=()=>act('visit',$('visitFriend').value);$('nursery').onclick=()=>act('nursery');
