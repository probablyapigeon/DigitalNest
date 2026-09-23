window.WorldBuilder=(()=>{
  let inspected=null, topology='';
  const host=document.createElement('div');
  host.innerHTML=`
    <dialog id="objectInspector" class="build-dialog"><div class="dialog-heading"><h2 id="inspectTitle">An object</h2><button class="icon-button" data-close="objectInspector" aria-label="Close object">Close</button></div><p id="inspectDescription"></p><p id="inspectSupplies"></p><button id="useObjectSelf" class="primary">Use myself</button><p id="selfReason" class="hint"></p><button id="useObjectBird" class="secondary">Ask bird</button><p id="birdReason" class="hint"></p><button id="inviteObjectBird" class="secondary">Invite bird here</button><p id="objectFeedback" role="status"></p></dialog>
    <dialog id="buildDialog" class="build-dialog"><div class="dialog-heading"><div><span class="eyebrow">A HOME YOU CAN GROW</span><h2 id="buildTitle">Build onto this world</h2></div><button class="icon-button" data-close="buildDialog">Close</button></div><p id="buildSupplies"></p><p>Build a structure or upgrade it to level 3. Birds with completed nests also build using their own parts.</p><button id="salvageBuildParts" class="secondary">Salvage 4 station parts</button><div id="blueprintCards"></div><p id="buildFeedback" role="status"></p></dialog>
    <dialog id="newWorldDialog" class="build-dialog"><div class="dialog-heading"><h2>A new little world</h2><button class="icon-button" data-close="newWorldDialog">Close</button></div><p id="newWorldSupplies"></p><form id="newWorldForm"><label>World name<input id="newWorldName" maxlength="40" required placeholder="Moonberry Meadow" autocomplete="off"></label><label>Scenery and activities<select id="newWorldKind"><option value="garden">Glass garden</option><option value="roost">Moon roost</option><option value="workshop">Workshop</option><option value="commons">Commons</option><option value="archive">Story archive</option><option value="nursery">Little foundry</option></select></label><label>Connect a portal to<select id="newWorldLink"></select></label><button id="createWorldSubmit" class="primary" type="submit">Build new world</button></form><p id="newWorldFeedback" role="status"></p></dialog>`;
  document.body.append(host);
  for(const button of host.querySelectorAll('[data-close]'))button.onclick=()=>$(button.dataset.close).close();
  const donate=document.createElement('button');donate.id='donateParts';donate.className='secondary';donate.textContent='Donate 1 part to world building';donate.onclick=()=>act('donate_parts');$('partsTray').append(donate);
  function inspect(room,id){inspected={room,id};update();$('objectInspector').showModal();}
  function feedback(id,ok){$(id).textContent=ok?'Done. Your changes are saved.':$('toast').textContent;}
  $('useObjectSelf').onclick=async()=>feedback('objectFeedback',await act('player_interact',{room:inspected.room,object:inspected.id}));
  $('useObjectBird').onclick=async()=>feedback('objectFeedback',await act('interact',{room:inspected.room,object:inspected.id}));
  $('inviteObjectBird').onclick=async()=>feedback('objectFeedback',await act('travel',inspected.room));
  $('buildWorld').onclick=()=>{update();$('buildDialog').showModal();};
  $('newWorld').onclick=()=>{update();$('newWorldLink').value=WorldRooms.current;$('newWorldDialog').showModal();};
  $('salvageBuildParts').onclick=async()=>feedback('buildFeedback',await act('salvage_supplies'));
  $('newWorldForm').onsubmit=async event=>{event.preventDefault();const ok=await act('create_world',{name:$('newWorldName').value,kind:$('newWorldKind').value,link:$('newWorldLink').value});if(ok){$('newWorldDialog').close();$('newWorldName').value='';WorldRooms.open(state.last_created_world);update();}else feedback('newWorldFeedback',false);};
  function update(){if(!state?.building)return;const room=WorldRooms.current,b=state.birds[selected],build=state.building;
    $('buildWorld').disabled=$('newWorld').disabled=!state.habitat_open||busy;donate.disabled=busy||b.scrap<1||build.supplies>=999;
    const worldIds=Object.keys(state.spaces),sig=worldIds.join('|');
    if(sig!==topology){topology=sig;const old=$('newWorldLink').value;$('newWorldLink').replaceChildren(...worldIds.map(id=>option(id,state.spaces[id].name)));if(worldIds.includes(old))$('newWorldLink').value=old;}
    $('newWorldSupplies').textContent=`${build.supplies} station parts available. A connected world costs ${build.world_cost} parts. ${worldIds.length}/${build.max_worlds} worlds built.`;
    $('createWorldSubmit').disabled=busy||build.supplies<build.world_cost||worldIds.length>=build.max_worlds;
    $('buildTitle').textContent=`Build in ${state.spaces[room].name}`;
    $('buildSupplies').textContent=`Station supplies: ${build.supplies} parts. ${names[selected]}'s tray: ${b.scrap} parts. New stations start with 24 building parts.`;
    $('salvageBuildParts').disabled=busy||state.tick-(state.last_player_salvage??-10)<2||build.supplies>995;
    $('blueprintCards').replaceChildren(...Object.entries(build.blueprints).map(([id,spec])=>{
      const card=document.createElement('article');card.className='blueprint-card';const level=build.structures[room]?.find(s=>s.type===id)?.level||0;
      const title=document.createElement('h3');title.textContent=`${spec.name}${level?` · Level ${level}`:''}`;
      const text=document.createElement('p');text.textContent=spec.effect;card.append(title,text);
      for(const payer of ['user','bird']){const reason=payer==='user'?build.reasons[room][id].user:build.reasons[room][id].birds[selected];const button=document.createElement('button');button.className='secondary';button.textContent=`${level?'Upgrade':'Build'} ${payer==='user'?'yourself':`with ${names[selected]}`} · ${spec.cost} parts`;button.disabled=busy||!!reason;button.onclick=async()=>feedback('buildFeedback',await act('build_structure',{room,blueprint:id,payer}));card.append(button);if(reason){const hint=document.createElement('small');hint.textContent=reason;card.append(hint);}}
      return card;
    }));
    if(inspected){const item=state.objects[inspected.room]?.find(o=>o.id===inspected.id);if(item){
      $('inspectTitle').textContent=`${item.name} / ${state.spaces[inspected.room].name}`;
      $('inspectDescription').textContent=`${item.label}. ${item.cost?`Uses ${item.cost} parts.`:'No parts needed.'} Used ${item.uses} times.`;
      $('inspectSupplies').textContent=`You: ${build.supplies} station parts. ${names[selected]}: ${b.scrap} parts, currently in ${state.spaces[b.room].name}.`;
      $('useObjectSelf').textContent=`Use myself${item.cost?` - ${item.cost} station parts`:''}`;$('useObjectSelf').disabled=busy||!!item.player_reason;
      $('selfReason').textContent=item.player_reason||'You can operate this object directly, even without a bird here.';
      $('useObjectBird').textContent=`Ask ${names[selected]} to ${item.label.toLowerCase()}`;$('useObjectBird').disabled=busy||!!item.reasons[selected];
      $('birdReason').textContent=item.reasons[selected]||'Ready to use their own parts.';
      $('inviteObjectBird').textContent=`Invite ${names[selected]} here`;$('inviteObjectBird').hidden=b.room===inspected.room;$('inviteObjectBird').disabled=busy;
    }}
  }
  function drawStructures(g,room,logical=true){if(!state?.building)return;
    g.save();if(!logical){g.translate(w/2,sceneY);g.scale(sceneScale,sceneScale);}
    for(const building of state.building.structures[room]||[]){const item=state.objects[room].find(o=>o.id==='built-'+building.type);if(!item)continue;const x=item.x,y=item.y;
      ellipse(g,x,y+17,45,18,'#243d3d66');round(g,x-32,y-11,64,31,8,'#b3b591','#d3d8ad');
      if(building.type==='solar'){line(g,[[x-23,y],[x-23,y-44]],'#9bb3a5',5);line(g,[[x+23,y],[x+23,y-44]],'#9bb3a5',5);round(g,x-39,y-58,78,24,5,'#466f88','#a3c9c5');for(let i=0;i<4;i++)line(g,[[x-28+i*18,y-57],[x-28+i*18,y-35]],'#86bec9',1);}
      else if(building.type==='planter'){for(let i=0;i<4;i++){const px=x-23+i*15;line(g,[[px,y],[px,y-32]],'#648d65',3);ellipse(g,px,y-36,8,9,['#d6ac8c','#e9c96e','#b8a6cf'][i%3]);}}
      else if(building.type==='shelter'){round(g,x-27,y-35,54,41,5,'#b9a382');g.beginPath();g.moveTo(x-40,y-35);g.lineTo(x,y-63);g.lineTo(x+40,y-35);g.closePath();g.fillStyle='#7c9d8d';g.fill();round(g,x-10,y-20,20,28,9,'#3e5a58');}
      else if(building.type==='library'){round(g,x-27,y-52,54,50,4,'#9e8b75');for(let i=0;i<5;i++)round(g,x-21+i*9,y-45,6,32,1,['#d0c08f','#9bb79f','#aaa2bc'][i%3]);}
      else if(building.type==='salvager'){round(g,x-29,y-45,58,40,7,'#809a96');ellipse(g,x-9,y-25,11,11,'#d7bf85');ellipse(g,x+12,y-25,8,8,'#4b6c70');}
      else{line(g,[[x,y],[x,y-64],[x-30,y-64],[x+30,y-64]],'#c8b987',4);for(let i=0;i<4;i++)line(g,[[x-24+i*16,y-64],[x-24+i*16,y-25+(i%2)*10]],'#d9d4a1',5);}
      label(g,'•'.repeat(building.level),x,y+33,13,'#f0d994');
    }g.restore();
  }
  return {inspect,update,drawStructures};
})();
