"""La hoja de estilo. Concepto: «el flujo y la lista». Pizarra verde de tienda (tablero perforado),
el esquema del sistema en tiza clara, y encima los objetos de la compra: etiquetas de producto,
tickets y talones. El coral de las etiquetas de precio marca la etapa que se prueba y lo que queda."""

CSS = r"""
:root{
  --noche:#0A130F;
  --fondo:#0F1F19;
  --fondo-2:#152921;
  --fondo-3:#1C3329;
  --perfo:rgba(214,236,224,.055);
  --hilo-o:rgba(214,236,224,.13);
  --crema:#F3F0E7;
  --trazo:#A6C2B4;
  --trazo-2:#6F8E80;
  --trazo-3:#4A6659;
  --papel:#EDF0EA;
  --papel-2:#E2E7E0;
  --ticket:#FFFEFA;
  --tinta:#10201A;
  --tinta-2:#4F6158;
  --tinta-3:#86968E;
  --hilo:#CDD6CF;
  --coral:#FF5B3F;
  --coral-2:#E8462A;
  --coral-s:rgba(255,91,63,.15);
  --salvia:#B7CDC2;
  --salvia-2:#8FA99C;
  --display:'Ubuntu Sans','Ubuntu',system-ui,sans-serif;
  --sans:'Ubuntu Sans','Ubuntu',system-ui,sans-serif;
  --mono:'Ubuntu Sans Mono','Ubuntu Mono',ui-monospace,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--noche);overflow:hidden}
body{font-family:var(--sans);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;font-variant-numeric:lining-nums}
h1,h2,h3,h4,p,ul,ol,figure,blockquote,dl,dd{margin:0;padding:0}
ul,ol{list-style:none}
#escenario{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;overflow:hidden;background:var(--fondo)}

/* ---------- láminas ---------- */
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;opacity:0;visibility:hidden;
  transition:opacity .32s ease,visibility 0s linear .32s;padding:78px 96px 0;color:var(--crema);background-color:var(--fondo);
  background-image:radial-gradient(circle,var(--perfo) 1.6px,transparent 1.9px);background-size:36px 36px;background-position:18px 18px}
.slide.activa{opacity:1;visibility:visible;transition:opacity .32s ease}
.slide.clara{color:var(--tinta);background-color:var(--papel);
  background-image:radial-gradient(circle,rgba(16,32,26,.075) 1.5px,transparent 1.8px)}
[data-paso]{opacity:0;transform:translateY(14px);transition:opacity .38s ease,transform .38s ease}
[data-paso].visto{opacity:1;transform:none}
[data-hasta]{transition:opacity .3s ease}
[data-hasta].oculto{opacity:0;pointer-events:none}
.todo [data-paso]{opacity:1!important;transform:none!important;transition:none!important}
.todo [data-hasta]{opacity:0!important}

/* ---------- tipografía ---------- */
.kick{display:flex;align-items:center;gap:14px;font:500 21px/1 var(--mono);color:var(--coral);letter-spacing:.01em}
.kick b{font-weight:600;border:1.6px solid currentColor;border-radius:5px;padding:5px 9px 4px;letter-spacing:.02em}
.clara .kick{color:var(--coral-2)}
.t{font:780 70px/1.04 var(--display);font-stretch:80%;letter-spacing:-.006em;margin-top:22px;max-width:1560px;text-wrap:balance}
.t.chico{font-size:60px}
.t em{font-style:normal;color:var(--coral)}
.clara .t em{color:var(--coral-2)}
.lead{font:400 34px/1.32 var(--sans);color:var(--trazo);margin-top:22px;max-width:1300px;text-wrap:pretty}
.clara .lead{color:var(--tinta-2)}
.lead b{color:var(--crema);font-weight:600}
.clara .lead b{color:var(--tinta)}
mark{color:inherit;background:linear-gradient(transparent 80%,var(--coral) 80%,var(--coral) 93%,transparent 93%);padding:0 .04em}
.remate{position:absolute;left:96px;right:96px;bottom:110px;font:720 46px/1.14 var(--display);font-stretch:84%;letter-spacing:-.004em;text-wrap:balance;max-width:1600px}
.et{font:500 19px/1.2 var(--mono);color:var(--trazo-2);letter-spacing:.01em}
.clara .et{color:var(--tinta-3)}
.mono{font-family:var(--mono)}
code{font:500 .86em var(--mono);background:var(--fondo-3);padding:2px 8px;border-radius:4px;color:var(--crema)}
.clara code{background:var(--papel-2);color:var(--tinta)}

/* ---------- fotos y productos ---------- */
.foto{background-size:cover;background-position:center;background-repeat:no-repeat;background-color:var(--fondo-3);flex:none;border-radius:4px}
.prod{background-size:contain;background-position:center;background-repeat:no-repeat;background-color:#fff;flex:none;background-origin:content-box}
.clara .prod{mix-blend-mode:multiply}

/* etiqueta de producto (colgante) */
.etq{position:relative;background:var(--ticket);color:var(--tinta);border-radius:8px;padding:16px 14px 12px;box-shadow:0 1px 0 rgba(0,0,0,.18),0 16px 30px -18px rgba(0,0,0,.6)}
.etq::before{content:"";position:absolute;left:50%;top:7px;width:9px;height:9px;margin-left:-4.5px;border-radius:50%;background:var(--fondo);box-shadow:inset 0 0 0 1.5px rgba(16,32,26,.25)}
.clara .etq::before{background:var(--papel)}
.etq .prod{width:100%!important;aspect-ratio:1;height:auto!important}
.etq .art{display:block;font:500 15px/1.2 var(--mono);color:var(--tinta-3);margin-top:8px;letter-spacing:.02em}
.etq .nom{display:block;font:700 21px/1.1 var(--display);font-stretch:85%;margin-top:3px}

/* ticket */
.ticket{position:relative;background:var(--ticket);color:var(--tinta);font-family:var(--mono);padding:30px 32px 30px;
  box-shadow:0 30px 50px -26px rgba(0,0,0,.7)}
.ticket::before,.ticket::after{content:"";position:absolute;left:0;right:0;height:12px;background-size:16px 12px;background-repeat:repeat-x}
.ticket::before{top:-11px;background-image:linear-gradient(45deg,transparent 50%,var(--ticket) 50%),linear-gradient(-45deg,transparent 50%,var(--ticket) 50%);background-position:0 0,0 0}
.ticket::after{bottom:-11px;background-image:linear-gradient(135deg,var(--ticket) 50%,transparent 50%),linear-gradient(-135deg,var(--ticket) 50%,transparent 50%)}
.tk-cab{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px dashed var(--hilo);padding-bottom:14px;margin-bottom:12px}
.tk-cab b{font:780 34px/1 var(--display);font-stretch:80%}
.tk-cab span{font:400 16px/1.2 var(--mono);color:var(--tinta-3);text-align:right}
.tk-l{display:flex;align-items:baseline;gap:10px;font:400 19px/1.25 var(--mono);padding:6px 0;white-space:nowrap}
.tk-l .tk-q{color:var(--tinta-3);width:34px;flex:none}
.tk-l .tk-n{font-weight:600;overflow:hidden;text-overflow:ellipsis}
.tk-l .tk-dots{flex:1;border-bottom:2px dotted var(--hilo);transform:translateY(-5px);min-width:20px}
.tk-l .tk-v{color:var(--tinta-2)}
.tk-tot{display:flex;justify-content:space-between;border-top:2px dashed var(--hilo);margin-top:12px;padding-top:14px;font:600 20px/1.2 var(--mono)}
.tk-pie{font:400 15px/1.35 var(--mono);color:var(--tinta-3);margin-top:12px}
.barras-cod{display:block}
.barras-cod rect{fill:currentColor}

/* talón: la decisión de cada experimento */
.talon{position:absolute;left:96px;right:96px;bottom:100px;display:grid;grid-template-columns:300px 1fr;background:var(--ticket);color:var(--tinta);
  border-radius:6px;box-shadow:0 22px 40px -24px rgba(16,32,26,.55),0 0 0 1px rgba(16,32,26,.06);min-height:124px}
.talon-cod{position:relative;padding:16px 22px 14px 28px;display:flex;flex-direction:column;justify-content:center;border-right:2.5px dashed var(--hilo);color:var(--tinta-2)}
.talon-cod::before,.talon-cod::after{content:"";position:absolute;right:-12px;width:22px;height:22px;border-radius:50%;background:var(--papel)}
.slide:not(.clara) .talon-cod::before,.slide:not(.clara) .talon-cod::after{background:var(--fondo)}
.talon-cod::before{top:-11px}.talon-cod::after{bottom:-11px}
.talon-cod span{font:500 14px/1 var(--mono);color:var(--tinta-3);letter-spacing:.03em}
.talon-cod i{font:500 17px/1 var(--mono);font-style:normal;color:var(--tinta-2);margin-top:9px}
.talon-cod b{font:800 38px/1 var(--display);font-stretch:76%;color:var(--coral-2);margin:4px 0 9px;white-space:nowrap}
.talon-cod .barras-cod{color:var(--tinta);opacity:.75}
.talon-txt{padding:20px 40px;display:flex;align-items:center;font:700 32px/1.22 var(--display);font-stretch:86%}
.talon-txt span{text-wrap:balance}
.talon-txt b{color:var(--coral-2)}

/* ---------- el esquema del flujo ---------- */
.flujo{display:block;width:100%;height:auto;overflow:visible;font-family:var(--sans)}
.flujo .reg{fill:rgba(255,255,255,.018);stroke:var(--trazo-3);stroke-width:1.4}
.flujo .reg-i{stroke-dasharray:5 7}
.flujo .reg-t{font:500 17px var(--mono);fill:var(--trazo-2);letter-spacing:.02em}
.flujo .fl{fill:none;stroke:var(--trazo-2);stroke-width:2.2}
.flujo .fl-d{stroke-dasharray:4 6}
.flujo .fl-t{font:500 15px var(--mono);fill:var(--trazo-2)}
.flujo .caja{fill:var(--fondo-2);stroke:var(--trazo-2);stroke-width:1.6;transition:stroke .25s,fill .25s}
.flujo .ico{color:var(--trazo);transition:color .25s}
.flujo .nom{font:760 27px var(--display);font-stretch:84%;fill:var(--crema);transition:fill .25s}
.flujo .sub{font:400 15.5px var(--mono);fill:var(--trazo-2);transition:fill .25s}
.flujo [data-k],.flujo .lineas{transition:opacity .3s ease}
.flujo.foco [data-k]:not(.on),.flujo.foco .lineas{opacity:.26}
.flujo .on .caja{stroke:var(--coral);stroke-width:3;fill:#2A2A20;fill:color-mix(in srgb,var(--coral) 13%,var(--fondo-2))}
.flujo .on .ico{color:var(--coral)}
.flujo .on .nom{fill:var(--coral)}
.flujo .on .sub{fill:var(--trazo)}
.flujo .on.reg,.flujo g.on>.reg{stroke:var(--coral);stroke-width:2.2}
.flujo g.on>.reg-t{fill:var(--coral)}
.flujo .pin circle{fill:var(--coral);stroke:var(--fondo);stroke-width:4}
.flujo .pin text{font:800 21px var(--display);font-stretch:80%;fill:var(--noche)}
.flujo .cfg rect{fill:var(--ticket)}
.flujo .cfg text{font:600 16px var(--mono);fill:var(--tinta)}
.flujo .fut rect{fill:var(--fondo);stroke:var(--coral);stroke-width:2;stroke-dasharray:6 5}
.flujo .fut use{color:var(--coral)}
.flujo .fut text{font:600 17px var(--mono);fill:var(--coral)}
.sin-texto .flujo text{display:none}

/* el esquema grande a la derecha (como en las láminas de experimento) */
.esq{position:absolute;left:944px;top:100px;width:884px}
.izq{position:absolute;left:96px;top:78px;width:790px}

/* ---------- gráficos ---------- */
.graf-b{width:100%}
.gb-tit{font:500 20px/1.2 var(--mono);color:var(--tinta-3);margin-bottom:14px}
.gb-fila{display:grid;grid-template-columns:var(--gb-et,360px) 1fr 120px;align-items:center;column-gap:22px;min-height:var(--gb-h,70px)}
.gb-eje{min-height:34px;align-items:end}
.gb-eje .gb-pista{height:26px}
.gb-eje .gb-pista span{position:absolute;bottom:4px;transform:translateX(-50%);font:400 16px var(--mono);color:var(--tinta-3)}
.gb-et{display:flex;align-items:center;gap:14px;font:600 25px/1.15 var(--sans)}
.gb-et small{display:block;font:400 16px/1.25 var(--mono);color:var(--tinta-3);margin-top:3px}
.gb-l,.letra{display:inline-grid;place-items:center;flex:none;min-width:36px;height:36px;padding:0 6px;border-radius:5px;background:var(--tinta);color:var(--papel);font:700 19px/1 var(--mono);font-style:normal}
.gb-pista{position:relative;height:var(--gb-bar,30px)}
.gb-pista>i{position:absolute;top:-8px;bottom:-8px;width:1px;background:var(--hilo)}
.gb-lleno{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--salvia-2);border-radius:0 3px 3px 0;opacity:1!important;transform:none!important;transition:width .7s cubic-bezier(.3,.7,.2,1),background-color .3s}
.gb-lleno.visto{width:var(--v)}
.todo .gb-lleno{width:var(--v);transition:none}
.gb-ics{position:absolute;inset:0}
.gb-ic{position:absolute;top:50%;height:2px;margin-top:-1px;background:var(--tinta)}
.gb-ic::before,.gb-ic::after{content:"";position:absolute;top:-8px;width:2px;height:18px;background:var(--tinta)}
.gb-ic::before{left:0}.gb-ic::after{right:0}
.gb-val{font:800 34px/1 var(--display);font-stretch:80%;color:var(--tinta);font-variant-numeric:tabular-nums}
.gb-fila.gana .gb-lleno{background:var(--coral)}
.gb-fila.gana .gb-val{color:var(--coral-2)}
.gb-fila.gana .gb-l{background:var(--coral-2)}
.graf-b.oscuro .gb-tit,.graf-b.oscuro .gb-eje .gb-pista span,.graf-b.oscuro .gb-et small{color:var(--trazo-2)}
.graf-b.oscuro .gb-pista>i{background:var(--hilo-o)}
.graf-b.oscuro .gb-lleno{background:var(--trazo-2)}
.graf-b.oscuro .gb-val{color:var(--crema)}
.graf-b.oscuro .gb-ic,.graf-b.oscuro .gb-ic::before,.graf-b.oscuro .gb-ic::after{background:var(--crema)}
.graf-b.oscuro .gb-l{background:var(--crema);color:var(--fondo)}

.graf-l{display:block;overflow:visible}
.gl-grilla{stroke:var(--hilo);stroke-width:1}
.gl-grilla.v{stroke-dasharray:2 5}
.gl-eje{font:400 17px var(--mono);fill:var(--tinta-3)}
.gl-xlab{font:500 17px var(--mono);fill:var(--tinta-3)}
.gl-banda{fill:var(--salvia);opacity:.55}
.gl-serie polyline{fill:none;stroke:var(--tinta);stroke-width:3.2;stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 1s ease}
.gl-serie.visto polyline,.todo .gl-serie polyline{stroke-dashoffset:0}
.gl-serie circle{fill:var(--tinta)}
.gl-serie.punt polyline{stroke:var(--salvia-2);stroke-width:2.6;stroke-dasharray:1;}
.gl-serie.punt circle{fill:var(--papel);stroke:var(--salvia-2);stroke-width:2.6}
.gl-et{font:500 18px var(--mono);fill:var(--tinta-2)}
.gl-marca circle{fill:none;stroke:var(--tinta);stroke-width:2.4}
.gl-marca text{font:700 22px var(--mono);fill:var(--tinta)}
.gl-marca.gana circle{stroke:var(--coral);stroke-width:3.4}
.gl-marca.gana text{fill:var(--coral-2)}

/* variantes del experimento */
.variantes{display:grid;gap:16px}
.variantes li{display:grid;grid-template-columns:auto 1fr;gap:18px;align-items:start}
.variantes b{display:block;font:700 30px/1.1 var(--display);font-stretch:86%}
.variantes span{display:block;font:400 22px/1.3 var(--sans);color:var(--trazo);margin-top:4px}
.variantes .letra{background:var(--crema);color:var(--fondo);margin-top:-1px}
.clara .variantes span{color:var(--tinta-2)}
.clara .variantes .letra{background:var(--tinta);color:var(--papel)}

/* ---------- interfaz ---------- */
#hud{position:absolute;left:96px;right:96px;bottom:0;height:58px;display:flex;align-items:center;gap:16px;font:400 18px/1 var(--mono);color:var(--trazo-2);z-index:5;pointer-events:none}
#hud i{flex:1;height:0;border-bottom:2px dotted currentColor;opacity:.5;transform:translateY(2px)}
#hud b{font-weight:600}
#hud.sobre-clara{color:var(--tinta-3)}
#hud.oculto{opacity:0}
#barra{position:absolute;left:0;bottom:0;height:6px;width:0;background:var(--coral);transition:width .32s ease;z-index:6}
#negro{position:fixed;inset:0;background:#000;display:none;z-index:40}
#negro.abierto{display:block}
#indice{position:fixed;inset:0;background:var(--noche);z-index:30;display:none;overflow:auto;padding:34px}
#indice.abierto{display:block}
#indice-grilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:24px}
.mini-l{border:0;background:none;padding:0;color:var(--crema);font:400 16px/1.3 var(--mono);text-align:left;cursor:pointer}
.mini-v{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;border-radius:4px;margin-bottom:8px;pointer-events:none}
.mini-v .slide{opacity:1;visibility:visible;transform-origin:0 0;transition:none}
.mini-l.actual .mini-v{outline:4px solid var(--coral)}
#notas{position:fixed;left:0;right:0;bottom:0;max-height:38vh;overflow:auto;background:rgba(10,19,15,.95);color:var(--crema);font:400 19px/1.45 var(--sans);padding:18px 28px;z-index:20;display:none;border-top:3px solid var(--coral)}
body.con-notas #notas{display:block}
#notas b{color:var(--coral)}
#ayuda{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;font:400 13px/1.4 var(--mono);color:rgba(243,240,231,.6);background:rgba(10,19,15,.8);padding:6px 10px;z-index:10;pointer-events:none;transition:opacity .8s}
body.sin-ayuda #ayuda{opacity:0}
#p-panel{display:none}
body.presentador #ayuda{display:none}
body.presentador #p-panel{display:grid;position:fixed;inset:0;grid-template-columns:minmax(0,62fr) minmax(0,38fr);grid-template-rows:auto 1fr;gap:16px;padding:16px;color:var(--crema);font-family:var(--sans);pointer-events:none}
#p-sig{position:relative;aspect-ratio:16/9;overflow:hidden;border-radius:4px;outline:1px solid var(--hilo-o)}
#p-sig .slide{opacity:1;visibility:visible;transform-origin:0 0;transition:none}
#p-info{grid-column:2;grid-row:2;overflow:auto;pointer-events:auto}
#p-reloj{font:800 54px/1 var(--display);font-stretch:80%;color:var(--coral)}
#p-plan{font:400 16px/1.3 var(--mono);color:var(--trazo);margin:8px 0 14px}
#p-notas{font:400 21px/1.42 var(--sans)}
#p-notas p{margin-bottom:12px}
#p-notas b{color:var(--coral)}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important}}
@media print{
  @page{size:1920px 1080px;margin:0}
  html,body{height:auto;overflow:visible;background:none}
  #escenario{position:static;transform:none!important;width:auto;height:auto;overflow:visible}
  .slide{position:relative;opacity:1;visibility:visible;break-after:page;transition:none}
  [data-paso]{opacity:1!important;transform:none!important}
  .gb-lleno{width:var(--v)!important}
  #hud,#barra,#ayuda,#indice,#notas,#p-panel,#negro{display:none!important}
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

CSS += r"""
/* =========================== láminas =========================== */
/* portada y gracias */
.portada{padding:0}
.esq-portada{position:absolute;left:860px;top:40px;width:1120px;opacity:.5;
  -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 34%);mask-image:linear-gradient(90deg,transparent 0,#000 34%)}
.portada-txt{position:absolute;left:96px;top:170px;width:900px}
.marca{font:800 260px/.86 var(--display);font-stretch:78%;letter-spacing:-.02em;margin:34px 0 34px -8px;color:var(--crema)}
.marca.gracias{font-size:220px}
.portada-preg{font:400 46px/1.18 var(--sans);color:var(--trazo)}
.portada-preg em{font-style:normal;color:var(--crema);font-weight:600}
.equipo{margin-top:56px;display:grid;gap:6px;font:500 28px/1.25 var(--sans)}

/* problema */
.pb-tres{display:grid;grid-template-columns:520px 520px 520px;gap:68px;margin-top:52px}
.pb-p figcaption{font:400 25px/1.32 var(--sans);color:var(--trazo);margin-top:18px;text-wrap:pretty}
.pb-p figcaption b{color:var(--crema);font-weight:600}
.pb-p.tuyo .foto{outline:3px solid var(--coral);outline-offset:6px}
.pb-tags{height:390px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px 0;align-content:center;justify-items:center}
.pb-tags .etq{transform:rotate(var(--r,0deg));padding:14px 12px 8px}
.pb-tags .etq .nom{font-size:17px}.pb-tags .etq .art{font-size:13px;margin-top:4px}
.pb-preg{position:absolute;left:96px;right:96px;bottom:104px;display:grid;grid-template-columns:repeat(3,1fr);gap:68px;border-top:2px dotted var(--trazo-3);padding-top:26px}
.pb-preg li{display:flex;gap:16px;align-items:baseline;font:700 30px/1.18 var(--display);font-stretch:86%}
.pb-preg b{font:600 22px/1 var(--mono);color:var(--coral);flex:none}

/* producto */
.pr-pie{font:400 20px/1.3 var(--mono);color:var(--trazo-2);margin-top:12px}

/* por qué RAG */
.rag-tres{display:grid;grid-template-columns:1fr 1fr 1.18fr;gap:56px;margin-top:50px;align-items:start}
.rag-c h3{font:760 34px/1.08 var(--display);font-stretch:84%}
.rag-c>p{font:400 24px/1.3 var(--sans);color:var(--tinta-2);margin:8px 0 30px;min-height:62px}
.rag-c.elegida h3{color:var(--coral-2)}
.rag-tk{padding:22px 24px}
.rag-tk .tk-cab b{font-size:28px}
.rag-tk .tk-l{font-size:18px}
.tk-vacio{font:400 40px/1 var(--mono);color:var(--hilo);text-align:center;padding:18px 0 8px}
.sello-tk{display:inline-block;margin-top:16px;font:700 17px/1 var(--mono);color:var(--coral-2);border:2.5px solid var(--coral-2);border-radius:5px;padding:7px 10px 6px;transform:rotate(-3deg);text-transform:uppercase;letter-spacing:.06em}
.rag-c.elegida .ticket{outline:3px solid var(--coral);outline-offset:-3px}
.rag-c.elegida .tk-q{color:var(--coral-2);font-weight:700}

/* catálogo */
.cat-izq{position:absolute;left:96px;top:250px;width:760px}
.cifra{display:flex;align-items:baseline;gap:22px;font:800 190px/.9 var(--display);font-stretch:76%;letter-spacing:-.01em}
.cifra i{font:300 90px/1 var(--sans);color:var(--trazo-2);font-style:normal}
.cifra .co{color:var(--coral)}
.cifra-pie{font:400 25px/1.32 var(--sans);color:var(--trazo);margin-top:14px;max-width:700px}
.cifras-ch{display:flex;gap:44px;margin-top:24px}
.cifras-ch div{font:400 22px/1.2 var(--sans);color:var(--trazo)}
.cifras-ch b{display:block;font:800 60px/1 var(--display);font-stretch:78%;color:var(--crema)}
.fuente{font:400 18px/1.3 var(--mono);color:var(--trazo-2);margin-top:20px}
.problemas{margin-top:30px;padding-top:20px;border-top:1px solid var(--hilo-o)}
.problemas ul{display:grid;gap:8px;margin-top:12px}
.problemas li{font:400 24px/1.3 var(--sans);color:var(--trazo);padding-left:28px;position:relative}
.problemas li::before{content:"";position:absolute;left:0;top:13px;width:14px;height:3px;background:var(--coral)}
.problemas b{color:var(--crema);font-weight:600}
.cat-ficha{position:absolute;left:920px;top:250px;width:904px;display:grid;grid-template-columns:270px 1fr;gap:34px;align-items:start}
.cat-etq{transform:rotate(-2.5deg);margin-top:24px}
.cat-etq .nom{font-size:26px}
.cat-tk{padding:24px 26px}
.ficha{display:grid;gap:7px}
.ficha div{display:grid;grid-template-columns:118px 1fr;gap:12px;font:400 17px/1.32 var(--mono)}
.ficha dt{color:var(--tinta-3)}
.ficha dd{color:var(--tinta)}

/* ground truth */
.gt-izq{position:absolute;left:96px;top:244px;width:760px}
.gt-izq .et{display:block;margin:18px 0 10px}
.gt-strip{display:flex;gap:6px}
.gt-p{border:1px solid var(--hilo);border-radius:4px}
.gt-der{position:absolute;left:910px;top:244px;width:914px}
.gt-der .et{display:block;margin-bottom:10px}
.gt-q{background:var(--ticket);padding:18px 22px;border-radius:6px;box-shadow:0 0 0 1px var(--hilo);margin-bottom:22px}
.gt-q div{font-size:16px;grid-template-columns:110px 1fr}
.rk-fila{display:flex;gap:12px}
.rk{position:relative;display:flex;flex-direction:column;align-items:center}
.rk .prod{border:1px solid var(--hilo);border-radius:4px}
.rk-n{font:600 16px/1 var(--mono);color:var(--tinta-3);margin-bottom:6px}
.rk.ok .prod{outline:4px solid var(--coral);outline-offset:-1px}
.rk.ok .rk-n{color:var(--coral-2)}
.rk-ok{font:700 15px/1 var(--mono);color:var(--coral-2);margin-top:8px}
.gt-cifras{position:absolute;left:96px;right:96px;bottom:100px;display:grid;grid-template-columns:auto auto auto 1fr;gap:56px;align-items:end;border-top:2px dotted var(--hilo);padding-top:20px}
.gt-cifras div{font:400 20px/1.25 var(--sans);color:var(--tinta-2);max-width:250px}
.gt-cifras b{display:block;font:800 64px/1 var(--display);font-stretch:78%;color:var(--tinta)}
.gt-cifras .gt-ic{max-width:none;font-size:22px}
.gt-cifras .gt-ic b{display:inline;font:600 22px var(--sans);color:var(--coral-2)}

/* ambientes vacíos */
.vac-izq{position:absolute;left:96px;top:240px;width:540px}
.vac-datos{display:grid;gap:12px;margin-top:22px}
.vac-datos li{font:400 23px/1.3 var(--sans);color:var(--trazo)}
.vac-datos b{font:800 30px/1 var(--display);font-stretch:80%;color:var(--crema);margin-right:4px}
.vac-nota{font:500 22px/1.3 var(--sans);color:var(--crema);margin-top:26px;padding-left:18px;border-left:3px solid var(--coral)}
.vac-grilla{position:absolute;left:690px;top:236px;width:1134px;display:grid;grid-template-columns:repeat(4,262px);gap:20px 28px}
.amb figcaption{margin-top:7px}
.amb b{font:700 19px/1.1 var(--display);font-stretch:88%;margin-right:8px}
.amb span{font:400 16px/1.2 var(--sans);color:var(--trazo)}
.amb .cred{display:block;font:400 12.5px/1.25 var(--mono);color:var(--trazo-2);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* v0 → v1 */
.v-col{position:absolute;top:250px}
.v-a{left:96px;width:470px}.v-b{left:640px;width:400px}.v-c{left:1114px;width:710px}
.v-et{font:500 20px/1 var(--mono);color:var(--tinta-3);margin-bottom:14px}
.v-et b{font:800 30px/1 var(--display);font-stretch:80%;color:var(--tinta);margin-right:8px}
.v-c .v-et b{color:var(--coral-2)}
.v-foto{position:relative}
.v-caja{position:absolute;border:3px solid var(--coral);box-shadow:0 0 0 1px rgba(0,0,0,.2)}
.v-nada{position:absolute;inset:auto 0 0 0;padding:10px 14px;font:600 20px/1 var(--mono);color:var(--crema);background:linear-gradient(transparent,rgba(10,19,15,.8))}
.v0-cadena{display:flex;align-items:center;gap:14px;margin-top:12px}
.v0-cadena .prod{border:1px solid var(--hilo)}
.v-fl{font:400 32px/1 var(--sans);color:var(--tinta-3)}
.v-txt{font:400 21px/1.32 var(--sans);color:var(--tinta-2);margin-top:12px}
.v-txt b{color:var(--tinta)}
.v-q{background:var(--ticket);padding:16px 20px;border-radius:6px;box-shadow:0 0 0 1px var(--hilo);margin-top:14px}
.v-q div{font-size:15.5px;grid-template-columns:104px 1fr}
.v-res{position:absolute;left:96px;right:96px;bottom:96px;display:grid;grid-template-columns:1fr 360px;gap:40px;align-items:end;border-top:2px dotted var(--hilo);padding-top:14px}
.v-barras{--gb-h:56px}
.v-res-n{font:400 26px/1.25 var(--sans);color:var(--tinta-2);padding-bottom:20px}
.v-res-n b{color:var(--coral-2)}

/* el flujo */
.etapas{display:grid;gap:20px;margin-top:40px}
.etapas li{padding-left:22px;border-left:3px solid var(--trazo-3);transition:border-color .25s}
.etapas b{display:block;font:740 32px/1.1 var(--display);font-stretch:84%;transition:color .25s}
.etapas span{display:block;font:400 22px/1.3 var(--sans);color:var(--trazo);margin-top:3px}
.etapas li.actual{border-color:var(--coral)}
.etapas li.actual b{color:var(--coral)}
.rem-flujo{left:944px;right:96px;bottom:92px;font-size:34px}

/* hiperparámetros */
.hiper{position:absolute;left:96px;top:236px;width:1000px;display:grid;gap:0}
.hiper li{display:grid;grid-template-columns:48px 300px 1fr 196px;align-items:center;gap:14px;min-height:54px;border-bottom:1px dotted var(--trazo-3)}
.hiper em{font:800 21px/1 var(--display);font-stretch:80%;font-style:normal;color:var(--noche);background:var(--coral);width:34px;height:34px;border-radius:50%;display:grid;place-items:center}
.hiper b{font:700 25px/1.1 var(--display);font-stretch:86%}
.hiper span{font:400 18px/1.2 var(--mono);color:var(--trazo)}
.hiper i{font:400 17px/1.2 var(--mono);font-style:normal;color:var(--trazo-2);text-align:right}
.hiper-pie{position:absolute;left:458px;top:952px;font:400 16px/1 var(--mono);color:var(--trazo-2)}
.esq-hiper{left:1140px;top:240px;width:690px}

/* métricas de retrieval */
.met-ej{margin-top:40px}
.met-ej>.et{display:block;margin-bottom:8px}
.met-cotas{position:relative;height:56px;margin-left:0}
.met-cotas div{position:absolute;left:0;bottom:6px;width:calc(var(--k)*148px - 12px);height:16px;border:2px solid var(--tinta-2);border-bottom:0}
.met-cotas div span{position:absolute;right:-2px;top:-24px;font:600 16px/1 var(--mono);color:var(--tinta-2);background:var(--papel);padding-left:6px}
.met-cotas div:nth-child(2){bottom:20px}.met-cotas div:nth-child(3){bottom:34px}
.met-cotas div:nth-child(2) span{color:var(--coral-2)}
.met-ej .rk-fila{gap:12px}
.met-rr{font:400 21px/1.2 var(--mono);color:var(--tinta-2);margin-top:12px}
.met-rr b{color:var(--coral-2)}
.met-defs{position:absolute;left:96px;right:96px;bottom:100px;display:grid;grid-template-columns:repeat(5,1fr);gap:34px;border-top:2px dotted var(--hilo);padding-top:22px}
.md h4{font:760 28px/1.05 var(--display);font-stretch:84%}
.md p{font:400 19px/1.35 var(--sans);color:var(--tinta-2);margin-top:8px}

/* jueces */
.jz-grilla{display:grid;grid-template-columns:1fr 1fr;gap:34px 80px;margin-top:46px}
.jz h4{font:760 32px/1.08 var(--display);font-stretch:84%}
.jz p{font:400 22px/1.34 var(--sans);color:var(--trazo);margin:8px 0 16px;max-width:780px}
.notas3{display:flex;gap:12px}
.notas3 div{display:flex;align-items:center;gap:10px;font:400 18px/1.2 var(--sans);background:var(--ticket);color:var(--tinta);border-radius:6px;padding:8px 14px 8px 8px}
.notas3 b{display:grid;place-items:center;width:36px;height:36px;border-radius:5px;background:var(--tinta);color:var(--ticket);font:700 20px/1 var(--mono)}
.notas3 div:first-child b{background:var(--coral-2)}
.dos-def{display:flex;gap:16px}
.dos-def div{font:400 19px/1.3 var(--sans);color:var(--trazo);border-left:3px solid var(--coral);padding-left:14px;max-width:340px}
.dos-def b{display:block;font:700 22px/1.2 var(--display);font-stretch:88%;color:var(--crema)}
.ordenes{display:flex;align-items:center;gap:16px}
.ordenes span{display:flex;gap:6px}
.ordenes i{font:700 22px/1 var(--mono);font-style:normal;background:var(--ticket);color:var(--tinta);width:46px;height:46px;border-radius:5px;display:grid;place-items:center}
.ordenes em{font:400 22px var(--mono);color:var(--trazo-2);font-style:normal}
.recibo-mini{display:flex;gap:0;background:var(--ticket);color:var(--tinta);border-radius:4px;padding:10px 6px;width:max-content}
.recibo-mini span{font:500 18px/1 var(--mono);padding:2px 16px;border-right:2px dotted var(--hilo)}
.recibo-mini span:last-child{border:0}

/* métricas de imagen */
.img-tres{display:grid;grid-template-columns:repeat(3,1fr);gap:54px;margin-top:44px}
.it h4{font:760 30px/1.08 var(--display);font-stretch:84%;margin-bottom:16px}
.it>p{font:400 19px/1.35 var(--sans);color:var(--tinta-2);margin-top:14px}
.par-fotos{display:flex;gap:12px}
.it-cifras{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;border-top:2px dotted var(--hilo);padding-top:12px}
.it-cifras.tres{grid-template-columns:1fr 1fr 1fr}
.it-cifras div{font:400 17px/1.25 var(--sans);color:var(--tinta-2)}
.it-cifras b{display:block;font:800 46px/1 var(--display);font-stretch:78%;color:var(--tinta)}
.id-lista{display:grid;gap:8px;height:190px;align-content:start}
.id-par{display:flex;align-items:center;gap:12px}
.id-par .prod,.id-par .foto{width:56px!important;height:56px!important;border:1px solid var(--hilo);background-color:#fff}
.id-fl{font:400 22px var(--sans);color:var(--tinta-3)}
.id-p{font:500 17px/1.2 var(--mono);color:var(--tinta-2)}
.siglip{display:grid;gap:10px;height:190px;align-content:start}
.sg-ped{font:italic 400 18px/1.35 var(--sans);color:var(--tinta-2);border-left:3px solid var(--coral);padding-left:12px}
.sg-x{font:600 17px/1 var(--mono);color:var(--tinta-3)}
.sg-img{font:400 18px/1.3 var(--mono);color:var(--tinta-2)}
.sg-img b{color:var(--tinta)}
.img-pie{position:absolute;left:96px;bottom:100px;font:400 22px/1.3 var(--sans);color:var(--tinta-2)}

/* cómo leemos */
.orden4{display:grid;grid-template-columns:repeat(4,1fr);gap:28px;margin-top:64px}
.orden4 li{position:relative;border-top:3px solid var(--trazo-3);padding-top:22px}
.orden4 li::after{content:"→";position:absolute;right:-24px;top:-22px;font:400 30px var(--sans);color:var(--trazo-2)}
.orden4 li:last-child::after{display:none}
.orden4 b{font:800 64px/1 var(--display);font-stretch:78%;color:var(--trazo-2)}
.orden4 h3{font:760 36px/1.1 var(--display);font-stretch:84%;margin-top:8px}
.orden4 p{font:400 22px/1.32 var(--sans);color:var(--trazo);margin-top:8px}
.orden4 li.dec{border-color:var(--coral)}
.orden4 li.dec b,.orden4 li.dec h3{color:var(--coral)}
.leer-demo{position:absolute;left:96px;right:96px;bottom:100px;display:grid;grid-template-columns:380px 1fr;gap:56px;align-items:center}
.leer-demo p{font:700 40px/1.2 var(--display);font-stretch:86%}

/* =========================== experimentos =========================== */
.porque{font:400 26px/1.36 var(--sans);color:var(--trazo);margin-top:26px;text-wrap:pretty}
.exp-blq{margin-top:30px;padding-top:22px;border-top:1px solid var(--hilo-o)}
.exp-blq .et{display:block;margin-bottom:16px}
.variantes b{font-size:27px}
.variantes span{font-size:20px}
.metrica{font:400 18px/1.4 var(--mono);color:var(--trazo-2);margin-top:18px}
.clara .metrica{color:var(--tinta-3)}
.adv{display:inline-block;margin-top:18px;font:600 17px/1 var(--mono);color:var(--coral);border:1.6px solid var(--coral);border-radius:999px;padding:7px 14px}
.vend{display:flex;gap:18px;align-items:center;margin-top:22px;background:var(--fondo-2);border-radius:8px;padding:12px 16px 12px 12px}
.vend .prod{border-radius:4px}
.vend .et{display:block}
.vend q{display:block;font:italic 400 21px/1.32 var(--sans);color:var(--crema);margin-top:6px;quotes:"«" "»"}
.e12-motivo{display:flex;align-items:center;gap:14px;margin-top:22px}
.e12-mt{font:500 18px/1.3 var(--mono);color:var(--coral);max-width:200px}
.res-2{display:grid;grid-template-columns:1fr 1fr;gap:80px;margin-top:50px}
.gb-compacto{--gb-et:280px}
.nota{font:400 27px/1.34 var(--sans);color:var(--tinta-2);margin-top:36px;max-width:1360px;text-wrap:pretty}
.nota.chica{font-size:21px;margin-top:16px}
.nota b{color:var(--tinta)}
.nota.aviso b{color:var(--coral-2)}
.minimapa{position:absolute;right:96px;top:62px;width:250px;background:var(--fondo);border-radius:8px;padding:10px 12px 8px}
.minimapa .flujo .reg{stroke-width:3}
.minimapa .flujo .caja{stroke-width:3}
.minimapa .flujo .fl{stroke-width:4}
.minimapa .flujo .pin circle{r:24}
.minimapa .flujo .pin text{display:block;font-size:30px;transform:translateY(4px)}
.minimapa>span{position:absolute;left:12px;bottom:-24px;font:500 14px/1 var(--mono);color:var(--tinta-3)}
.res-e1{display:grid;grid-template-columns:1fr 470px;gap:70px;margin-top:40px}
.graf-b.sep{margin-top:26px}
.grande-n{align-self:center}
.grande-n b{display:block;font:800 200px/.9 var(--display);font-stretch:76%;color:var(--coral-2);letter-spacing:-.02em}
.grande-n span{display:block;font:600 26px/1.25 var(--sans);margin-top:10px}
.grande-n p{font:400 23px/1.3 var(--sans);color:var(--tinta-2);margin-top:20px;padding-top:16px;border-top:2px dotted var(--hilo)}
.unica .un-izq{position:absolute;left:96px;top:130px;width:700px}
.unica .un-der{position:absolute;left:880px;top:250px;width:944px}
.unica .porque{font-size:23px;color:var(--tinta-2)}
.unica .exp-blq{border-color:var(--hilo)}
.gb-unica{--gb-et:300px;--gb-h:80px}
.gl-tit{font:500 20px/1.2 var(--mono);color:var(--tinta-3);margin-bottom:6px}
.r-8{margin-top:24px}
.r8-n{position:absolute;right:96px;top:420px;width:340px;font-size:24px}
.r-9{margin-top:50px;width:1500px}
.gb-9{--gb-et:520px;--gb-h:84px}
.r-10a,.r-10b{display:grid;grid-template-columns:1fr 1fr;gap:70px;margin-top:40px}
.r-10b{margin-top:24px}
.marcador{border-bottom:2px dotted var(--hilo);padding-bottom:12px;margin-bottom:16px}
.mk-t{display:flex;align-items:baseline;gap:14px;font:700 28px/1 var(--display);font-stretch:86%}
.mk-t b{font:800 76px/1 var(--display);font-stretch:76%}
.mk-t i{font:300 50px/1 var(--sans);font-style:normal;color:var(--tinta-3)}
.mk-s{font:400 17px/1.2 var(--mono);color:var(--tinta-3);margin-top:6px}
.tiles{display:flex;flex-wrap:wrap;gap:10px}
.tj{width:200px;background:var(--ticket);border-radius:6px;padding:10px 12px;box-shadow:0 0 0 1px var(--hilo)}
.tj b{display:block;font:700 19px/1.1 var(--display);font-stretch:88%}
.tj span{display:block;font:400 15px/1.2 var(--sans);color:var(--tinta-3)}
.tj em{display:inline-block;margin-top:8px;font:600 14px/1 var(--mono);font-style:normal;padding:4px 7px;border-radius:4px;background:var(--papel-2);color:var(--tinta-2)}
.tj.t-a em{background:var(--tinta);color:var(--ticket)}
.tj.t-b em{background:var(--coral-2);color:#fff}
.giro{font:700 34px/1.2 var(--display);font-stretch:86%;margin-top:34px;max-width:1300px;padding-left:20px;border-left:4px solid var(--coral)}
.r10-cifras{display:grid;grid-template-columns:repeat(3,1fr);gap:50px;margin-top:22px}
.r10-cifras div{font:400 18px/1.25 var(--sans);color:var(--tinta-2)}
.r10-cifras b{display:block;font:800 40px/1 var(--display);font-stretch:78%;color:var(--tinta);margin-bottom:4px}
.r-11{margin-top:40px}
.r11-rep{margin-top:30px}
.rep-et{font:700 25px var(--display);font-stretch:86%;fill:var(--tinta)}
.rep-p{fill:var(--tinta)}
.rep-t{font:700 20px var(--mono);fill:var(--coral-2)}
.e12-grilla{display:grid;grid-template-columns:repeat(4,400px);gap:42px;margin-top:40px}
.e12-c{position:relative}
.e12-c figcaption{display:flex;gap:12px;align-items:flex-start;margin-top:12px}
.e12-t{flex:1}
.e12-t b{display:block;font:700 22px/1.1 var(--display);font-stretch:88%}
.e12-t i{font:400 15px/1.2 var(--mono);color:var(--tinta-3);font-style:normal}
.e12-v{text-align:right;font:400 15px/1.2 var(--mono);color:var(--tinta-3)}
.e12-v b{display:block;font:800 40px/1 var(--display);font-stretch:78%;color:var(--tinta)}
.e12-v i{display:block;font-style:normal}
.e12-c.mal .e12-v b{color:var(--coral-2)}
.e12-sello{position:absolute;left:16px;top:16px;font:700 16px/1 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:#fff;background:var(--coral-2);padding:7px 10px;border-radius:4px;transform:rotate(-3deg)}
.e12-c.gana .foto{outline:4px solid var(--coral);outline-offset:5px}
.e12-c.gana .letra{background:var(--coral-2)}
.e12-n{margin-top:24px;font-size:24px}

/* =========================== cierre =========================== */
.e2e-fila{display:flex;gap:22px;align-items:flex-start;margin-top:34px}
.e2e-fila.e2e-2{margin-top:30px}
.e2e-et{width:200px;flex:none;padding-top:8px}
.e2e-et b{display:block;font:760 36px/1 var(--display);font-stretch:84%}
.e2e-et span{display:block;font:400 18px/1.3 var(--mono);color:var(--trazo-2);margin-top:6px}
.intento{position:relative}
.intento figcaption{font:400 16px/1 var(--mono);color:var(--trazo-2);margin-top:8px}
.sello{position:absolute;left:12px;bottom:40px;display:flex;flex-direction:column;gap:3px;font:400 13px/1.2 var(--mono);padding:7px 10px;border-radius:4px;transform:rotate(-2deg)}
.sello b{font:700 17px/1 var(--mono);text-transform:uppercase;letter-spacing:.06em}
.sello.no{background:var(--coral-2);color:#fff}
.sello.ok{background:var(--ticket);color:var(--tinta)}
.sello.ok b{color:var(--tinta)}
.e2e-tk{width:330px;padding:16px 18px;margin-left:8px}
.e2e-tk .tk-cab{padding-bottom:8px;margin-bottom:4px}
.e2e-tk .tk-cab b{font-size:24px}
.e2e-tk .li{grid-template-columns:44px 1fr auto;padding:3px 0}
.e2e-tk .li .prod{width:44px!important;height:44px!important}
.e2e-tk .li-t b{font-size:17px}
.iter-tk{margin-top:44px;padding:22px 34px}
.it-cab,.it-l{display:grid;grid-template-columns:54px 1fr 500px 500px;gap:24px;align-items:baseline}
.it-cab{font:500 15px/1.2 var(--mono);color:var(--tinta-3);border-bottom:2px dashed var(--hilo);padding-bottom:10px}
.it-l{padding:19px 0;border-bottom:1px dotted var(--hilo)}
.it-n{font:500 16px/1 var(--mono);color:var(--tinta-3)}
.it-p{font:400 24px/1.25 var(--sans);color:var(--tinta-2)}
.it-c{font:700 27px/1.15 var(--display);font-stretch:88%}
.it-m{font:600 21px/1.2 var(--mono);color:var(--coral-2);text-align:right}
.iter-pie{display:flex;justify-content:space-between;align-items:center;margin-top:12px}
.camino-w{margin-top:36px}
.cm-b rect{fill:var(--salvia-2)}
.cm-b.gana rect{fill:var(--coral)}
.cm-guia{stroke:var(--tinta-3);stroke-width:1.5;stroke-dasharray:4 5}
.cm-v{font:800 46px var(--display);font-stretch:78%;fill:var(--tinta)}
.cm-b.gana .cm-v{fill:var(--coral-2)}
.cm-d{font:600 20px var(--mono);fill:var(--tinta-3)}
.cm-et{font:500 19px var(--sans);fill:var(--tinta-2)}
.costo-tk{position:absolute;left:96px;top:270px;width:900px;padding:30px 36px}
.costo-tk .tk-l{font-size:24px;padding:12px 0}
.costo-tk .tk-l b{font:800 40px/1 var(--display);font-stretch:78%}
.costo-tk .tk-tot{font-size:19px;font-weight:500}
.costo-tk .tk-tot span:last-child{font:800 30px/1 var(--display);font-stretch:78%}
.costo-tk .barras-cod{margin-top:16px;color:var(--tinta)}
.costo-notas{position:absolute;left:1090px;top:290px;width:734px;display:grid;gap:34px}
.costo-notas h4{font:760 32px/1.1 var(--display);font-stretch:84%}
.costo-notas p{font:400 23px/1.34 var(--sans);color:var(--trazo);margin-top:6px}
.lim-dos{display:grid;grid-template-columns:1fr 1fr;gap:90px;margin-top:50px}
.lim-dos .et{display:block;margin-bottom:12px}
.lim{counter-reset:l}
.lim li{counter-increment:l;display:grid;grid-template-columns:52px 1fr;font:600 30px/1.22 var(--display);font-stretch:88%;padding:16px 0;border-bottom:1px dotted var(--trazo-3)}
.lim li::before{content:counter(l,decimal-leading-zero);font:500 18px/1.8 var(--mono);color:var(--trazo-2)}
.lim.fut li::before{color:var(--coral)}
.lim-sig{font:600 26px/1.3 var(--sans);color:var(--coral);margin-top:30px}
.fpasos{display:grid;gap:18px;margin-top:34px}
.fpasos li{display:grid;grid-template-columns:44px 1fr;gap:12px;padding-left:16px;border-left:3px solid var(--trazo-3);transition:border-color .25s}
.fpasos em{font:800 32px/1 var(--display);font-stretch:78%;font-style:normal;color:var(--trazo-2)}
.fpasos b{display:block;font:740 28px/1.1 var(--display);font-stretch:84%}
.fpasos span{display:block;font:400 19px/1.32 var(--sans);color:var(--trazo);margin-top:3px}
.fpasos span b{display:inline;font:600 19px var(--sans);color:var(--crema)}
.fpasos li.actual{border-color:var(--coral)}
.fpasos li.actual em,.fpasos li.actual>div>b{color:var(--coral)}
.f3d{margin-top:22px;border:2px dashed var(--coral);border-radius:8px;padding:14px 18px}
.f3d .et{color:var(--coral)}
.f3d p{font:400 19px/1.35 var(--sans);color:var(--trazo);margin-top:6px}
.f3d b{color:var(--crema)}
.esq-fut{width:860px;left:964px;top:80px}
.falta{position:absolute;left:964px;right:96px;top:812px}
.falta ul{display:grid;grid-template-columns:1fr 1fr;gap:6px 30px;margin-top:8px}
.falta li{font:400 18px/1.3 var(--sans);color:var(--trazo);padding-left:18px;position:relative}
.falta li::before{content:"";position:absolute;left:0;top:10px;width:9px;height:3px;background:var(--coral)}
.conc-izq{position:absolute;left:96px;top:78px;width:1030px}
.conc{display:grid;gap:22px;margin-top:42px}
.conc li{display:grid;grid-template-columns:64px 1fr;align-items:baseline;border-bottom:1px dotted var(--trazo-3);padding-bottom:18px}
.conc em{font:800 40px/1 var(--display);font-stretch:78%;font-style:normal;color:var(--coral)}
.conc p{font:400 34px/1.22 var(--sans);color:var(--trazo)}
.conc p b{font-weight:700;color:var(--crema)}
.conc-der{position:absolute;left:1184px;top:200px}
.conc-et{margin-top:10px;font:400 17px/1.2 var(--mono);color:var(--trazo-2)}

/* =========================== ajustes =========================== */
/* producto */
.pr-entra{position:absolute;left:96px;top:262px;width:420px}
.pr-entra .et,.pr-img .et{display:block;margin-bottom:12px}
.pedido{font:italic 400 20px/1.42 var(--sans);color:var(--trazo);margin-top:20px;padding-left:18px;border-left:3px solid var(--coral)}
.pr-img{position:absolute;left:572px;top:262px}
.pr-ticket{position:absolute;left:1376px;top:240px;width:452px;padding:22px 24px 18px;transform:rotate(1.2deg)}
.pr-ticket[data-paso]{transform:translateY(30px) rotate(1.2deg)}
.pr-ticket[data-paso].visto,.todo .pr-ticket[data-paso]{transform:rotate(1.2deg)!important}
.li{display:grid;grid-template-columns:52px 1fr auto;gap:12px;align-items:center;padding:5px 0;border-bottom:1px dotted var(--hilo)}
.li-t{min-width:0}
.li-t b{display:block;font:700 19px/1.1 var(--display);font-stretch:88%}
.li-t span{display:block;font:400 14px/1.2 var(--mono);color:var(--tinta-3);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.li-q{font:700 20px/1 var(--mono)}

/* preguntas: columna izquierda */
.izq .t.chico{font-size:58px}
.izq.denso .t.chico{font-size:52px}
.izq.denso .porque{font-size:22px;margin-top:16px}
.izq.denso .exp-blq{margin-top:18px;padding-top:14px}
.izq.denso .variantes{gap:9px}
.izq.denso .variantes b{font-size:23px}
.izq.denso .variantes span{font-size:17px;margin-top:1px}
.izq.denso .e12-motivo{margin-top:14px}
.izq.denso .metrica{font-size:16px;margin-top:10px}

/* resultados: barras más grandes */
.res-2 .graf-b,.res-e1 .graf-b{--gb-h:92px;--gb-bar:40px}
.res-e1 .graf-b{--gb-h:78px}
.gb-et{font-size:27px}
.gb-val{font-size:44px}
.gb-tit{font-size:21px}
.gb-9{--gb-h:104px;--gb-bar:44px}
.gb-9 .gb-et{font-size:30px}
.r-11 .graf-b{--gb-h:80px}
.nota{font-size:28px}

/* cómo leemos */
.leer-demo{grid-template-columns:480px 480px 1fr;gap:48px;align-items:start;bottom:96px}
.ld-s{position:relative;width:480px;height:270px;border-radius:6px;overflow:hidden;padding:22px 24px}
.ld-s.osc{background:var(--fondo-3);box-shadow:inset 0 0 0 1px var(--hilo-o)}
.ld-s.clr{background:var(--papel)}
.ld-s i{display:block;height:9px;border-radius:2px;background:var(--trazo-2);margin-bottom:9px;width:150px}
.ld-s .ld-k{width:70px;height:12px;background:none;border:2px solid var(--coral);margin-bottom:16px}
.ld-s .ld-t{height:17px;width:200px;background:var(--crema)}
.ld-s .ld-t.c{width:120px;background:var(--coral);margin-bottom:22px}
.ld-s.clr .ld-t{background:var(--tinta);width:160px;margin-bottom:24px}
.ld-s .ld-p{width:180px;height:7px;background:var(--trazo-3)}
.ld-s .ld-p.c{width:120px}
.ld-esq{position:absolute;right:16px;top:20px;width:212px}
.ld-b{display:block;height:20px;width:var(--w);background:var(--salvia-2);border-radius:0 3px 3px 0;margin:0 0 12px 60px}
.ld-b.g{background:var(--coral)}
.ld-tal{position:absolute;left:24px;right:24px;bottom:20px;height:52px;background:var(--ticket);border-radius:4px;box-shadow:0 8px 16px -10px rgba(0,0,0,.4)}
.ld-tal i{position:absolute;left:96px;top:0;bottom:0;width:0;height:auto;border-left:2px dashed var(--hilo);margin:0;background:none}
.ld-f figcaption{font:400 21px/1.32 var(--sans);color:var(--trazo);margin-top:14px}
.ld-f figcaption b{color:var(--crema)}
.leer-demo p{font:700 40px/1.2 var(--display);font-stretch:86%;align-self:center}
.orden4{margin-top:52px}

/* por qué RAG */
.rag-tres{margin-top:46px}
.rag-tk{padding:26px 28px}
.rag-tk .tk-cab b{font-size:32px}
.rag-tk .tk-l{font-size:20px;padding:9px 0}
.rag-c>p{font-size:25px}
.sello-tk{font-size:19px;margin-top:22px}

/* jueces */
.jz-grilla{gap:60px 90px;margin-top:60px}
.jz h4{font-size:38px}
.jz p{font-size:25px;margin:10px 0 22px}
.notas3 div{font-size:20px;padding:10px 16px 10px 10px}
.notas3 b{width:42px;height:42px;font-size:23px}
.dos-def div{font-size:21px;max-width:380px}
.dos-def b{font-size:25px}
.ordenes i{width:54px;height:54px;font-size:25px}
.recibo-mini span{font-size:21px;padding:4px 20px}

/* métricas de imagen */
.img-tres{gap:60px;margin-top:50px}
.it h4{font-size:34px}
.par-fotos .foto{width:262px!important;height:197px!important}
.id-lista{height:197px;gap:10px}
.id-par .prod,.id-par .foto{width:58px!important;height:58px!important}
.id-p{font-size:19px}
.siglip{height:197px}
.sg-ped{font-size:19px}
.sg-img{font-size:19px}
.it-cifras b{font-size:54px}
.it-cifras div{font-size:18px}
.it>p{font-size:21px}

/* limitaciones */
.lim li{font-size:34px;padding:20px 0}
.lim-dos{margin-top:56px}

/* E10 */
.tj{width:232px;padding:12px 14px}
.tj b{font-size:22px}
.tj span{font-size:16px}
.tj em{font-size:15px}
.r-10a .tiles{gap:14px}
.r-10a{margin-top:56px}
.mk-t{font-size:30px}


/* futuro: medidas reales */
.izq.ancho{width:810px}
.esq-fut{left:950px;width:878px;top:84px}
.falta{left:950px;top:820px}
.flujo .fut-sub rect{fill:none;stroke:var(--coral);stroke-width:2.4;stroke-dasharray:7 6}
.flujo .fut-sub text{font:600 16px var(--mono);fill:var(--coral)}

/* camino */
.camino-w{margin-top:26px}

body.modo-todo .slide{transition:none}
/* problema */
.pb-tags .etq .nom{font-size:16px}
/* por qué RAG, más grande */
.rag-c h3{font-size:38px}
.rag-c>p{font-size:26px;min-height:68px}
.rag-tk .tk-l{font-size:21px;padding:11px 0}
.rag-tk .tk-cab b{font-size:34px}
.tk-vacio{padding:30px 0 16px;font-size:48px}
/* métricas de retrieval */
.met-cotas div{width:calc(var(--k)*162px - 12px)}
.met-cotas{height:62px}
.md h4{font-size:31px}
.md p{font-size:21px}
/* jueces */
.jz-grilla{gap:80px 100px;margin-top:70px}
/* métricas de imagen */
.par-fotos{position:relative;display:block}
.par-fotos>.foto{width:536px!important;height:402px!important}
.pf-in{position:absolute;left:12px;top:12px;background:var(--ticket);padding:5px 5px 3px;border-radius:4px;box-shadow:0 8px 20px -10px rgba(0,0,0,.6)}
.pf-in .foto{width:176px!important;height:132px!important}
.pf-in span{display:block;font:400 13px/1.2 var(--mono);color:var(--tinta-3);margin-top:3px}
.id-lista{height:402px;gap:14px}
.id-cab{display:grid;grid-template-columns:100px 32px 100px 1fr;gap:12px;font:400 14px/1.2 var(--mono);color:var(--tinta-3)}
.id-cab span:nth-child(2){grid-column:3}
.id-cab span:nth-child(3){grid-column:4}
.id-par{display:grid;grid-template-columns:100px 32px 100px 1fr;gap:12px;align-items:center}
.id-par .prod,.id-par .foto{width:100px!important;height:100px!important}
.id-fl{text-align:center;font-size:26px}
.id-p{font:400 19px/1.2 var(--mono);color:var(--tinta-2)}
.id-p b{font:800 40px/1 var(--display);font-stretch:78%;color:var(--tinta);margin-right:4px}
.siglip{height:402px;gap:16px}
.sg-ped{font-size:21px;line-height:1.4}
.sg-x{font-size:16px;margin-top:8px}
.sg-b{display:grid;grid-template-columns:150px 1fr 70px;align-items:center;gap:12px}
.sg-b span{font:400 17px/1.2 var(--mono);color:var(--tinta-2)}
.sg-b i{display:block;height:30px;width:var(--w);background:var(--coral);border-radius:0 3px 3px 0}
.sg-b.v i{background:var(--salvia-2)}
.sg-b b{font:800 36px/1 var(--display);font-stretch:78%}
.img-tres{margin-top:40px}
.it h4{margin-bottom:14px}
.it-cifras b{font-size:50px}
.img-pie{bottom:96px;font-size:20px}
/* barras compactas */
.gb-compacto{--gb-et:304px}
/* futuro: medidas */
.fpasos span,.fpasos span b{font-size:20px}
.fpasos b{font-size:30px}
.f3d p{font-size:20px}

.minimapa{width:212px;top:66px;padding:8px 10px 6px}
.res-2{margin-top:66px}
.fpasos .op{display:block;font-style:normal;margin-top:2px}
.r-10a .tj{width:262px;padding:14px 16px}
.r-10a .tj b{font-size:25px}
.r-10a .tj span{font-size:17px}
.r-10a .mk-t b{font-size:96px}
.r-10a .mk-t{font-size:34px}
.r-10a+.nota{margin-top:50px}
.it-cab>:last-child{text-align:right}
/* E13 · réplica: la pregunta (oscura), los prompts (oscura) y los resultados (clara) */
.r13-izq .porque{font-size:24px;margin-top:20px}
.r13-izq .exp-blq{margin-top:24px;padding-top:18px}
.r13-grid{display:grid;grid-template-columns:repeat(3,246px);gap:26px}
.r13-cab{margin-bottom:6px}
.r13-cab .foto{border-radius:4px}
.r13-cab b{display:block;font:700 22px/1.1 var(--display);font-stretch:88%;color:var(--crema);margin-top:9px}
.r13-cab span{display:block;font:400 15px/1.2 var(--mono);color:var(--trazo-2);margin-top:3px}
.r13-v{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:start;padding:9px 0 8px;border-top:1px dotted var(--hilo-o)}
.r13-v b{display:block;font:700 21px/1.1 var(--display);font-stretch:88%;color:var(--crema)}
.r13-v span{display:block;font:400 16px/1.25 var(--sans);color:var(--trazo);margin-top:2px}
.r13-v .letra{min-width:30px;height:30px;font-size:16px;background:var(--crema);color:var(--fondo)}
.r13-r1{position:absolute;left:944px;top:826px;width:884px;display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap}
.r13-r1 figure{position:relative}
.r13-r1 .foto{border-radius:4px}
.r13-r1 figcaption{font:400 15px/1.2 var(--mono);color:var(--trazo-2);margin-top:6px}
.r13-r1>i{font:400 26px/1 var(--mono);color:var(--trazo-2);font-style:normal;margin-top:56px}
.r13-r1 em{position:absolute;left:8px;top:8px;font:700 13px/1 var(--mono);text-transform:uppercase;letter-spacing:.05em;color:#fff;background:var(--coral-2);padding:5px 7px;border-radius:3px;transform:rotate(-3deg);font-style:normal}
.r13-r1 p{width:100%;font:400 16px/1.3 var(--mono);color:var(--coral);margin-top:-2px}
.p13{position:absolute;left:96px;right:96px;top:236px;display:grid;grid-template-columns:800px 1fr;gap:40px;align-items:start}
.p13-izq{display:grid;gap:22px}
.p13-tk .pr-tx{font-size:15.5px;line-height:1.46}
.p13-b .et{display:block;margin-bottom:10px}
.p13-ej .pr-tx{font-size:15px;line-height:1.42;padding:12px 18px}
.p13-b p{font:400 19px/1.36 var(--sans);color:var(--trazo);margin-top:12px;text-wrap:pretty}
.p13-b p b{color:var(--crema);font-weight:600}
.p13-der .et{display:block;margin-bottom:10px}
.p13-l{list-style:none;margin:0;padding:4px 22px}
.p13-l li{display:grid;grid-template-columns:36px 1fr;gap:14px;padding:12px 0;border-top:1px dotted var(--hilo)}
.p13-l li:first-child{border-top:0}
.p13-l .letra{background:var(--tinta);color:var(--papel);min-width:32px;height:32px;font-size:16px}
.p13-l b{display:block;font:700 20px/1.1 var(--display);font-stretch:88%;color:var(--tinta)}
.p13-l p{font:400 15px/1.45 var(--mono);color:var(--tinta-2);margin-top:4px}
.p13-l .hl{color:var(--tinta);font-weight:600;background:rgba(255,91,63,.17);box-shadow:inset 0 -2px 0 var(--coral);padding:0 2px;border-radius:2px}
.r13{display:grid;grid-template-columns:968px 1fr;gap:44px;margin-top:40px}
.r13-f{display:grid;grid-template-columns:272px 1fr 64px 112px 120px;column-gap:16px;align-items:center;min-height:50px;border-top:1px dotted var(--hilo)}
.r13-f.cab{min-height:30px;border-top:0;align-items:end;font:400 15px/1.15 var(--mono);color:var(--tinta-3)}
.r13-f.cab>span:nth-child(n+3){text-align:right}
.r13-eje{position:relative;height:20px}
.r13-eje span{position:absolute;bottom:0;transform:translateX(-50%);font:400 15px/1 var(--mono);color:var(--tinta-3)}
.r13-g{font:500 16px/1 var(--mono);color:var(--tinta-3);padding:16px 0 8px;letter-spacing:.02em}
.r13-n{display:flex;align-items:center;gap:12px;font:600 22px/1.1 var(--sans)}
.r13-n .letra{min-width:32px;height:32px;font-size:16px}
.r13-f .gb-pista{height:24px}
.r13-x{text-align:right;font:800 30px/1 var(--display);font-stretch:80%;font-variant-numeric:tabular-nums}
.r13-x.d{font:700 22px/1 var(--display);font-stretch:84%}
.r13-x.d.no{color:var(--coral-2)}
.r13-f.r1{min-height:40px}
.r13-f.r1 .r13-n{font-size:18px;color:var(--tinta-2);font-weight:500;padding-left:44px}
.r13-f.r1 .r13-x{font-size:22px;color:var(--tinta-3)}
.r13-f.r1 .r13-x.d.no{color:var(--coral-2)}
.r13-f.r1 .gb-pista{height:14px}
.r13-f.r1 .gb-lleno{background:var(--hilo)}
.r13-f.gana .gb-lleno{background:var(--coral)}
.r13-f.gana .r13-x:not(.d){color:var(--coral-2)}
.r13-f.gana .letra{background:var(--coral-2)}
.r13-ims{display:grid;grid-template-columns:328px 328px;gap:16px 20px;align-content:start}
.r13-im{position:relative}
.r13-im .foto{border-radius:4px}
.r13-im>i{position:absolute;left:12px;top:12px;font:700 14px/1 var(--mono);text-transform:uppercase;letter-spacing:.05em;color:#fff;background:var(--coral-2);padding:6px 8px;border-radius:4px;transform:rotate(-3deg);font-style:normal}
.r13-pie{font:400 16px/1.3 var(--mono);color:var(--tinta-3);margin-top:16px}
.r13-ims{margin-top:14px}
.r13-im figcaption{display:grid;grid-template-columns:auto 1fr auto;gap:4px 10px;margin-top:8px;align-items:center}
.r13-im figcaption .letra{min-width:30px;height:30px;font-size:16px}
.r13-im b{display:block;font:700 19px/1.1 var(--display);font-stretch:88%}
.r13-im figcaption.sin-l{grid-template-columns:1fr}
.r13-im .sin-l .r13-det{grid-column:1}
.r13-det{grid-column:2/4;font:400 14.5px/1.25 var(--sans);color:var(--tinta-2)}
.r13-num{font:500 15px/1 var(--mono);color:var(--tinta-2)}
"""

# --- revisión del 2026-11-12: los componentes nuevos, con el mismo lenguaje
# (van en una hoja aparte, CSS_REV, que se incluye última: después de la del recorrido) -------------------
CSS_REV = r"""
.nb{white-space:nowrap}
.cred-l{font:400 13.5px/1.3 var(--mono);color:var(--trazo-2);margin-top:8px}
.clara .cred-l{color:var(--tinta-3)}
.remate.chico{font-size:34px;line-height:1.18;bottom:96px;max-width:1700px}

/* por qué RAG: los tres desafíos de la clase */
.rag-tres.tres{grid-template-columns:1fr 1fr 1fr;gap:52px;margin-top:38px}
.rag-d{display:block;font:600 19px/1 var(--mono);color:var(--coral-2);letter-spacing:.02em;margin-bottom:12px}
.rag-tres.tres .rag-c h3{font-size:34px;min-height:74px}
.rag-tres.tres .rag-c>p{font-size:23px;min-height:62px;margin:8px 0 22px}
.sello-tk.ok{color:var(--tinta-2);border-color:var(--tinta-2)}
.rag-tres.tres .rag-tk .tk-tot{font-size:17px}

/* desafíos */
.dz-flujos{display:grid;gap:14px;margin-top:30px}
.dz-fila{display:flex;align-items:stretch}
.dz-n{width:270px;flex:none;align-self:center}
.dz-n b{display:block;font:760 27px/1.1 var(--display);font-stretch:84%}
.dz-n span{display:block;font:500 17px/1.2 var(--mono);color:var(--tinta-3);margin-top:4px}
.dz-fila.nueva .dz-n span{color:var(--coral-2)}
.dz-c{flex:1;border-radius:8px;padding:11px 16px 12px;min-height:72px;display:flex;flex-direction:column;justify-content:center}
.dz-c b{display:block;font:700 23px/1.1 var(--display);font-stretch:88%}
.dz-c span{display:block;font:400 16.5px/1.25 var(--sans);color:var(--tinta-3);margin-top:3px}
.dz-fila.vieja .dz-c{border:2px dashed var(--tinta-3)}
.dz-fila.nueva .dz-c{background:var(--ticket);box-shadow:0 0 0 2.5px var(--coral)}
.dz-fila>i{flex:none;width:40px;display:grid;place-items:center;font:400 26px/1 var(--sans);font-style:normal;color:var(--tinta-3)}
.dz-abajo{position:absolute;left:96px;right:96px;top:424px;display:grid;grid-template-columns:860px 1fr;gap:64px}
.dz-abajo .et{display:block;margin-bottom:12px}
.dz-v0{display:flex;align-items:center;gap:14px;margin-bottom:16px}
.dz-v0 .prod{border:1px solid var(--hilo)}
.dz-v0 p{font:400 19px/1.3 var(--sans);color:var(--tinta-2);max-width:240px;margin-left:8px}
.dz-barras{--gb-et:170px;--gb-h:60px;--gb-nota:220px}
.dz-barras .gb-tit{font-size:17px;margin-bottom:6px}
.dz-otros{display:grid;gap:20px}
.dz-otros li{padding-left:20px;border-left:3px solid var(--coral)}
.dz-otros b{display:block;font:740 26px/1.12 var(--display);font-stretch:86%}
.dz-otros span{display:block;font:400 19.5px/1.34 var(--sans);color:var(--tinta-2);margin-top:4px;text-wrap:pretty}

/* barras con la diferencia pareada a la derecha */
.graf-b.con-nota .gb-fila{grid-template-columns:var(--gb-et,360px) 1fr 120px var(--gb-nota,300px)}
.gb-nota{font:500 19px/1.2 var(--mono);color:var(--tinta-2);white-space:nowrap}
.gb-fila.gana .gb-nota{color:var(--coral-2);font-weight:600}
.graf-b.oscuro .gb-fila.gana .gb-val{color:var(--coral)}

/* el mapa de los experimentos: pines llenos y huecos, y el banco de prueba */
.flujo .pin.hueco circle{fill:var(--fondo);stroke:var(--coral);stroke-width:3}
.flujo .pin.hueco text{fill:var(--coral)}
.flujo .banco .sub{font:400 17px var(--mono);fill:var(--trazo)}
.hiper.h14{top:226px;width:1010px}
.hiper.h14 li{grid-template-columns:44px 350px 1fr;min-height:44px;gap:14px}
.hiper.h14 b{font-size:24px}
.hiper.h14 span{font-size:17.5px}
.hiper li.tram em{background:none;box-shadow:inset 0 0 0 2.5px var(--coral);color:var(--coral)}
.hiper.h14 li:nth-child(8){margin-top:14px;border-top:1px dotted var(--trazo-3)}
.hiper-pie{left:96px;top:auto;bottom:84px;width:1010px;font-size:16px;line-height:1.45}
.hiper-pie b{color:var(--coral);font-weight:600}
.esq-hiper{left:1150px;top:226px;width:680px}
.hiper-rm{left:1150px;top:190px}
.rx em.hueco{background:none;box-shadow:inset 0 0 0 2.5px var(--coral);color:var(--coral)}
.rx em.no{background:none;border:2px dashed var(--trazo-2);color:var(--trazo-2);font-size:18px}

/* el generador y los jueces; las trampas */
.jz p b{color:var(--crema);font-weight:600}
.jz-grilla.gen{gap:40px 90px;margin-top:38px}
.jz-grilla.gen .jz h4{font-size:33px;display:flex;align-items:baseline;gap:16px}
.jz h4 b{font:800 54px/1 var(--display);font-stretch:78%;color:var(--coral)}
.jz h4 em{font-style:normal;color:var(--coral)}
.jz-grilla.gen .jz p{font-size:21.5px;margin:8px 0 14px}
.jz-q{display:flex;gap:12px;flex-wrap:wrap}
.jz-q span{font:italic 400 18px/1.3 var(--sans);color:var(--crema);background:var(--fondo-2);border-radius:6px;padding:7px 12px}
.jz-pr .pr-tx{font-size:15.5px;padding:10px 18px 12px}
.jz-pr .pr-cab{padding:9px 18px 8px}
.jz-pr .pr-cab b{font-size:16px}
.jz-grilla.tr{gap:44px 90px;margin-top:52px}
.jz-grilla.tr .jz h4{font-size:34px;display:flex;gap:16px;align-items:baseline}
.jz h4 i{font:600 20px/1 var(--mono);font-style:normal;color:var(--coral);flex:none}
.jz-grilla.tr .jz p{font-size:23px;margin:10px 0 0 30px}

/* la imagen: las 11 corridas finales */
.img-dos{display:grid;grid-template-columns:560px 1fr;gap:70px;margin-top:30px}
.img-dos .it h4{font-size:32px;margin-bottom:10px}
.img-dos .it>.et{display:block;margin-bottom:12px}
.img-dos .id-lista{height:auto;gap:8px}
.img-dos .id-cab,.img-dos .id-par{grid-template-columns:66px 28px 66px 1fr;gap:12px}
.img-dos .id-par .prod,.img-dos .id-par .foto{width:66px!important;height:66px!important}
.img-dos .id-p b{font-size:32px}
.img-dos .id-par.ok .id-p b{color:var(--coral-2)}
.img-dos .it>p{font-size:19px;margin-top:12px}
.img-dos .it-cifras{margin-top:12px}
.img-dos .it-cifras b{font-size:44px}
.fines{display:grid;grid-template-columns:repeat(6,1fr);gap:12px 14px}
.fin .foto{width:100%!important;height:auto!important;aspect-ratio:3/2;border-radius:4px}
.fin figcaption{font:500 14.5px/1.2 var(--mono);color:var(--tinta-2);margin-top:5px}
.fin figcaption b{font-weight:700;color:var(--tinta);margin-right:8px}
.fin.no .foto{outline:3px solid var(--coral-2);outline-offset:-3px}
.fin.no figcaption b{color:var(--coral-2)}
.fin-res{font:400 16.5px/1.25 var(--sans);color:var(--tinta-2);align-self:start}
.fin-res b{display:block;font:800 44px/1 var(--display);font-stretch:78%;color:var(--tinta)}

/* recorrido: el plan, la búsqueda híbrida, la elección, la imagen */
.rp-tec{font:400 18px/1.4 var(--sans);color:var(--trazo);margin-top:14px;text-wrap:pretty}
.rp-tec span{display:block;font:500 14px/1 var(--mono);color:var(--coral);margin-bottom:6px;letter-spacing:.02em}
.rp-tec b{color:var(--crema);font-weight:600}
.rt-banda.rb{gap:40px}
.rb-izq{width:1064px}
.rb-cab,.rb-par.tres{grid-template-columns:1fr 176px 1fr;width:1064px}
.rb-tres{display:flex;flex-direction:column;justify-content:center;gap:12px;padding:0 14px}
.rb-tres div{border-left:3px solid var(--coral);padding-left:10px}
.rb-tres b{display:block;font:760 21px/1.1 var(--display);font-stretch:84%;color:var(--crema)}
.rb-tres span{display:block;font:400 14px/1.3 var(--sans);color:var(--trazo);margin-top:2px}
.rb-tres span i{font-style:normal;color:var(--coral)}
.rb-tres p{margin-top:6px;padding-top:10px;border-top:1px dotted var(--trazo-3);text-align:center}
.rb-tres p b{font:800 44px/1 var(--display);font-stretch:78%;color:var(--coral)}
.rb-tres p span{font:500 13px/1.3 var(--mono);color:var(--trazo-2);margin-top:4px}
.rb-doc-f{display:flex;gap:12px;align-items:center;margin-bottom:8px;padding-bottom:8px;border-bottom:2px dashed var(--hilo)}
.rb-doc-f .prod{border-radius:4px;border:1px solid var(--hilo)}
.rb-doc-f span{font:500 13.5px/1.35 var(--mono);color:var(--tinta-3)}
.rb-doc-f span i{font-style:italic;font-family:var(--sans);color:var(--tinta-2)}
.rb-der{width:624px;gap:20px}
.rb-filtro{background:var(--fondo-2);border:1px solid var(--trazo-3);border-radius:6px;padding:12px 16px 14px}
.rb-filtro p{display:flex;gap:8px;flex-wrap:wrap}
.rb-filtro code{font-size:17px;padding:4px 10px}
.rb-pasan{font:400 17px/1.3 var(--sans);color:var(--trazo);margin-top:10px}
.rb-pasan b{font:800 26px/1 var(--display);font-stretch:80%;color:var(--coral);margin:0 2px}
.rb-c{width:112px}
.rb-c em{font-size:24px}
.rb-c b{font-size:14px;color:var(--trazo)}
.rb-c span{font-size:13px;line-height:1.25;color:var(--trazo-2)}
.rb-c.uno .prod{outline:3px solid var(--coral);outline-offset:2px}
.rb-c.uno b{color:var(--coral)}
.re-izq{width:700px;gap:8px}
.re-der{width:984px;gap:6px}
.re-fila{grid-template-columns:128px auto 1fr;gap:14px;padding:7px 0}
.re-c .prod{opacity:.6}
.re-why{font-size:16px;line-height:1.34}
.re-pie{font:400 15.5px/1.4 var(--mono);color:var(--trazo-2);margin-top:6px;padding-top:10px;border-top:1px dotted var(--trazo-3)}
.re-pie b{color:var(--coral);font-weight:600}
.rs-rama.otra .vers em{color:var(--trazo-2);border-color:var(--trazo-3)}
.ri2-der{width:500px;margin-left:44px}
.ri2-ints.cuatro{grid-template-columns:repeat(4,1fr);gap:8px}
.ri2-ints .foto{width:100%!important;height:auto!important;aspect-ratio:3/2}
.ri2-ints .orig .foto{opacity:1}
.ri2-ints .orig b{font:600 14px/1.3 var(--mono);color:var(--crema);text-decoration:none}
.ri2-tot{font:400 16.5px/1.4 var(--sans);color:var(--trazo)}
.ri2-tot b{color:var(--crema);font-weight:600}
.ri2-cred{position:absolute;left:0;margin:0}
.rl-l{grid-template-columns:38px 150px 190px 1fr 44px}

/* experimentos */
.res-e1 .grande-n>b{font-size:170px}
.res-e1 .grande-n>span{font-size:22px}
.res-e3{display:grid;grid-template-columns:1fr 420px;gap:56px;margin-top:30px}
.gb-e3{--gb-et:330px;--gb-h:53px;--gb-bar:26px;--gb-nota:300px}
.gb-e3 .gb-et{font-size:23px}
.gb-e3 .gb-val{font-size:32px}
.gb-e3 .gb-l{min-width:30px;height:30px;font-size:16px}
.res-e3 .grande-n>b{font-size:150px}
.res-e3 .grande-n p{font-size:21px}
.res-2.r-2{margin-top:76px;gap:70px}
.r-2 .graf-b{--gb-h:66px;--gb-bar:32px}
.r-2 .gb-val{font-size:36px}
.r2-n{margin-top:18px}
.r2-nota{font-size:25px;margin-top:22px;max-width:1500px}
.cm-b.v1 rect{fill:var(--tinta-2)}
.cm-ic{fill:none;stroke:var(--tinta);stroke-width:2}
.cm-h5{font:500 15px var(--mono);fill:var(--papel)}
.cm-v{font-size:42px}
.cm-d{font:500 15px var(--mono);fill:var(--tinta-3)}
.cm-d.sube{fill:var(--coral-2);font-weight:600}
.cm-et{font-size:18px}
.cm-ap rect{fill:none;stroke:var(--tinta-3);stroke-width:2.2;stroke-dasharray:7 6}
.cm-ap .cm-v{fill:var(--tinta-2);font-size:36px}
.cm-sep{stroke:var(--tinta-3);stroke-width:1.5;stroke-dasharray:3 6}
.cm-apt{font:500 16px var(--mono);fill:var(--tinta-3)}
.fam-ej{display:flex;gap:18px;align-items:flex-start;margin-top:22px;padding-top:18px;border-top:2px dotted var(--hilo)}
.fam-ej figure{flex:none;text-align:center}
.fam-ej .prod{border:1px solid var(--hilo);border-radius:4px}
.fam-ej figcaption{font:500 14px/1.2 var(--mono);color:var(--tinta-3);margin-top:6px}
.fam-ej p{font:400 20px/1.36 var(--sans);color:var(--tinta-2)}
.fam-ej p .et{display:block;margin-bottom:6px;font-size:16px}
.fam-ej p b{color:var(--tinta)}
.r-5{display:grid;grid-template-columns:540px 1fr;gap:40px;margin-top:60px;align-items:start}
.r5-izq .et{display:block}
.r5-num{display:flex;align-items:baseline;gap:16px;font:800 96px/1 var(--display);font-stretch:76%;margin-top:14px;color:var(--tinta-2)}
.r5-num i{font:300 56px/1 var(--sans);font-style:normal;color:var(--tinta-3)}
.r5-num b{color:var(--coral-2)}
.r5-d{font:500 20px/1.3 var(--mono);color:var(--tinta-2);margin-top:10px}
.r5-l{display:grid;gap:14px;margin-top:28px;padding-top:20px;border-top:2px dotted var(--hilo)}
.r5-l li{font:400 22px/1.36 var(--sans);color:var(--tinta-2);padding-left:22px;position:relative}
.r5-l li::before{content:"";position:absolute;left:0;top:14px;width:12px;height:3px;background:var(--coral)}
.r5-l b{color:var(--tinta)}
.r-10b.r-6{margin-top:30px}
.r-7{display:grid;grid-template-columns:1fr 770px;gap:60px;margin-top:64px;align-items:start}
.r7-b{--gb-h:66px;margin-top:6px}
.r-7 .mk-t b{font-size:96px}
.r-7 .mk-t{font-size:32px}
.rag-q{padding:24px 28px 22px}
.rag-q .tk-cab b{font-size:32px}
.rag-q .tk-l{font-size:17.5px;padding:7px 0}
.rag-q .tk-l .tk-v{color:var(--tinta);font-weight:600}
.rag-q .tk-pie{font:400 17px/1.4 var(--sans);color:var(--tinta-2);margin-top:14px;padding-top:12px;border-top:2px dashed var(--hilo)}
.rep-f .rep-t{fill:var(--tinta)}
.rep-f.gana .rep-p,.rep-f.gana .rep-t{fill:var(--coral-2)}
.rep-f.gana .gl-banda{fill:var(--coral);opacity:.22}
.tram-tk{margin-top:76px;padding:20px 32px 16px}
.tr-cab,.tr-l{display:grid;grid-template-columns:46px 250px 500px 1fr;gap:22px;align-items:start}
.tr-cab{font:500 15px/1.2 var(--mono);color:var(--tinta-3);border-bottom:2px dashed var(--hilo);padding-bottom:10px}
.tr-l{padding:15px 0 16px;border-bottom:1px dotted var(--hilo)}
.tr-l:last-child{border-bottom:0}
.tr-l>b{font:740 26px/1.12 var(--display);font-stretch:86%}
.tp{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;box-shadow:inset 0 0 0 2.5px var(--coral-2);color:var(--coral-2);font:800 19px/1 var(--display);font-stretch:80%;font-style:normal}
.tp.no{box-shadow:inset 0 0 0 2px var(--hilo);color:var(--tinta-3)}
.tr-q{font:400 17.5px/1.42 var(--mono);color:var(--tinta-2)}
.tr-q b{color:var(--tinta);font-weight:700}
.tr-r{font:400 20px/1.36 var(--sans);color:var(--tinta-2);text-wrap:pretty}
.tram-rem{font-size:30px}

/* Ejercicio 4 */
.ej-izq{position:absolute;left:96px;top:236px;width:800px}
.ej-der{position:absolute;left:960px;top:236px;width:864px}
.ej-izq .et,.ej-der .et{display:block;margin-bottom:10px}
.ej-p{font:400 23px/1.4 var(--sans);color:var(--trazo);margin-bottom:26px;text-wrap:pretty}
.ej-p b{color:var(--crema);font-weight:600}
.ej-trio{display:grid;gap:14px;margin-bottom:26px}
.ej-trio div{display:grid;grid-template-columns:230px 1fr;gap:20px;align-items:center;border-top:1px dotted var(--trazo-3);padding-top:12px}
.ej-trio b{font:800 52px/1 var(--display);font-stretch:76%;color:var(--coral);white-space:nowrap}
.ej-trio span{font:400 19.5px/1.34 var(--sans);color:var(--trazo)}
.ej-q{font:italic 400 24px/1.3 var(--sans);color:var(--crema);border-left:3px solid var(--coral);padding-left:16px;margin-bottom:22px}
.ej-q span{display:block;font:400 17px/1.3 var(--mono);font-style:normal;color:var(--trazo-2);margin-top:6px}
.caso5{display:flex;gap:12px}
.cz{position:relative;text-align:center}
.cz .prod{border-radius:5px;opacity:.72}
.cz span{display:block;font:500 14px/1 var(--mono);color:var(--trazo-2);margin-top:6px}
.cz.ok .prod{opacity:1;outline:4px solid var(--coral);outline-offset:2px}
.cz.ok span{color:var(--coral);font-weight:700}
.ej-c{font:400 20px/1.36 var(--sans);color:var(--trazo);margin:12px 0 20px}
.ej-c b{color:var(--crema);font-weight:600}
.ej-anot{display:flex;gap:18px;align-items:center}
.ej-anot .et{margin:0}
.ej-anot .cz .prod{width:84px!important;height:84px!important}
.ej-yaml{margin-bottom:26px}
.ej-yaml .pr-tx{font-size:19px;line-height:1.62;padding:16px 22px 18px;white-space:pre}
.ej-yaml .del{color:var(--tinta-3);text-decoration:line-through;text-decoration-color:rgba(16,32,26,.4)}
.ej-yaml .add{display:inline-block;width:calc(100% + 44px);color:var(--tinta);font-weight:700;background:rgba(255,91,63,.17);box-shadow:inset 3px 0 0 var(--coral);margin:0 -22px;padding:0 22px}
.ej-yaml .com{font-style:normal;color:var(--tinta-3)}
.ej-por{display:grid;gap:14px;counter-reset:p}
.ej-por li{counter-increment:p;display:grid;grid-template-columns:40px 1fr;font:400 22px/1.38 var(--sans);color:var(--trazo)}
.ej-por li::before{content:counter(p);font:800 26px/1.2 var(--display);font-stretch:78%;color:var(--coral)}
.ej-por b{color:var(--crema);font-weight:600}
.hb-svg{display:block;width:864px;height:auto;overflow:visible;font-family:var(--sans)}
.hb rect{fill:var(--fondo-2);stroke:var(--trazo-2);stroke-width:1.6}
.hb.nueva rect{stroke:var(--coral);stroke-width:2.6;fill:color-mix(in srgb,var(--coral) 13%,var(--fondo-2))}
.hb-t{font:760 22px var(--display);font-stretch:86%;fill:var(--crema)}
.hb-s{font:400 15.5px var(--mono);fill:var(--trazo)}
.hb-tag{font:600 13px var(--mono);fill:var(--trazo-2);letter-spacing:.04em}
.hb.nueva .hb-tag{fill:var(--coral)}
.hb-fl{fill:none;stroke:var(--trazo-2);stroke-width:2}
.hb-fl.nueva{stroke:var(--coral)}
.ej-caso2{display:flex;gap:22px;align-items:flex-end;margin-top:18px}
.ej-caso2 .cz .prod{width:84px!important;height:84px!important}
.ej-caso2 .ej-c{margin:0 0 20px}
.ver-tk{margin-top:24px;padding:14px 30px 10px}
.v-l{display:grid;grid-template-columns:1fr 290px 350px 500px;gap:16px;align-items:center;min-height:42px;border-bottom:1px dotted var(--hilo);font:400 21px/1.2 var(--sans)}
.v-l:last-child{border-bottom:0}
.v-l.v-cab{min-height:34px;border-bottom:2px dashed var(--hilo)}
.v-n{color:var(--tinta-2)}
.v-a,.v-b{text-align:center;font:500 21px/1.2 var(--mono);color:var(--tinta-2)}
.v-cab .v-a,.v-cab .v-b,.v-cab .v-d{font:500 15px/1 var(--mono);color:var(--tinta-3);letter-spacing:.03em}
.v-l:not(.v-cab) .v-b{font-weight:700;color:var(--tinta);background:var(--coral-s);align-self:stretch;display:grid;place-items:center}
.v-d{font:500 17px/1.25 var(--mono);color:var(--tinta-2)}
.v-sec{font:500 15px/1 var(--mono);color:var(--coral-2);letter-spacing:.02em;padding:14px 0 8px;border-bottom:1px dotted var(--hilo)}
.ver-tk code{font-size:18px;background:none;padding:0}
.ver-dos{position:absolute;left:96px;right:96px;top:764px;display:grid;grid-template-columns:1fr 1fr;gap:40px}
.ver-dos div{font:400 21px/1.36 var(--sans);color:var(--tinta-2);padding:12px 20px 13px 24px;border-radius:6px;background:var(--ticket)}
.ver-dos b{color:var(--tinta)}
.ver-dos .claro{box-shadow:inset 4px 0 0 var(--tinta),0 0 0 1px var(--hilo)}
.ver-dos .no{box-shadow:inset 4px 0 0 var(--coral),0 0 0 1px var(--hilo)}
.ver-dos .no b{color:var(--coral-2)}

/* cierre: costo, limitaciones, trabajo futuro, conclusiones */
.costo-tk{top:250px;width:840px;padding:26px 32px}
.costo-tk .tk-l{font-size:20px;padding:10px 0}
.costo-tk .tk-l b{font-size:36px}
.costo-tk .tk-tot span:last-child{font-size:38px;color:var(--coral-2)}
.costo-tk .tk-pie{font-size:14.5px}
.costo-der{position:absolute;left:1010px;top:236px;width:814px}
.costo-tot{display:flex;align-items:baseline;gap:20px;margin-bottom:22px}
.costo-tot b{font:800 96px/1 var(--display);font-stretch:76%;color:var(--crema)}
.costo-tot span{font:400 22px/1.34 var(--sans);color:var(--trazo)}
.gb-costo{--gb-et:330px;--gb-h:46px;--gb-bar:22px}
.gb-costo .gb-et{font-size:21px;font-weight:500}
.gb-costo .gb-val{font-size:28px}
.gb-costo .gb-fila{grid-template-columns:var(--gb-et) 1fr 84px}
.costo-n{font:400 19.5px/1.4 var(--sans);color:var(--trazo);margin-top:22px;text-wrap:pretty}
.costo-n b{color:var(--crema);font-weight:600}
.lim-dos{margin-top:40px;gap:80px}
.lim2 li{padding:13px 0;align-items:baseline}
.lim2 li b{display:block;font:740 28px/1.15 var(--display);font-stretch:86%;color:var(--crema)}
.lim2 li span{display:block;font:400 20.5px/1.36 var(--sans);color:var(--trazo);margin-top:4px;text-wrap:pretty}
.fut-izq{position:absolute;left:96px;top:236px;width:800px}
.fut-izq .et,.fut-der .et{display:block;margin-bottom:8px}
.futl li{padding:9px 0}
.futl li b{font-size:26px}
.futl li span{font-size:19px}
.fut-der{position:absolute;left:980px;top:236px;width:844px}
.gb-fut{--gb-et:280px;--gb-h:44px;--gb-bar:22px}
.gb-fut .gb-et{font-size:21px;font-weight:500}
.gb-fut .gb-val{font-size:30px}
.gb-fut .gb-fila{grid-template-columns:var(--gb-et) 1fr 84px}
.fut-fotos{display:grid;grid-template-columns:340px 340px;gap:20px;margin-top:16px}
.fut-fotos .foto{width:100%!important;height:auto!important;aspect-ratio:1024/643;border-radius:4px}
.fut-fotos figcaption{font:400 14.5px/1.3 var(--mono);color:var(--trazo-2);margin-top:6px}
.fut-n{font:400 17.5px/1.4 var(--sans);color:var(--trazo);margin-top:12px;text-wrap:pretty}
.fut-n b{color:var(--crema);font-weight:600}
.conc-izq{width:1010px}
.conc5{gap:14px;margin-top:34px}
.conc5 li{padding-bottom:13px;grid-template-columns:56px 1fr}
.conc5 p{font-size:27px;line-height:1.26}
.conc5 em{font-size:36px}
.conc-der.conc4{left:1170px;top:226px;width:656px;display:grid;grid-template-columns:1fr 1fr;gap:16px 20px}
.conc4 .foto{width:100%!important;height:auto!important;aspect-ratio:3/2;border-radius:4px}
.conc4 .conc-et{grid-column:1/3;margin-top:0}
.conc4 .conc-et span{display:block;line-height:1.35}
"""
CSS_REV += r"""
.jz-rep{grid-column:1/3;font:400 19.5px/1.4 var(--sans);color:var(--trazo);border-left:3px solid var(--coral);padding-left:16px;margin:-14px 0;text-wrap:pretty}
.jz-rep b{color:var(--crema);font-weight:600}
"""
CSS_REV += r"""
.reg-card dd.nohay{color:var(--tinta-3);font-weight:400}
.amb .cred{white-space:normal;overflow:visible;line-height:1.3}
.re-der{gap:2px}
.re-fila{padding:5px 0}
.re-pie{margin-top:2px;padding-top:8px}
.ej-por li p{margin:0}
"""
CSS_REV += r"""
.grande-n p b{display:inline;font:inherit;font-weight:700;color:var(--tinta);letter-spacing:0}
.grande-n p span{display:inline;font:inherit;margin:0}
.res-e3 .grande-n{align-self:start;margin-top:86px}
"""
CSS_REV += r"""
.met-cotas div:nth-child(1){z-index:3}
.met-cotas div:nth-child(2){z-index:2}
.jz-grilla.gen .jz h4>span{display:block}
.rq-p{font:400 17px/1.4 var(--sans);color:var(--tinta-2);margin:0 0 6px}
.rq-p b{color:var(--tinta)}
.rag-q .tk-pie b{color:var(--tinta)}
.img-dos .it-cifras.tres{grid-template-columns:1fr 1fr 1.2fr;margin-top:16px}
.img-dos .fines+.it-cifras b{font-size:44px}
"""
CSS_REV += r"""
.r7-et{display:block;margin-bottom:10px}
.rag-q .tk-cab span{font-size:15px}
.rag-q .tk-l.sep{margin-top:8px;padding-top:14px;border-top:2px dashed var(--hilo)}
"""
CSS_REV += r"""
.met-cotas{height:86px}
.met-cotas div{bottom:6px;height:12px}
.met-cotas div:nth-child(2){bottom:32px}
.met-cotas div:nth-child(3){bottom:58px}
.met-cotas div span{left:calc(100% + 12px);right:auto;top:-8px;background:none;padding:0;white-space:nowrap}
.r-7{margin-top:76px}
"""
CSS_REV += r"""
.v-l .v-a,.v-l .v-b{width:auto;left:auto}
"""
