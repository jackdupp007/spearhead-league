// Anime pixel-chibi character builder for the Spearhead League app.
// Draws an original 32x40 character from a spec, then adds soft shading and a coloured outline.
function chibiGrid(sp){
 const W=32,H=40,g=[];for(let y=0;y<H;y++)g.push(new Array(W).fill(null));
 const hx=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
 const set=(x,y,c)=>{x=Math.round(x);y=Math.round(y);if(x>=0&&x<W&&y>=0&&y<H&&c)g[y][x]=typeof c==="string"?hx(c):c};
 const rect=(x0,y0,x1,y1,c)=>{for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)set(x,y,c)};
 const ell=(cx,cy,rx,ry,c,ok)=>{for(let y=Math.floor(cy-ry);y<=Math.ceil(cy+ry);y++)for(let x=Math.floor(cx-rx);x<=Math.ceil(cx+rx);x++){const d=((x-cx)/rx)**2+((y-cy)/ry)**2;if(d<=1&&(!ok||ok(x,y)))set(x,y,c)}};
 const mixc=(c,t,f)=>c.map((v,i)=>Math.round(v+(t[i]-v)*f));
 const S=sp.skin,HA=sp.hair,A=sp.a,B=sp.b,C=sp.c,E=sp.eye||"#3a6fd6";
 const wide=sp.body==="wide",ghost=sp.body==="ghost";
 // ---- behind the body: long hair, cape, tail, weapon ----
 if(sp.hairStyle==="long")rect(7,12,24,28,HA),ell(16,28,8.5,3,HA);
 if(sp.cape)rect(9,23,22,34,sp.cape),ell(15.5,34,6.5,2,sp.cape);
 if(sp.tail==="rat"){for(let i=0;i<9;i++)set(22+i*0.9,33-Math.sin(i/2)*3,"#e7a5a8")}
 if(sp.tail==="lizard"){for(let i=0;i<8;i++){set(21+i,34-i*0.6,S);set(21+i,35-i*0.6,S)}}
 const wpn=sp.weapon,wc=sp.wcol||"#c9ced6";
 if(wpn==="spear"||wpn==="staff"||wpn==="scythe"||wpn==="gun"){for(let y=8;y<37;y++)set(26,y,wpn==="staff"?"#8a5a2b":wpn==="gun"?"#5a4030":"#8a6a4a");
  if(wpn==="spear")rect(25,5,27,8,wc),set(26,4,wc);
  if(wpn==="staff")ell(26,7,2,2,sp.orb||"#ff6ad5");
  if(wpn==="scythe"){for(let i=0;i<7;i++)set(25-i,8+i*0.35,wc),set(25-i,9+i*0.35,wc)}
  if(wpn==="gun")rect(25,8,27,18,"#6b6f78"),rect(25,8,27,9,C)}
 // ---- body ----
 if(ghost){ell(16,30,8,7,A);for(let x=8;x<=24;x+=3)rect(x,35,x+1,38,A);ell(16,27,6,3,B)}
 else{
  const tw=wide?[8,23]:[11,20];
  rect(tw[0],23,tw[1],32,A);                         // torso
  rect(tw[0],23,tw[1],24,B);                         // collar / shoulders
  rect(tw[0],30,tw[1],31,B);                         // belt
  if(C)rect(15,30,16,31,C);                          // buckle
  if(sp.chest==="skin")rect(tw[0]+1,25,tw[1]-1,29,S);
  if(sp.chest==="plate")rect(tw[0]+2,25,tw[1]-2,29,C);
  if(sp.belly)ell(15.5,28,wide?7:4,4,sp.belly);
  rect(tw[0]-2,24,tw[0]-1,30,A);rect(tw[1]+1,24,tw[1]+2,30,A); // arms
  rect(tw[0]-2,30,tw[0]-1,31,S);rect(tw[1]+1,30,tw[1]+2,31,S); // hands
  rect(12,33,14,36,B);rect(17,33,19,36,B);                     // legs
  rect(11,37,14,38,sp.boots||"#3a2c2a");rect(17,37,20,38,sp.boots||"#3a2c2a");
 }
 // short weapons in the right hand
 if(wpn==="sword"){for(let y=16;y<30;y++)set(24+ (wide?3:0),y,wc);rect(23+(wide?3:0),29,25+(wide?3:0),29,C||"#c9a14a")}
 if(wpn==="axe"||wpn==="hammer"||wpn==="club"){const x=24+(wide?3:0);for(let y=18;y<32;y++)set(x,y,"#7a5232");
  if(wpn==="axe")ell(x+1,19,2.5,3,wc,(xx)=>xx>=x);if(wpn==="hammer")rect(x-2,17,x+2,20,wc);if(wpn==="club")ell(x,19,2.5,3.5,"#8a6a4a")}
 if(wpn==="dagger"){const x=24+(wide?3:0);for(let y=24;y<31;y++)set(x,y,wc)}
 // ---- head ----
 const hy=13;
 if(sp.ears==="pointy"){for(let i=0;i<4;i++){set(5-i*0.6,15-i,S);set(26+i*0.6,15-i,S)}}
 if(sp.ears==="rat"){ell(7,5,4,4,HA);ell(25,5,4,4,HA);ell(7,5,2,2,"#e7a5a8");ell(25,5,2,2,"#e7a5a8")}
 ell(16,hy,10.5,9.5,S);                              // face
 if(sp.snout)ell(16,19,5,3,S);
 // hair / headgear
 const hs=sp.hairStyle;
 if(hs==="short"||hs==="long"||hs==="spiky"||hs==="messy"){
  ell(16,hy-3,11,7,HA,(x,y)=>y<=hy-1);
  for(let x=6;x<=26;x++){const d=(x*7)%4;rect(x,hy-2,x,hy-1+(d>1?1:0)+(hs==="messy"?((x*3)%3):0),HA)} // bangs
  rect(5,hy-2,7,hy+5,HA);rect(25,hy-2,27,hy+5,HA);  // side locks
  if(hs==="spiky")for(let x=6;x<=26;x+=3){set(x,hy-10,HA);set(x+1,hy-11,HA);set(x,hy-11,HA)}
  if(sp.hairHi)for(let x=10;x<=15;x++)set(x,hy-7+((x-10)>>2),mixc(hx(HA),[255,255,255],.45));
 }
 if(hs==="mohawk"){rect(13,hy-14,18,hy-6,HA);for(let x=13;x<=18;x+=2)set(x,hy-15,HA)}
 if(hs==="topknot"){ell(16,hy-10,2.5,2.5,HA)}
 if(hs==="helmet"||hs==="horns"||hs==="visor"){
  ell(16,hy-2,11.5,9,sp.helm||A,(x,y)=>y<=hy-1);rect(5,hy-2,8,hy+6,sp.helm||A);rect(24,hy-2,27,hy+6,sp.helm||A);
  rect(6,hy-2,26,hy-1,C||"#c9a14a");
  if(sp.plume)for(let y=hy-15;y<hy-9;y++)rect(15,y,17,y,sp.plume);
  if(hs==="horns"){for(let i=0;i<7;i++){rect(4-i*0.4,hy-6-i,5-i*0.4,hy-6-i,sp.horn||"#d8c08a");rect(27+i*0.4,hy-6-i,28+i*0.4,hy-6-i,sp.horn||"#d8c08a")}}
  if(hs==="visor")rect(9,hy+1,23,hy+2,"#2a2630");
 }
 if(hs==="hood"||hs==="pointhood"||hs==="beakhood"){
  ell(16,hy-1,12,10.5,HA,(x,y)=>!(y>hy-2&&x>7&&x<25&&y<hy+9));
  rect(4,hy,7,hy+9,HA);rect(25,hy,28,hy+9,HA);
  if(hs==="pointhood")for(let i=0;i<9;i++)rect(16-Math.floor((9-i)/3)+i*0.5,hy-10-i*0.4,17+Math.floor((9-i)/3)+i*0.5,hy-10-i*0.4,HA);
  if(hs==="beakhood"){ell(16,hy-9,6,3,C);for(let i=0;i<6;i++)rect(22+i,hy-2+i*0.4,24+i,hy-1+i*0.4,C)}
 }
 if(sp.leaves){for(let x=5;x<=27;x+=2){ell(x,hy-8+((x*5)%3),2,2,sp.leaves)}for(let i=0;i<5;i++){set(8-i,hy-10-i,"#6b4a2a");set(24+i,hy-10-i,"#6b4a2a")}}
 if(sp.crown)for(let x=10;x<=22;x+=3)rect(x,hy-11,x+1,hy-9,sp.crown);
 // face details
 const ey=hy+2;
 if(sp.face!=="dark"){
  const eye=(x0)=>{if(sp.eyes==="hollow"){rect(x0,ey,x0+2,ey+2,"#2a2028");set(x0+1,ey+1,E);return}
   rect(x0,ey-1,x0+2,ey-1,"#2a2028");                // lash
   rect(x0,ey,x0+2,ey+2,E);rect(x0,ey+2,x0+2,ey+2,mixc(hx(E),[0,0,0],.35));
   set(x0,ey,[255,255,255]);set(x0+2,ey+1,mixc(hx(E),[255,255,255],.5))};
  eye(10);eye(19);
  if(sp.blush!==false){set(9,ey+4,"#f19aa0");set(10,ey+4,"#f19aa0");set(22,ey+4,"#f19aa0");set(23,ey+4,"#f19aa0")}
  if(sp.mouth==="tusk"){rect(14,ey+5,18,ey+5,"#5a2a2a");set(13,ey+4,"#fff4dc");set(19,ey+4,"#fff4dc")}
  else if(sp.mouth==="grin"){rect(13,ey+5,19,ey+5,"#5a2a2a");for(let x=14;x<=18;x+=2)set(x,ey+5,"#fff")}
  else if(sp.mouth==="teeth"){rect(13,ey+4,19,ey+5,"#2a2028");for(let x=13;x<=19;x+=2)set(x,ey+4,"#efe6cf")}
  else{set(15,ey+5,"#a8505a");set(16,ey+5,"#a8505a")}
 }else{ell(16,hy+3,7,5.5,"#141018");set(12,ey+1,E);set(13,ey+1,E);set(19,ey+1,E);set(20,ey+1,E)}
 if(sp.beard){ell(16,hy+9,8,6,sp.beard,(x,y)=>y>=hy+5);rect(14,ey+4,18,ey+4,sp.beard)}
 if(sp.horn1){for(let i=0;i<5;i++)rect(18+i*0.3,hy-9-i,19+i*0.3,hy-9-i,sp.horn1)}
 // ---- shading + soft coloured outline ----
 const out=g.map(r=>r.slice()),filled=(x,y)=>x>=0&&x<W&&y>=0&&y<H&&g[y][x];
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const c=g[y][x];if(!c)continue;
  const same=(xx,yy)=>filled(xx,yy)&&g[yy][xx].join()===c.join();
  if(!same(x,y-1)||!same(x-1,y))out[y][x]=mixc(c,[255,255,255],.18);
  if(!same(x,y+1)||!same(x+1,y))out[y][x]=mixc(c,[20,10,30],.28)}
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(g[y][x])continue;
  const n=[[0,1],[0,-1],[1,0],[-1,0]].map(([dx,dy])=>filled(x+dx,y+dy)?g[y+dy][x+dx]:null).find(Boolean);
  if(n)out[y][x]=mixc(n,[22,12,30],.72)}
 return out;
}
const CHIBI={
 "Stormcast Eternals":{skin:"#f3d3b5",hair:"#e8c35a",hairStyle:"helmet",helm:"#e0b040",c:"#2f6fd0",plume:"#2f6fd0",a:"#e0b040",b:"#2f5fa8",eye:"#3aa0ff",weapon:"hammer",wcol:"#e8eef6"},
 "Cities of Sigmar":{skin:"#f3d3b5",hair:"#6a4428",hairStyle:"short",hairHi:1,a:"#7d8796",b:"#9a2b2b",c:"#e2c35a",eye:"#4a7a3a",weapon:"gun",cape:"#9a2b2b"},
 "Fyreslayers":{skin:"#f0b98e",hair:"#ff6a1a",hairStyle:"mohawk",beard:"#ff7a22",a:"#c9772b",b:"#8a4a1a",c:"#f2c14e",chest:"skin",eye:"#2a2028",weapon:"axe",wcol:"#f2c14e"},
 "Kharadron Overlords":{skin:"#f0c8a0",hair:"#e8e4dc",hairStyle:"helmet",helm:"#4d6b80",c:"#d6a640",beard:"#ece8e0",a:"#4d6b80",b:"#2e4555",eye:"#5ad0ff",weapon:"gun"},
 "Helsmiths of Hashut":{skin:"#b07a62",hair:"#1f1a1a",hairStyle:"horns",helm:"#3b2f2f",horn:"#c4492b",c:"#c4492b",beard:"#1f1a1a",a:"#3b2f2f",b:"#5a2a20",eye:"#ff7a2a",weapon:"hammer",wcol:"#9a8f86"},
 "Lumineth Realm-lords":{skin:"#f6e2d0",hair:"#f6eec8",hairStyle:"long",hairHi:1,ears:"pointy",a:"#f2f4f8",b:"#c8a24a",c:"#4ec3d6",eye:"#3ec6e0",weapon:"spear"},
 "Daughters of Khaine":{skin:"#f6dccb",hair:"#c0182a",hairStyle:"long",hairHi:1,ears:"pointy",a:"#4a1a26",b:"#2a2229",c:"#d7b25a",eye:"#c0182a",weapon:"sword"},
 "Idoneth Deepkin":{skin:"#dbe8ee",hair:"#eaf4f6",hairStyle:"long",hairHi:1,ears:"pointy",a:"#2c8a8c",b:"#1d4f6b",c:"#c2e6dd",eye:"#38d6c6",weapon:"spear",wcol:"#c2e6dd"},
 "Hedonites of Slaanesh":{skin:"#f1d5ea",hair:"#c9a0ff",hairStyle:"long",hairHi:1,ears:"pointy",a:"#8a3f9e",b:"#e2a3d8",c:"#f2d36b",eye:"#ff5ad0",weapon:"sword"},
 "Seraphon":{skin:"#5fb27a",hair:"#d43d3d",hairStyle:"spiky",tail:"lizard",snout:1,a:"#d6a640",b:"#2a7a6a",c:"#4ad0e0",eye:"#ffd02a",weapon:"spear",blush:false},
 "Skaven":{skin:"#c9b8a8",hair:"#7a6455",hairStyle:"hood",ears:"rat",tail:"rat",a:"#4d5a3a",b:"#3a3226",c:"#7dff4a",eye:"#7dff4a",weapon:"dagger",mouth:"teeth"},
 "Sylvaneth":{skin:"#9a7048",hair:"#5f9e3e",leaves:"#6fbf4a",a:"#7a5a3a",b:"#5c4228",c:"#b6ff5a",eye:"#b6ff5a",weapon:"staff",orb:"#b6ff5a",blush:false},
 "Soulblight Gravelords":{skin:"#efe6ea",hair:"#1c1a24",hairStyle:"long",hairHi:1,a:"#6e1a2a",b:"#1c1a24",c:"#c8b06a",eye:"#ff2a3a",weapon:"sword",cape:"#2a0f18",blush:false},
 "Ossiarch Bonereapers":{skin:"#efe6cf",hair:"#3d3a52",hairStyle:"visor",helm:"#e8dfc6",c:"#9b6dd1",plume:"#9b6dd1",eyes:"hollow",a:"#3d3a52",b:"#e8dfc6",eye:"#b98bff",weapon:"spear",mouth:"teeth",blush:false},
 "Nighthaunt":{skin:"#7fe3c8",hair:"#2f6e66",hairStyle:"hood",face:"dark",body:"ghost",a:"#7fe3c8",b:"#5cc1a8",c:"#d6fff4",eye:"#eafffa",weapon:"scythe"},
 "Flesh-eater Courts":{skin:"#d8ccc0",hair:"#f0ece6",hairStyle:"messy",crown:"#d6a640",a:"#6b2230",b:"#3a2a2a",c:"#d6a640",eye:"#ff3b3b",cape:"#6b2230",mouth:"teeth",blush:false},
 "Blades of Khorne":{skin:"#f0c8a8",hair:"#2a1a1a",hairStyle:"horns",helm:"#a51f1f",horn:"#d9c08a",c:"#d9c08a",a:"#a51f1f",b:"#4a3b36",eye:"#ffcc33",weapon:"axe",mouth:"grin"},
 "Slaves to Darkness":{skin:"#e8c8b0",hair:"#2a2a30",hairStyle:"horns",helm:"#3b3f4a",horn:"#c9b77a",c:"#c9b77a",a:"#3b3f4a",b:"#262a33",eye:"#ff4a4a",weapon:"sword",cape:"#5a1a1a"},
 "Disciples of Tzeentch":{skin:"#7fb0ff",hair:"#3f6fd6",hairStyle:"beakhood",c:"#e3b23c",a:"#e3b23c",b:"#3f6fd6",eye:"#ff59e6",weapon:"staff",orb:"#ff59e6"},
 "Maggotkin of Nurgle":{skin:"#a7b86a",hair:"#6f7d3e",hairStyle:"topknot",horn1:"#e8dcb0",body:"wide",belly:"#9aa860",a:"#6f7d3e",b:"#4a5228",c:"#c9b867",eye:"#ffd84a",weapon:"axe",wcol:"#8a7a5a",mouth:"grin",blush:false},
 "Ironjawz":{skin:"#6fae4a",hair:"#4f8a3a",hairStyle:"helmet",helm:"#8a8f96",c:"#e0b830",a:"#c8a32a",b:"#5a5f66",chest:"plate",eye:"#ff4a4a",weapon:"axe",mouth:"tusk",blush:false},
 "Kruleboyz":{skin:"#7aa65a",hair:"#3a3f2a",hairStyle:"hood",a:"#3a3f2a",b:"#5a4a2a",c:"#c9b867",eye:"#ffdf4a",weapon:"spear",mouth:"tusk",blush:false},
 "Gloomspite Gitz":{skin:"#8fca5a",hair:"#26222e",hairStyle:"pointhood",a:"#26222e",b:"#3a3444",c:"#d9c24a",eye:"#ff3b3b",weapon:"dagger",mouth:"grin",blush:false},
 "Ogor Mawtribes":{skin:"#e2b08a",hair:"#3a2a22",hairStyle:"topknot",body:"wide",chest:"plate",a:"#5a3a2a",b:"#3a2a22",c:"#c9c9c9",eye:"#3a2028",weapon:"club",mouth:"grin"},
 "Sons of Behemat":{skin:"#dca07c",hair:"#6b4a2a",hairStyle:"messy",body:"wide",belly:"#dca07c",a:"#6b5a3a",b:"#4a3a2a",c:"#a08050",eye:"#4a6a3a",weapon:"club",mouth:"grin"}
};
