"""CSS y JS de la presentación (separados del contenido)."""

CSS = r"""
:root{
  --lino:#F2ECE2; --lino-2:#E9E1D3; --papel:#FBF8F2;
  --nogal:#2B211B; --nogal-2:#5D4F45; --nogal-3:#8B7C70;
  --hilo:#DDD3C4; --hilo-2:#C4B6A3;
  --terracota:#B0502A; --terracota-2:#D9825E; --terracota-suave:#F1DED1;
  --salvia:#56785D; --salvia-suave:#DCE6D9;
  --ocre:#C68F2B; --ocre-suave:#F4E6C6;
  --grafito:#7E858C; --grafito-suave:#E3E3DF;
  --noche:#221B16; --noche-2:#2F261F; --noche-tx:#EDE5D8; --noche-tx2:#B9AC9C;
  --serif:'Noto Serif Display','Noto Serif',Georgia,serif;
  --sans:'Cabin','Segoe UI',system-ui,sans-serif;
  --mono:'Ubuntu Sans Mono','DejaVu Sans Mono',ui-monospace,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#16120f;overflow:hidden}
body{font-family:var(--sans);color:var(--nogal);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
img{display:block}
b,strong{font-weight:600}
#stage{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;overflow:hidden;background:var(--lino)}
.slide{position:absolute;inset:0;width:1920px;height:1080px;padding:70px 104px 112px;background:var(--lino);
  display:flex;flex-direction:column;opacity:0;visibility:hidden;transition:opacity .3s ease,visibility 0s linear .3s;overflow:hidden}
.slide.on{opacity:1;visibility:visible;transition:opacity .3s ease}
[data-step]{transition:opacity .4s ease,transform .4s ease}
.off{opacity:0!important;transform:translateY(12px);pointer-events:none}
svg .off{transform:none}
[data-until]{transition:opacity .3s ease}
.gone{opacity:0!important;pointer-events:none}
body.static *{transition:none!important;animation:none!important}

/* ---------- encabezado ---------- */
.hd{display:grid;grid-template-columns:1fr auto;column-gap:48px;align-items:start;margin-bottom:30px}
.eb{font:500 21px/1 var(--mono);color:var(--terracota);display:flex;align-items:center;gap:12px;margin-bottom:18px}
.eb i.sw{width:13px;height:13px;background:var(--terracota);display:inline-block}
.eb .dim{color:var(--nogal-3)}
h2.t{font:400 58px/1.08 var(--serif);letter-spacing:-.012em;color:var(--nogal);text-wrap:balance;max-width:1340px}
h2.t em{font-style:italic;color:var(--terracota)}
.lead{font:400 27px/1.42 var(--sans);color:var(--nogal-2);max-width:1280px;margin-top:16px;text-wrap:pretty}
.lead strong{color:var(--nogal)}

/* ---------- pasos de un experimento ---------- */
.steps{display:flex;align-items:center;list-style:none;margin-top:4px}
.steps .s{display:flex;align-items:center;gap:10px;font:500 18px/1 var(--mono);color:var(--nogal-3);white-space:nowrap}
.steps .s i{width:30px;height:30px;border-radius:50%;border:1.6px solid var(--hilo-2);display:grid;place-items:center;font:600 15px/1 var(--mono);font-style:normal;color:var(--nogal-3)}
.steps .bar{width:26px;height:1.6px;background:var(--hilo-2);margin:0 10px}
.steps .s.done{color:var(--nogal-2)}
.steps .s.done i{background:var(--nogal);border-color:var(--nogal);color:var(--lino)}
.steps .s.cur{color:var(--nogal);font-weight:700}
.steps .s.cur i{background:var(--terracota);border-color:var(--terracota);color:#fff}

.blk{margin-bottom:30px}
.blk:last-child{margin-bottom:0}
.lbl{font:600 18px/1 var(--mono);color:var(--terracota);display:flex;align-items:center;gap:10px;margin-bottom:12px}
.lbl b{width:24px;height:24px;border-radius:50%;background:var(--terracota);color:#fff;display:grid;place-items:center;font:600 13px/1 var(--mono)}
.blk p,.blk li{font:400 24px/1.42 var(--sans);color:var(--nogal-2);text-wrap:pretty}
.blk p+p{margin-top:10px}
.blk strong,.blk b.k{color:var(--nogal);font-weight:600}
.blk ul{list-style:none;display:flex;flex-direction:column;gap:8px;margin-top:8px}
.blk li{padding-left:26px;position:relative}
.blk li::before{content:"";position:absolute;left:2px;top:15px;width:12px;height:1.6px;background:var(--terracota)}
code,.mono{font-family:var(--mono);font-size:.88em;color:var(--nogal)}

.xg{flex:1;display:grid;grid-template-columns:660px 1fr;column-gap:64px;min-height:0}
.xg.wide{grid-template-columns:560px 1fr}
.xl{display:flex;flex-direction:column}
.res{position:relative;min-height:0}
.res .rin{height:100%;display:flex;flex-direction:column;justify-content:center}
.ph{position:absolute;inset:0;border:1.6px dashed var(--hilo-2);border-radius:4px;display:grid;place-items:center;
  background:repeating-linear-gradient(135deg,transparent 0 16px,rgba(196,182,163,.18) 16px 17px);
  font:500 20px/1 var(--mono);color:var(--nogal-3)}
.ph span{background:var(--lino);padding:10px 16px}
.dec{margin-top:26px;background:var(--noche);color:var(--noche-tx);border-radius:4px;padding:22px 32px;display:grid;grid-template-columns:150px 1fr;column-gap:24px;align-items:baseline}
.dec .k{font:600 18px/1.3 var(--mono);color:var(--ocre)}
.dec p{font:400 25px/1.4 var(--sans);text-wrap:pretty}
.dec p strong{color:#fff}
.note{font:400 18px/1.4 var(--sans);color:var(--nogal-3);margin-top:14px}
.note b{color:var(--nogal-2)}
.cap{font:400 16px/1.35 var(--mono);color:var(--nogal-3)}

/* ---------- tarjetas y piezas ---------- */
.card{background:var(--papel);border:1px solid var(--hilo);border-radius:6px;padding:28px 30px}
.card h3{font:600 26px/1.25 var(--sans);color:var(--nogal);margin-bottom:10px}
.card p{font:400 22px/1.45 var(--sans);color:var(--nogal-2)}
.chip{display:inline-flex;align-items:center;gap:8px;font:500 18px/1 var(--mono);padding:9px 14px;border-radius:999px;border:1.4px solid var(--hilo-2);color:var(--nogal-2);background:transparent;white-space:nowrap}
.chip.si{background:var(--terracota);border-color:var(--terracota);color:#fff}
.chip.pend{border-style:dashed;color:var(--nogal-3)}
.chip.v0{background:var(--grafito-suave);border-color:var(--grafito-suave)}
.etag{display:inline-block;font:600 16px/1 var(--mono);color:var(--terracota);background:var(--terracota-suave);padding:7px 10px;border-radius:4px;white-space:nowrap}
.etag.pend{color:var(--nogal-3);background:var(--lino-2)}
.quote{font:italic 400 27px/1.42 var(--serif);color:var(--nogal);position:relative;padding-left:34px;text-wrap:pretty}
.quote::before{content:"«";position:absolute;left:0;top:-6px;font:400 54px/1 var(--serif);color:var(--terracota)}
.big{font:400 76px/1 var(--serif);color:var(--nogal);letter-spacing:-.01em}
.big.t{color:var(--terracota)}
.kl{font:400 20px/1.35 var(--sans);color:var(--nogal-2);margin-top:8px}

.ficha{width:var(--fs);margin:0;display:flex;flex-direction:column;gap:8px}
.ficha .fph{position:relative;width:var(--fs);height:var(--fs);background:#fff;border:1px solid var(--hilo);border-radius:3px;overflow:hidden}
.ficha .fph img{width:100%;height:100%;object-fit:contain}
.ficha.hi .fph{box-shadow:0 0 0 4px var(--terracota);border-color:var(--terracota)}
.ficha .qty{position:absolute;right:7px;top:7px;background:var(--terracota);color:#fff;font:700 17px/1 var(--mono);padding:6px 8px;border-radius:12px}
.ficha .rk{position:absolute;left:6px;top:6px;font:600 16px/1 var(--mono);color:var(--nogal);background:rgba(255,255,255,.92);border:1px solid var(--hilo);padding:4px 7px;border-radius:3px}
.ficha.hi .rk{background:var(--terracota);color:#fff;border-color:var(--terracota)}
.ficha .ftag{position:absolute;left:0;right:0;bottom:0;background:var(--terracota);color:#fff;font:600 14px/1 var(--mono);padding:6px 8px;text-align:center}
.ficha .fcap b{display:block;font:500 16px/1.25 var(--sans);color:var(--nogal);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ficha .fcap span{display:block;font:400 14px/1.3 var(--mono);color:var(--nogal-3);margin-top:3px}
.grades{display:flex;gap:4px}
.grades i{flex:1;height:7px;border-radius:2px;display:block}
.grades i.g2{background:var(--salvia)} .grades i.g1{background:var(--ocre)} .grades i.g0{background:var(--terracota)}

.foto{margin:0}
.foto .fimg{position:relative;background:#fff;padding:8px;box-shadow:0 1px 0 rgba(43,33,27,.06),0 24px 44px -26px rgba(43,33,27,.6)}
.foto .fimg img{width:100%;height:100%;object-fit:cover}
.foto figcaption{font:400 16px/1.35 var(--mono);color:var(--nogal-3);margin-top:12px}
.foto .badge{position:absolute;left:18px;top:18px;font:600 16px/1 var(--mono);padding:7px 10px;border-radius:3px;background:rgba(34,27,22,.82);color:#fff}
.foto .badge.ok{background:var(--salvia)} .foto .badge.no{background:var(--terracota)}

/* ---------- gráficos SVG ---------- */
svg.chart{display:block;overflow:visible}
svg text{font-family:var(--sans)}
.c-tick{font:400 17px var(--mono);fill:var(--nogal-3)}
.c-lab{font:400 22px var(--sans);fill:var(--nogal)}
.c-lab.b{font-weight:600}
.c-sub{font:400 17px var(--sans);fill:var(--nogal-3)}
.c-sub.b{font-weight:600;fill:var(--nogal-2)}
.c-val{font:600 21px var(--mono);fill:var(--nogal)}
.c-val.m{fill:var(--terracota)}
.c-note{font:italic 400 17px var(--sans);fill:var(--nogal-2)}
.legend{display:flex;gap:26px;font:400 18px/1 var(--sans);color:var(--nogal-2);margin-bottom:14px;flex-wrap:wrap}
.legend i{display:inline-block;width:16px;height:16px;border-radius:50%;vertical-align:-2px;margin-right:8px}

/* ---------- diagrama de arquitectura ---------- */
svg.arch{width:100%;height:auto;display:block;overflow:visible}
.arch .ab rect,.arch .ab-llm rect,.arch .ab-out rect{fill:var(--papel);stroke:var(--hilo-2);stroke-width:1.6}
.arch .ab-llm rect{fill:#FFFDF9;stroke:var(--nogal-2)}
.arch .ab-out rect{fill:var(--terracota-suave);stroke:var(--terracota);stroke-width:2.4}
.arch .ab-t{font:600 25px var(--sans);fill:var(--nogal)}
.arch .ab-l{font:400 19px var(--sans);fill:var(--nogal-2)}
.arch .ab-tag{font:600 16px var(--mono);fill:var(--terracota)}
.arch .ab-rag{font:500 17px var(--mono);fill:var(--terracota)}
.arch .ab-lane{font:500 17px var(--mono);fill:var(--nogal-3)}
.arch .aa{fill:none;stroke:var(--nogal-2);stroke-width:1.8}
.arch .aa.dash{stroke-dasharray:5 6}
.arch .ab-badge rect{fill:var(--nogal);stroke:none}
.arch .ab-badge text{font:700 16px var(--mono);fill:#fff}

/* ---------- separadores ---------- */
.slide.div{background:var(--noche);color:var(--noche-tx);padding:0}
.div .dl{position:absolute;left:104px;top:150px;width:760px}
.div .dk{font:500 22px/1 var(--mono);color:var(--ocre);margin-bottom:26px}
.div h2{font:400 92px/1.02 var(--serif);letter-spacing:-.015em;color:var(--noche-tx);text-wrap:balance}
.div h2 em{font-style:italic;color:var(--terracota-2)}
.div .ds{font:400 29px/1.45 var(--sans);color:var(--noche-tx2);margin-top:28px;text-wrap:pretty}
.div ol{list-style:none;margin-top:44px;display:flex;flex-direction:column;gap:14px;border-top:1px solid #4a3d33;padding-top:26px}
.div ol li{font:400 23px/1.3 var(--sans);color:var(--noche-tx);display:grid;grid-template-columns:70px 1fr;align-items:baseline}
.div ol li b{font:600 19px/1 var(--mono);color:var(--terracota-2)}
.div .dr{position:absolute;right:70px;top:120px;width:900px}
svg.planta{width:100%;height:auto;display:block;overflow:visible}
.planta .pl-old{fill:none;stroke:#CDBFAE;stroke-opacity:.55;stroke-width:1.8}
.planta .pl-new{fill:rgba(217,130,94,.22);stroke:var(--terracota-2);stroke-width:2.4}
.planta .pl-lab{font:500 18px var(--mono);fill:#A8998A}
.planta .pl-tag{font:600 19px var(--mono);fill:var(--terracota-2)}

/* ---------- portada ---------- */
.slide.cover{padding:0}
.cover .cl{position:absolute;left:104px;top:120px;width:700px}
.cover h1{font:400 178px/.92 var(--serif);letter-spacing:-.03em;color:var(--nogal);margin:26px 0 30px}
.cover h1 em{font-style:italic;color:var(--terracota)}
.cover .sub{font:400 33px/1.36 var(--sans);color:var(--nogal-2);text-wrap:pretty}
.cover .team{position:absolute;left:104px;bottom:96px;font:400 23px/1.6 var(--sans);color:var(--nogal-2)}
.cover .team b{color:var(--nogal);font-weight:600}
.split{position:absolute;right:104px;top:150px;width:940px;height:705px;background:#fff;padding:10px;box-shadow:0 30px 60px -30px rgba(43,33,27,.6)}
.split .in{position:relative;width:100%;height:100%;overflow:hidden}
.split img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.split .after{clip-path:inset(0 0 0 50%)}
.split .line{position:absolute;top:0;bottom:0;left:50%;width:3px;margin-left:-1.5px;background:#fff}
.split .knob{position:absolute;top:50%;left:50%;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.25);display:grid;place-items:center;font:700 18px/1 var(--mono);color:var(--nogal)}
.slide.on .split .after{animation:sweep 1.8s cubic-bezier(.6,.05,.25,1) .5s both}
.slide.on .split .line,.slide.on .split .knob{animation:slide 1.8s cubic-bezier(.6,.05,.25,1) .5s both}
@keyframes sweep{from{clip-path:inset(0 0 0 100%)}to{clip-path:inset(0 0 0 50%)}}
@keyframes slide{from{left:100%}to{left:50%}}
.split .lab{position:absolute;bottom:18px;font:600 17px/1 var(--mono);color:#fff;background:rgba(34,27,22,.78);padding:8px 12px;border-radius:3px}
.split .lab.a{left:18px} .split .lab.b{right:18px}
.cover .scap{position:absolute;right:104px;top:880px;width:940px;font:400 16px/1.4 var(--mono);color:var(--nogal-3)}

/* ---------- tablas de variantes, línea de tiempo ---------- */
.vt{display:grid;grid-template-columns:270px 1fr 140px;column-gap:28px;border-top:1px solid var(--hilo)}
.vt>div{border-bottom:1px solid var(--hilo);padding:10px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap;min-height:58px}
.vt .st{font:600 21px/1.2 var(--sans);color:var(--nogal)}
.vt .ex{justify-content:flex-end;gap:6px}
.vt .hdr{font:500 16px/1 var(--mono);color:var(--nogal-3);min-height:40px}

.tl{position:relative;flex:1}
.tl .axis{position:absolute;left:0;right:0;top:50%;height:2px;background:var(--nogal-2)}
.tl .ev{position:absolute;width:390px}
.tl .ev .dot{position:absolute;left:-9px;width:18px;height:18px;border-radius:50%;background:var(--lino);border:3px solid var(--nogal)}
.tl .ev.v0 .dot{border-color:var(--grafito)}
.tl .ev.next .dot{border-style:dashed;border-color:var(--terracota)}
.tl .ev .stem{position:absolute;left:0;width:1.5px;background:var(--hilo-2)}
.tl .ev .bx{position:absolute;left:-2px;width:390px;padding-left:18px;border-left:3px solid var(--terracota)}
.tl .ev.v0 .bx{border-left-color:var(--grafito)}
.tl .ev.next .bx{border-left-style:dashed}
.tl .ev .dt{font:600 18px/1 var(--mono);color:var(--terracota);margin-bottom:8px}
.tl .ev.v0 .dt{color:var(--grafito)}
.tl .ev h4{font:600 23px/1.2 var(--sans);color:var(--nogal);margin-bottom:6px}
.tl .ev p{font:400 18px/1.38 var(--sans);color:var(--nogal-2)}

/* ---------- juez de a pares ---------- */
.jg{display:grid;grid-template-columns:repeat(11,1fr);gap:10px}
.jr{display:flex;flex-direction:column;gap:6px;align-items:center}
.jr .th{width:100%;aspect-ratio:4/3;background:#ddd;border-radius:2px;overflow:hidden}
.jr .th img{width:100%;height:100%;object-fit:cover}
.jr .v{display:flex;gap:6px}
.jr .v i{width:22px;height:22px;border-radius:50%;display:block;border:2px solid transparent}
.vi{background:var(--grafito)} .vt2{background:var(--terracota)} .vtie{background:transparent;border-color:var(--hilo-2)!important}
.jr .w{font:600 15px/1 var(--mono);color:var(--nogal-2);text-align:center;min-height:16px}
.jr .w.t{color:var(--terracota)}
.jr .nm{font:400 14px/1.2 var(--mono);color:var(--nogal-3);text-align:center;min-height:34px}

/* ---------- HUD, notas, índice ---------- */
#hud{position:absolute;left:104px;right:104px;bottom:38px;height:26px;display:flex;align-items:center;gap:28px;font:500 16px/1 var(--mono);color:var(--nogal-3);pointer-events:none;z-index:5}
#hud .sec{width:250px;white-space:nowrap}
#hud .rule{flex:1;position:relative;height:16px}
#hud .rule .ln{position:absolute;left:0;right:0;top:8px;height:1px;background:var(--hilo-2)}
#hud .rule .fill{position:absolute;left:0;top:7px;height:3px;background:var(--terracota);width:0;transition:width .3s ease}
#hud .rule .tk{position:absolute;top:2px;width:1px;height:13px;background:var(--hilo-2)}
#hud .num{width:110px;text-align:right}
#stage.dark #hud{color:#8E8072}
#stage.dark #hud .rule .ln,#stage.dark #hud .rule .tk{background:#4f4237}
#stage.nohud #hud{display:none}
#notes{position:fixed;left:0;right:0;bottom:0;max-height:42vh;overflow:auto;background:rgba(22,18,15,.96);color:#EDE5D8;font:400 17px/1.5 var(--sans);padding:18px 28px;display:none;z-index:50;border-top:2px solid var(--terracota)}
#notes.open{display:block}
#notes h5{font:600 14px/1 var(--mono);color:var(--ocre);margin:10px 0 6px}
#hint{position:fixed;right:18px;top:14px;z-index:40;font:500 13px/1.6 var(--mono);color:#A8998A;text-align:right;transition:opacity .6s;pointer-events:none}
#hint.fade{opacity:0}
#ov{position:fixed;inset:0;background:rgba(22,18,15,.97);z-index:60;display:none;overflow:auto;padding:30px}
#ov.open{display:block}
#ov .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
#ov .th{position:relative;aspect-ratio:16/9;border:1.5px solid #4a3d33;border-radius:6px;overflow:hidden;cursor:pointer;background:var(--lino)}
#ov .th.cur,#ov .th:hover{border-color:var(--terracota-2)}
#ov .th .mini{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;pointer-events:none}
#ov .th .mini .slide{opacity:1;visibility:visible}
#ov .th .mini .off,#ov .th .mini .gone{opacity:1!important;transform:none}
#ov .th .mini .ph{display:none}
#ov .th .n{position:absolute;right:6px;bottom:6px;z-index:2;font:600 12px/1 var(--mono);background:rgba(22,18,15,.85);color:#EDE5D8;padding:4px 7px;border-radius:4px}
#black{position:fixed;inset:0;background:#000;z-index:90;display:none}
#black.open{display:block}
"""

JS = r"""
(function(){
  'use strict';
  var stage=document.getElementById('stage');
  var slides=[].slice.call(stage.querySelectorAll(':scope > .slide'));
  var N=slides.length, cur=0, step=0;
  var ALL=/[?&]all/.test(location.search);
  if(/[?&](all|static)/.test(location.search)) document.body.classList.add('static');
  var NOTES=window.__NOTES||[];
  function maxStep(s){var m=0;s.querySelectorAll('[data-step]').forEach(function(e){var v=+e.getAttribute('data-step');if(v>m)m=v;});return m;}
  function phase(s,st){var p=s.getAttribute('data-phases');if(p){p=p.split(',');return +p[Math.min(st,p.length-1)];}var po=+(s.getAttribute('data-po')||0);return po+st;}
  function render(){
    slides.forEach(function(s,i){s.classList.toggle('on',i===cur);});
    var s=slides[cur];
    s.querySelectorAll('[data-step]').forEach(function(e){e.classList.toggle('off',+e.getAttribute('data-step')>step);});
    s.querySelectorAll('[data-until]').forEach(function(e){e.classList.toggle('gone',step>=+e.getAttribute('data-until'));});
    var st=s.querySelector('.steps');
    if(st){var ph=phase(s,step);st.querySelectorAll('.s').forEach(function(e,i){e.classList.toggle('done',i<ph);e.classList.toggle('cur',i===ph);});}
    stage.classList.toggle('dark',s.classList.contains('div'));
    stage.classList.toggle('nohud',s.classList.contains('cover'));
    document.getElementById('hud-sec').textContent=s.getAttribute('data-sec')||'';
    document.getElementById('hud-num').textContent=(cur+1)+' / '+N;
    document.getElementById('hud-fill').style.width=((cur+(step+1)/(maxStep(s)+1))/N*100)+'%';
    var nt=document.getElementById('notes');
    nt.innerHTML='<h5>'+(cur+1)+' · '+(s.getAttribute('data-title')||'')+'</h5>'+(NOTES[cur]||'');
    var h='#/'+(cur+1)+(step?'.'+step:'');
    try{history.replaceState(null,'',location.pathname+location.search+h);}catch(e){}
  }
  function go(i,st){cur=Math.max(0,Math.min(N-1,i));var m=maxStep(slides[cur]);step=ALL?m:(st==='end'?m:Math.min(st||0,m));render();}
  function next(){if(step<maxStep(slides[cur])){step++;render();}else if(cur<N-1)go(cur+1,0);}
  function prev(){if(step>0){step--;render();}else if(cur>0)go(cur-1,'end');}
  function fit(){var s=Math.min(innerWidth/1920,innerHeight/1080);var x=(innerWidth-1920*s)/2,y=(innerHeight-1080*s)/2;stage.style.transform='translate('+x+'px,'+y+'px) scale('+s+')';}
  addEventListener('resize',fit);fit();
  // marcas de sección en la regla del HUD
  var rule=document.getElementById('hud-rule'),last=null;
  slides.forEach(function(s,i){var sec=s.getAttribute('data-sec');if(sec!==last&&i>0){var t=document.createElement('i');t.className='tk';t.style.left=(i/N*100)+'%';rule.appendChild(t);}last=sec;});
  // índice
  var ovBuilt=false;
  function buildOv(){if(ovBuilt)return;ovBuilt=true;var g=document.getElementById('ov-grid');
    slides.forEach(function(s,i){var th=document.createElement('div');th.className='th';var m=document.createElement('div');m.className='mini';
      var c=s.cloneNode(true);c.classList.add('on');m.appendChild(c);th.appendChild(m);
      var n=document.createElement('span');n.className='n';n.textContent=(i+1)+' · '+(s.getAttribute('data-title')||'');th.appendChild(n);
      th.addEventListener('click',function(){toggleOv(false);go(i,0);});g.appendChild(th);});
    sizeOv();}
  function sizeOv(){document.querySelectorAll('#ov .th').forEach(function(th,i){th.querySelector('.mini').style.transform='scale('+(th.clientWidth/1920)+')';th.classList.toggle('cur',i===cur);});}
  function toggleOv(f){var o=document.getElementById('ov');var open=f!==undefined?f:!o.classList.contains('open');if(open){buildOv();o.classList.add('open');sizeOv();}else o.classList.remove('open');}
  addEventListener('resize',function(){if(ovBuilt)sizeOv();});
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey)return;
    var ov=document.getElementById('ov').classList.contains('open');
    switch(e.key){
      case 'ArrowRight':case ' ':case 'PageDown':case 'ArrowDown': if(!ov){next();e.preventDefault();}break;
      case 'ArrowLeft':case 'PageUp':case 'ArrowUp': if(!ov){prev();e.preventDefault();}break;
      case 'Home': go(0,0);break;
      case 'End': go(N-1,0);break;
      case 'f':case 'F': if(document.fullscreenElement)document.exitFullscreen();else if(document.documentElement.requestFullscreen)document.documentElement.requestFullscreen();break;
      case 'o':case 'O': toggleOv();break;
      case 'n':case 'N': document.getElementById('notes').classList.toggle('open');break;
      case 'b':case 'B': document.getElementById('black').classList.toggle('open');break;
      case 'Escape': toggleOv(false);document.getElementById('black').classList.remove('open');break;
    }
  });
  stage.addEventListener('click',function(e){if(String(window.getSelection&&window.getSelection()))return;var x=e.clientX/innerWidth;if(x<0.2)prev();else next();});
  document.getElementById('black').addEventListener('click',function(){this.classList.remove('open');});
  setTimeout(function(){var h=document.getElementById('hint');if(h)h.classList.add('fade');},6000);
  var m=location.hash.match(/^#\/(\d+)(?:\.(\d+))?/);
  go(m?+m[1]-1:0,m&&m[2]?+m[2]:0);
  addEventListener('hashchange',function(){var mm=location.hash.match(/^#\/(\d+)(?:\.(\d+))?/);if(mm){var i=+mm[1]-1,s=mm[2]?+mm[2]:0;if(i!==cur||s!==step)go(i,s);}});
})();
"""
