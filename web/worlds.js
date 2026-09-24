/* World navigation is a view onto the one saved flock, never a second simulation. */
window.WorldRooms = (() => {
  let current='workshop', following=false, signature='';
  const pinned=new Set();
  const coordinates={workshop:[30,235],commons:[345,235],garden:[655,20],roost:[655,450],nursery:[345,450],archive:[30,20]};
  function open(id){if(!state?.spaces[id])return;current=id;following=false;for(const k of Object.keys(poses))delete poses[k];$('worldMap').close();update();window.WorldLife?.update();}
  function preview(canvas,id){const g=canvas.getContext('2d');g.clearRect(0,0,300,150);g.save();g.translate(150,72);g.scale(.32,.26);if(state.spaces[id].kind==='workshop'){drawStation(g);SpaceArt.decorate(g,state.spaces[id].design);}else SpaceArt.draw(g,state.spaces[id].kind,0,state,state.spaces[id].name,state.spaces[id].design);window.WorldBuilder?.drawStructures(g,id,true);for(const [i,key] of state.spaces[id].residents.entries())bird(g,-160+(i%4)*100,55+Math.floor(i/4)*60,.95,key,0,false,true,false);g.restore();}
  function card(id,pin=false){const room=state.spaces[id],el=document.createElement('article');el.className='world-card';el.dataset.room=id;
    if(!pin){const [x,y]=coordinates[id];el.style.left=x+'px';el.style.top=y+'px';}
    const button=document.createElement('button');button.className='world-open';button.setAttribute('aria-label',`Open ${room.name}`);button.onclick=()=>open(id);
    const art=document.createElement('canvas');art.width=300;art.height=150;art.setAttribute('aria-hidden','true');
    const title=document.createElement('strong');title.textContent=room.name;
    const residents=document.createElement('small');residents.textContent=room.residents.map(k=>names[k]).join(' · ')||'A quiet little moment';
    button.append(art,title,residents);el.append(button);preview(art,id);
    if(pin){const close=document.createElement('button');close.className='unpin';close.textContent='×';close.setAttribute('aria-label',`Unpin ${room.name}`);close.onclick=()=>{pinned.delete(id);signature='';update()};el.append(close);}
    if(state.birds[selected].room===id)el.classList.add('bird-here');
    return el;
  }
  function routes(){const svg=$('mapRoutes');svg.replaceChildren();const done=new Set();
    for(const [id,room] of Object.entries(state.spaces))for(const other of room.links){const edge=[id,other].sort().join(':');if(done.has(edge))continue;done.add(edge);
      const a=coordinates[id],b=coordinates[other];const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',`M ${a[0]+135} ${a[1]+95} L ${b[0]+135} ${b[1]+95}`);path.setAttribute('class','portal-route');svg.append(path);
    }
    const crossing=state.birds[selected].crossing;
    if(crossing&&state.tick-crossing.tick<=1){const a=coordinates[crossing.source],b=coordinates[crossing.target];const trail=document.createElementNS('http://www.w3.org/2000/svg','path');trail.setAttribute('d',`M ${a[0]+135} ${a[1]+95} L ${b[0]+135} ${b[1]+95}`);trail.setAttribute('class','bird-trail');svg.append(trail);}
  }
  function update(){if(!state?.spaces)return;
    const available=state.habitat_open;
    for(const id of ['worldMapButton','followBird','inviteBird','pinWorld'])$(id).disabled=!available||busy;
    if(!available){current='workshop';return;}
    const extra=Object.keys(state.spaces).filter(id=>!['workshop','commons','garden','roost','nursery','archive'].includes(id));
    extra.forEach((id,i)=>coordinates[id]=[30+(i%3)*310,680+Math.floor(i/3)*220]);
    const height=680+Math.ceil(extra.length/3)*220;
    $('mapBoard').style.height=height+'px';$('mapRoutes').style.height=height+'px';$('mapRoutes').setAttribute('viewBox',`0 0 960 ${height}`);
    if(following&&current!==state.birds[selected].room){current=state.birds[selected].room;for(const k of Object.keys(poses))delete poses[k];}
    const room=state.spaces[current];
    $('sceneTitle').textContent=room.name;$('sceneSubtitle').textContent=room.subtitle;
    $('followBird').textContent=`${following?'Following':'Follow'} ${names[selected]}`;$('followBird').setAttribute('aria-pressed',String(following));
    $('inviteBird').textContent=`Invite ${names[selected]} here`;
    $('inviteBird').disabled=busy||state.birds[selected].room===current;
    $('pinWorld').textContent=pinned.has(current)?'Unpin world':'Pin world';
    $('worldStatus').textContent=state.paused?'Time is resting. So are the birds.':`${room.residents.length} here · ${names[selected]}: ${state.birds[selected].activity}`;
    const sig=JSON.stringify([current,selected,state.tick,state.paused,keys,state.birds[selected].destination,[...pinned],Object.values(state.spaces).map(r=>[r.residents,r.links]),state.building?.structures]);
    if(sig===signature)return;signature=sig;
    $('portalLinks').replaceChildren(...room.links.map(id=>{const b=document.createElement('button');b.textContent=`↗ ${state.spaces[id].name}`;b.onclick=()=>open(id);return b;}));
    $('mapCards').replaceChildren(...Object.keys(state.spaces).map(id=>card(id)));routes();
    $('pinnedWorlds').hidden=!pinned.size;$('pinnedWorlds').replaceChildren(...[...pinned].map(id=>card(id,true)));
    const b=state.birds[selected];$('journeyStatus').textContent=`${names[selected]} is in ${state.spaces[b.room].name}${b.destination?` · Heading to ${state.spaces[b.destination].name}`:''}. Amber outlines show their current world. Invitations take effect as station time advances.`;
  }
  $('worldMapButton').onclick=()=>{update();$('worldMap').showModal();};$('closeWorldMap').onclick=()=>$('worldMap').close();
  $('followBird').onclick=()=>{following=!following;signature='';update();window.WorldLife?.update();window.WorldBuilder?.update();};
  $('inviteBird').onclick=()=>act('travel',current);
  $('pinWorld').onclick=()=>{if(pinned.has(current))pinned.delete(current);else pinned.add(current);signature='';update();};
  const viewport=$('mapViewport');let drag=null;
  viewport.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag={x:e.clientX,y:e.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.setPointerCapture(e.pointerId);});
  viewport.addEventListener('pointermove',e=>{if(drag){viewport.scrollLeft=drag.left+drag.x-e.clientX;viewport.scrollTop=drag.top+drag.y-e.clientY;}});
  viewport.addEventListener('pointerup',()=>drag=null);viewport.addEventListener('pointercancel',()=>drag=null);
  update();return {get current(){return current;},update,open};
})();
