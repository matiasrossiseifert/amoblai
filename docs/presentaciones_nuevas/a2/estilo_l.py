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
