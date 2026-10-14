(() => {
'use strict';
const canvas=document.getElementById('game'); let ctx=canvas.getContext('2d',{alpha:false});
const W=1280,H=720,GROUND=585,FPS=60,step=1/FPS;
const $=id=>document.getElementById(id);
const bg=new Image();bg.src='assets/saigon-night.png';
const keys=new Set();
// Alpha 0.2: atlas is optional; vector renderer remains a safe fallback.
const SPRITE_POSES=['idle','walk','jump','crouch','block','lp','hp','lk','hk','special','super','hit'];
const SPRITE_W=448,SPRITE_H=360,SPRITE_COLS=4,SPRITE_ROWS=SPRITE_POSES.length;
// 60-tick animation timing source of truth. Frames are illustrations, not simulation ticks.
const ANIM_TICKS={idle:[13,10,14,11],walk:[7,6,7,6],jump:[7,8,8,8],crouch:[12,12,12,12],block:[6,6,7,7],hit:[5,5,7,8]};
const CANCEL_ROUTES={lp:['lp','lk','special'],lk:['hp','special'],hp:['special','super'],hk:['special','super']};
let showTrainingPanel=true;
let trainingStats={event:'CHƯA CÓ ĐÒN',damage:0,combo:0,frame:0,attacker:'-'};
const spriteAtlases={minh:new Image(),linh:new Image()};
// Alpha 0.6: artist-approved frames are optional overlay atlases. Never replace the
// vector-derived fallback; incomplete art always falls back pose by pose.
const artistAtlases={minh:new Image(),linh:new Image()};
const artistPoseSets={minh:new Set(),linh:new Set()};
const artistAtlasReady={minh:false,linh:false};
const artistManifest={status:'loading',error:null};
fetch('assets/sprites/artist/manifest.json').then(response=>{
 if(!response.ok)throw new Error(`HTTP ${response.status}`);
 return response.json();
}).then(manifest=>{
 if(manifest.schemaVersion!==1||JSON.stringify(manifest.tileSize)!==JSON.stringify([SPRITE_W,SPRITE_H])||
    JSON.stringify(manifest.grid)!==JSON.stringify([SPRITE_COLS,SPRITE_ROWS]))throw new Error('incompatible artist atlas manifest');
 const fighters=['minh','linh'];
 for(const kind of fighters){
  const record=manifest.characters?.[kind],poses=record?.poses;
  if(!Array.isArray(poses)||poses.some(p=>!SPRITE_POSES.includes(p)))throw new Error(`invalid ${kind} poses`);
  if(poses.length===0)continue;
  const img=artistAtlases[kind];
  img.onload=()=>{
   if(img.naturalWidth===SPRITE_COLS*SPRITE_W&&img.naturalHeight===SPRITE_ROWS*SPRITE_H){
    artistPoseSets[kind]=new Set(poses);
    artistAtlasReady[kind]=true;
   }else artistManifest.error=`${kind}: atlas dimensions invalid`;
  };
  img.onerror=()=>{artistManifest.error=`${kind}: artist overlay did not load`;};
  // File name is hard-coded, never a user-supplied URL.
  img.src=`assets/sprites/artist/${kind}-overlay.png`;
 }
 artistManifest.status='loaded';
}).catch(error=>{artistManifest.status='fallback';artistManifest.error=String(error);});
const portraits={minh:new Image(),linh:new Image()};
for(const kind of ['minh','linh'])portraits[kind].src=`assets/portraits/${kind}.webp`;
let afterimages=[],superCard=null,reduceMotion=false;

for(const kind of ['minh','linh'])spriteAtlases[kind].src=`assets/sprites/${kind}-atlas.png`;
let showCombatBoxes=false,preferAtlas=true;

const MOVE={
 lp:{name:'ĐẤM NHẸ',start:4,active:2,recovery:9,range:97,damage:35,hitstun:19,blockstun:13,push:13,level:'mid',meter:16},
 hp:{name:'THIẾT TRỌNG QUYỀN',start:9,active:3,recovery:18,range:127,damage:85,hitstun:23,blockstun:15,push:35,level:'mid',meter:28},
 lk:{name:'ĐÁ NHẸ',start:6,active:2,recovery:11,range:121,damage:45,hitstun:19,blockstun:14,push:19,level:'low',meter:17},
 hk:{name:'HOÀNH CƯỚC',start:11,active:3,recovery:21,range:154,damage:90,hitstun:25,blockstun:15,push:44,level:'mid',meter:29},
 special:{name:'SPECIAL',start:14,active:7,recovery:21,range:215,damage:95,hitstun:27,blockstun:19,push:56,level:'mid',meter:36},
 super:{name:'SUPER',start:10,active:13,recovery:30,range:258,damage:280,hitstun:37,blockstun:22,push:115,level:'mid',meter:0}
};
let mode='ai',difficulty='normal',training=false,state='menu',round=1,timer=99,frame=0,roundStart=0,roundEnd=0,hitFreeze=0,shake=0,comment='',commentFrames=0;
let particles=[],flashes=[],p1,p2,accum=0,last=performance.now(),sound=false,audio=null;
const P1={left:'KeyA',right:'KeyD',up:'KeyW',down:'KeyS',lp:'KeyJ',hp:'KeyK',lk:'KeyU',hk:'KeyI',special:'KeyQ',super:'KeyE'};
const P2={left:'ArrowLeft',right:'ArrowRight',up:'ArrowUp',down:'ArrowDown',lp:'Digit1',hp:'Digit2',lk:'Digit4',hk:'Digit5',special:'Digit0',super:'Digit9'};
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
function actor(kind,x,isAI=false){return {kind,name:kind==='minh'?'MINH':'LINH',x,y:0,vy:0,face:kind==='minh'?1:-1,hp:kind==='minh'?1000:950,maxHp:kind==='minh'?1000:950,meter:0,roundWins:0,action:'idle',actionFrame:0,stun:0,stunState:'',grounded:true,block:false,crouch:false,attackUsed:false,confirmed:false,queue:null,moveDir:0,isAI,aiMove:0,aiDecide:0,aiAttackDelay:0,combo:0,lastHit:0,walkSpeed:kind==='minh'?3.3:4.0};}
function resetMatch(){trainingStats={event:'CHƯA CÓ ĐÒN',damage:0,combo:0,frame:0,attacker:'-'};p1=actor('minh',348,false);p2=actor('linh',932,mode==='ai');round=1;afterimages=[];superCard=null;startRound(true);}
function startRound(first=false){if(!first)round++;p1.x=348;p2.x=932;for (let p of [p1,p2]){p.y=0;p.vy=0;p.hp=p.maxHp;p.meter=first?0:p.meter;p.action='idle';p.actionFrame=0;p.stun=0;p.block=false;p.crouch=false;p.combo=0;p.queue=null;p.confirmed=false;p.grounded=true;p.aiDecide=0;}timer=99;roundStart=115;roundEnd=0;particles=[];flashes=[];state='fight';$('resultOverlay').classList.add('hidden');$('startOverlay').classList.add('hidden');$('pauseOverlay').classList.add('hidden');comment='ROUND '+round;commentFrames=105;}
function requestAttack(p,type){if(state!=='fight'||roundStart>0||roundEnd>0||p.hp<=0)return false;const mv=MOVE[type];if(!mv)return false;if(type==='super'&&p.meter<300){if(!p.isAI){comment='CẦN 300 MOMENTUM';commentFrames=30;}return false;}
 if(p.stun>0||!p.grounded)return false;
 if(p.action!=='idle'&&p.action!=='walk'&&p.action!=='crouch'&&p.action!=='block'){
  const current=MOVE[p.action];
  const canCancel=current&&p.confirmed&&p.actionFrame>=current.start&&p.actionFrame<=current.start+current.active+8&&(CANCEL_ROUTES[p.action]||[]).includes(type);
  if(!canCancel){if(current&&p.actionFrame>current.start+current.active+current.recovery-6){p.queue=type;return true;}return false;}
  p.queue=null; // Hit/block-confirmed cancel skips recovery without changing the 60Hz sim.

 }
 p.action=type;p.actionFrame=0;p.attackUsed=false;p.confirmed=false;p.block=false;p.crouch=false;p.moveDir=0;if(type==='super'){p.meter-=300;superCard={kind:p.kind,frames:32};comment='SUPER · '+(p.kind==='minh'?'THIẾT QUYỀN PHÁ GIỚI':'PHONG ẢNH THẬP LIÊN');commentFrames=85;shake=10;playSound('super');} else if(type==='special')playSound('whoosh');return true;
}
function handleActionInput(e){let id=e.code; if(e.repeat)return;if(id==='KeyH'){showCombatBoxes=!showCombatBoxes;return;}if(id==='KeyT'){showTrainingPanel=!showTrainingPanel;return;}if(id==='KeyM'){reduceMotion=!reduceMotion;return;}if(id==='KeyV'){preferAtlas=!preferAtlas;return;}if(id==='KeyP'){if(state==='fight'){state='paused';$('pauseOverlay').classList.remove('hidden')}else if(state==='paused'){state='fight';$('pauseOverlay').classList.add('hidden')}return;}if(id==='Enter'&&(state==='menu'||state==='result')){begin(false);return;}if(id==='KeyR'&&state!=='menu'){begin(training);return;}
 for(let [p,controls] of [[p1,P1],[p2,P2]]){
  if(!p||p.isAI)continue;
  for(let k of ['lp','hp','lk','hk','special','super'])if(id===controls[k])requestAttack(p,k);
 }
}
window.addEventListener('keydown',e=>{if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();keys.add(e.code);handleActionInput(e);});
window.addEventListener('keyup',e=>keys.delete(e.code));
window.addEventListener('blur',()=>keys.clear());
function begin(t=false){mode=$('modeSelect').value;difficulty=$('difficultySelect').value;training=t;resetMatch();}
$('startBtn').onclick=()=>begin(false);$('trainingBtn').onclick=()=>begin(true);$('restartBtn').onclick=()=>begin(training);$('rematchBtn').onclick=()=>begin(training);$('resumeBtn').onclick=()=>{if(state==='paused'){state='fight';$('pauseOverlay').classList.add('hidden');}};
$('menuBtn').onclick=()=>{state='menu';$('resultOverlay').classList.add('hidden');$('startOverlay').classList.remove('hidden');};
$('modeSelect').onchange=e=>{mode=e.target.value;if(state==='fight'||state==='paused')begin(training);};
$('difficultySelect').onchange=e=>{difficulty=e.target.value;};
$('soundBtn').onclick=()=>{sound=!sound;$('soundBtn').textContent=sound?'♪ TẮT ÂM':'♪ BẬT ÂM';if(sound&&!audio){try{audio=new(window.AudioContext||window.webkitAudioContext)();}catch{sound=false;}}};
function playSound(type){if(!sound||!audio)return;try{const at=audio.currentTime,o=audio.createOscillator(),g=audio.createGain();o.connect(g);g.connect(audio.destination);let freq=type==='hit'?125:type==='block'?290:type==='super'?490:215;o.type=type==='hit'?'sawtooth':'triangle';o.frequency.setValueAtTime(freq,at);o.frequency.exponentialRampToValueAtTime(Math.max(50,freq*.38),at+.12);g.gain.setValueAtTime(.09,at);g.gain.exponentialRampToValueAtTime(.001,at+.14);o.start(at);o.stop(at+.15);}catch{}}
function getControl(p,opp){if(p.isAI)return aiControl(p,opp);const c=p===p1?P1:P2;return {left:keys.has(c.left),right:keys.has(c.right),up:keys.has(c.up),down:keys.has(c.down)};}
function aiControl(p,opp){const dist=opp.x-p.x, abs=Math.abs(dist),facing=dist>=0?1:-1;
 if(p.aiDecide--<=0){p.aiDecide={easy:36,normal:23,hard:11}[difficulty]+Math.floor(Math.random()*14);const aggress={easy:.33,normal:.55,hard:.74}[difficulty];p.aiMove=abs>210?facing:abs<72?-facing:Math.random()<aggress?facing:0;
 if(abs<190&&Math.random()<aggress&&p.aiAttackDelay<=0){const r=Math.random();requestAttack(p,r<.35?'lp':r<.56?'lk':r<.77?'hp':r<.91?'hk':'special');p.aiAttackDelay={easy:53,normal:29,hard:16}[difficulty];}
 if(abs<140&&opp.action&&MOVE[opp.action]&&Math.random()<({easy:.17,normal:.38,hard:.55}[difficulty]))p.aiMove=-facing;
 }
 if(p.aiAttackDelay>0)p.aiAttackDelay--;
 if(roundStart>0)return {left:false,right:false,up:false,down:false};
 const moving=p.aiMove<0?{left:true,right:false}:{left:false,right:p.aiMove>0};return {...moving,up:false,down:false};}
function updatePlayer(p,opp){p.face=p.x<=opp.x?1:-1;
 if(p.stun>0){p.stun--;p.actionFrame++;p.x=clamp(p.x,65,W-65);if(p.stun===0){p.action='idle';p.actionFrame=0;}return;}
 const input=getControl(p,opp),dir=(input.right?1:0)-(input.left?1:0);
 const backward=(p.face===1?input.left:input.right);
 const attacking=!!MOVE[p.action];
 if(attacking){p.actionFrame++;if(p.action==='special'&&p.actionFrame>=MOVE.special.start&&p.actionFrame<=(MOVE.special.start+MOVE.special.active))p.x+=p.face*(p.kind==='linh'?7:3.5);if(p.action==='super'&&p.actionFrame>=MOVE.super.start&&p.actionFrame<MOVE.super.start+MOVE.super.active)p.x+=p.face*5;
  const mv=MOVE[p.action];if(p.actionFrame>mv.start+mv.active+mv.recovery){p.action='idle';p.actionFrame=0;if(p.queue){const queued=p.queue;p.queue=null;requestAttack(p,queued);}}
 } else if(p.grounded){
   if(input.up){p.grounded=false;p.vy=-14;p.action='jump';p.block=false;}
   else if(input.down){p.crouch=true;p.block=backward;p.action=backward?'block':'crouch';p.moveDir=0;}
   else if(backward){p.block=true;p.crouch=false;p.action='block';p.x+=dir*p.walkSpeed*.6;p.moveDir=dir;}
   else if(dir){p.block=false;p.crouch=false;p.action='walk';p.x+=dir*p.walkSpeed;p.moveDir=dir;}
   else{p.block=false;p.crouch=false;p.action='idle';p.moveDir=0;}
 } else {p.x+=dir*p.walkSpeed*.8;}
 if(!p.grounded){p.y+=p.vy;p.vy+=.72;if(p.y>=0){p.y=0;p.vy=0;p.grounded=true;if(!attacking){p.action='idle';p.actionFrame=0;spawnDust(p.x,GROUND);}}}
 p.x=clamp(p.x,82,W-82);
 if(p.action==='idle'||p.action==='walk'||p.action==='block'||p.action==='crouch'||p.action==='jump')p.actionFrame++;
}
// World-space rectangles, with origins anchored to the ground plane.
// Data is deliberately independent of visual sprite pixels.
const ATTACK_BOXES={
 lp:{x:37,y:-209,w:106,h:86},hp:{x:44,y:-224,w:142,h:95},
 lk:{x:36,y:-109,w:132,h:71},hk:{x:38,y:-188,w:175,h:110},
 special:{x:51,y:-191,w:222,h:118},super:{x:46,y:-240,w:275,h:215}
};
function attackBoxes(p){const spec=ATTACK_BOXES[p.action];if(!spec)return [];
 const extra=(p.kind==='linh'&&(p.action==='lk'||p.action==='hk'))?13:0;
 const x=p.face===1?p.x+spec.x:p.x-spec.x-spec.w-extra;
 return [{x,y:GROUND+p.y+spec.y,w:spec.w+extra,h:spec.h}];
}
function hurtBoxes(p){const crouched=(p.crouch&&p.grounded)||(p.action==='crouch');const y=GROUND+p.y;
 return crouched?[{x:p.x-45,y:y-161,w:90,h:157}]:[
  {x:p.x-39,y:y-266,w:78,h:143},
  {x:p.x-42,y:y-124,w:84,h:121}
 ];
}
function intersects(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;}
function drawCombatBoxes(){if(!showCombatBoxes)return;ctx.save();ctx.lineWidth=2;
 for(const p of [p1,p2]){
  ctx.strokeStyle='#57ec8c';ctx.fillStyle='#57ec8c28';
  for(const b of hurtBoxes(p)){ctx.fillRect(b.x,b.y,b.w,b.h);ctx.strokeRect(b.x,b.y,b.w,b.h);}
  if(MOVE[p.action]&&p.actionFrame>=MOVE[p.action].start&&p.actionFrame<MOVE[p.action].start+MOVE[p.action].active){
   ctx.strokeStyle='#ff536f';ctx.fillStyle='#ff536f33';
   for(const b of attackBoxes(p)){ctx.fillRect(b.x,b.y,b.w,b.h);ctx.strokeRect(b.x,b.y,b.w,b.h);}
  }
 }
 ctx.restore();}
function checkHit(attacker,defender){const mv=MOVE[attacker.action];if(!mv||attacker.attackUsed||attacker.stun>0)return;const af=attacker.actionFrame;if(af<mv.start||af>=mv.start+mv.active)return;
 const boxes=attackBoxes(attacker);
 if(!boxes.some(a=>hurtBoxes(defender).some(b=>intersects(a,b))))return;
 attacker.attackUsed=true;attacker.confirmed=true;
 const blocked=defender.block&&defender.grounded&&!(mv.level==='low'&&!defender.crouch);
 if(blocked){trainingStats={event:'GUARD',damage:attacker.action==='super'?35:0,combo:0,frame,attacker:attacker.kind};defender.stun=mv.blockstun;defender.stunState='block';defender.action='block';defender.actionFrame=0;defender.hp=Math.max(0,defender.hp-(attacker.action==='super'?35:0));defender.meter=Math.min(300,defender.meter+11);attacker.meter=Math.min(300,attacker.meter+mv.meter*.45);comment='GUARD!';commentFrames=25;spawnImpact(defender.x-attacker.face*33,GROUND+defender.y-145,'block');hitFreeze=attacker.action==='super'?10:4;shake=1;playSound('block');}
 else {const combo=frame-defender.lastHit<110?defender.combo+1:1;defender.combo=combo;defender.lastHit=frame;const scaling=Math.max(.4,1-.1*(combo-1)),dmg=Math.round(mv.damage*scaling);trainingStats={event:mv.name,damage:dmg,combo,frame,attacker:attacker.kind};defender.hp=Math.max(0,defender.hp-dmg);defender.stun=mv.hitstun;defender.stunState='hit';defender.action='hit';defender.actionFrame=0;defender.block=false;defender.crouch=false;defender.x+=attacker.face*mv.push;attacker.meter=Math.min(300,attacker.meter+mv.meter);defender.meter=Math.min(300,defender.meter+Math.round(mv.meter*.42));hitFreeze=attacker.action==='super'?14:attacker.action==='lp'?5:8;shake=attacker.action==='super'?14:attacker.action==='hp'||attacker.action==='hk'?6:3;spawnImpact(defender.x-attacker.face*27,GROUND+defender.y-147,attacker.kind);playSound('hit');if(combo>=2){comment=combo+' HIT COMBO';commentFrames=55;}
  if(defender.hp<=0){defender.action='ko';defender.stun=0;roundEnd=145;comment='K.O.!';commentFrames=105;shake=19;playSound('super');}
 }
}
function spawnImpact(x,y,type){let cols=type==='minh'?['#ffc39b','#ff5437','#ffd5af']:type==='linh'?['#e6ffff','#48c6fa','#7f9ffc']:['#8ae6ff','#e8ffff','#9afaff'];
 for(let n=0;n<18;n++){let a=Math.random()*Math.PI*2,s=2+Math.random()*9;particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s,life:12+Math.random()*17,max:30,size:2+Math.random()*7,col:cols[n%cols.length]});}
 flashes.push({x,y,r:13,life:16,color:cols[1]});}
function spawnDust(x,y){for(let i=0;i<10;i++){particles.push({x,y,vx:(Math.random()-.5)*6,vy:-Math.random()*3,life:10+Math.random()*17,size:3+Math.random()*8,col:'#a1a7bb'});}}
function finishRound(){if(training){p1.hp=p1.maxHp;p2.hp=p2.maxHp;roundEnd=0;timer=99;roundStart=60;comment='TRAINING RESET';commentFrames=45;return;}
 const winner=p1.hp>p2.hp?p1:p2.hp>p1.hp?p2:null;
 if(winner)winner.roundWins++;
 if(p1.roundWins>=2||p2.roundWins>=2){state='result';$('resultOverlay').classList.remove('hidden');$('winnerText').textContent=(p1.roundWins>p2.roundWins?'MINH':'LINH')+' THẮNG!';$('winnerDetail').textContent='TỈ SỐ '+p1.roundWins+' - '+p2.roundWins+' · '+(p1.roundWins>p2.roundWins?'THIẾT QUYỀN':'PHONG ẢNH')+' LÀ NGƯỜI CHIẾN THẮNG';}
 else startRound();}
function update(){frame++;
 if(state!=='fight')return;
 if(superCard){superCard.frames--;if(superCard.frames<=0)superCard=null;}
 for(const a of afterimages)a.life--;afterimages=afterimages.filter(a=>a.life>0);
 if(hitFreeze>0){hitFreeze--;return;}
 if(roundStart>0){roundStart--;if(roundStart===10){comment='FIGHT!';commentFrames=48;}return;}
 if(roundEnd>0){roundEnd--;if(roundEnd===0)finishRound();return;}
 if(!training&&frame%60===0){timer=Math.max(0,timer-1);if(timer===0){roundEnd=130;comment='TIME OVER!';commentFrames=95;}}
 if(commentFrames>0)commentFrames--;
 if(shake>0)shake*=.84;if(shake<.3)shake=0;
 updatePlayer(p1,p2);updatePlayer(p2,p1);
 if(!reduceMotion&&frame%3===0){
  for(const p of [p1,p2]){
   const mv=MOVE[p.action];
   if(mv&&(p.action==='special'||p.action==='super'||p.action==='hk')&&p.actionFrame>=mv.start-2&&p.actionFrame<mv.start+mv.active+3){
    afterimages.push({kind:p.kind,x:p.x,y:p.y,face:p.face,action:p.action,actionFrame:p.actionFrame,life:13,max:13});
   }
  }
  if(afterimages.length>22)afterimages.splice(0,afterimages.length-22);
 }
 // body push prevention; collisions stay symmetrical to reduce corner trapping
 let dx=p2.x-p1.x;if(Math.abs(dx)<76){let push=(76-Math.abs(dx))*.5;let sign=dx>=0?1:-1;p1.x=clamp(p1.x-sign*push,65,W-65);p2.x=clamp(p2.x+sign*push,65,W-65);}
 checkHit(p1,p2);checkHit(p2,p1);
 for(let particle of particles){particle.x+=particle.vx;particle.y+=particle.vy;particle.vx*=.94;particle.vy+=.14;particle.life--;}particles=particles.filter(p=>p.life>0);
 for(let s of flashes){s.life--;s.r+=4;}flashes=flashes.filter(s=>s.life>0);
}
function rounded(x,y,w,h,r=8){ctx.beginPath();ctx.roundRect(x,y,w,h,r);}
function t(str,x,y,font,color='#fff',align='left'){ctx.font=font;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(str,x,y);ctx.textAlign='left';}
function drawBackground(){if(bg.complete&&bg.naturalWidth)ctx.drawImage(bg,0,0,W,H);else{ctx.fillStyle='#111b33';ctx.fillRect(0,0,W,H);}const veil=ctx.createLinearGradient(0,0,0,H);veil.addColorStop(0,'#02071622');veil.addColorStop(.65,'#04041100');veil.addColorStop(1,'#04071373');ctx.fillStyle=veil;ctx.fillRect(0,0,W,H);
 // animated light shafts and fine atmospheric droplets
 const time=frame/FPS;ctx.save();ctx.globalAlpha=.05;for(let i=0;i<38;i++){let x=(i*149+time*26)%W;ctx.strokeStyle='#80c9fd';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,(i*111+frame*.9)%H);ctx.lineTo(x-5,(i*111+frame*.9)%H+16);ctx.stroke();}ctx.restore();}
function limb(points,width,inner,outer='#0d1323',accent){ctx.save();ctx.lineCap='round';ctx.lineJoin='round';ctx.strokeStyle=outer;ctx.lineWidth=width+7;ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0],points[i][1]);ctx.stroke();ctx.strokeStyle=inner;ctx.lineWidth=width;ctx.stroke();if(accent){ctx.globalAlpha=.35;ctx.strokeStyle=accent;ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(points[0][0]-width*.13,points[0][1]-2);for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0]-width*.13,points[i][1]-3);ctx.stroke();}ctx.restore();}
function poly(pts,fill,stroke='#0d1424',sw=5){ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=sw;ctx.lineJoin='round';ctx.stroke();}}
function ellipse(x,y,rx,ry,fill,stroke='#111526',width=4){ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke();}}
// Alpha 0.5: deterministic hand-ink-inspired cel line work, shared by gameplay fallback and baked atlases.
function inkPath(pts,color='#141522',width=2.2){ctx.save();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();ctx.moveTo(...pts[0]);for(const pt of pts.slice(1))ctx.lineTo(...pt);ctx.stroke();ctx.restore();}
function inkDot(x,y,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();}
function foldLines(list,color='#361d30',weight=1.8){list.forEach(pts=>inkPath(pts,color,weight));}
function drawFighterVector(p,atX=p.x,atY=GROUND+p.y,scale=1, forceAction=null){const isM=p.kind==='minh',action=forceAction||p.action,tt=(p.actionFrame||frame)/10,move=action==='walk',duck=action==='crouch'||(action==='block'&&p.crouch),block=action==='block',hit=action==='hit'||action==='ko';const isPunch=['lp','hp'].includes(action),isKick=['lk','hk'].includes(action),isSpecial=action==='special',isSuper=action==='super';let mv=MOVE[action],prog=mv?clamp((p.actionFrame-mv.start)/(mv.active+1),0,1):0;const active=mv&&p.actionFrame>=mv.start-1&&p.actionFrame<mv.start+mv.active+3;
 const swinging=isPunch&&active, kicking=isKick&&active,lunging=(isSpecial||isSuper)&&active;
 const skin=isM?'#e6a17e':'#efd0ae',glove=isM?'#e8e6dc':'#255aab',upper=isM?'#ad2434':'#286cbb',upperLight=isM?'#f6544d':'#5ba1f1',pants=isM?'#202637':'#e8eaf3',pantsShade=isM?'#111827':'#adb9d6',edge='#101522';const walkPhase=move?Math.sin((p.actionFrame||frame)*.24)*22:0;const float=move?Math.abs(walkPhase)*.10:Math.sin((p.actionFrame||frame)*.095)*2.3;
 ctx.save();ctx.translate(atX,atY);ctx.scale((p.face||1)*scale,scale);ctx.translate(0,duck?38:0);ctx.translate(0,-float);
 // fade shadow beneath model (on ground)
 ctx.save();ctx.translate(0,-(duck?38:0)+float-p.y);ctx.scale(1/scale,1/scale);ctx.fillStyle='#010614a0';ctx.beginPath();ctx.ellipse(0,9,67,13,0,0,Math.PI*2);ctx.fill();ctx.restore();
 let hipY=duck?-78:-100,torsoY=duck?-132:-171,headY=duck?-179:-220;const leaning=hit?-17:lunging?22:0;
 const rearFoot=[-41-walkPhase,-4],frontFoot=[42+walkPhase,-2],rearKnee=[-36+walkPhase*.6,-53],frontKnee=[32-walkPhase*.6,-54];
 if(kicking){frontKnee[0]=60;frontKnee[1]=-112;frontFoot[0]=isM?162:187;frontFoot[1]=-121-(action==='hk'?18:0);}
 if(isSpecial||isSuper){frontKnee[0]+=17;frontFoot[0]+=29;}
 if(action==='jump'){rearFoot[0]-=14;rearFoot[1]-=26;frontFoot[0]+=22;frontFoot[1]-=45;rearKnee[1]-=19;frontKnee[1]-=12;}
 if(duck){frontKnee[0]+=38;rearKnee[0]-=15;frontKnee[1]+=10;rearKnee[1]+=16;frontFoot[0]+=20;}
 // rear leg
 limb([[-19,hipY],rearKnee,rearFoot],isM?26:23,pantsShade,edge,isM?'#656375':'#f8faff');
 poly([[rearFoot[0]-26,rearFoot[1]-4],[rearFoot[0]+24,rearFoot[1]-4],[rearFoot[0]+32,rearFoot[1]+8],[rearFoot[0]-25,rearFoot[1]+7]],isM?'#6b2531':'#283a68',edge,3);
 // Cloth topology: back knee, side seam, wrapped cuff and inked shoe sole.
 inkPath([[-23,hipY+8],[-32+walkPhase*.45,rearKnee[1]+12],[-34-walkPhase*.85,rearFoot[1]-19]],isM?'#62657a':'#fffdfa',2.5);
 foldLines([[[-30,rearKnee[1]-13],[-45,rearKnee[1]-3],[-38,rearKnee[1]+9]],
            [[rearFoot[0]-14,rearFoot[1]-17],[rearFoot[0]+11,rearFoot[1]-14]]],isM?'#434456':'#a3b1d5');
 inkPath([[rearFoot[0]-23,rearFoot[1]+5],[rearFoot[0]+28,rearFoot[1]+5]],'#070c19',3);
 for(let lace=0;lace<3;lace++)inkPath([[rearFoot[0]-2+lace*7,rearFoot[1]-7],[rearFoot[0]+3+lace*7,rearFoot[1]-2]],'#e1e6f0',1.4);
 // trailing sash / jacket coattail
 if(isM){poly([[-27,torsoY+20],[-64,torsoY+33],[-79,torsoY+79],[-21,torsoY+61]],'#8a2531',edge,4);}else{
  const sw=Math.sin((p.actionFrame||frame)*.07)*12;
  poly([[-28,torsoY+20],[-66,torsoY+35],[-106+sw,torsoY+92],[-54,torsoY+69]],'#1a60c6',edge,4);
  poly([[32,torsoY+19],[56,torsoY+52],[29+sw,torsoY+109],[15,torsoY+65]],'#458adb',edge,4);
 }
 // rear arm
 const shoulderBack=[-28+leaning*.3,torsoY-15], elbowBack=[-58+leaning*.3,torsoY+33],fistBack=[-31,torsoY-17];
 limb([shoulderBack,elbowBack,fistBack],isM?21:17,upper,edge,upperLight);ellipse(...fistBack,isM?14:12,isM?14:11,glove,edge,3);
 // torso cel shaded polygons
 let topY=torsoY-31;
 poly([[-31+leaning*.25,topY],[24+leaning*.25,topY-1],[43+leaning*.3,torsoY+37],[22,hipY+9],[-23,hipY+7],[-45,torsoY+35]],upper,edge,6);
 if(isM){poly([[-4,topY+8],[17,topY+8],[17,hipY+1],[-13,hipY]],'#f3e9e2',edge,2);poly([[27,topY+2],[41,torsoY+27],[12,torsoY+34],[13,topY+9]],upperLight,'',0);ctx.strokeStyle='#7b1b2d';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(16,topY+1);ctx.lineTo(10,hipY+5);ctx.stroke();}
 else{poly([[-21,topY+5],[29,topY+2],[12,hipY-6],[-12,hipY-7]],'#f1f2ed',edge,2);poly([[31,topY+1],[40,torsoY+28],[22,torsoY+25]],upperLight,'',0);ctx.strokeStyle='#1e5398';ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(-22,hipY+1);ctx.lineTo(25,hipY+1);ctx.stroke();}
 // Tailored combat uniform: collar, zipper, directional shading and threadwork.
 if(isM){
  poly([[-31,topY],[-4,topY+7],[-10,torsoY+5],[-23,topY+17]],'#de4d4c',edge,2);
  poly([[21,topY],[10,topY+10],[20,torsoY+11],[31,topY+16]],'#fd7971',edge,2);
  inkPath([[0,topY+8],[2,topY+34],[1,hipY+4]],'#bfc7cf',2.2);
  inkDot(1,hipY-2,2.5,'#f2bd55');
  inkPath([[-31,torsoY+9],[-37,torsoY+27],[-27,torsoY+41]],'#ee6a60',2.4);
  foldLines([[[-34,torsoY+35],[-22,torsoY+30],[-17,torsoY+38]],
            [[29,torsoY+40],[15,torsoY+31]],
            [[-18,hipY+1],[10,hipY+1]]],'#6b2134',2.1);
  // Diamond sleeve patch identifies Minh when viewed at gameplay scale.
  poly([[31,topY+18],[38,topY+21],[35,topY+30],[27,topY+25]],'#ffd0b1','#5c1427',1.4);
 }else{
  poly([[-23,topY+4],[-4,topY+17],[5,topY+10],[-8,topY+2]],'#75bdf5',edge,2);
  poly([[27,topY+4],[13,topY+19],[5,topY+11],[12,topY+2]],'#67bafa',edge,2);
  inkPath([[-7,topY+16],[-9,hipY-5],[15,hipY-5]],'#d1deef',2);
  inkPath([[-32,torsoY+23],[-19,torsoY+32],[-30,torsoY+41]],'#123a8a',2);
  foldLines([[[-16,hipY+8],[12,hipY+7]],[[26,torsoY+41],[32,torsoY+49]],
             [[-27,topY+25],[-16,topY+33]]],'#20569b',2);
  // Belt ornament + flowing knot.
  poly([[-10,hipY-2],[1,hipY-7],[12,hipY-1],[1,hipY+7]],'#f6c47c','#153766',2);
 }
 // front leg, reaches forward for kicks
 limb([[17,hipY],frontKnee,frontFoot],isM?29:25,pants,edge,isM?'#505869':'#fff');
 poly([[frontFoot[0]-24,frontFoot[1]-5],[frontFoot[0]+26,frontFoot[1]-6],[frontFoot[0]+32,frontFoot[1]+7],[frontFoot[0]-25,frontFoot[1]+8]],isM?'#9a2631':'#284b83',edge,4);
 // Articulated knee fabric and tailored hems; follow the pose rather than fixed pixels.
 inkPath([[19,hipY+12],[frontKnee[0]-5,frontKnee[1]+2],[frontFoot[0]-9,frontFoot[1]-15]],isM?'#596074':'#f9ffff',2.6);
 foldLines([[[frontKnee[0]-16,frontKnee[1]-9],[frontKnee[0]+5,frontKnee[1]-13]],
            [[frontKnee[0]-10,frontKnee[1]+7],[frontKnee[0]+12,frontKnee[1]+3]],
            [[frontFoot[0]-16,frontFoot[1]-13],[frontFoot[0]+11,frontFoot[1]-14]]],isM?'#4c5060':'#9baad1',2.1);
 inkPath([[frontFoot[0]-21,frontFoot[1]+5],[frontFoot[0]+28,frontFoot[1]+5]],'#080e19',3);
 for(let lace=0;lace<3;lace++)inkPath([[frontFoot[0]-1+lace*7,frontFoot[1]-7],[frontFoot[0]+5+lace*7,frontFoot[1]-3]],isM?'#f1dde1':'#f1f9ff',1.5);
 // Protective shin/ankle straps and folds.
 if(!isM){inkPath([[frontFoot[0]-6,frontFoot[1]-17],[frontFoot[0]+16,frontFoot[1]-15]],'#2b72c3',3.3);
  inkPath([[rearFoot[0]-9,rearFoot[1]-16],[rearFoot[0]+13,rearFoot[1]-14]],'#2b72c3',3.2);}
 // neck and ears
 ctx.save();ctx.translate(leaning*.32,0);poly([[-11,topY-14],[11,topY-14],[15,topY+7],[-10,topY+9]],skin,edge,3);
 // hair ponytail for Linh behind face
 if(!isM){const wig=Math.sin((p.actionFrame||frame)*.115)*10+walkPhase*.3;limb([[-12,headY-29],[-58,headY-38],[-83+wig,headY-66],[-101+wig,headY-60]],13,'#121d3a','#080e21','#6672aa');}
 // face + jaw
 poly([[-23,headY-24],[8,headY-31],[24,headY-10],[17,headY+18],[-2,headY+30],[-23,headY+8]],skin,edge,4);
 poly([[-25,headY-28],[14,headY-37],[28,headY-20],[15,headY-19],[3,headY-13],[-19,headY-15]],'#101827',edge,2);
 if(isM){poly([[-23,headY-31],[5,headY-42],[2,headY-24],[-9,headY-26],[-16,headY-16]],'#101322','',0);poly([[0,headY-41],[19,headY-32],[10,headY-14]],'#1c222a','',0);}else{poly([[-26,headY-23],[-16,headY-44],[16,headY-39],[28,headY-22],[13,headY-27],[0,headY-16]],'#111a33','',0);}
 ctx.strokeStyle='#172032';ctx.lineWidth=2.4;ctx.beginPath();ctx.moveTo(6,headY-4);ctx.lineTo(17,headY-5);ctx.stroke();ctx.beginPath();ctx.moveTo(18,headY+6);ctx.lineTo(22,headY+12);ctx.stroke();
 // Facial planes, ears, ink eyebrows, eyes, nose and individual hair locks.
 ellipse(-21,headY-1,4,8,skin,edge,1.5);
 poly([[0,headY-7],[18,headY-7],[14,headY-2],[2,headY-2]],'#f6efdc','',0);
 inkPath([[1,headY-8],[18,headY-9]],'#101324',2.6);
 inkPath([[3,headY-4],[13,headY-4]],'#0c1c2c',2.2);
 inkDot(11,headY-4,2.3,'#1b2639');inkDot(12,headY-4.5,.85,'#faffff');
 inkPath([[18,headY+1],[16,headY+8],[20,headY+10]],'#a86150',1.4);
 inkPath([[4,headY+16],[11,headY+17],[15,headY+15]],'#994c43',1.7);
 inkPath([[-14,headY+5],[-9,headY+14]],'#f4c0a0',1.7);
 // Hair texture is rendered on top of the heavy cel-shadow masses.
 for(let lock=0;lock<5;lock++){
  let hx=-21+lock*9;inkPath([[hx,headY-24-(lock%2)*7],[hx+6,headY-30+(lock%3)*2],[hx+10,headY-25]],lock%2?'#41475b':'#626070',1.3);
 }
 if(!isM){inkPath([[-12,headY-37],[-1,headY-43],[20,headY-31]],'#7385bd',1.6);
  inkPath([[-31,headY-37],[-59,headY-44],[-82,headY-63]],'#506397',2.1);}
 ctx.restore();
 // foreground attacking arm
 const shoulder=[27+leaning*.2,torsoY-13];let elbow=[52+leaning,torsoY+10],fist=[40+leaning,torsoY-18];
 if(swinging){elbow=[83,torsoY-30];fist=[isM?148:137,torsoY-36];}
 if(lunging){elbow=[87,torsoY-28];fist=[isSuper?185:165,torsoY-31];}
 if(block){elbow=[42,torsoY-33];fist=[13,torsoY-73];}
 if(hit){elbow=[9,torsoY+31];fist=[-23,torsoY+21];}
 limb([shoulder,elbow,fist],isM?23:18,upper,edge,upperLight);
 ellipse(fist[0],fist[1],isM?17:14,isM?16:13,glove,edge,3);
 // Glove wraps, knuckle construction and sleeve folds attach to striking hand.
 inkPath([[shoulder[0]+3,shoulder[1]+8],[elbow[0]-7,elbow[1]-5]],isM?'#ff766e':'#92bded',2.3);
 inkPath([[elbow[0]-9,elbow[1]+7],[elbow[0]+7,elbow[1]+6]],isM?'#711f32':'#214a92',2.1);
 for(let band=-1;band<=1;band++)inkPath([[fist[0]-6+band*4,fist[1]-9],[fist[0]-2+band*4,fist[1]+9]],isM?'#9696a3':'#adc8f0',1.2);
 inkPath([[fist[0]+5,fist[1]-11],[fist[0]+12,fist[1]-5]],'#101726',1.5);
 if(isM){ctx.strokeStyle='#b5a69c';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(fist[0]-4,fist[1]-4);ctx.lineTo(fist[0]+7,fist[1]+6);ctx.stroke();}
 if(isSpecial||isSuper){if(active){ctx.save();ctx.shadowColor=isM?'#ff714d':'#58caff';ctx.shadowBlur=isSuper?50:27;ctx.strokeStyle=isM?'#ff8d5d':'#74d9ff';ctx.lineWidth=isSuper?14:9;ctx.beginPath();ctx.ellipse(125,torsoY-18,62,23,-.2,-Math.PI/2,Math.PI/2);ctx.stroke();ctx.restore();}}
 ctx.restore();}
function animationPhase(p,action=p.action){
 if(action==='ko')return 3;
 const mv=MOVE[action];
 if(!mv){const timing=ANIM_TICKS[action]||ANIM_TICKS.idle;let tick=Math.max(0,p.actionFrame);const total=timing.reduce((a,b)=>a+b,0);tick%=total;
  for(let col=0;col<timing.length;col++){if(tick<timing[col])return col;tick-=timing[col];}return 3;}

 const af=p.actionFrame;
 if(af<mv.start)return 0;
 if(af<mv.start+Math.max(1,Math.ceil(mv.active/2)))return 1;
 if(af<mv.start+mv.active)return 2;
 return 3;
}
function drawFighter(p,atX=p.x,atY=GROUND+p.y,scale=1,forceAction=null){
 const action=forceAction||p.action,poseName=action==='ko'?'hit':action;
 const hasArtist=artistAtlasReady[p.kind]&&artistPoseSets[p.kind].has(poseName);
 const image=hasArtist?artistAtlases[p.kind]:spriteAtlases[p.kind];
 if(preferAtlas&&image.complete&&image.naturalWidth===SPRITE_COLS*SPRITE_W&&image.naturalHeight===SPRITE_ROWS*SPRITE_H){
  const pose=Math.max(0,SPRITE_POSES.indexOf(action==='ko'?'hit':action));const col=animationPhase(p,action);
  ctx.save();ctx.translate(atX,atY);
  const idle=action==='idle',walking=action==='walk';
  const breathe=idle?Math.sin(frame*.08+(p.kind==='minh'?0:1.5))*.012:0;
  const lean=walking?Math.sin((p.actionFrame||frame)*.24)*.025:0;
  const stretch=(action==='special'||action==='super')&&col===2?.055:0;
  ctx.scale((p.face||1)*scale*(1+stretch+lean-breathe*.35),scale*(1-stretch+breathe));
  ctx.drawImage(image,col*SPRITE_W,pose*SPRITE_H,SPRITE_W,SPRITE_H,-SPRITE_W/2+(action==='super'?48:0),-SPRITE_H+34+(action==='crouch'?54:0),SPRITE_W,SPRITE_H);
  ctx.restore();return;
 }
 drawFighterVector(p,atX,atY,scale,forceAction);
}
function drawAfterimages(){
 if(reduceMotion)return;
 for(const ghost of afterimages){
  ctx.save();ctx.globalAlpha=.28*ghost.life/ghost.max;
  ctx.filter=ghost.kind==='minh'?'sepia(.75) saturate(2.5) hue-rotate(-25deg)':'sepia(.85) saturate(2.8) hue-rotate(155deg)';
  drawFighter({...ghost},ghost.x,GROUND+ghost.y,1,ghost.action);
  ctx.restore();
 }
}
function drawSuperCard(){
 if(!superCard||reduceMotion)return;
 const isM=superCard.kind==='minh',im=portraits[superCard.kind];
 const alpha=clamp(Math.min(superCard.frames,32-superCard.frames)/8,0,1);
 ctx.save();ctx.globalAlpha=alpha*.93;
 ctx.fillStyle='#080c1fd9';ctx.beginPath();ctx.moveTo(0,190);ctx.lineTo(W,150);ctx.lineTo(W,385);ctx.lineTo(0,430);ctx.closePath();ctx.fill();
 const accent=isM?'#f26350':'#5ac8ff';ctx.strokeStyle=accent;ctx.lineWidth=8;
 ctx.beginPath();ctx.moveTo(0,188);ctx.lineTo(W,150);ctx.moveTo(0,430);ctx.lineTo(W,385);ctx.stroke();
 if(im.complete&&im.naturalWidth){
  const px=isM?155:W-465;ctx.drawImage(im,px,145,300,300);
 }
 ctx.shadowColor=accent;ctx.shadowBlur=15;
 ctx.fillStyle='#fff4ef';ctx.font='italic 900 45px Impact, Arial Black, sans-serif';ctx.textAlign='center';
 ctx.fillText(isM?'THIẾT QUYỀN PHÁ GIỚI':'PHONG ẢNH THẬP LIÊN',W/2,isM?340:340);
 ctx.restore();
}
function drawPortrait(kind,x,y){
 const im=portraits[kind],size=80;
 ctx.save();ctx.fillStyle='#081328';ctx.fillRect(x-3,y-3,size+6,size+6);
 if(im.complete&&im.naturalWidth)ctx.drawImage(im,x,y,size,size);
 else{ctx.fillStyle=kind==='minh'?'#a83c35':'#2367a2';ctx.fillRect(x,y,size,size);}
 ctx.strokeStyle=kind==='minh'?'#fc9073':'#7dc5ff';ctx.lineWidth=3;ctx.strokeRect(x,y,size,size);
 ctx.restore();
}
function drawTrainingPanel(){
 if(!training||!showTrainingPanel||state==='menu')return;
 const p=p1,opp=p2,mv=MOVE[p.action],elapsed=trainingStats.frame?frame-trainingStats.frame:0;
 ctx.save();ctx.fillStyle='#080e20e0';ctx.fillRect(24,149,292,153);ctx.strokeStyle='#63bde7';ctx.lineWidth=2;ctx.strokeRect(24,149,292,153);
 t('TRAINING · FRAME DATA',39,171,'900 17px Arial','#93dafa');
 t('MOVE: '+(mv?mv.name:p.action.toUpperCase()),39,195,'bold 13px Arial','#fff');
 t('FRAME: '+p.actionFrame+(mv?' / '+(mv.start+mv.active+mv.recovery):''),39,216,'bold 13px Arial','#eff5ff');
 t('LAST: '+trainingStats.event,39,237,'bold 13px Arial','#fcae8b');
 t('DAMAGE: '+trainingStats.damage+'   COMBO: '+trainingStats.combo,39,258,'bold 13px Arial','#fef1d5');
 t('HITSTUN: '+opp.stun+'   CANCEL: '+(p.confirmed?'READY':'-'),39,280,'bold 13px Arial','#95dfb8');
 ctx.restore();
}
function drawFX(){ctx.save();for(let fx of flashes){const alpha=fx.life/16;ctx.globalAlpha=alpha;ctx.strokeStyle=fx.color;ctx.lineWidth=4;ctx.beginPath();ctx.arc(fx.x,fx.y,fx.r,0,Math.PI*2);ctx.stroke();ctx.lineWidth=2;for(let i=0;i<8;i++){const a=i*Math.PI/4;ctx.beginPath();ctx.moveTo(fx.x+Math.cos(a)*fx.r*.5,fx.y+Math.sin(a)*fx.r*.5);ctx.lineTo(fx.x+Math.cos(a)*fx.r*2.0,fx.y+Math.sin(a)*fx.r*2.0);ctx.stroke();}}
 for(let q of particles){ctx.globalAlpha=Math.max(0,q.life/q.max);ctx.fillStyle=q.col;ctx.beginPath();ctx.moveTo(q.x,q.y);ctx.lineTo(q.x+q.vx*2.1,q.y+q.vy*2.1);ctx.lineTo(q.x-q.vy*.2-q.size,q.y+q.vx*.2);ctx.closePath();ctx.fill();}ctx.restore();}
function meterBar(p,x,reverse=false){const cw=280,segments=3,per=cw/segments;for(let i=0;i<3;i++){const xx=reverse?x+cw-(i+1)*per:x+i*per;ctx.fillStyle='#162d45';ctx.fillRect(xx,64,per-5,8);let fill=clamp((p.meter-i*100)/100,0,1);ctx.fillStyle=reverse?'#60c2f2':'#fa795b';ctx.fillRect(xx+(reverse?(per-5)*(1-fill):0),64,(per-5)*fill,8);}}
function hud(){ctx.save();let grad=ctx.createLinearGradient(0,0,0,112);grad.addColorStop(0,'#060915df');grad.addColorStop(1,'#080c1805');ctx.fillStyle=grad;ctx.fillRect(0,0,W,120);const hpW=394;
 // fighter name plaques
 ctx.fillStyle='#0a1027e6';ctx.fillRect(20,20,540,75);ctx.fillRect(W-560,20,540,75);
 t('MINH',125,40,'900 25px Impact, sans-serif','#ffe5d9');t('THIẾT QUYỀN',125,91,'900 13px Arial, sans-serif','#ff8e7b');
 t('LINH',W-125,40,'900 25px Impact, sans-serif','#e1f2ff','right');t('PHONG ẢNH',W-125,91,'900 13px Arial, sans-serif','#81d5ff','right');
 ctx.fillStyle='#2c354b';ctx.fillRect(125,48,hpW,15);ctx.fillRect(W-125-hpW,48,hpW,15);
 const h1=clamp(p1.hp/p1.maxHp,0,1),h2=clamp(p2.hp/p2.maxHp,0,1);
 let red=ctx.createLinearGradient(0,0,hpW,0);red.addColorStop(0,'#dd4135');red.addColorStop(1,'#f7a051');let blue=ctx.createLinearGradient(W-hpW,0,W,0);blue.addColorStop(0,'#87d2ff');blue.addColorStop(1,'#347ad6');
 ctx.fillStyle=red;ctx.fillRect(125,48,hpW*h1,15);ctx.fillStyle=blue;ctx.fillRect(W-125-hpW*h2,48,hpW*h2,15);
 ctx.strokeStyle='#e7ebf7a8';ctx.lineWidth=2;ctx.strokeRect(125,48,hpW,15);ctx.strokeRect(W-125-hpW,48,hpW,15);
 t(`${p1.hp} / ${p1.maxHp}`,520,41,'bold 12px Arial','#e8bdb4','right');t(`${p2.hp} / ${p2.maxHp}`,W-520,41,'bold 12px Arial','#b4cfee','left');
 for(let i=0;i<2;i++){ellipse(545+i*22,76,7,7,i<p1.roundWins?'#f36f4a':'#293044','#101522',2);ellipse(W-545-i*22,76,7,7,i<p2.roundWins?'#5cc2f2':'#293044','#101522',2);}
 meterBar(p1,167);meterBar(p2,W-447,true);
 ctx.fillStyle='#0c1529';ctx.strokeStyle='#ee866e';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(600,12);ctx.lineTo(680,12);ctx.lineTo(700,52);ctx.lineTo(680,96);ctx.lineTo(600,96);ctx.lineTo(580,52);ctx.closePath();ctx.fill();ctx.stroke();t(String(timer),640,70,'900 50px Impact, sans-serif','#fff9eb','center');t('ROUND '+round,640,112,'900 15px Arial, sans-serif','#fff4e3','center');
 if(training)t('TRAINING MODE · HP AUTO RESET',W/2,139,'bold 13px Arial','#bfe8ff','center');
 if(commentFrames>0&&comment){ctx.globalAlpha=clamp(commentFrames/16,0,1);ctx.save();ctx.shadowColor='#0c0b16';ctx.shadowBlur=21;ctx.strokeStyle='#111526';ctx.lineWidth=10;ctx.font='italic 900 52px Impact, Arial Black, sans-serif';ctx.textAlign='center';ctx.strokeText(comment,W/2,208);ctx.fillStyle=comment.includes('SUPER')?'#ffa56d':'#fff4e5';ctx.fillText(comment,W/2,208);ctx.restore();}
 drawPortrait('minh',22,18);drawPortrait('linh',W-102,18);ctx.restore();}
function draw(){ctx.save();if(shake>0){ctx.translate((Math.random()-.5)*shake,(Math.random()-.5)*shake*.7);}drawBackground();
 // sprite silhouettes, player in front with highlights
 drawAfterimages();drawFighter(p1);drawFighter(p2);drawCombatBoxes();drawFX();drawSuperCard();ctx.restore();hud();drawTrainingPanel();
 if(state==='menu'){// in-arcade background action preview
 } if(state==='paused'){ctx.fillStyle='#03081544';ctx.fillRect(0,0,W,H);}
}
function loop(time){let dt=Math.min(.05,(time-last)/1000);last=time;accum+=dt;let iterations=0;while(accum>=step&&iterations<4){update();accum-=step;iterations++;}draw();requestAnimationFrame(loop);}
// renders an RGBA sprite atlas from the same character illustration code used by the prototype.
window.makeSpriteAtlas=function(kind='minh'){
 const c=document.createElement('canvas');c.width=SPRITE_COLS*SPRITE_W;c.height=SPRITE_ROWS*SPRITE_H;
 const outside=ctx;const tileCtx=c.getContext('2d');
 for(let row=0;row<SPRITE_POSES.length;row++){
  const pose=SPRITE_POSES[row];
  for(let col=0;col<4;col++){
   const sprite=actor(kind,0);sprite.face=1;sprite.action=pose;
   const mv=MOVE[pose];
   sprite.actionFrame=mv?[Math.max(0,mv.start-3),mv.start,mv.start+Math.ceil(mv.active/2),mv.start+mv.active+3][col]:col*7;
   ctx=tileCtx;ctx.save();ctx.translate(col*SPRITE_W+SPRITE_W/2-(pose==='super'?48:0),row*SPRITE_H+SPRITE_H-34-(pose==='crouch'?54:0));
   drawFighterVector(sprite,0,0,1,pose);ctx.restore();ctx=outside;
  }
 }
 return c.toDataURL('image/png');
};
window.__combatDebug=()=>({spriteRevision:'artist-overlay-v0.6',artistManifest:{...artistManifest},artistReady:{...artistAtlasReady},artistPoseCoverage:Object.fromEntries(Object.entries(artistPoseSets).map(([kind,poses])=>[kind,[...poses]])),showTrainingPanel,trainingStats,animationTimings:ANIM_TICKS,cancelConfirmed:{p1:p1.confirmed,p2:p2.confirmed},reduceMotion,portraitReady:Object.fromEntries(Object.entries(portraits).map(([k,img])=>[k,img.complete&&img.naturalWidth>0])),afterimages:afterimages.length,boxes:{p1:{hurt:hurtBoxes(p1),attack:attackBoxes(p1)},p2:{hurt:hurtBoxes(p2),attack:attackBoxes(p2)}},showCombatBoxes,preferAtlas,atlasReady:Object.fromEntries(Object.entries(spriteAtlases).map(([k,img])=>[k,img.complete&&img.naturalWidth===SPRITE_COLS*SPRITE_W&&img.naturalHeight===SPRITE_ROWS*SPRITE_H]))});
window.__gameDebug=()=>({state,round,timer,p1:{x:p1.x,hp:p1.hp,meter:p1.meter,action:p1.action},p2:{x:p2.x,hp:p2.hp,meter:p2.meter,action:p2.action},particles:particles.length,hitFreeze});
resetMatch();state='menu';$('startOverlay').classList.remove('hidden');requestAnimationFrame(loop);
})();
