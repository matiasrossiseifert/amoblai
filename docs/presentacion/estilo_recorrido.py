"""La hoja de estilo del recorrido por las fases: el mapa que avanza (el mismo esquema del flujo, en
modo «ruta»), los extractos de prompts como impresos, la historia de versiones y los ejemplos."""

CSS = r"""
/* =========================== el mapa del recorrido =========================== */
.flujo.ruta .reg-t{font-size:25px;font-weight:600}
.flujo.ruta .fl-t,.flujo.ruta .sub{display:none}
.flujo.ruta .num{font:600 27px var(--mono);fill:var(--trazo-2);letter-spacing:.02em}
.flujo.ruta .ok{font:700 26px var(--sans);fill:var(--coral)}
.flujo.ruta .nom{font-size:41px;font-stretch:80%}
.flujo.ruta .fl{stroke:var(--trazo-3)}
.flujo.ruta .fl.hecha{stroke:var(--coral);stroke-width:3.2;stroke-dasharray:none}
.flujo.ruta .pin circle{stroke-width:5}
.flujo.ruta .pin text{font-size:27px}
/* en el recorrido el foco no apaga lo ya visto: lo recorrido queda marcado, lo que falta, tenue */
.flujo.ruta.foco .lineas{opacity:1}
.flujo.ruta.foco [data-k="indexing"],.flujo.ruta.foco [data-k="consulta"]{opacity:.7}
.flujo.ruta.foco .nodo:not(.on){opacity:.3}
.flujo.ruta.foco .nodo.visto:not(.on){opacity:1}
.flujo.ruta .nodo.visto .caja{fill:var(--fondo-3);stroke:var(--trazo)}
.flujo.ruta .nodo.visto .num{fill:var(--coral)}
.flujo.ruta .nodo.on .num{fill:var(--coral)}
.flujo.ruta .nodo.on .ok{display:none}
.flujo.ruta .on .caja{stroke-width:4}

/* la lámina de una fase: título y bajada a la izquierda, el mapa arriba a la derecha, la banda abajo */
.rmapa{position:absolute;right:96px;top:58px;width:520px}
.rt-t{max-width:1150px}
.izq-rt{position:absolute;left:96px;top:78px;width:1160px}
.rt-lead{font:400 26px/1.36 var(--sans);color:var(--trazo);margin-top:20px;max-width:1150px;text-wrap:pretty}
.rt-lead b{color:var(--crema);font-weight:600}
.rt-lead code{font-size:.84em}
.rt-banda{position:absolute;left:96px;right:96px;top:500px;bottom:96px;display:flex;gap:44px;align-items:flex-start}
.rt-banda>*{flex:none}
.rt-banda .et{display:block;margin-bottom:12px}

/* =========================== el prompt, como se manda =========================== */
.pr-tk{position:relative;background:var(--ticket);color:var(--tinta);border-radius:6px;box-shadow:0 26px 44px -26px rgba(0,0,0,.75);overflow:hidden}
.pr-cab{display:flex;justify-content:space-between;align-items:baseline;gap:20px;padding:13px 22px 11px;border-bottom:2px dashed var(--hilo);background:#F6F4EC}
.pr-cab b{font:600 19px/1 var(--mono);color:var(--tinta)}
.pr-cab span{font:400 15px/1 var(--mono);color:var(--tinta-3)}
.pr-tx{margin:0;padding:14px 22px 16px;font:400 16.5px/1.5 var(--mono);white-space:pre-wrap;color:var(--tinta-2);tab-size:2}
.pr-tx .hl{color:var(--tinta);font-weight:600;background:rgba(255,91,63,.17);box-shadow:inset 0 -2px 0 var(--coral);padding:0 2px;border-radius:2px}
.pr-tx .ph{font-style:normal;color:var(--coral-2);font-weight:600}
.pr-tx .el{display:block;color:var(--tinta-3);line-height:1.1;margin:2px 0}

/* =========================== versiones de un prompt =========================== */
.vers{display:grid;gap:0;counter-reset:v}
.vers li{display:grid;grid-template-columns:96px 1fr;gap:16px;padding:11px 0 12px;border-top:1px dotted var(--trazo-3);align-items:start}
.vers li:first-child{border-top:0;padding-top:0}
.vers em{font:600 19px/1 var(--mono);font-style:normal;color:var(--coral);border:2px solid var(--coral);border-radius:5px;padding:6px 0 5px;text-align:center;margin-top:1px}
.vers li.actual em{background:var(--coral);color:var(--noche)}
.vers li.fuera em{color:var(--trazo-2);border-color:var(--trazo-3);border-style:dashed}
.vers b{display:block;font:700 22px/1.2 var(--display);font-stretch:88%;color:var(--crema)}
.vers span{display:block;font:400 18.5px/1.32 var(--sans);color:var(--trazo);margin-top:3px;text-wrap:pretty}
.vers span i{font-style:normal;color:var(--salvia)}

/* =========================== experimentos que decidieron la fase =========================== */
.rx{display:grid;gap:12px}
.rx li{display:grid;grid-template-columns:40px 1fr;gap:14px;align-items:start}
.rx em{font:800 21px/1 var(--display);font-stretch:80%;font-style:normal;color:var(--noche);background:var(--coral);width:36px;height:36px;border-radius:50%;display:grid;place-items:center}
.rx b{display:block;font:700 21px/1.2 var(--display);font-stretch:88%;color:var(--crema)}
.rx span{display:block;font:400 18px/1.3 var(--sans);color:var(--trazo);margin-top:2px}

/* =========================== 0 · el mapa completo =========================== */
.rm-izq{position:absolute;left:96px;top:78px;width:700px}
.rm-grupos{display:grid;gap:26px;margin-top:40px}
.rm-g{border-left:3px solid var(--trazo-3);padding:2px 0 4px 22px;transition:border-color .3s}
.rm-g h3{font:600 20px/1.2 var(--mono);color:var(--coral);letter-spacing:.01em}
.rm-g p{font:400 25px/1.36 var(--sans);color:var(--trazo);margin-top:8px;text-wrap:pretty}
.rm-g p b{color:var(--crema);font-weight:600}
.rm-g.actual{border-left-color:var(--coral)}
.rm-esq{position:absolute;left:880px;top:84px;width:950px}
.rem-rm{left:96px;right:auto;width:700px;bottom:104px;font-size:38px}

/* =========================== 1 · catálogo =========================== */
.rc-col{width:300px}
.rc-cifra{font:800 112px/.9 var(--display);font-stretch:76%;letter-spacing:-.01em;color:var(--crema);display:flex;align-items:baseline;gap:12px}
.rc-cifra i{font:300 56px/1 var(--sans);font-style:normal;color:var(--trazo-2)}
.rc-cifra .co{color:var(--coral)}
.rc-src{font:500 17px/1.35 var(--mono);color:var(--trazo-2);margin-top:12px}
.rc-l{display:grid;gap:6px;margin-top:16px}
.rc-l li{font:400 20px/1.3 var(--sans);color:var(--trazo);padding-left:22px;position:relative}
.rc-l li::before{content:"";position:absolute;left:0;top:12px;width:11px;height:3px;background:var(--coral)}
.rc-l b{color:var(--crema);font-weight:600}
.reg-card{width:500px;background:var(--ticket);color:var(--tinta);border-radius:8px;box-shadow:0 26px 44px -26px rgba(0,0,0,.75);
  display:grid;grid-template-columns:150px 1fr;gap:0 18px;padding:18px 20px 16px}
.reg-card .prod{grid-row:1/3;width:150px!important;height:150px!important;border-radius:4px}
.reg-card h4{font:600 15px/1.2 var(--mono);color:var(--tinta-3);letter-spacing:.02em}
.reg-card h4 b{color:var(--coral-2);font-weight:700}
.reg-card dl{display:grid;gap:4px;margin-top:8px}
.reg-card dl div{display:grid;grid-template-columns:98px 1fr;gap:10px;font:400 16px/1.3 var(--mono)}
.reg-card dt{color:var(--tinta-3)}
.reg-card dd{color:var(--tinta);font-weight:500}
.reg-card dd.falta{color:var(--tinta-3);font-weight:400}
.reg-card q{grid-column:1/3;display:block;margin-top:14px;padding-top:12px;border-top:2px dashed var(--hilo);font:italic 400 16px/1.38 var(--sans);color:var(--tinta-2)}
.reg-card q::before,.reg-card q::after{content:none}
.reg-card q span{font:500 13.5px/1 var(--mono);font-style:normal;color:var(--tinta-3);display:block;margin-bottom:6px;letter-spacing:.02em}
.rc-tot{position:absolute;left:96px;right:96px;bottom:104px;display:flex;align-items:center;gap:22px;border-top:2px dotted var(--trazo-3);padding-top:18px}
.rc-tot b{font:800 46px/1 var(--display);font-stretch:78%;color:var(--crema)}
.rc-tot span{font:400 22px/1.3 var(--sans);color:var(--trazo)}
.rc-tot .rx{margin-left:auto;grid-auto-flow:column;gap:40px}

/* =========================== 2 · descripción =========================== */
.rd-vers{margin-top:22px;max-width:1150px}
.rd-vers li{grid-template-columns:118px 1fr}
.rd-vers b{display:inline;font-size:21px}
.rd-vers span{display:inline;font-size:19px;margin:0 0 0 8px}
.rd-ej{width:560px}
.rd-ej .ej-par{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:start}
.rd-ej .prod{border-radius:6px}
.rd-ej .ej-por{font:400 17px/1.38 var(--mono);color:var(--trazo);margin-top:4px}
.rd-ej .ej-por b{color:var(--crema);font-weight:500}
.ficha-tk{background:var(--ticket);color:var(--tinta);border-radius:6px;padding:14px 18px;margin-top:16px;box-shadow:0 22px 40px -26px rgba(0,0,0,.7)}
.ficha-tk .ficha div{grid-template-columns:104px 1fr;font-size:15.5px;gap:10px}
.rd-ej .rx{margin-top:22px}

/* =========================== 3 · índice =========================== */
.ri{flex-direction:column;gap:30px}
.ri-svg{width:1728px;height:auto;display:block;overflow:visible}
.ri-svg .caja-t{fill:var(--ticket)}
.ri-svg .caja-m{fill:var(--fondo-2);stroke:var(--coral);stroke-width:2.5}
.ri-svg .t-et{font:500 16px var(--mono);fill:var(--trazo-2);letter-spacing:.02em}
.ri-svg .t-mono{font:400 16px var(--mono);fill:var(--tinta-2)}
.ri-svg .t-mono b,.ri-svg .t-mono .k{fill:var(--tinta-3)}
.ri-svg .t-mono .d{fill:var(--tinta);font-weight:600}
.ri-svg .t-mod{font:780 34px var(--display);font-stretch:82%;fill:var(--crema)}
.ri-svg .t-mod-s{font:400 17px var(--mono);fill:var(--trazo)}
.ri-svg .flr{fill:none;stroke:var(--trazo-2);stroke-width:2.4}
.ri-svg .vb{fill:var(--coral)}
.ri-svg .vb.n{fill:var(--salvia-2)}
.ri-svg .v0{stroke:var(--trazo-3);stroke-width:1.4}
.ri-svg .t-v{font:500 16px var(--mono);fill:var(--trazo)}
.ri-svg .t-vn{font:780 30px var(--display);font-stretch:80%;fill:var(--crema)}
.ri-dec{display:grid;grid-template-columns:repeat(3,1fr);gap:18px 48px;width:1728px}
.ri-dec li{grid-template-columns:40px 1fr}
.ri-dec em.no{background:none;border:2px dashed var(--trazo-2);color:var(--trazo-2);font-size:18px}

/* =========================== 4 y 5 · del pedido al plan =========================== */
.rp-ent{width:440px}
.rp-ent .foto{border-radius:6px}
.rp-ped{margin-top:14px;font:400 18.5px/1.38 var(--sans);color:var(--crema);border-left:3px solid var(--coral);padding:2px 0 2px 16px;text-wrap:pretty}
.rp-vista{font:400 16px/1.35 var(--mono);color:var(--trazo-2);margin-top:12px}
.rp-fl{align-self:center;font:300 54px/1 var(--sans);color:var(--trazo-2);margin:0 -18px}
.rp-plan{width:560px;padding:20px 24px 18px}
.rp-plan .tk-cab b{font-size:28px}
.rp-room{font:italic 400 16px/1.38 var(--sans);color:var(--tinta-2);margin-bottom:10px}
.rp-pz{display:grid;grid-template-columns:28px 1fr auto;gap:10px;font:400 16.5px/1.25 var(--mono);padding:5px 0;border-top:1px dotted var(--hilo)}
.rp-pz:first-of-type{border-top:0}
.rp-pz .q{color:var(--tinta-3)}
.rp-pz b{font-weight:600}
.rp-pz .md{color:var(--tinta-3);white-space:nowrap}
.rp-pz.uno{background:rgba(255,91,63,.1);box-shadow:inset 3px 0 0 var(--coral)}
.rp-q{width:560px}
.rp-q .ficha-tk{margin-top:0}
.rp-q .rp-why{font:italic 400 17px/1.38 var(--sans);color:var(--trazo);margin-top:14px;text-wrap:pretty}
.rp-q .rp-why span{font:500 14px/1 var(--mono);font-style:normal;color:var(--trazo-2);display:block;margin-bottom:6px}

/* =========================== 5 · el prompt del plan =========================== */
.rpp-vers{width:640px}
.rpp-ex{margin-top:20px}

/* =========================== 6 · búsqueda =========================== */
.rb-par{display:grid;grid-template-columns:1fr 92px 1fr;width:1060px;align-items:stretch}
.rb-par .ficha-tk{margin:0;padding:12px 16px}
.rb-par .ficha div{grid-template-columns:92px 1fr;font-size:14.5px;gap:8px}
.rb-par .ficha{gap:5px}
.rb-cos{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}
.rb-cos b{font:800 40px/1 var(--display);font-stretch:78%;color:var(--coral)}
.rb-cos span{font:500 15px/1.2 var(--mono);color:var(--trazo-2);text-align:center}
.rb-cos i{font:300 40px/1 var(--sans);font-style:normal;color:var(--trazo-2)}
.rb-cab{display:grid;grid-template-columns:1fr 92px 1fr;width:1060px}
.rb-der{width:580px;display:grid;gap:22px}
.rb-where{background:var(--fondo-2);border:1px solid var(--trazo-3);border-radius:6px;padding:12px 16px;font:400 15.5px/1.45 var(--mono);color:var(--trazo);white-space:pre-wrap}
.rb-where b{color:var(--crema);font-weight:600}
.rb-where i{font-style:normal;color:var(--coral)}
.rb-cands{display:flex;gap:14px}
.rb-c{display:flex;flex-direction:column;gap:6px;width:130px}
.rb-c .prod{border-radius:5px}
.rb-c b{font:600 15px/1.2 var(--mono);color:var(--crema)}
.rb-c span{font:400 14px/1.2 var(--mono);color:var(--trazo-2)}
.rb-c em{font:700 22px/1 var(--display);font-style:normal;font-stretch:80%;color:var(--crema)}
.rb-c.uno em{color:var(--coral)}
.rb-nota{font:400 16px/1.35 var(--mono);color:var(--trazo-2)}
.rb-nota b{color:var(--coral);font-weight:600}

/* =========================== 7 · elección =========================== */
.re-izq{width:760px;display:grid;gap:18px}
.re-izq .vers li{grid-template-columns:96px 1fr;padding:8px 0}
.re-der{width:880px;display:grid;gap:14px}
.re-fila{display:grid;grid-template-columns:150px auto 1fr;gap:16px;align-items:center;padding:8px 0;border-top:1px dotted var(--trazo-3)}
.re-fila:first-of-type{border-top:0}
.re-pz b{display:block;font:700 22px/1.1 var(--display);font-stretch:86%;color:var(--crema)}
.re-pz span{display:block;font:400 14px/1.3 var(--mono);color:var(--trazo-2);margin-top:4px}
.re-cs{display:flex;gap:8px}
.re-c{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px}
.re-c .prod{border-radius:5px;opacity:.55}
.re-c span{font:500 13px/1 var(--mono);color:var(--trazo-2)}
.re-c.elegido .prod{opacity:1;outline:3px solid var(--coral);outline-offset:2px}
.re-c.elegido span{color:var(--coral);font-weight:700}
.re-c i{position:absolute;top:-10px;right:-10px;font:800 17px/1 var(--display);font-style:normal;font-stretch:80%;background:var(--coral);color:var(--noche);border-radius:12px;padding:4px 7px 3px}
.re-why{font:italic 400 17px/1.36 var(--sans);color:var(--trazo);text-wrap:pretty}
.re-why b{font-style:normal;color:var(--crema);font-weight:600}

/* =========================== 8 · escena =========================== */
.rs-arbol{width:720px;display:grid;gap:26px}
.rs-rama h3{font:600 18px/1.2 var(--mono);color:var(--trazo-2);margin-bottom:10px;letter-spacing:.01em}
.rs-rama.gana h3{color:var(--coral)}
.rs-rama .vers li{padding:7px 0 8px}
.rs-rama .vers b{font-size:20px}
.rs-rama .vers span{font-size:17px}
.rs-rama.pierde .vers em{color:var(--trazo-2);border-color:var(--trazo-3)}
.rs-tk{width:960px}
.rs-tk .pr-tx{font-size:15.5px}

/* =========================== 9 y 10 · imagen y control =========================== */
.ri2{gap:0}
.ri2-par{position:relative;width:1180px;height:470px}
.ri2-par .foto{position:absolute;top:0;border-radius:6px}
.ri2-a{left:0}
.ri2-b{left:680px}
.ri2-par .cap{position:absolute;top:372px;font:500 16px/1.2 var(--mono);color:var(--trazo-2)}
.ri2-gen{position:absolute;left:500px;top:110px;width:160px;text-align:center}
.ri2-gen b{display:block;font:760 25px/1.1 var(--display);font-stretch:84%;color:var(--crema)}
.ri2-gen span{display:block;font:400 15px/1.3 var(--mono);color:var(--trazo-2);margin-top:6px}
.ri2-gen i{display:block;font:300 48px/1 var(--sans);font-style:normal;color:var(--trazo-2);margin-top:4px}
.ri2-prods{position:absolute;left:0;top:408px;display:flex;gap:8px;align-items:center}
.ri2-prods .prod{border-radius:4px}
.ri2-prods span{font:500 15px/1.2 var(--mono);color:var(--trazo-2);margin-left:6px}
.ri2-sift{position:absolute;left:0;top:0;width:1180px;height:360px;overflow:visible;pointer-events:none}
.ri2-sift line{stroke:var(--coral);stroke-width:1.3;opacity:.8}
.ri2-sift circle{fill:var(--coral)}
.ri2-veredicto{position:absolute;left:680px;top:408px;width:500px;font:400 17px/1.35 var(--mono);color:var(--trazo)}
.ri2-veredicto b{font:800 30px/1 var(--display);font-stretch:80%;color:var(--coral);margin-right:8px}
.ri2-der{width:410px;margin-left:44px;display:grid;gap:12px}
.ri2-regla{font:400 18px/1.4 var(--sans);color:var(--trazo);border-left:3px solid var(--coral);padding-left:16px}
.ri2-regla b{color:var(--crema);font-weight:600}
.ri2-ints{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.ri2-ints figure{position:relative}
.ri2-ints .foto{border-radius:4px}
.ri2-ints figcaption{font:500 13.5px/1.25 var(--mono);color:var(--trazo-2);margin-top:6px}
.ri2-ints figcaption b{display:block;font:800 22px/1 var(--display);font-stretch:80%;color:var(--crema)}
.ri2-ints .no b{color:var(--trazo-2);text-decoration:line-through;text-decoration-color:var(--coral);text-decoration-thickness:2px}
.ri2-ints .no .foto{opacity:.55}
.ri2-ints .si .foto{outline:3px solid var(--coral);outline-offset:2px}
.ri2-ints .si b{color:var(--coral)}

/* =========================== 11 · lo que sale =========================== */
.rl-tk{width:980px;padding:22px 28px 20px}
.rl-tk .tk-cab b{font-size:30px}
.rl-l{display:grid;grid-template-columns:44px 210px 120px 1fr 54px;gap:14px;align-items:center;font:400 16.5px/1.2 var(--mono);padding:4px 0;border-top:1px dotted var(--hilo)}
.rl-l:first-of-type{border-top:0}
.rl-l .prod{border-radius:3px}
.rl-l b{font:700 19px/1.1 var(--display);font-stretch:86%}
.rl-l .id{color:var(--tinta-2)}
.rl-l .tr{color:var(--tinta-3);font-size:14.5px}
.rl-l .tr i{font-style:normal;color:var(--coral-2);font-weight:700}
.rl-l .q{text-align:right;font-weight:700}
.rl-fin{width:640px}
.rl-fin .foto{border-radius:6px}
.rl-fin p{font:400 17px/1.35 var(--mono);color:var(--trazo-2);margin-top:10px}
.rem-rl{bottom:100px}
"""
CSS += r"""
.flujo.ruta .nodo.on .caja{stroke:var(--coral);stroke-width:4;fill:color-mix(in srgb,var(--coral) 13%,var(--fondo-2))}
.flujo.ruta .nodo.on .nom{fill:var(--coral)}
"""

# --- ajustes después de las capturas ----------------------------------------------------------
CSS += r"""
.rt-banda:has(> .rc-mitad){justify-content:space-between;gap:0}
.rc-mitad{display:flex;gap:26px;align-items:flex-start}
.rc-col{width:290px}
.rc-cifra{font-size:84px;gap:8px}
.rc-cifra i{font-size:40px}
.rc-l li{font-size:19px}
.reg-card{width:506px;grid-template-columns:130px 1fr;gap:0 18px}
.reg-card>.prod,.reg-card>.foto{grid-row:auto;width:130px!important;height:130px!important;border-radius:4px}
.rg-n{font:600 15.5px/1.3 var(--mono);color:var(--tinta);margin:6px 0 4px}
.reg-card dl{margin-top:4px;gap:2px}
.reg-card dl div{grid-template-columns:76px 1fr;font-size:15px}
.reg-card q{grid-column:1/3}
.ri-svg .t-mono.chico{font-size:14.5px}
.rc-tot>b{font:800 46px/1 var(--display);font-stretch:78%;color:var(--crema)}
.rc-tot>span{font:400 22px/1.3 var(--sans);color:var(--trazo)}
.rc-tot .rx b{font:700 21px/1.2 var(--display);font-stretch:88%;color:var(--crema)}
.rc-tot .rx span{font:400 18px/1.3 var(--sans);color:var(--trazo)}
.hiper-rm{position:absolute;left:1140px;top:198px;font:500 16px/1.2 var(--mono);color:var(--trazo-2)}
.hiper-rm b{color:var(--coral);font-weight:600}
.rb-der{width:620px}
.rb-where{font:400 14px/1.45 var(--mono);white-space:pre;overflow:hidden}
.rb-where u{text-decoration:none;color:var(--trazo-2)}
.rb-nota{margin-top:18px;width:1060px}
.ri2-sift line{stroke-width:1.1;opacity:.6}
.rl-tk{padding:18px 28px 16px}
.rl-tk .tk-cab{padding-bottom:10px;margin-bottom:6px}
.rl-l{grid-template-columns:38px 196px 116px 1fr 50px;padding:2px 0;font-size:15.5px}
.rl-l b{font-size:18px}
.rd-ej .ficha-tk{margin-top:12px;padding:12px 16px}
.rd-ej .ficha div{font-size:14px;gap:8px}
.rd-ej .ficha{gap:3px}
.rd-ej .ej-par{grid-template-columns:120px 1fr}
"""
