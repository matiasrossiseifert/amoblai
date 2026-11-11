"""El sistema visual: una lámina de interiorismo. Papel claro, tinta, el cobalto de lo que el
sistema elige y el naranja del resaltador; las láminas oscuras son un cianotipo (plano azul)."""

CSS = r"""
:root{
  --papel:#F4F4F0; --papel-2:#ECEDE8; --hoja:#FFFFFF;
  --tinta:#13202C; --tinta-2:#4A5767; --tinta-3:#7E8A98; --hilo:#D5DADD; --hilo-2:#BCC4CA;
  --plano:#173A78; --plano-2:#102C5E; --plano-3:#1E4590; --trazo:#A9C0EC; --trazo-2:#6E8DCB;
  --cobalto:#2453D6; --cobalto-2:#1A3FA8; --cobalto-suave:#DFE6FA;
  --naranja:#FF9A3D; --marcador:#FFC98F; --cota:#E2462F; --verde:#3F8F5A; --grafito:#9AA4AF;
  --sans:'Ubuntu Sans V','Ubuntu Sans',system-ui,sans-serif;
  --mono:'Go Mono','Ubuntu Sans Mono',ui-monospace,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:#0B1A38}
body{font-family:var(--sans);color:var(--tinta);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
#escenario{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;overflow:hidden}
img{display:block}
b,strong{font-weight:640}

/* ------------------------------------------------ láminas */
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;visibility:hidden;opacity:0;
  transition:opacity .32s ease,visibility 0s linear .32s;background:var(--papel);color:var(--tinta);font-stretch:96%}
.slide.activa{visibility:visible;opacity:1;transition:opacity .32s ease}
/* el marco de la lámina, como en una hoja de plano */
.slide::before{content:"";position:absolute;inset:26px 26px 26px 26px;border:1px solid var(--hilo);pointer-events:none}
.oscura{background-color:var(--plano);color:#fff;
  background-image:linear-gradient(rgba(255,255,255,.075) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.075) 1px,transparent 1px),
  linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
  background-size:200px 200px,200px 200px,40px 40px,40px 40px;background-position:-1px -1px}
.oscura::before{border-color:rgba(169,192,236,.35)}
.cuerpo{position:absolute;left:72px;right:72px;top:64px;bottom:118px}

[data-desde]{opacity:0;transform:translateY(14px);transition:opacity .38s ease,transform .38s ease}
[data-desde].visible{opacity:1;transform:none}
svg [data-desde]{transform:none}
[data-hasta].oculto{opacity:0;transition:opacity .25s ease}

/* ------------------------------------------------ tipografía */
.t{font:740 68px/1.02 var(--sans);font-stretch:75%;letter-spacing:-.004em;text-wrap:balance;max-width:1560px}
.t em{font-style:normal;color:var(--cobalto)}
.oscura .t em{color:var(--naranja)}
.bajada{font:400 32px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:18px;max-width:1300px;text-wrap:balance}
.oscura .bajada{color:var(--trazo)}
.etq{font:400 21px/1.2 var(--mono);color:var(--tinta-3);letter-spacing:.01em}
.oscura .etq{color:var(--trazo)}
.etq b{font-weight:700;color:var(--tinta)}
mark{color:inherit;background:linear-gradient(transparent 58%,var(--marcador) 58%,var(--marcador) 92%,transparent 92%);padding:0 .06em}
.oscura mark,.decision mark{background:none;color:var(--naranja);padding:0}
.cita{font-family:var(--sans);font-style:italic;font-stretch:95%}
code,.mono{font-family:var(--mono)}

/* el rótulo de cada lámina: una llamada de detalle de plano (círculo con número y línea) */
.llamada{display:flex;align-items:center;gap:14px;font:400 22px/1 var(--mono);color:var(--cobalto);margin-bottom:22px}
.llamada i{flex:none;width:46px;height:46px;border:1.6px solid currentColor;border-radius:50%;display:grid;place-items:center;font:700 17px/1 var(--mono);font-style:normal}
.llamada s{flex:none;width:44px;height:0;border-top:1.6px solid currentColor;text-decoration:none}
.oscura .llamada{color:var(--naranja)}

/* frase de cierre */
.remate{position:absolute;left:72px;right:72px;bottom:132px;font:700 42px/1.16 var(--sans);font-stretch:82%;letter-spacing:-.002em;text-wrap:balance}
.oscura .remate{color:#fff}

/* ------------------------------------------------ pie: el cajetín */
#pie{position:absolute;left:26px;right:26px;bottom:26px;height:62px;display:flex;align-items:stretch;z-index:5;pointer-events:none;
  border-top:1px solid var(--hilo);font:400 19px/1 var(--mono);color:var(--tinta-3)}
#pie>div{display:flex;align-items:center;padding:0 22px;border-right:1px solid var(--hilo)}
#pie>div:last-child{border-right:0}
#pie .p-marca{width:250px;color:var(--tinta);font-weight:700;letter-spacing:.01em;gap:12px}
#pie .p-sec{flex:1}
#pie .p-sala{width:112px;justify-content:center;padding:0}
#pie .p-sala svg{width:96px;height:58px}
#pie .p-num{width:210px;justify-content:flex-end;color:var(--tinta)}
#pie.sobre-plano{color:var(--trazo);border-color:rgba(169,192,236,.35)}
#pie.sobre-plano>div{border-color:rgba(169,192,236,.35)}
#pie.sobre-plano .p-marca,#pie.sobre-plano .p-num{color:#fff}
#pie.sin,#pie.sin+#barra{display:none}
#barra{position:absolute;left:26px;bottom:24px;height:4px;width:0;background:var(--cobalto);z-index:6;transition:width .3s ease}
#barra.sobre-plano{background:var(--naranja)}

/* ------------------------------------------------ la habitación */
.sala{display:block;overflow:visible;--ink:var(--tinta);--top:#FFFFFF;--sx:#ECEEEC;--sy:#DDE1E2;--wall:#FAFAF7;--floor:#ECEDE7;
  --acc:var(--cobalto);--accs:#D7E1FB;--accx:#C3D2F7;--accy:#AFC2F2;--cot:#E2462F;--vano:#DCE6EE;--fant:var(--cobalto)}
.oscura .sala,.sala.azul{--ink:#E8EFFF;--top:#204A97;--sx:#1C428A;--sy:#183B7D;--wall:#1B4087;--floor:#173A7A;
  --acc:var(--naranja);--accs:rgba(255,154,61,.30);--accx:rgba(255,154,61,.22);--accy:rgba(255,154,61,.16);--cot:var(--naranja);--vano:#21498F;--fant:var(--naranja)}
.sala polygon,.sala path,.sala line{stroke:var(--ink);stroke-width:1.25;stroke-linejoin:round;stroke-linecap:round}
.sala .piso{fill:var(--floor);stroke-width:1.4}
.sala .grilla{fill:none;stroke-width:.6;opacity:.28}
.sala .muro{fill:var(--wall);stroke-width:1.6}
.sala .corte{fill:url(#rayado);stroke-width:1.6}
.oscura .sala .corte,.sala.azul .corte{fill:url(#rayado-o)}
.sala .canto{fill:var(--wall);stroke-width:1.6}
.sala .vano{fill:var(--vano);stroke-width:1}
.sala .jamba{fill:var(--sy)}
.sala .marco{fill:var(--ink);stroke:none}
.oscura .sala .marco,.sala.azul .marco{fill:#CFDCF7}
.sala .baranda{stroke-width:1;opacity:.55}.sala .baranda.f{stroke-width:.7;opacity:.35}
.sala .zoc{stroke-width:.8;opacity:.45}
.sala .aire polygon{fill:var(--top);stroke-width:1}
.sala .m .ft{fill:var(--top)}.sala .m .fx{fill:var(--sx)}.sala .m .fy{fill:var(--sy)}
.sala .m.lana .ft{fill:#FBFAF6}.oscura .sala .m.lana .ft,.sala.azul .m.lana .ft{fill:#22509E}
.sala .m.verde polygon{fill:#A7CBA3}.oscura .sala .m.verde polygon,.sala.azul .m.verde polygon{fill:#2F6E7E}
.sala .m.tela polygon{fill:#FBFBF9;stroke-width:1}.oscura .sala .m.tela polygon,.sala.azul .m.tela polygon{fill:#22509E}
.sala .det{stroke-width:.75;opacity:.55}
.sala .hoja{fill:none;stroke-width:1.25}.sala .hoja.f{stroke-width:.9}
.sala .m{transition:opacity .35s ease}
.sala .m.nuevo polygon,.sala .m.nuevo path{stroke:var(--acc);stroke-width:1.9}
.sala .m.nuevo .ft{fill:var(--accs)}.sala .m.nuevo .fx{fill:var(--accx)}.sala .m.nuevo .fy{fill:var(--accy)}
.sala .m.apagado{opacity:.28}
.sala .cota line{stroke:var(--cot);stroke-width:1.2}
.sala .cota .ref{stroke-width:.8;opacity:.6}
.sala .ct{fill:var(--cot);font-family:var(--mono);stroke:none}
/* cajas de alambre: fantasmas del plan y cajas 3D */
.sala .fantasma .ar,.sala .caja3d .ar{stroke:var(--fant);stroke-width:1.8;stroke-dasharray:7 6}
.sala .fantasma .oc,.sala .caja3d .oc{stroke:var(--fant);stroke-width:1;stroke-dasharray:2 5;opacity:.7}
.sala .fantasma polygon{fill:var(--fant);fill-opacity:.07;stroke:none}
.sala .caja3d .ar{stroke-dasharray:none;stroke-width:2}
.sala .caja3d .cf{fill:var(--fant);fill-opacity:.16;stroke:none}.sala .caja3d .cf2{fill:var(--fant);fill-opacity:.10;stroke:none}
.sala .caja3d .ct2{fill:var(--fant);fill-opacity:.24;stroke:none}
.sala .caja3d.sin .ar{stroke-dasharray:8 6;stroke:var(--cot)}
.sala .caja3d.sin polygon{fill:var(--cot)}
/* rótulos sobre el dibujo */
.sala .rot .lin{fill:none;stroke-width:1.2}
.sala .rot .pto{fill:var(--ink);stroke:none}
.sala .rot .rt{font:500 21px var(--sans);font-stretch:85%;fill:var(--ink);stroke:none}
.sala .rot .rs{font:400 16px var(--mono);fill:var(--ink);opacity:.7;stroke:none}
.sala .rot .rt,.sala .rot .rs{paint-order:stroke fill;stroke:var(--halo,#F4F4F0);stroke-width:6px;stroke-linejoin:round}
.oscura .sala,.sala.azul{--halo:#173A78}
.sala .rot.acc .lin{stroke:var(--acc)}.sala .rot.acc .pto{fill:var(--acc)}.sala .rot.acc .rt{fill:var(--acc);font-weight:700}
.sala .rot .num{fill:var(--acc);stroke:none}.sala .rot .numt{font:700 16px var(--mono);fill:#fff;stroke:none}
.oscura .sala .rot .numt,.sala.azul .rot .numt{fill:var(--plano)}
.sala .preg circle{fill:var(--naranja);stroke:none}
.sala .preg text{font:800 26px var(--sans);fill:var(--tinta);stroke:none;text-anchor:middle}
.sala .preg .halo{fill:var(--naranja);opacity:.25}

/* ------------------------------------------------ piezas comunes */
.hoja{background:var(--hoja);border:1px solid var(--hilo);box-shadow:0 1px 0 rgba(19,32,44,.05),0 22px 40px -28px rgba(19,32,44,.45)}
.oscura .hoja{border:0;color:var(--tinta);box-shadow:0 2px 0 rgba(0,0,0,.2),0 30px 60px -24px rgba(0,0,0,.55)}
.foto{position:relative;background:#fff;padding:8px;box-shadow:0 1px 0 rgba(19,32,44,.06),0 24px 40px -26px rgba(19,32,44,.55)}
.foto img{width:100%;height:100%;object-fit:cover}
.foto figcaption,.pie-foto{font:400 17px/1.3 var(--mono);color:var(--tinta-3);margin-top:10px}
.oscura .pie-foto{color:var(--trazo)}
.chip{display:inline-flex;align-items:center;font:400 19px/1 var(--mono);padding:9px 13px;border-radius:3px;background:var(--papel-2);color:var(--tinta-2);white-space:nowrap}
.chip.si{background:var(--cobalto);color:#fff}
.chip.v0{background:none;box-shadow:inset 0 0 0 1px var(--hilo-2);color:var(--tinta-3)}
.chip.pend{background:none;box-shadow:inset 0 0 0 1.4px var(--cota);color:var(--cota)}
.sello{position:absolute;left:14px;top:14px;font:700 15px/1 var(--mono);padding:7px 10px;border-radius:2px;color:#fff;background:var(--cota);letter-spacing:.02em}
.sello.ok{background:var(--verde)}
.sello.neutro{background:var(--tinta)}

/* ficha de producto */
.ficha{position:relative;display:flex;flex-direction:column;gap:8px;width:var(--fs);margin:0}
.ficha .fi{position:relative;width:var(--fs);height:var(--fs);background:#fff;border:1px solid var(--hilo);display:grid;place-items:center}
.ficha .fi img{width:100%;height:100%;object-fit:contain}
.ficha.hi .fi{border:2.5px solid var(--cobalto);box-shadow:0 0 0 4px var(--cobalto-suave)}
.ficha .pos{position:absolute;left:0;top:0;min-width:30px;height:30px;padding:0 6px;display:grid;place-items:center;background:var(--tinta);color:#fff;font:700 16px/1 var(--mono)}
.ficha.hi .pos{background:var(--cobalto)}
.ficha .cant{position:absolute;right:6px;top:6px;font:700 16px/1 var(--mono);color:var(--cobalto)}
.ficha .tag{position:absolute;left:50%;bottom:-12px;transform:translateX(-50%);background:var(--cobalto);color:#fff;font:700 14px/1 var(--mono);padding:5px 8px;white-space:nowrap}
.ficha figcaption{display:flex;flex-direction:column;gap:3px}
.ficha figcaption b{font:600 19px/1.15 var(--sans);font-stretch:88%}
.ficha figcaption span{font:400 14px/1.25 var(--mono);color:var(--tinta-3)}
.ficha .notas{display:flex;gap:3px;height:7px}
.ficha .notas i{flex:1;border-radius:1px}
.ficha .notas i.g2{background:var(--verde)}.ficha .notas i.g1{background:#E8B04B}.ficha .notas i.g0{background:var(--cota)}

/* ------------------------------------------------ experimentos */
.xcab{display:flex;justify-content:space-between;align-items:flex-start;gap:40px}
.xcab .llamada{margin-bottom:0}
.pasos-x{display:flex;align-items:flex-end;gap:0;font:400 17px/1 var(--mono);color:var(--tinta-3);margin-top:2px}
.pasos-x span{display:flex;flex-direction:column;gap:9px;width:150px;position:relative}
.pasos-x span::after{content:"";height:3px;background:var(--hilo);display:block}
.pasos-x span::before{content:"";position:absolute;left:0;bottom:-5px;height:13px;border-left:1.4px solid var(--hilo-2)}
.pasos-x span:last-child{width:150px}
.pasos-x span.hecho{color:var(--tinta-2)}.pasos-x span.hecho::after{background:var(--tinta-2)}
.pasos-x span.ahora{color:var(--cobalto);font-weight:700}.pasos-x span.ahora::after{background:var(--cobalto)}
.xt{margin-top:26px}
.xg{position:absolute;left:72px;right:72px;top:262px;bottom:236px;display:grid;grid-template-columns:560px 1fr;column-gap:64px}
.xg.ancho{grid-template-columns:470px 1fr;column-gap:52px}
.xl{display:flex;flex-direction:column;gap:30px;min-height:0}
.bloque .bt{font:400 19px/1 var(--mono);color:var(--cobalto);margin-bottom:12px;display:flex;align-items:center;gap:10px}
.bloque .bt::after{content:"";flex:1;border-top:1px solid var(--hilo)}
.bloque p,.bloque li{font:400 27px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.bloque p+p{margin-top:10px}
.bloque p strong,.bloque li strong{color:var(--tinta)}
.bloque ul{list-style:none;display:flex;flex-direction:column;gap:8px}
.bloque li{padding-left:28px;position:relative}
.bloque li::before{content:"";position:absolute;left:2px;top:.62em;width:14px;border-top:2px solid var(--cobalto)}
.xr{position:relative;min-width:0;min-height:0}
.decision{position:absolute;left:72px;right:72px;bottom:118px;min-height:96px;background:var(--plano);color:#fff;display:grid;grid-template-columns:200px 1fr;align-items:center;column-gap:28px;padding:22px 36px}
.decision .k{font:400 20px/1.2 var(--mono);color:var(--trazo);display:flex;align-items:center;gap:10px}
.decision .k::before{content:"";width:12px;height:12px;background:var(--naranja);display:block}
.decision p{font:400 28px/1.3 var(--sans);font-stretch:90%}
.decision p strong{font-weight:700;color:var(--naranja)}

/* ------------------------------------------------ gráficos */
.graf{display:block;overflow:visible;font-family:var(--sans)}
.graf text{fill:var(--tinta)}
.graf .lab{font:500 27px var(--sans);font-stretch:88%}
.graf .sub{font:400 17px var(--mono);fill:var(--tinta-3)}
.graf .val{font:700 26px var(--mono)}
.graf .val.main{fill:var(--cobalto)}
.graf .tick{font:400 18px var(--mono);fill:var(--tinta-3)}
.graf .eje{stroke:var(--hilo-2);stroke-width:1}
.graf .riel{fill:var(--papel-2)}
.graf .bar{transition:transform .7s cubic-bezier(.2,.7,.2,1);transform-box:fill-box;transform-origin:left center}
.graf .bar.main{fill:var(--cobalto)}.graf .bar.alt{fill:var(--grafito)}.graf .bar.muted{fill:#C9CFD5}.graf .bar.ink{fill:var(--tinta)}.graf .bar.good{fill:var(--verde)}
.graf .ic line{stroke:var(--tinta);stroke-width:2}
.graf .ic rect{fill:var(--tinta);opacity:.12}
.graf .ref line{stroke:var(--cota);stroke-width:1.6;stroke-dasharray:5 5}
.graf .ref text{font:400 18px var(--mono);fill:var(--cota)}
.graf .grid line{stroke:var(--hilo);stroke-width:1}
.graf .leyenda{font:400 18px var(--mono);fill:var(--tinta-2)}
.graf [data-desde]{transition:opacity .45s ease}
.graf .res .bar{transform:scaleX(0)}
.graf .res.visible .bar{transform:scaleX(1)}
.graf .res [data-crece]{transition:transform .7s cubic-bezier(.2,.7,.2,1);transform-box:fill-box;transform-origin:left center}
.graf .linea{fill:none;stroke-width:3.4;stroke-linejoin:round;stroke-linecap:round}
.graf .linea.trazo{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 1s ease}
.graf .res.visible .linea.trazo{stroke-dashoffset:0}
.ley{display:flex;flex-wrap:wrap;gap:8px 26px;font:400 18px/1.2 var(--mono);color:var(--tinta-2);margin-bottom:14px}
.ley i{display:inline-block;width:18px;height:10px;margin-right:9px;vertical-align:1px}
.nota{font:400 19px/1.4 var(--mono);color:var(--tinta-3);margin-top:12px}
.nota b{color:var(--tinta);font-weight:700}

/* ------------------------------------------------ portada y separadores */
.portada .p-txt{position:absolute;left:96px;top:150px;width:820px}
.portada h1{font:780 210px/.86 var(--sans);font-stretch:75%;letter-spacing:-.018em;margin:18px 0 40px}
.portada h1 em{font-style:normal;color:var(--naranja)}
.portada .p-baj{font:400 38px/1.24 var(--sans);font-stretch:90%;color:#fff;text-wrap:balance}
.portada .p-baj span{color:var(--trazo)}
.portada .equipo{position:absolute;left:96px;bottom:104px;font:500 27px/1.42 var(--sans);font-stretch:90%}
.portada .equipo .etq{display:block;margin-bottom:12px}
.portada .p-sala{position:absolute;right:30px;top:40px;width:1090px}
.separador .s-num{font:780 260px/.8 var(--sans);font-stretch:75%;color:transparent;-webkit-text-stroke:2px var(--trazo-2);letter-spacing:-.02em}
.separador .s-txt{position:absolute;left:96px;top:150px;width:760px}
.separador h2{font:760 96px/.98 var(--sans);font-stretch:75%;letter-spacing:-.012em;margin:30px 0 26px;text-wrap:balance}
.separador h2 em{font-style:normal;color:var(--naranja)}
.separador .s-baj{font:400 32px/1.3 var(--sans);font-stretch:92%;color:var(--trazo);text-wrap:balance}
.separador .s-lista{list-style:none;margin-top:44px;display:grid;gap:12px}
.separador .s-lista li{display:grid;grid-template-columns:76px 1fr;align-items:baseline;font:400 28px/1.2 var(--sans);font-stretch:90%}
.separador .s-lista b{font:700 22px/1 var(--mono);color:var(--naranja)}
.separador .s-sala{position:absolute;right:40px;top:70px;width:1000px}

/* ------------------------------------------------ índice, negro, notas */
#negro{position:fixed;inset:0;background:#000;display:none;z-index:40}
#negro.abierto{display:block}
#indice{position:fixed;inset:0;background:#0B1A38;z-index:30;display:none;overflow:auto;padding:36px}
#indice.abierto{display:block}
#indice-grilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}
.mini-l{border:0;background:none;padding:0;color:#fff;font:400 16px/1.25 var(--mono);text-align:left;cursor:pointer}
.mini-v{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;margin-bottom:8px;pointer-events:none}
.mini-v .slide{opacity:1;visibility:visible;transform-origin:0 0;transition:none}
.mini-v [data-desde]{opacity:1;transform:none}
.mini-v .graf .res .bar{transform:none}
.mini-l.actual .mini-v{outline:4px solid var(--naranja)}
#notas{position:fixed;left:0;right:0;bottom:0;max-height:40vh;overflow:auto;background:rgba(11,26,56,.96);color:#fff;font:400 20px/1.45 var(--sans);padding:18px 28px;z-index:20;display:none;border-top:3px solid var(--naranja)}
#notas.abierto{display:block}
#notas h5{font:700 15px/1 var(--mono);color:var(--naranja);margin-bottom:10px}
#notas p{margin-bottom:8px}
#notas .np{color:var(--naranja);font-family:var(--mono);font-size:.85em}
body.todo [data-desde],body:not(.listo) .slide,body:not(.listo) [data-desde]{transition:none!important}
body.todo .graf .bar,body.todo .graf .linea{transition:none!important}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important}}
@media print{
  @page{size:1920px 1080px;margin:0}
  html,body{height:auto;overflow:visible;background:none}
  #escenario{position:static;transform:none!important;width:auto;height:auto;overflow:visible}
  .slide{position:relative;opacity:1;visibility:visible;break-after:page;transition:none}
  [data-desde]{opacity:1!important;transform:none!important}
  .graf .res .bar{transform:none!important}
  #pie,#barra,#indice,#negro,#notas{display:none!important}
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

JS = r"""
(function(){
  'use strict';
  var $=function(s,r){return (r||document).querySelector(s);};
  var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));};
  var esc=$('#escenario');
  var lam=$$('#escenario > .slide');
  var N=lam.filter(function(s){return !s.dataset.anexo;}).length;
  var TODO=/[?&]all/.test(location.search);
  if(TODO) document.body.classList.add('todo');
  var NOTAS=window.__NOTAS||[];
  var cur=0,paso=0;
  function pasosDe(i){var m=0;$$('[data-desde]',lam[i]).forEach(function(e){m=Math.max(m,+e.dataset.desde);});return m;}
  function escalar(){var s=Math.min(innerWidth/1920,innerHeight/1080);esc.style.transform='translate('+((innerWidth-1920*s)/2)+'px,'+((innerHeight-1080*s)/2)+'px) scale('+s+')';}
  function aplicar(s,p){
    $$('[data-desde]',s).forEach(function(e){e.classList.toggle('visible',+e.dataset.desde<=p);});
    $$('[data-hasta]',s).forEach(function(e){e.classList.toggle('oculto',p>=+e.dataset.hasta);});
    $$('[data-en]',s).forEach(function(e){e.classList.toggle('actual',e.dataset.en.split(' ').indexOf(String(p))!==-1);});
    var fs=s.dataset.fases;
    var px=$('.pasos-x',s);
    if(px){var f=fs?+fs.split(',')[Math.min(p,fs.split(',').length-1)]:p;$$('span',px).forEach(function(e,i){e.classList.toggle('hecho',i<f);e.classList.toggle('ahora',i===f);});}
    // capas de la habitación: data-capas='{"0":"a b","1":"c"}' → clases on/off por paso
    if(s.dataset.capas){var c=JSON.parse(s.dataset.capas);var on=(c[p]||'').split(' ');
      $$('[data-capa]',s).forEach(function(e){var ks=e.dataset.capa.split(' ');e.classList.toggle('on',ks.some(function(k){return on.indexOf(k)!==-1;}));});}
  }
  function dibujar(){
    lam.forEach(function(s,i){s.classList.toggle('activa',i===cur);});
    var s=lam[cur];aplicar(s,paso);
    var osc=s.classList.contains('oscura');
    var pie=$('#pie');pie.classList.toggle('sobre-plano',osc);pie.classList.toggle('sin',s.classList.contains('sin-pie'));
    $('#barra').classList.toggle('sobre-plano',osc);
    $('#p-sec').textContent=s.dataset.seccion||'';
    $('#p-num').textContent=s.dataset.anexo?('anexo '+s.dataset.anexo):('lámina '+(cur+1)+' / '+N);
    var mini=$('#p-sala');var m=$('template.mini-'+(s.dataset.cap||'0'));mini.innerHTML=m?m.innerHTML:'';
    var pl=$('#p-planta');if(pl){var ks=(s.dataset.planta||'').split(' ').filter(Boolean);pl.classList.toggle('vacia',!ks.length);if(ks.length){if(!pl.firstChild){var tl=$('template.llave');pl.innerHTML=tl?tl.innerHTML:'';}$$('[data-f]',pl).forEach(function(e){e.classList.toggle('act',ks.indexOf(e.dataset.f)!==-1);});}}
    var tot=pasosDe(cur)+1;
    $('#barra').style.width=((s.dataset.anexo?1:(cur+(paso+1)/tot)/N)*1868)+'px';
    var nt=$('#notas');nt.innerHTML='<h5>'+(cur+1)+' · '+(s.dataset.titulo||'')+' · paso '+(paso+1)+'/'+tot+'</h5>'+(NOTAS[cur]||'');
    try{history.replaceState(null,'',location.pathname+location.search+'#/'+(cur+1)+(paso?'.'+paso:''));}catch(e){}
  }
  function ir(i,p){cur=Math.max(0,Math.min(lam.length-1,i));var m=pasosDe(cur);paso=TODO?m:(p==='fin'?m:Math.max(0,Math.min(m,p||0)));dibujar();}
  function sig(){if(paso<pasosDe(cur)){paso++;dibujar();}else if(cur<N-1)ir(cur+1,0);}
  function ant(){if(paso>0){paso--;dibujar();}else if(cur>0)ir(cur-1,'fin');}
  var indice=$('#indice');
  function abrirIndice(a){indice.classList.toggle('abierto',a);if(!a)return;var g=$('#indice-grilla');
    if(!g.children.length){lam.forEach(function(s,i){var b=document.createElement('button');b.className='mini-l';var v=document.createElement('div');v.className='mini-v';
      var c=s.cloneNode(true);c.classList.add('activa');v.appendChild(c);b.appendChild(v);
      b.appendChild(document.createTextNode((s.dataset.anexo?'anexo '+s.dataset.anexo:(i+1))+' · '+(s.dataset.titulo||'')));
      b.addEventListener('click',function(){abrirIndice(false);ir(i,0);});g.appendChild(b);});}
    $$('.mini-l',indice).forEach(function(b,i){b.classList.toggle('actual',i===cur);var v=$('.mini-v',b);$('.slide',v).style.transform='scale('+v.clientWidth/1920+')';});}
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey)return;var ab=indice.classList.contains('abierto');
    switch(e.key){
      case 'ArrowRight':case 'ArrowDown':case 'PageDown':case ' ':case 'Enter': if(!ab){sig();e.preventDefault();}break;
      case 'ArrowLeft':case 'ArrowUp':case 'PageUp':case 'Backspace': if(!ab){ant();e.preventDefault();}break;
      case 'Home': ir(0,0);e.preventDefault();break;
      case 'End': ir(N-1,0);e.preventDefault();break;
      case 'f':case 'F': if(document.fullscreenElement)document.exitFullscreen();else if(document.documentElement.requestFullscreen)document.documentElement.requestFullscreen().catch(function(){});break;
      case 'o':case 'O': abrirIndice(!ab);break;
      case 'b':case 'B': $('#negro').classList.toggle('abierto');break;
      case 'n':case 'N': $('#notas').classList.toggle('abierto');break;
      case 'Escape': abrirIndice(false);$('#negro').classList.remove('abierto');if(lam[cur].dataset.anexo)ir(N-1,0);break;
    }
  });
  esc.addEventListener('click',function(e){if(e.target.closest('[data-ir]')){ir(+e.target.closest('[data-ir]').dataset.ir,0);return;}var x=e.clientX/innerWidth;if(x<0.2)ant();else sig();});
  $('#negro').addEventListener('click',function(){this.classList.remove('abierto');});
  var x0=null;
  addEventListener('touchstart',function(e){x0=e.changedTouches[0].clientX;},{passive:true});
  addEventListener('touchend',function(e){if(x0===null)return;var d=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(d)>50){if(d<0)sig();else ant();}},{passive:true});
  addEventListener('resize',function(){escalar();if(indice.classList.contains('abierto'))abrirIndice(true);});
  var m=location.hash.match(/^#\/?(\d+)(?:\.(\d+))?/);
  escalar();ir(m?+m[1]-1:0,m&&m[2]?+m[2]:0);requestAnimationFrame(function(){requestAnimationFrame(function(){document.body.classList.add('listo');});});
  addEventListener('hashchange',function(){var mm=location.hash.match(/^#\/?(\d+)(?:\.(\d+))?/);if(mm){var i=+mm[1]-1,p=mm[2]?+mm[2]:0;if(i!==cur||p!==paso)ir(i,p);}});
})();
"""
