"""El CSS propio de cada lámina (la grilla de cada una). Lo común está en estilo.py."""

CSS_L = r"""
/* flechas sueltas */
.fl line,.fl path{stroke:var(--tinta);stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round}
.oscura .fl line,.oscura .fl path{stroke:var(--trazo)}

/* ---------- 2 · el problema */
.dos-cam{position:absolute;left:72px;right:72px;top:318px;bottom:246px;display:grid;grid-template-columns:1fr 1fr;column-gap:72px}
.cam{display:flex;flex-direction:column;min-height:0}
.cam .etq{margin-bottom:14px}
.cam-fig{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;border-top:1px solid var(--hilo);border-bottom:1px solid var(--hilo);padding:10px 0}
.cam-fig.sala-gen svg{height:100%;width:auto;max-width:100%}
.grilla-cat{display:grid;grid-template-columns:repeat(3,150px);gap:20px 34px;align-content:center}
.grilla-cat .ficha figcaption span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cam-t{font:400 27px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:20px;max-width:760px}
.cam-t b{color:var(--tinta)}

/* ---------- 3 · qué hace */
.f3a,.f3b,.f3c{position:absolute;top:244px}
.f3a{left:72px;width:520px}.f3b{left:680px;width:520px}.f3c{left:1288px;width:560px}
.f3a .etq,.f3b .etq,.f3c .etq{margin-bottom:14px}
.pedido{font-size:22px;line-height:1.36;color:var(--tinta-2);margin-top:22px;border-left:3px solid var(--cobalto);padding-left:18px}
.lista8{display:grid;grid-template-columns:repeat(4,116px);gap:18px 18px}
.lista8 .ficha figcaption b{font-size:17px}
.lista8 .ficha figcaption span{font-size:13px}
.porque{font-size:22px;line-height:1.36;color:var(--tinta-2);margin-top:26px}
.porque .etq{display:block;font-style:normal;font-size:16px;margin-bottom:6px}

/* ---------- 4 · el programa */
.programa{position:absolute;left:72px;right:72px;top:268px;display:grid;grid-template-columns:80px 560px 1fr 330px;align-items:center}
.programa>div{padding:0 18px 0 0}
.programa .ph{font:400 18px/1 var(--mono);color:var(--tinta-3);padding-bottom:16px;border-bottom:1.6px solid var(--tinta)}
.programa .pn,.programa .pr,.programa .pm,.programa .pe{height:96px;display:flex;align-items:center;border-bottom:1px solid var(--hilo)}
.programa .pn{font:700 22px/1 var(--mono);color:var(--cobalto)}
.programa .pr{font:600 31px/1.15 var(--sans);font-stretch:86%}
.programa .pm{font:400 24px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.programa .pe{gap:6px;flex-wrap:wrap;align-content:center}
.programa .pe .chip{padding:7px 9px;font-size:17px}

/* ---------- separadores: ajustes */
.separador .s-txt{top:118px}
.separador .s-num{font-size:200px}

/* ---------- 6 · indexing */
.indexado{position:absolute;left:72px;top:250px;display:grid;grid-template-columns:repeat(4,384px);column-gap:64px}
.ix{display:flex;flex-direction:column}
.ixn{width:44px;height:44px;border-radius:50%;border:1.6px solid var(--cobalto);color:var(--cobalto);display:grid;place-items:center;font:700 18px/1 var(--mono);margin-bottom:14px}
.ixh{font:700 34px/1.05 var(--sans);font-stretch:80%;margin-bottom:16px;min-height:36px}
.ixfig{height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}
.ix1 .ixfig img{width:220px;height:220px;object-fit:contain}
.ix1 .ixfig .etq{font-size:16px}
.doc8{align-items:stretch;justify-content:center;padding:18px 20px;gap:0}
.l8{font:400 15.5px/1.95 var(--mono);color:var(--tinta-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.l8 span{display:inline-block;width:92px;color:var(--cobalto);font-weight:700}
.vec .vgrid{display:grid;grid-template-columns:repeat(8,26px);gap:4px}
.vec .vgrid i{width:26px;height:26px;background:var(--cobalto);display:block}
.db svg{width:200px;height:210px}
.ix p{font:400 23px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:18px;min-height:92px}
.ix p b{color:var(--tinta)}
.ixr{margin-top:16px;padding-top:12px;border-top:1px solid var(--hilo);color:var(--cobalto)!important}

/* ---------- 7 · por pedido, por capas */
.etapas{position:absolute;left:72px;top:262px;width:490px;display:flex;flex-direction:column;gap:0}
.et{padding:20px 0 20px 26px;border-left:3px solid var(--hilo);opacity:.42;transition:opacity .3s,border-color .3s}
.et.actual{opacity:1;border-left-color:var(--cobalto)}
.etn{font:740 38px/1 var(--sans);font-stretch:78%;display:flex;align-items:baseline;gap:14px}
.etn span{font:400 18px/1 var(--mono);color:var(--tinta-3)}
.et p{font:400 22px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin:8px 0 8px}
.et .etq{font-size:16px;color:var(--cobalto)}
.abanico{position:absolute;background:var(--hoja);border:1px solid var(--hilo);padding:8px 10px 10px;box-shadow:0 14px 30px -18px rgba(19,32,44,.5)}
.ab-k{display:block;font:400 15px/1 var(--mono);color:var(--tinta-3);margin-bottom:7px}
.ab-t{display:flex;gap:5px}
.ab-t .ct{position:relative;width:62px;height:62px;border:1px solid var(--hilo);display:block;background:#fff}
.ab-t .ct img{width:100%;height:100%;object-fit:contain}
.ab-t .ct i{position:absolute;left:0;top:0;font:700 12px/1 var(--mono);font-style:normal;background:var(--tinta);color:#fff;padding:3px 4px}
.abanico .ct{transition:opacity .3s}
.abanico.actual .ct{opacity:.28}
.abanico.actual .ct.ch{opacity:1;outline:3px solid var(--cobalto);outline-offset:1px}
.ab-lin path{fill:none;stroke:var(--cobalto);stroke-width:1.6;stroke-dasharray:5 5}.ab-lin circle{fill:var(--cobalto)}
.capa-foto{position:absolute}
.capa-foto .foto{width:100%;aspect-ratio:4/3}

/* ---------- 8 · documento y consulta */
.dq{position:absolute;left:72px;right:72px;top:252px;display:grid;grid-template-columns:1fr 150px 1fr;align-items:stretch}
.dqc{padding:22px 28px 18px}
.dqh{display:flex;gap:18px;align-items:center;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--hilo)}
.dqh img{width:84px;height:84px;object-fit:contain;flex:none}
.dqh img.rm{width:112px;height:84px;object-fit:cover}
.dqh b{display:block;font:700 26px/1.1 var(--sans);font-stretch:84%;margin:6px 0 4px}
.dqh span{font:400 17px/1.2 var(--mono);color:var(--tinta-3)}
.dqh .etq{font-size:16px;color:var(--cobalto)}
.dqc .l8{font-size:17px;line-height:1.85}
.dqc .l8 span{width:108px}
.dqmid{display:flex;align-items:center;justify-content:center;position:relative}
.dqmid::before{content:"";position:absolute;left:14px;right:14px;top:50%;border-top:2px solid var(--cobalto)}
.dqmid span{position:relative;background:var(--papel);padding:8px 10px;font:700 20px/1 var(--mono);color:var(--cobalto)}
.dqs{position:absolute;left:72px;right:72px;top:722px;display:grid;grid-template-columns:520px 1fr;column-gap:40px;align-items:start}
.dqsl p{font:400 25px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:12px}
.dqsl p b{color:var(--cobalto)}
.tira{display:flex;gap:22px}
.tira .ficha figcaption b{font:700 18px/1 var(--mono);text-align:center}

/* ---------- 9 · variantes: la planilla */
.planilla{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:330px 1fr 230px;align-items:center}
.planilla .ph{font:400 17px/1 var(--mono);color:var(--tinta-3);padding-bottom:12px;border-bottom:1.6px solid var(--tinta)}
.planilla .ph.d,.planilla .px{text-align:right;justify-content:flex-end}
.planilla .pd,.planilla .pa,.planilla .px{height:53px;display:flex;align-items:center;border-bottom:1px solid var(--hilo)}
.planilla .pd{font:600 25px/1 var(--sans);font-stretch:86%}
.planilla .pa{gap:8px}
.planilla .pa .chip{padding:7px 11px;font-size:17px}
.planilla .px{gap:8px}
.xe{font:700 17px/1 var(--mono);color:var(--cobalto);border:1.4px solid var(--cobalto);border-radius:14px;padding:5px 9px}
.xe.pend{color:var(--cota);border-color:var(--cota)}

/* ---------- 10 · línea de tiempo */
.tl{position:absolute;inset:0}
.tl-eje{position:absolute;left:0;top:0;width:1920px;height:1080px}
.tl-eje line{stroke:var(--tinta);stroke-width:2}
.tl-eje line.tk{stroke-width:2}
.ev{position:absolute;width:296px;padding-left:16px;border-left:1.4px solid var(--hilo-2)}
.ev.up{padding-bottom:4px}.ev.dn{padding-top:4px}
.ev.der{border-left:0;border-right:1.4px solid var(--hilo-2);padding-left:0;padding-right:16px;text-align:right}
.evd{font:700 20px/1 var(--mono);color:var(--cobalto);margin-bottom:10px}
.ev h4{font:700 31px/1.08 var(--sans);font-stretch:82%;margin-bottom:8px}
.ev p{font:400 21px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.ev.v0 .evd{color:var(--tinta-3)}
.ev.sig .evd{color:var(--cota)}

/* ---------- 12 · ground truth */
.gt{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:760px 1fr;column-gap:60px}
.anot{display:grid;grid-template-columns:repeat(7,104px);gap:14px;margin-top:14px}
.cifras{position:absolute;left:892px;right:72px;top:560px;display:grid;grid-template-columns:1fr 1fr;gap:26px 40px}
.cifras>div{border-top:1.6px solid var(--tinta);padding-top:12px}
.cifras b{display:block;font:740 64px/1 var(--sans);font-stretch:78%;margin-bottom:8px}
.cifras span{font:400 21px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.cifras .acc b{color:var(--cobalto)}
.cifras .acc{border-top-color:var(--cobalto)}

/* ---------- 13 · las métricas */
.mq{position:absolute;left:72px;right:72px;top:236px;display:flex;gap:22px;align-items:baseline}
.mq .etq{flex:none}
.mq p{font:400 21px/1.3 var(--mono);color:var(--tinta-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mq p b{color:var(--cobalto)}
.cinta{position:absolute;left:72px;top:292px;display:flex;gap:14px}
.cinta-l{position:absolute;left:72px;top:448px;font:400 20px/1 var(--mono);color:var(--tinta-2)}
.cinta-l b{color:var(--cobalto)}
.metricas{position:absolute;left:72px;right:72px;top:504px;display:grid;grid-template-columns:repeat(5,1fr);column-gap:22px}
.mc{border-top:1.6px solid var(--tinta);padding-top:16px;display:flex;flex-direction:column;min-height:330px}
.mn{font:740 34px/1 var(--sans);font-stretch:78%;margin-bottom:12px}
.mc p{font:400 21px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);flex:1}
.mc code{font:400 18px/1.3 var(--mono);color:var(--tinta-3);margin:12px 0 6px}
.mc b{font:700 46px/1 var(--mono);color:var(--cobalto);letter-spacing:-.02em}

/* ---------- 14 · intervalos */
.boot{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:560px 1fr;column-gap:64px}
.boot .xl{gap:34px}
"""

CSS_L += r"""
/* ---------- E5 · números grandes */
.bign{display:grid;grid-template-columns:1fr;gap:34px;padding-top:24px}
.bn{border-top:1.6px solid var(--tinta);padding-top:14px;display:grid;grid-template-columns:430px 1fr;align-items:center;column-gap:30px}
.bnv{font:740 112px/1 var(--sans);font-stretch:76%;color:var(--cobalto);letter-spacing:-.01em;min-height:112px}
.bnv small{font-size:52px;color:var(--tinta-3);font-weight:500}
.bnv.sm{font-size:76px}
.bn p{font:400 26px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}

/* ---------- E7 · dónde ayuda */
.e7b{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:900px 1fr;column-gap:70px}
.e7r .etq{margin-bottom:6px}
.e7c{font:400 25px/1.2 var(--sans);font-stretch:92%;color:var(--tinta-2);margin:16px 0 12px}
.e7c b{color:var(--cobalto)}
.e7r .tira{gap:14px}

/* ---------- E11 · RAGAS */
.rg{display:grid;grid-template-columns:260px 1fr 1fr;column-gap:30px;row-gap:0}
.rg-res{display:contents}
.rg-h{font:400 18px/1 var(--mono);color:var(--tinta-3);padding-bottom:12px;border-bottom:1.6px solid var(--tinta)}
.rg-l{font:600 25px/1.1 var(--sans);font-stretch:86%;display:flex;align-items:center;height:70px;border-bottom:1px solid var(--hilo)}
.rg-b{display:grid;grid-template-columns:1fr 70px 96px;align-items:center;column-gap:10px;height:70px;border-bottom:1px solid var(--hilo)}
.rbar{position:relative;height:22px;background:var(--papel-2)}
.rbar i{position:absolute;left:0;top:0;bottom:0;background:var(--cobalto)}
.rbar em.vara{position:absolute;top:-8px;bottom:-8px;width:3px;margin-left:-1.5px;background:var(--cota)}
.rv{font:700 22px/1 var(--mono);color:var(--cobalto)}
.rn{font:400 15px/1.1 var(--mono);color:var(--tinta-3)}
.rq{margin-top:22px;border-left:3px solid var(--cota);padding-left:20px}
.rq .etq{color:var(--cota);margin-bottom:8px}
.rq p{font-size:25px;line-height:1.3;color:var(--tinta)}

/* ---------- E12 · diseño */
.e12a{position:absolute;left:72px;right:72px;top:262px;bottom:118px;display:grid;grid-template-columns:780px 1fr;column-gap:72px}
.cmp{display:grid;grid-template-columns:220px 1fr 1fr;margin-top:6px}
.cmp>div{height:52px;display:flex;align-items:center;border-bottom:1px solid var(--hilo);font:400 23px/1 var(--sans);font-stretch:92%}
.cmp .ch{font:700 19px/1 var(--mono);color:var(--tinta);border-bottom:1.6px solid var(--tinta)}
.cmp .cl{color:var(--tinta-3);font:400 18px/1 var(--mono)}
.cmp .cv{font:700 25px/1 var(--mono)}
.juez{background:var(--hoja);border:1px solid var(--hilo);padding:18px 22px;margin-top:-6px}
.jrow{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.jo{font:400 17px/1 var(--mono);color:var(--tinta-3);width:80px}
.jb{font:700 18px/1 var(--mono);padding:9px 12px;background:var(--papel-2);color:var(--tinta-2)}
.jb.t{background:var(--cobalto);color:#fff}
.jv{font:400 18px/1 var(--mono);color:var(--tinta-3)}
.juez p{font:400 22px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:6px}
.defs{display:grid;grid-template-columns:230px 1fr;gap:8px 18px;font:400 19px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.defs dt{font:700 17px/1.4 var(--mono);color:var(--cobalto)}

/* ---------- E12 · resultados */
.e12b{position:absolute;left:72px;right:72px;top:250px}
.jg{display:grid;grid-template-columns:repeat(11,1fr);column-gap:12px;position:relative;padding-top:30px}
.jgk{position:absolute;left:0;right:0;top:0;display:grid;grid-template-columns:5fr 6fr;column-gap:12px;font:400 16px/1 var(--mono);color:var(--tinta-3)}
.jgk span{border-top:1.6px solid var(--tinta);padding-top:6px}
.jgk span+span{border-top-color:var(--cobalto);color:var(--cobalto)}
.jr .th{aspect-ratio:4/3;overflow:hidden;background:#fff}
.jr .th img{width:100%;height:100%;object-fit:cover}
.jr .nm{font:500 18px/1.1 var(--sans);font-stretch:86%;margin:8px 0 6px;min-height:20px}
.jr .v{display:flex;align-items:center;gap:5px}
.jr .v i{width:16px;height:16px;border-radius:50%;display:block}
.jr .v i.vt{background:var(--cobalto)}.jr .v i.vi{background:var(--grafito)}.jr .v i.ve{background:none;box-shadow:inset 0 0 0 2px var(--grafito)}
.jr .v b{font:700 13px/1 var(--mono);color:var(--tinta-3);margin-left:4px}
.jr .v b.t{color:var(--cobalto)}
.credito{font:400 14px/1.35 var(--mono);color:var(--tinta-3);margin-top:12px}
.e12g{display:grid;grid-template-columns:1fr 1fr 1.5fr;column-gap:26px;margin-top:22px}
.cc{border-top:1.6px solid var(--tinta);padding-top:12px}
.cc.hi{border-top-color:var(--cobalto)}
.ccn{font:740 58px/1 var(--sans);font-stretch:78%;margin:8px 0}
.cc.hi .ccn{color:var(--cobalto)}
.cc p{font:400 21px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.cc p+p{margin-top:6px}
.cc strong{color:var(--cobalto)}

/* ---------- E12 · un caso */
.loft{position:absolute;left:72px;right:72px;top:258px;display:grid;grid-template-columns:500px 1fr;column-gap:60px}
.loft .pedido{font-size:22px}
.lst{gap:16px}
.lst .ficha figcaption b{font-size:16px}
.lst .ficha figcaption span{font-size:13px}
.gley{display:flex;gap:22px;font:400 16px/1 var(--mono);color:var(--tinta-3);margin-top:18px;align-items:center}
.gley i{display:inline-block;width:18px;height:7px;margin-right:7px;vertical-align:2px}
.gley i.g2{background:var(--verde)}.gley i.g1{background:#E8B04B}.gley i.g0{background:var(--cota)}
.lfr .porque{margin-top:18px;font-size:22px}

/* ---------- E13 · métricas de imagen */
.imet{position:absolute;left:72px;right:72px;top:236px;bottom:220px;display:grid;grid-template-columns:repeat(4,1fr);column-gap:28px}
.im{display:flex;flex-direction:column;border-top:1.6px solid var(--tinta);padding-top:14px;min-height:0}
.imn{font:740 30px/1.05 var(--sans);font-stretch:78%;display:flex;align-items:center;gap:12px;margin-bottom:12px}
.imn i{flex:none;width:36px;height:36px;border-radius:50%;border:1.6px solid var(--cobalto);color:var(--cobalto);display:grid;place-items:center;font:700 15px/1 var(--mono);font-style:normal}
.im p{font:400 21px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.im .imf{width:100%;margin-top:14px;background:#fff}
.im p.nota{font:400 16px/1.4 var(--mono);color:var(--tinta-3)}
.pares{display:flex;flex-direction:column;gap:10px;margin-top:14px}
.par{display:grid;grid-template-columns:96px 96px 1fr;column-gap:10px;align-items:center}
.par img{width:96px;height:96px;object-fit:cover;background:#fff;border:1px solid var(--hilo)}
.par img:first-child{object-fit:contain}
.par span{font:400 16px/1.3 var(--mono);color:var(--tinta-2)}
.im-gr{margin-top:auto!important;font:700 30px/1.15 var(--sans)!important;font-stretch:82%!important;color:var(--tinta)!important;border-left:4px solid var(--cobalto);padding-left:16px}

/* ---------- E13 · prompt */
.vgrid{display:grid;grid-template-columns:330px 1fr;row-gap:18px;column-gap:18px}
.vr{display:grid;grid-template-columns:330px 330px;column-gap:18px}
.vt{margin:0}
.vi{position:relative;width:330px;height:220px;overflow:hidden;background:#fff}
.vi img{width:100%;height:100%;object-fit:cover}
.vt figcaption{margin-top:7px;display:flex;flex-direction:column;gap:2px}
.vt figcaption b{font:600 19px/1.15 var(--sans);font-stretch:88%}
.vt figcaption span{font:400 14px/1.2 var(--mono);color:var(--tinta-3)}

/* ---------- E13 · el control */
.atts{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:repeat(4,1fr);column-gap:24px}
.at{margin:0}
.ai{position:relative;aspect-ratio:4/3;overflow:hidden;background:#fff}
.ai img{width:100%;height:100%;object-fit:cover}
.at figcaption{margin-top:10px;display:flex;flex-direction:column;gap:4px}
.at figcaption b{font:700 24px/1.1 var(--sans);font-stretch:84%}
.at figcaption span{font:400 17px/1.25 var(--mono);color:var(--tinta-2)}
.atn{position:absolute;left:72px;top:720px;font-size:19px}

/* ---------- E14 · réplica */
.rgrid{display:grid;grid-template-columns:repeat(3,380px);gap:16px 20px}
.rt{margin:0}
.ri{position:relative;overflow:hidden;background:#fff}
.ri img{width:100%;height:100%;object-fit:cover}
.rt figcaption{margin-top:6px;display:flex;flex-direction:column;gap:1px}
.rt figcaption b{font:600 19px/1.1 var(--sans);font-stretch:88%}
.rt figcaption span{font:400 14px/1.2 var(--mono);color:var(--tinta-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk{height:220px;display:flex;flex-direction:column;justify-content:space-between}
.rk>div{border-top:1.6px solid var(--tinta);padding-top:6px;display:grid;grid-template-columns:110px 1fr;align-items:center;column-gap:12px}
.rk b{font:740 44px/1 var(--sans);font-stretch:78%}
.rk span{font:400 17px/1.2 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.rk .acc{border-top-color:var(--cobalto)}.rk .acc b{color:var(--cobalto)}
.ri.pend{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;background:repeating-linear-gradient(-45deg,transparent 0 9px,rgba(226,70,47,.08) 9px 10px),var(--papel);border:1.4px dashed var(--cota)}
.ri.pend small{font:400 15px/1.3 var(--mono);color:var(--cota);text-align:center;max-width:80%}

/* ---------- T4 */
.t4tag{position:absolute;left:72px;right:72px;top:240px;display:flex;align-items:center;gap:20px}
.t4{position:absolute;left:72px;right:72px;top:300px;display:grid;grid-template-columns:80px 1fr 1fr 230px 240px}
.t4h{font:400 17px/1 var(--mono);color:var(--tinta-3);padding:0 14px 12px 0;border-bottom:1.6px solid var(--tinta)}
.t4c{font:400 21px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);padding:12px 14px 12px 0;border-bottom:1px solid var(--hilo)}
.t4c code{font:400 15px/1.3 var(--mono);color:var(--tinta);background:var(--papel-2);padding:1px 4px}
.t4c.b{font:700 19px/1.3 var(--mono);color:var(--cota)}
.t4c.m{font:400 18px/1.3 var(--mono)}
.t4tot{position:absolute;left:72px;right:72px;bottom:130px;font:400 23px/1.35 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.t4tot b{color:var(--tinta)}

/* ---------- cierre */
.lam-decidimos .planilla .chip.si{background:var(--cobalto);color:#fff}
.camino{position:absolute;left:72px;right:72px;top:262px}
.costo{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:680px 1fr;column-gap:80px}
.gran{font:740 120px/1 var(--sans);font-stretch:76%;color:var(--cobalto);margin:8px 0 18px}
.gran.g2{color:var(--tinta);font-size:96px}
.cbar{display:flex;height:66px;gap:3px}
.cb{display:flex;flex-direction:column;justify-content:center;padding:0 12px;color:#fff;min-width:0}
.cb b{font:700 18px/1 var(--mono)}.cb span{font:400 16px/1.2 var(--mono);opacity:.9;margin-top:4px}
.cb0{background:var(--cobalto-2)}.cb1{background:var(--cobalto)}.cb2{background:var(--tinta)}
.apr{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:1fr 1fr;column-gap:80px}
.act{font:400 19px/1 var(--mono);color:var(--cobalto);padding-bottom:12px;border-bottom:1.6px solid var(--cobalto);margin-bottom:6px}
.lim .act{color:var(--cota);border-bottom-color:var(--cota)}
.apri{display:grid;grid-template-columns:44px 1fr;column-gap:12px;padding:18px 0;border-bottom:1px solid var(--hilo)}
.apr .apri span{font:700 24px/1.3 var(--mono);color:var(--cobalto)}
.apr .lim .apri span{color:var(--cota)}
.apr .apri p{font:400 26px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.apr .apri p strong{color:var(--tinta)}

/* ---------- futuro · cajas */
.fcols{position:absolute;left:72px;right:72px;top:352px;display:grid;grid-template-columns:repeat(3,560px);column-gap:48px}
.fch{display:flex;flex-direction:column;gap:6px;margin-bottom:12px;border-top:1.6px solid var(--tinta);padding-top:10px}
.fcol:nth-child(2) .fch{border-top-color:var(--cobalto)}
.fcol:nth-child(3) .fch{border-top-color:var(--naranja)}
.fcn{font:740 34px/1 var(--sans);font-stretch:78%}
.fcol:nth-child(2) .fcn{color:var(--cobalto)}
.fcol:nth-child(3) .fcn{color:#D9701B}
.fch .etq{font-size:17px}
.fth{display:flex;gap:16px;margin-top:14px}
.rt.mini figcaption b{font:400 14px/1.1 var(--mono);color:var(--tinta-2)}
.fnum{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:860px 1fr;column-gap:70px}
.ktab{display:grid;grid-template-columns:300px repeat(3,1fr)}
.kh{font:700 19px/1 var(--mono);padding-bottom:12px;border-bottom:1.6px solid var(--tinta);text-align:right}
.kh:nth-child(3){color:var(--cobalto)}.kh:nth-child(4){color:#D9701B}
.kl{font:400 22px/1.2 var(--sans);font-stretch:92%;color:var(--tinta-2);height:76px;display:flex;align-items:center;border-bottom:1px solid var(--hilo)}
.kv{height:76px;display:flex;align-items:center;justify-content:flex-end;font:700 34px/1 var(--mono);border-bottom:1px solid var(--hilo)}
.kv.acc{color:var(--cobalto)}
.kv.pend .chip{font-size:15px;padding:6px 9px}
.fnl .nota{margin-top:18px}
.ppl{display:flex;flex-direction:column;gap:5px}
.pp{display:grid;grid-template-columns:160px 1fr;align-items:center;column-gap:16px;border-bottom:1px solid var(--hilo);padding-bottom:5px}
.ppn{font:600 23px/1 var(--sans);font-stretch:86%}
.ppb{display:flex;flex-direction:column;gap:3px}
.ppr{display:grid;grid-template-columns:1fr 70px;align-items:center;column-gap:10px;height:17px}
.ppr i{display:block;height:13px;background:var(--grafito)}
.ppr b{font:700 15px/1 var(--mono);color:var(--tinta-2)}
.ppr.pend i{width:100%;height:0;border-top:1.4px dashed var(--cota);background:none}
.ppr.pend b{color:var(--cota);font-weight:400}

/* ---------- futuro · medidas reales */
.fps{position:absolute;left:72px;top:258px;width:600px;display:flex;flex-direction:column;gap:20px}
.fp{display:grid;grid-template-columns:50px 1fr;column-gap:16px}
.fp i{width:44px;height:44px;border-radius:50%;background:var(--cobalto);color:#fff;display:grid;place-items:center;font:700 18px/1 var(--mono);font-style:normal}
.fp b{font:740 31px/1.05 var(--sans);font-stretch:78%;display:block;margin:4px 0 6px}
.fp p{font:400 22px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.fp p b{display:inline;font:700 22px/1 var(--mono);color:var(--cobalto);margin:0}
.fmas{background:var(--plano);color:#fff;padding:18px 24px;margin-top:6px}
.fmas .etq{color:var(--naranja);display:block;margin-bottom:8px}
.fmas p{font:400 23px/1.3 var(--sans);font-stretch:90%}
.fmas strong{color:var(--naranja)}
.lam-medidas .sala .cota.med line{stroke:var(--cobalto)}.lam-medidas .sala .cota.med .ct{fill:var(--cobalto);font-weight:700}
.lam-medidas .sala .rot.sinm .lin{stroke:var(--cota)}.lam-medidas .sala .rot.sinm .pto{fill:var(--cota)}
.lam-medidas .sala .rot.sinm .rt{fill:var(--cota)}.lam-medidas .sala .rot.sinm .rs{fill:var(--cota);opacity:1}

/* ---------- gracias */
.gracias .g-txt{position:absolute;left:96px;top:150px;width:760px}
.gracias h1{font:780 210px/.86 var(--sans);font-stretch:75%;letter-spacing:-.018em;margin:18px 0 18px}
.gracias .g-sub{font:400 46px/1.2 var(--sans);font-stretch:90%;color:var(--naranja)}
.gracias .equipo{position:absolute;left:96px;bottom:104px;font:500 27px/1.42 var(--sans);font-stretch:90%}
.gracias .equipo .etq{display:block;margin-bottom:12px}
.g-sala{position:absolute;right:30px;top:40px;width:1090px}
.g-fotos{position:absolute;left:96px;top:468px;display:grid;grid-template-columns:300px 44px 300px;align-items:center}
.g-fotos figure{margin:0}
.g-fotos .foto{width:300px;height:225px;padding:6px}
.g-fotos .gf{font:400 34px/1 var(--mono);color:var(--naranja);text-align:center}
.gracias figcaption{font:400 16px/1 var(--mono);color:var(--trazo);margin-top:9px}
.g-fotos .pie-foto{grid-column:1/-1;margin-top:10px;font-size:16px;max-width:640px}
/* ---------- anexo */
.rai{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:330px 1fr 1.25fr}
.rai .rh{font:400 17px/1 var(--mono);color:var(--tinta-3);padding:0 20px 12px 0;border-bottom:1.6px solid var(--tinta)}
.rai .r1,.rai .r2,.rai .r3{padding:15px 20px 15px 0;border-bottom:1px solid var(--hilo);font:400 21px/1.3 var(--sans);font-stretch:92%}
.rai .r1{font-weight:700;font-stretch:84%;font-size:24px}
.rai .r2{color:var(--tinta-2)}
.abl{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:1fr 1fr;column-gap:50px}
.abt{display:grid;grid-template-columns:1fr repeat(5,96px)}
.abh{font:400 14px/1 var(--mono);color:var(--tinta-3);padding-bottom:8px;border-bottom:1.6px solid var(--tinta);text-align:right}
.abh:first-child{text-align:left}
.ab1{font:400 15px/1 var(--mono);height:36px;display:flex;align-items:center;border-bottom:1px solid var(--hilo);white-space:nowrap;overflow:hidden}
.ab1.hi{color:var(--cobalto);font-weight:700}
.ab2{font:400 15px/1 var(--mono);height:36px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--hilo);color:var(--tinta-2)}
.abn{position:absolute;left:72px;bottom:120px}
"""

CSS_L += r"""
.lam-medidas .sala .rot .rt{font-size:25px}.lam-medidas .sala .rot .rs{font-size:18px}
.apr .apri p{font-size:28px}
"""

CSS_L += r"""
/* ---------- futuro · réplica, ronda 1 y ronda 2 */
.fcols.r1{top:262px;grid-template-columns:repeat(3,520px);column-gap:108px}
.rt.mini .sello{left:6px;top:6px;font-size:12px;padding:4px 6px}
/* el prompt común y la línea que cambia */
.r2p{position:absolute;left:72px;right:72px;top:256px;display:grid;grid-template-columns:600px 1fr;column-gap:44px}
.r2h .prb p{font-size:15.5px;margin-bottom:7px}
.prb p.cmbt{font:700 13px/1 var(--mono);color:var(--cobalto);margin:12px 0 5px}
.prb p.cambia{color:var(--cobalto);font-weight:700;background:var(--cobalto-suave);margin:0 -10px 10px;padding:6px 10px}
.r2h .nota{font-size:16px;margin-top:14px}
.r2c,.r2f{display:grid;grid-template-columns:178px 236px 1fr;column-gap:18px}
.r2c{font:400 14px/1 var(--mono);color:var(--tinta-3);padding-bottom:9px;border-bottom:1.6px solid var(--tinta)}
.r2f{padding:10px 0;border-bottom:1px solid var(--hilo);align-items:start}
.r2n b{display:block;font:740 25px/1.02 var(--sans);font-stretch:80%}
.r2n span{display:block;margin-top:5px;font:400 13px/1.2 var(--mono);color:var(--tinta-3)}
.r2e{display:flex;gap:7px;align-items:flex-start}
.r2e figure{margin:0}
.r2e img{display:block;width:80px;height:50px;object-fit:cover;border:1px solid var(--hilo)}
.r2e figcaption{font:400 11px/1 var(--mono);color:var(--tinta-3);margin-top:4px}
.r2m{font:400 11.5px/1.25 var(--mono);color:var(--tinta-3);padding-top:13px;white-space:nowrap}
.r2t p{font:400 16px/1.42 var(--mono);color:var(--tinta-2)}
.r2t p.r2x{font:400 16px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-3);margin-top:3px}
.r2t p.r2x b{font:700 14px/1 var(--mono);color:var(--tinta-2)}
/* el lugar en palabras */
.r2w{position:absolute;left:72px;right:72px;top:256px;display:grid;grid-template-columns:900px 1fr;column-gap:56px}
.r2wl{display:flex;flex-direction:column;gap:20px}
.r2wl .prb p{font-size:15px}
.r2a{font:400 21px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:10px}
.r2a b{color:var(--tinta);font-weight:680}
.r2wr{display:flex;flex-direction:column;gap:14px}
.r2par{display:flex;gap:20px}
.r2o{font:400 21px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.r2o b{color:var(--tinta);font-weight:680}
.r2ojo{position:absolute;left:72px;right:72px;bottom:132px;font:400 25px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);border-left:4px solid var(--cota);padding:6px 0 6px 18px}
.r2ojo b{color:var(--cota)}
/* la comparación */
.r2r{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:990px 1fr;column-gap:46px}
.rtr{display:grid;grid-template-columns:250px 1fr 130px 160px;column-gap:16px;align-items:center;height:45px;border-bottom:1px solid var(--hilo)}
.rth{height:auto;padding-bottom:10px;border-bottom:1.6px solid var(--tinta);font:400 15px/1.15 var(--mono);color:var(--tinta-3);align-items:end}
.rth div:nth-child(n+3){text-align:right}
.rtg{font:400 15px/1 var(--mono);color:var(--tinta-3);padding:15px 0 8px;border-bottom:1px solid var(--hilo)}
.rtg.g2{color:var(--cobalto)}
.rn{font:600 22px/1.05 var(--sans);font-stretch:86%}
.ri2{display:grid;grid-template-columns:1fr 64px 146px;align-items:center;column-gap:10px}
.ri2 i{display:block;height:14px;background:var(--grafito)}
.ri2 b{font:700 24px/1 var(--mono);text-align:right}
.ri2 small{font:400 13px/1 var(--mono);color:var(--tinta-3);white-space:nowrap}
.rl{font:700 24px/1 var(--mono);text-align:right}
.rd{text-align:right;font:700 19px/1 var(--mono)}
.rd .mal{color:var(--cota)}.rd .bien{color:var(--verde)}.rd .no{color:var(--tinta-3);font-weight:400}
.rtr.r1 .rn,.rtr.r1 .ri2 b,.rtr.r1 .rl{color:var(--tinta-3);font-weight:500}
.rtr.r1 .ri2 i{background:#CDD3DA}
.rtr.hi{background:var(--cobalto-suave);box-shadow:-10px 0 0 var(--cobalto-suave),10px 0 0 var(--cobalto-suave)}
.rtr.hi .rn,.rtr.hi .ri2 b,.rtr.hi .rl{color:var(--cobalto)}.rtr.hi .rn{font-weight:740}
.rtr.hi .ri2 i{background:var(--cobalto)}
.r2r .nota{font-size:16px;margin-top:12px}
.r2im{display:grid;grid-template-columns:repeat(2,360px);gap:12px 20px}
/* anexo · réplica */
.axg{position:absolute;left:72px;right:72px;top:244px;display:grid;grid-template-columns:repeat(6,270px);column-gap:31px}
.axc{display:flex;flex-direction:column;gap:10px}
.axh{border-top:1.6px solid var(--tinta);padding-top:8px}
.axh b{display:block;font:740 22px/1.05 var(--sans);font-stretch:80%}
.axh span{font:400 13px/1.2 var(--mono);color:var(--tinta-3)}
.axc .rt figcaption span{white-space:normal;font-size:12px;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.amtab{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:300px 130px repeat(6,1fr) 140px}
.amh{font:400 15px/1.1 var(--mono);color:var(--tinta-3);padding-bottom:10px;border-bottom:1.6px solid var(--tinta);text-align:right}
.amh:first-child{text-align:left}
.amg{grid-column:1/-1;font:400 15px/1 var(--mono);color:var(--cobalto);padding:16px 0 8px;border-bottom:1px solid var(--hilo)}
.amn{font:600 22px/1 var(--sans);font-stretch:86%;height:50px;display:flex;align-items:center;border-bottom:1px solid var(--hilo)}
.amn.hi{color:var(--cobalto);font-weight:740}
.amw,.amt{font:400 18px/1 var(--mono);height:50px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--hilo);color:var(--tinta-2)}
.amt{font-weight:700;color:var(--tinta)}
.amv{height:50px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--hilo);padding-right:10px;background:rgba(36,83,214,calc(var(--a) * .3))}
.amv b{font:700 18px/1 var(--mono)}
.amno{position:absolute;left:72px;bottom:120px}
"""

CSS_L += r"""
/* ================= revisión del 2026-11-12: láminas nuevas ================= */
.nb{white-space:nowrap}
.graf .notag{font:400 17px var(--mono);fill:var(--tinta-2)}
.graf .notag.main{fill:var(--cobalto);font-weight:700}
.xc.tram{border-style:dashed;border-color:var(--tinta-2)}.xc.tram b{color:var(--tinta);border-color:var(--tinta-2)}
/* 3 · qué hace: la lista de cinco */
.lista8.l5{grid-template-columns:repeat(3,150px);gap:16px 22px}
/* 4 · por qué RAG */
.tres{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:repeat(3,1fr);column-gap:48px}
.d3{border-top:1.6px solid var(--tinta);padding-top:16px}
.d3.hi{border-top-color:var(--cobalto)}
.d3n{font:700 22px/1 var(--mono);color:var(--cobalto);margin-bottom:14px}
.d3 .etq{margin-bottom:10px}.d3.hi .etq{color:var(--cobalto)}
.d3 h3{font:740 40px/1.05 var(--sans);font-stretch:78%;margin-bottom:14px;text-wrap:balance}
.d3 p{font:400 26px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.d3 p b{color:var(--tinta)}
.dos-n{position:absolute;left:72px;right:72px;top:672px;display:grid;grid-template-columns:1fr 1fr;column-gap:64px;border-top:1px solid var(--hilo);padding-top:20px}
.dos-n p{font:400 25px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.dos-n p b{color:var(--tinta)}
/* dos bancos de prueba */
.bancos{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:860px 1fr;column-gap:64px}
.bnh{display:flex;align-items:baseline;gap:16px;border-top:1.6px solid var(--tinta);padding-top:10px;margin-bottom:14px}
.bnh b{font:740 34px/1 var(--sans);font-stretch:78%}
.bnh span{font:400 17px/1 var(--mono);color:var(--tinta-3)}
.bn2 .bnh{border-top-color:var(--cobalto)}.bn2 .bnh b{color:var(--cobalto)}
.bng{display:grid;grid-template-columns:372px 1fr;column-gap:24px}
.bng .etq{font-size:16px}
.anot2{display:grid;grid-template-columns:repeat(7,58px);gap:8px;margin-top:10px}
.cifras.c4{position:static;margin-top:18px;grid-template-columns:repeat(4,1fr);gap:0 22px}
.cifras.c4 b{font-size:50px}.cifras.c4 span{font-size:18px}
.bnota{font:400 23px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:16px;border-left:4px solid var(--cobalto);padding-left:16px}
.bnota b{color:var(--tinta)}
.bth{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.bth .bt img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}
.bn2 .credito{margin-top:8px}
.bt2{font:400 23px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);margin:12px 0 18px}
.bt2 b{color:var(--tinta)}
.bn2 .juez{margin-top:0}
/* las métricas, con el valor de hoy */
.mc p b{font:inherit;font-weight:640;color:var(--tinta);letter-spacing:0}
.metricas.m2 .mc{min-height:392px}
.mhoy{margin-top:12px;border-top:1px solid var(--hilo);padding-top:8px;font:400 18px/1.2 var(--mono);color:var(--tinta-2)}
.mhoy span{display:block;font-size:14px;color:var(--tinta-3);margin-bottom:4px}
.mc .mhoy b{font:700 18px/1.2 var(--mono);letter-spacing:0;color:var(--cobalto)}
/* el generador y los jueces */
.gen{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:860px 1fr;column-gap:60px}
.gm{display:grid;grid-template-columns:200px 1fr;column-gap:22px;align-items:start;border-top:1.6px solid var(--tinta);padding-top:14px;margin-bottom:20px}
.gmv{font:740 92px/.95 var(--sans);font-stretch:76%;color:var(--cobalto)}
.gm h3{font:740 30px/1.05 var(--sans);font-stretch:80%;margin-bottom:8px}
.gm p{font:400 22px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.gm p b{color:var(--tinta)}
.gbar{grid-column:1/-1;position:relative;height:18px;background:var(--papel-2);margin:14px 0 8px}
.gbar em{position:absolute;left:0;top:0;bottom:0;background:var(--cobalto)}
.gbar i{position:absolute;top:-6px;width:4px;height:30px;margin-left:-2px;background:var(--tinta)}
.gbar u{position:absolute;top:-8px;bottom:-8px;width:3px;margin-left:-1.5px;background:var(--cota);text-decoration:none}
.gbar u span{position:absolute;left:8px;top:-12px;white-space:nowrap;font:400 14px/1 var(--mono);color:var(--cota)}
.gbar u.b{background:var(--tinta-3)}.gbar u.b span{color:var(--tinta-3);left:auto;right:8px}
.gm .gn,.gn{grid-column:1/-1;font:400 18px/1.4 var(--sans);font-stretch:94%;color:var(--tinta-2);margin-top:4px}
.gn.sobre{font:400 15.5px/1.4 var(--mono);color:var(--tinta-3)}
.gr .pr{margin-bottom:14px}
.gnotas .apri,.dzr .apri{display:grid;grid-template-columns:36px 1fr;column-gap:10px;padding:10px 0;border-bottom:1px solid var(--hilo)}
.gnotas .apri span,.dzr .apri span{font:700 20px/1.35 var(--mono);color:var(--cobalto)}
.gnotas .apri p,.dzr .apri p{font:400 21px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.gnotas .apri p strong,.dzr .apri p strong{color:var(--tinta)}
/* la imagen: las 11 finales */
.imgm{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:800px 1fr;column-gap:56px}
.pares2{display:grid;grid-template-columns:repeat(5,1fr);column-gap:14px;margin-bottom:10px}
.pr2{display:flex;flex-direction:column;gap:6px}
.pr2 img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border:1px solid var(--hilo);display:block}
.pr2 img.rec{object-fit:cover}
.pr2 i{display:block;width:100%;aspect-ratio:1;border:1px dashed var(--hilo-2)}
.pr2 span{font:700 15px/1.2 var(--mono);color:var(--tinta-3);text-align:center}
.pr2 span.ok{color:var(--verde)}
.gm.g2{grid-template-columns:auto 1fr;margin-top:14px;margin-bottom:0;align-items:center}
.gm.g2 .gmv{font-size:74px;white-space:nowrap}
.fin2{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.fi2{position:relative}
.fi2 img{width:100%;aspect-ratio:3/2;object-fit:cover;display:block}
.fi2 .sello{left:6px;top:6px;font-size:12.5px;padding:5px 7px}
.finr{display:flex;flex-direction:column;justify-content:center;padding-left:10px}
.finr b{font:740 60px/1 var(--sans);font-stretch:76%;color:var(--cobalto)}
.finr span{font:400 18px/1.25 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:6px}
/* las trampas */
.trampas{position:absolute;left:72px;right:72px;top:262px;display:grid;grid-template-columns:1fr 1fr;gap:26px 64px}
.tp{border-top:1.6px solid var(--cota);padding-top:14px;display:grid;grid-template-columns:54px 1fr;column-gap:8px}
.tpn{font:700 22px/1.5 var(--mono);color:var(--cota);grid-row:1/3}
.tp h3{font:740 32px/1.08 var(--sans);font-stretch:80%;margin-bottom:8px}
.tp p{font:400 23px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2);grid-column:2}
/* el recorrido: la búsqueda híbrida, dibujada */
.hib{display:block;height:auto;overflow:visible}
.hib .hb{fill:#fff;stroke:var(--tinta);stroke-width:1.4}
.hib .hb.n{fill:var(--cobalto-suave);stroke:var(--cobalto);stroke-width:2}
.hib .ht{font:600 17px var(--sans);font-stretch:88%;fill:var(--tinta)}
.hib .hs{font:400 12.5px var(--mono);fill:var(--tinta-3)}
.hib .hg{font:700 10.5px var(--mono);fill:var(--tinta-3);letter-spacing:.04em}
.hib .hg.n{fill:var(--cobalto)}
.hib .hf{stroke:var(--tinta-2);stroke-width:1.4}.hib .hf.n{stroke:var(--cobalto)}
.hib .hp{fill:var(--tinta-2)}.hib .hp.n{fill:var(--cobalto)}
.hib .hn{font:400 12px var(--mono);fill:var(--tinta-3)}
.tram4{display:flex;flex-direction:column;gap:12px}
.fp4 .p4{font-size:24px;line-height:1.4;margin-top:8px}
.p4b{margin-top:26px}
.rc6 .g3{column-gap:36px}
.tira.c6{gap:14px}
.tira.c6 .ficha figcaption b{font-size:17px}
.e7g{display:flex;flex-direction:column;gap:6px;margin:4px 0 10px}
.e7f{display:grid;grid-template-columns:150px 1fr;align-items:center}
.e7k{font:600 20px/1 var(--sans);font-stretch:86%}
.e7f .ct{width:54px;height:54px;opacity:.5}
.e7f .ct.ch{opacity:1;outline:3px solid var(--cobalto);outline-offset:1px}
/* los desafíos */
.dz{position:absolute;left:72px;right:72px;top:246px;display:flex;flex-direction:column;gap:14px}
.dz-p{display:grid;grid-template-columns:250px 1fr;align-items:center;column-gap:10px}
.dz-k b{display:block;font:740 26px/1.05 var(--sans);font-stretch:80%}
.dz-k span{font:400 15px/1.2 var(--mono);color:var(--tinta-3)}
.dz-k.ok span{color:var(--cobalto)}
.dz-p svg{width:100%;height:auto}
.dz2{position:absolute;left:72px;right:72px;top:478px;display:grid;grid-template-columns:820px 1fr;column-gap:60px}
.dzl .etq{margin-bottom:8px;color:var(--cobalto)}
.dzl .nota{font-size:17px}
/* experimentos */
.vars{display:grid;grid-template-columns:1fr 1fr;column-gap:30px;margin-top:4px}
.vr2{display:grid;grid-template-columns:104px 104px 1fr;column-gap:10px;align-items:center;border-top:1px solid var(--hilo);padding-top:10px}
.vr2 figure{margin:0}
.vr2 img{width:104px;height:104px;object-fit:contain;background:#fff;border:1px solid var(--hilo);display:block}
.vr2 figure.p img{border:2px solid var(--cobalto)}
.vr2 figcaption{font:400 12px/1.2 var(--mono);color:var(--tinta-3);margin-top:4px}
.vr2 p{font:400 19px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.vr2 p b{color:var(--tinta)}
.e5n{display:grid;grid-template-columns:1fr 1fr;column-gap:30px;margin-top:4px}
.e5n div{border-top:1.6px solid var(--tinta);padding-top:8px}
.e5n b{display:block;font:700 27px/1.1 var(--mono);color:var(--cobalto);margin-bottom:4px}
.e5n span{font:400 18px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.lam-e6 .e6a{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:1fr 1fr;column-gap:64px}
.lam-e6 .e6a .bloque p{font-size:23px}
.e12b.e6b{top:398px}
.e6b .jr .th{aspect-ratio:16/10}
.e6b .ccn{font-size:46px;margin:4px 0}
.e6b .ccn small{font:400 20px var(--mono);color:var(--tinta-3)}
.e6b .e12g{margin-top:14px;grid-template-columns:1fr 1fr 1.3fr}
.e6b .cc p{font-size:19px}
.x7{display:grid;grid-template-columns:150px 1fr;column-gap:16px;row-gap:8px;align-items:center}
.x7k b{display:block;font:740 22px/1.05 var(--sans);font-stretch:80%}
.x7k span{font:400 13px/1.25 var(--mono);color:var(--tinta-3);display:block;margin-top:4px}
.x7a{display:flex;gap:20px;align-items:center}
.x7 .jg{display:flex;gap:6px;padding-top:0}
.x7 .jr{width:84px;flex:none}
.x7 .jr .nm{font-size:13px;margin:4px 0 3px;min-height:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.x7 .jr .v i{width:11px;height:11px}.x7 .jr .v b{display:none}
.x7 .cc{padding-top:6px;flex:1}
.x7 .ccn{font-size:42px;margin:0 0 2px}
.x7 .cc p{font-size:16.5px;line-height:1.3}
.x7 .cc.x7s{display:grid;grid-template-columns:auto 1fr;column-gap:18px;align-items:center}
.lam-e7 .credito{margin-top:6px;font-size:12.5px}
.hoja.rag{padding:12px 20px 14px;margin-top:8px}
.rag h3{font:740 24px/1.1 var(--sans);font-stretch:80%;margin-bottom:6px;color:var(--cobalto)}
.rag p{font:400 18.5px/1.36 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.rag p b{color:var(--tinta)}
/* de trámite */
div.tram{position:absolute;left:72px;right:72px;top:246px;display:grid;grid-template-columns:330px 520px 1fr;column-gap:36px}
.trh{font:400 16px/1 var(--mono);color:var(--tinta-3);padding-bottom:10px;border-bottom:1.6px solid var(--tinta)}
.tr1,.tr2,.tr3{padding:12px 0;border-bottom:1px solid var(--hilo);display:flex;align-items:center;min-height:122px}
.tr1 .xrf p{font:740 28px/1.08 var(--sans);font-stretch:80%;color:var(--tinta)}
.tr1 .xrf.sin p{font-size:25px}
.tr3 p{font:400 21px/1.34 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.mb{display:flex;flex-direction:column;gap:6px;width:100%}
.mbr{display:grid;grid-template-columns:170px 1fr auto;align-items:center;column-gap:10px}
.mbr span{font:400 16px/1 var(--mono);color:var(--tinta-2);white-space:nowrap}
.mbr i{display:block;height:12px;background:var(--papel-2)}.mbr i em{display:block;height:100%;background:var(--grafito)}
.mbr b{font:700 17px/1 var(--mono);color:var(--tinta-2);white-space:nowrap}
.mbr.hi span{color:var(--tinta);font-weight:700}.mbr.hi i em{background:var(--cobalto)}.mbr.hi b{color:var(--cobalto)}
.tgr b{display:block;font:740 46px/1 var(--sans);font-stretch:78%;color:var(--cobalto);margin-bottom:6px}
.tgr span{font:400 17px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.lam-tram .remate{font-size:36px}
/* ejercicio 4 */
.v1{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:820px 1fr;column-gap:64px}
.v1l{display:flex;flex-direction:column;gap:24px}
.v1 .bloque p{font-size:24px}
.v1 code{font:400 .86em var(--mono);background:var(--papel-2);padding:1px 6px}
.trio{display:grid;grid-template-columns:repeat(3,1fr);column-gap:22px}
.trio div{border-top:1.6px solid var(--tinta);padding-top:10px}
.trio b{display:block;font:740 46px/1 var(--sans);font-stretch:78%;color:var(--cobalto);margin-bottom:8px;white-space:nowrap}
.trio span{font:400 19px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.v1r .vend{font-size:21px;margin:8px 0 12px;color:var(--tinta-2);border-left:3px solid var(--hilo-2);padding-left:14px}
.v1r .e2{font-size:16px;margin:10px 0 8px}
.tira.f5{gap:12px}
.v1r .nota{font-size:16px;margin-top:8px}
.v2{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:760px 1fr;column-gap:72px}
.v2 .etq{margin-bottom:10px}
.yml pre{font:400 19px/1.6 var(--mono);color:var(--tinta-2)}
.yml .del{color:var(--cota);background:rgba(226,70,47,.08);display:inline-block;width:100%}
.yml .add{color:var(--cobalto-2);background:var(--cobalto-suave);font-weight:700;display:inline-block;width:100%}
.yml i{font-style:normal;color:var(--tinta-3)}
.v2p{margin-top:24px}
.v2p .apri{display:grid;grid-template-columns:40px 1fr;column-gap:10px;padding:11px 0;border-bottom:1px solid var(--hilo)}
.v2p .apri span{font:700 22px/1.3 var(--mono);color:var(--cobalto)}
.v2p .apri p{font:400 23px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.v2p .apri p strong{color:var(--tinta)}
.v2c{margin-top:12px}
.v2f{display:flex;gap:18px;align-items:center}
.v2f .nota{margin:0;font-size:17px;max-width:260px}
.v2f .ficha{--fs:92px!important}
.dosv{position:absolute;left:72px;right:72px;top:246px;display:grid;grid-template-columns:560px 250px 330px 1fr;align-items:stretch}
.dh{font:400 16px/1 var(--mono);color:var(--tinta-3);padding:0 16px 10px;border-bottom:1.6px solid var(--tinta)}
.dh.c{text-align:center}.dh.v{color:var(--cobalto);font-weight:700}
.dl,.d1,.d2,.dd{display:flex;align-items:center;min-height:44px;padding:0 16px;border-bottom:1px solid var(--hilo)}
.dl{font:500 23px/1.15 var(--sans);font-stretch:88%;padding-left:0}
.d1,.d2{justify-content:center;font:700 23px/1 var(--mono)}
.d1{color:var(--tinta-2)}
.d2{color:var(--cobalto);background:var(--cobalto-suave)}
.dd{font:400 18px/1.2 var(--mono);color:var(--tinta-2)}
.ds{grid-column:1/-1;font:400 16px/1 var(--mono);color:var(--cobalto);padding:15px 0 8px;border-bottom:1px solid var(--hilo-2)}
.dosv code{font:400 17px var(--mono)}
.dosn{position:absolute;left:72px;right:72px;top:722px;display:grid;grid-template-columns:1fr 1fr;column-gap:36px}
.dosn div{font:400 21px/1.34 var(--sans);font-stretch:92%;color:var(--tinta-2);padding:10px 18px;border-left:4px solid var(--verde);background:#fff}
.dosn .no{border-left-color:var(--cota)}
.dosn b{color:var(--tinta)}
/* cierre */
.apr.lims .apri p{font-size:23px}
.apr.lims .apri{padding:13px 0}
.fut{position:absolute;left:72px;right:72px;top:250px;display:grid;grid-template-columns:800px 1fr;column-gap:64px}
.fut .act{font:400 19px/1 var(--mono);color:var(--cobalto);padding-bottom:12px;border-bottom:1.6px solid var(--cobalto);margin-bottom:4px}
.fut .act.r{color:var(--tinta-2);border-bottom-color:var(--tinta)}
.futl .apri{display:grid;grid-template-columns:40px 1fr;column-gap:10px;padding:11px 0;border-bottom:1px solid var(--hilo)}
.futl .apri span{font:700 21px/1.3 var(--mono);color:var(--cobalto)}
.futl .apri p{font:400 22px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.futl .apri p strong{color:var(--tinta)}
.futf{display:grid;grid-template-columns:1fr 1fr;column-gap:16px;margin-top:2px}
.futf figure{margin:0}
.futf img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.futf figcaption{font:400 14px/1.25 var(--mono);color:var(--tinta-3);margin-top:5px}
.futr .nota{font-size:16px;margin-top:10px}
.concl{position:absolute;left:72px;right:72px;top:232px;display:grid;grid-template-columns:1080px 1fr;column-gap:60px}
.cl .apri{display:grid;grid-template-columns:48px 1fr;column-gap:10px;padding:13px 0;border-bottom:1px solid var(--hilo)}
.cl .apri span{font:700 24px/1.3 var(--mono);color:var(--cobalto)}
.cl .apri p{font:400 25px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.cl .apri p strong{color:var(--tinta)}
.cr .etq{font-size:16px;margin-bottom:10px}
.cth{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cth img{width:100%;aspect-ratio:3/2;object-fit:cover;display:block}
.cr .credito{margin-top:10px}
"""
