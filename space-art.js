/* Original procedural room illustrations. Shared by the main view and world-map previews. */
window.SpaceArt = (()=>{
  function box(g,x,y,w,h,r,c,s){g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=c;g.fill();if(s){g.strokeStyle=s;g.lineWidth=1;g.stroke()}}
  function oval(g,x,y,rx,ry,c){g.beginPath();g.ellipse(x,y,rx,ry,0,0,Math.PI*2);g.fillStyle=c;g.fill()}
  function stroke(g,pts,c,w=2){g.beginPath();pts.forEach((p,i)=>i?g.lineTo(...p):g.moveTo(...p));g.strokeStyle=c;g.lineWidth=w;g.lineCap='round';g.stroke()}
  function text(g,s,x,y,c='#c6d1b4',size=9){g.fillStyle=c;g.font=`${size}px Segoe UI,sans-serif`;g.textAlign='center';g.fillText(s,x,y)}
  function plant(g,x,y,size=1){g.save();g.translate(x,y);g.scale(size,size);box(g,-15,0,30,25,5,'#9b8661');oval(g,0,0,15,5,'#405d43');stroke(g,[[0,0],[0,-48]],'#b0c397',3);for(let i=0;i<4;i++){g.save();g.translate(i%2?9:-8,-12-i*9);g.rotate(i%2?.7:-.7);oval(g,0,0,8,17,i%2?'#aecb95':'#78a782');g.restore()}g.restore()}
  function lamp(g,x,y){stroke(g,[[x,y-55],[x,y]],'#8d9c85',2);oval(g,x,y,25,9,'#b9b48d');oval(g,x,y+3,20,5,'#e9d49b')}
  function base(g,id,t){
    const palettes={garden:['#3f655b','#76936c'],roost:['#354659','#667488'],archive:['#51475d','#86766c'],nursery:['#525a4c','#8f9476'],commons:['#604e49','#927e69']};
    const [wall,floor]=palettes[id]||palettes.commons;
    oval(g,0,178,440,105,'#071a2240');box(g,-415,-223,830,380,105,wall,'#a5b49644');
    box(g,-383,-198,766,230,80,'#17333d','#adc3b455');
    g.save();g.beginPath();g.roundRect(-383,-198,766,230,80);g.clip();
    for(let i=0;i<55;i++)oval(g,Math.sin(i*77)*370,-184+(i*41%199),i%8===0?1.7:.7,i%8===0?1.7:.7,'#dbe1b96b');
    if(id==='roost'){oval(g,208,-107,73,73,'#b2c1b6');oval(g,225,-120,66,66,'#17333d');}
    if(id==='garden'){const light=g.createLinearGradient(0,-198,0,32);light.addColorStop(0,'#b9d39a44');light.addColorStop(1,'#7eafa122');g.fillStyle=light;g.fillRect(-383,-198,766,230);for(let i=-2;i<3;i++)stroke(g,[[i*140,-195],[i*170,30]],'#afc1aa66',4);}
    g.restore();oval(g,0,59,440,187,'#243c40');oval(g,0,44,440,181,floor);oval(g,0,39,424,171,wall+'55');
    g.save();g.beginPath();g.ellipse(0,39,420,169,0,0,Math.PI*2);g.clip();for(let i=-5;i<6;i++){stroke(g,[[i*80-110,-135],[i*80+120,225]],'#dce3c11a',1);stroke(g,[[-440,i*46],[440,i*46]],'#dce3c11a',1)}g.restore();
    lamp(g,-255,-167);lamp(g,255,-167);
  }
  function draw(g,id,t=0,world={},name=null){
    base(g,id,t);
    if(id==='garden'){
      for(const [x,y,s] of [[-300,-52,1.7],[-230,-65,1.2],[260,-58,1.6],[325,-25,1.1],[-290,108,1.3],[220,140,1.2]])plant(g,x,y,s);
      oval(g,0,72,138,64,'#496f66');oval(g,0,67,125,54,'#89aaa0');oval(g,0,67,112,46,'#628f85');
      for(let i=0;i<4;i++){g.strokeStyle='#c8dec33b';g.lineWidth=1;g.beginPath();g.ellipse(10,66,30+i*22+Math.sin(t)*3,10+i*7,0,0,Math.PI*2);g.stroke()}
      for(let i=0;i<7;i++)oval(g,-70+i*23,69+Math.sin(i*2)*16,12,6,'#a4bc86');
      box(g,-175,-85,340,42,10,'#829477','#c0c9a2');for(let i=0;i<5;i++)plant(g,-145+i*66,-70,.65);
      text(g,name||'THE GLASS GARDEN',0,-152,'#d5e0b8',12);text(g,'GROW SLOWLY. THAT IS ALLOWED.',0,180,'#d2d2ac',8);
      for(let i=0;i<8;i++)oval(g,Math.sin(t*.18+i*2)*320,-80+Math.cos(t*.24+i)*100,2,2,'#d8e9ac99');
    } else if(id==='roost'){
      for(let i=0;i<8;i++){let x=-270+(i%4)*180,y=-40+Math.floor(i/4)*145;stroke(g,[[x-33,y],[x-33,y+33]],'#31454d',6);stroke(g,[[x+33,y],[x+33,y+33]],'#31454d',6);oval(g,x,y,57,23,'#9aab99');oval(g,x,y-4,48,17,'#364c55');for(let j=0;j<6;j++)stroke(g,[[x-39+j*14,y+3],[x-29+j*12,y-12]],'#c3bea0',2);box(g,x+32,y-19,16,15,4,'#637976');oval(g,x+40,y-12,3,3,'#cde6a7');text(g,String(i+1).padStart(2,'0'),x,y+52,'#c1ccbb',9)}
      text(g,name||'THE MOON ROOST',-100,-149,'#c1cce1',12);text(g,'DO NOT DISTURB THE DREAMING CIRCUITS',0,199,'#c6d0c1',8);
      stroke(g,[[-335,-101],[-220,-72],[-70,-95],[100,-72],[330,-104]],'#a7b4a4',2);for(let i=0;i<12;i++)oval(g,-310+i*56,-91+Math.sin(i/11*Math.PI)*17,3,3,'#d5d8a5');
    } else if(id==='nursery'){
      box(g,-305,-107,610,97,18,'#9aab8b','#d3d7ac');
      for(let i=0;i<4;i++){const x=-224+i*150;box(g,x-51,-95,102,73,15,'#4e746c','#bcd3ae');oval(g,x,-48,31,12,'#b7bd91');oval(g,x,-60,19,24,'#e3d7aa');stroke(g,[[x-8,-64],[x+3,-58],[x-2,-48]],'#aab38a',2);oval(g,x+36,-81,3,3,'#d5eda6');text(g,'NURSERY '+(i+1),x,3,'#d9dec0',8)}
      oval(g,0,115,145,60,'#c4bb9180');oval(g,0,110,126,49,'#d6cba580');
      for(let i=0;i<5;i++){g.save();g.translate(-90+i*44,110+Math.sin(i)*18);g.rotate(i*.3);box(g,-13,-13,26,26,5,['#91b5a0','#d7b080','#b0a2c6'][i%3]);g.restore()}
      text(g,name||'THE LITTLE FOUNDRY',0,-151,'#e5ddb7',12);text(g,'NEW VOICES, OLD FAMILY WORDS',0,193,'#dadbc0',8);
      stroke(g,[[-110,-220],[-110,-171]],'#b9caa1',2);stroke(g,[[-155,-172],[-65,-172]],'#c9d2ad',2);for(let i=0;i<3;i++){stroke(g,[[-147+i*36,-172],[-147+i*36,-146]],'#c9d2ad',1);oval(g,-147+i*36,-141,7,7,['#d5bc86','#9fc2ae','#b5add1'][i])}
    } else if(id==='archive'){
      for(const x of [-280,280]){box(g,x-59,-136,118,169,7,'#9b8a74');for(let row=0;row<4;row++){box(g,x-50,-125+row*39,100,29,3,'#3f414b');for(let i=0;i<7;i++){const height=17+(i*7+row*5)%10;box(g,x-45+i*13,-98+row*39-height,10,height,2,['#a7b49a','#c3aa8c','#a499b9'][i%3])}}}
      for(const x of [-135,135]){stroke(g,[[x-55,107],[x-55,143]],'#41474a',6);stroke(g,[[x+55,107],[x+55,143]],'#41474a',6);box(g,x-79,77,158,41,8,'#b8a17d');box(g,x-37,61,74,26,5,'#7e98a2');box(g,x-29,65,58,14,3,'#29464d');text(g,'a → b → chirp',x,76,'#c6ddb3',8);box(g,x-18,96,36,13,2,'#e0d2ac')}
      oval(g,0,-47,60,29,'#8d9e8c');box(g,-24,-87,48,47,9,'#d1c49b');box(g,-18,-81,36,31,5,'#415c61');text(g,'Aa',0,-59,'#d2e4b4',19);
      text(g,name||'THE STORY ARCHIVE',0,-151,'#dcc9de',12);text(g,'A WORD IS A LITTLE THING YOU CAN GIVE AWAY',0,194,'#d3c5be',8);
    } else {
      oval(g,0,41,140,61,'#bca98a');oval(g,0,35,129,53,'#c8b796');oval(g,0,34,101,38,'#a18e70');
      for(let i=0;i<6;i++){const a=i*Math.PI/3,x=Math.cos(a)*190,y=40+Math.sin(a)*85;oval(g,x,y+10,29,11,'#4b5148');box(g,x-27,y-13,54,29,10,['#8eac94','#b4a0b3','#c4ab7e'][i%3])}
      for(let i=0;i<3;i++){box(g,-24+i*25,14,16,16,4,'#eee0b7');oval(g,-16+i*25,14,8,3,'#7b7560')}
      box(g,-336,-94,132,75,10,'#3d5753','#b3b390');for(let i=0;i<6;i++)stroke(g,[[-319+i*19,-75],[-319+i*19,-33]],'#e3b96f',5);
      box(g,221,-104,113,76,9,'#63746b');oval(g,249,-73,15,15,'#334f50');oval(g,304,-73,15,15,'#334f50');box(g,271,-89,13,31,3,'#cbb889');
      for(let i=0;i<3;i++)text(g,'♫',250+i*26,-120-Math.sin(t+i)*6,'#cbdcb0',18);
      text(g,name||'THE COMMONS',0,-153,'#e2c6ac',12);text(g,'ALL FLUFF, FEATHERS & FIRMWARE WELCOME',0,196,'#d8c6ad',8);
    }
  }
  return {draw};
})();
