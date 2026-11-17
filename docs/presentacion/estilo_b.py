CSS = r"""
/* ===== parte B: D16–D23, con menos texto ===== */
/* D16 · desafíos */
.dz-c{min-height:64px}
.dz-c b{font-size:24px}
.dz-abajo{top:450px;grid-template-columns:900px 1fr;gap:90px}
.dz-v0{gap:18px;margin-bottom:40px}
.dz-barras{--gb-h:66px}
.b-otros{display:grid;gap:52px;margin-top:14px}
.b-otros li{display:flex;align-items:baseline;gap:20px;font:740 36px/1.12 var(--display);font-stretch:86%}
.b-otros i{flex:none;font:700 22px/1 var(--mono);font-style:normal;color:var(--coral-2);width:40px;height:40px;border-radius:50%;
  box-shadow:inset 0 0 0 2.5px var(--coral);display:grid;place-items:center;transform:translateY(-4px)}
/* D17 · cómo medimos la búsqueda */
.gt-q{margin-bottom:36px}
.gt-q div{font-size:19px;grid-template-columns:120px 1fr}
.gt-cifras.b-gt{left:910px;right:96px;top:738px;bottom:auto;grid-template-columns:repeat(3,auto);justify-content:start;gap:80px;padding-top:24px}
.gt-cifras.b-gt div{font-size:23px;max-width:320px}
.gt-cifras.b-gt b{font-size:76px}
/* D18 · ambientes vacíos */
.b-vac{top:236px;height:658px;display:flex;align-items:center}
.b-vac .vac-nota{font-size:36px;line-height:1.32;margin-top:0;padding-left:26px;border-left-width:5px}
.b-vac .vac-nota b{white-space:nowrap}
.lj{width:540px}
.lj .et{display:block;margin-bottom:18px}
.lj ol{margin:0;padding:0;list-style:none;display:grid;gap:26px}
.lj li{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center;border-top:1px dotted var(--hilo);padding-top:22px}
.lj p{margin:0;font:400 23px/1.32 var(--sans);color:var(--tinta-2)}
.lj p b{color:var(--tinta)}
.lj-ab{display:flex;gap:6px;flex-wrap:wrap}
.lj-ab i{font:700 21px/1 var(--mono);font-style:normal;background:var(--ticket);box-shadow:0 0 0 1.5px var(--hilo);color:var(--tinta);width:42px;height:42px;border-radius:5px;display:grid;place-items:center}
.lj-n i{border-radius:50%;color:var(--coral-2)}
.lj-o{flex-direction:column;gap:8px}
.lj-o span{display:flex;gap:6px}
/* D19 · métricas del buscador */
.met-defs.b-defs{top:668px;bottom:auto;gap:40px;padding-top:26px}
.b-md h4{font-size:30px}
.b-md>b{display:block;font:800 50px/1 var(--display);font-stretch:78%;color:var(--coral-2);margin-top:12px;white-space:nowrap}
.b-md>small{display:block;min-height:19px;font:500 15px/1.2 var(--mono);color:var(--tinta-3);margin-top:6px}
.b-md p{font-size:25px;line-height:1.35;margin-top:14px}
/* D20 · el generador y los jueces */
.b-gen{display:grid;grid-template-columns:1fr 1fr;gap:110px;margin-top:60px}
.b-m>b{display:block;font:800 124px/.86 var(--display);font-stretch:76%;color:var(--coral)}
.b-m h4{font:760 38px/1.1 var(--display);font-stretch:84%;margin-top:14px}
.b-m p{font:400 26px/1.34 var(--sans);color:var(--trazo);margin:10px 0 22px;max-width:740px}
.b-m .et{display:block;margin-bottom:10px}
.b-m .jz-q span{font-size:21px}
.b-vara{font:800 58px/1 var(--display);font-stretch:78%;color:var(--trazo)}
.b-jueces{position:absolute;left:96px;right:96px;top:730px;display:flex;align-items:center;justify-content:space-between;gap:60px;
  border-top:2px dotted var(--trazo-3);padding-top:28px}
.b-jueces h4{font:760 34px/1.1 var(--display);font-stretch:84%}
.b-jueces p{font:400 24px/1.34 var(--sans);color:var(--trazo);margin-top:8px}
.b-jueces .ordenes i{box-shadow:0 0 0 1.5px var(--hilo)}
/* D21 · la imagen */
.b-img{margin-top:90px}
.b-img .it>p:not(.cred-l){font-size:24px;margin-top:20px}
.b-img .fines{grid-template-columns:repeat(4,1fr);gap:14px 18px}
.b-img .fin figcaption{font-size:16px}
.b-img .it>p.cred-l{font:400 13.5px/1.4 var(--mono);margin-top:12px}
/* advertencias */
.b-tr{margin-top:70px;border-top:2px solid var(--tinta)}
.b-trf{display:grid;grid-template-columns:76px 700px 1fr;gap:30px;align-items:baseline;padding:40px 0;border-bottom:2px dotted var(--hilo)}
.b-trf i{font:700 24px/1 var(--mono);font-style:normal;color:var(--coral-2);width:46px;height:46px;border-radius:50%;
  box-shadow:inset 0 0 0 2.5px var(--coral);display:grid;place-items:center;transform:translateY(-6px)}
.b-trf b{font:760 38px/1.1 var(--display);font-stretch:84%}
.b-trf p{font:400 27px/1.32 var(--sans);color:var(--tinta-2)}
/* D23 · el mapa */
.hiper-pie{bottom:auto;top:884px}
/* D16 · cuatro desafíos, cada uno con cómo lo resolvimos */
.dz4{position:absolute;left:96px;right:96px;top:380px;margin:0;padding:0;list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:110px 80px}
.dz4 li{display:grid;grid-template-columns:84px 1fr;border-top:2px solid var(--hilo);padding-top:30px}
.dz4 i{font:800 70px/.9 var(--display);font-stretch:78%;font-style:normal;color:var(--coral-2)}
.dz4 b{display:block;font:760 52px/1.08 var(--display);font-stretch:82%;color:var(--tinta)}
.dz4 p{margin:16px 0 0;font:400 32px/1.3 var(--sans);color:var(--tinta-2)}
/* el mapa de los experimentos: el 8 tiene lámina propia; los de trámite arrancan en el 9 */
.hiper.h14 li{min-height:40px}
.hiper.h14 li:nth-child(8){margin-top:0;border-top:0}
.hiper.h14 li:nth-child(9){margin-top:14px;border-top:1px dotted var(--trazo-3)}
/* experimento 8 · buscar por imagen */
.e8-v0{margin:10px 0 34px}
.e8-b{--gb-et:200px;--gb-nota:250px}
/* el punto de partida: fase · arrancamos con · lo prueba */
.pt-l{position:absolute;left:96px;right:96px;top:262px;margin:0;padding:0;list-style:none}
.pt-l li{display:grid;grid-template-columns:330px 1fr 230px;align-items:center;padding:13px 0;border-bottom:1px dotted var(--hilo)}
.pt-l li b{font:760 34px/1.1 var(--display);font-stretch:84%;color:var(--tinta)}
.pt-l li span{font:400 30px/1.25 var(--sans);color:var(--tinta-2)}
.pt-l li div{display:flex;gap:10px;justify-content:flex-end}
.pt-l .tp{width:42px;height:42px;font-size:22px}
.pt-l li.pt-cab{border-bottom:2px dashed var(--hilo);padding:0 0 10px}
.pt-l li.pt-cab b,.pt-l li.pt-cab span,.pt-l li.pt-cab div{font:500 18px/1.2 var(--mono);color:var(--tinta-3)}
.pt-pie{position:absolute;left:96px;right:96px;top:878px;display:grid;grid-template-columns:1fr 1fr;gap:60px}
.pt-pie p{margin:0;font:400 27px/1.3 var(--sans);color:var(--tinta-2);padding-left:20px;border-left:4px solid var(--coral)}
.pt-pie b{color:var(--tinta);font-weight:600}
/* sobre qué configuración corrió cada experimento */
.sobre{margin:22px 0 0;font:400 22px/1.3 var(--sans);color:var(--tinta-3)}
.sobre span{font:500 17px/1 var(--mono);color:var(--coral-2);margin-right:6px}
.tr-s{display:block;margin-top:6px;font:400 15px/1.25 var(--mono);color:var(--tinta-3);font-stretch:100%}
/* D20 sin valores: la fórmula en lugar del número */
.b-m>b.fx{font:700 58px/1.05 var(--display);font-stretch:80%;color:var(--coral);white-space:nowrap}
.b-gen .b-m h4{margin-top:22px}
.b-gen{margin-top:190px}
.b-gen .b-m p{font-size:32px}
.b-gen .b-m h4{font-size:44px}
.b-gen .b-m .et{margin-top:6px;font-size:19px}
.slide .b-jueces{top:740px}
/* D21: el control, la foto contra la imagen */
.rc-par{display:flex;gap:24px}
.rc-par figure{margin:0}
.rc-par figcaption{font:500 16px/1.2 var(--mono);color:var(--tinta-3);margin-top:8px}
/* faithfulness, en un caso: entra → juez → sale */
.fj-col{position:absolute;top:290px}
.fj-col .et{display:block;margin:0 0 10px}
.fj-in{left:96px;width:640px}
.fj-fotos{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fj-fotos .prod{border:1px solid var(--hilo);background-color:#fff}
.fj-l{font:400 19px/1.35 var(--sans);color:var(--tinta-2);margin:10px 0 26px}
.fj-l code,.fj-cl code{font:500 17px/1.3 var(--mono);color:var(--tinta)}
.fj-ped{font:400 21px/1.35 var(--sans);color:var(--tinta-2);margin:0 0 26px}
.fj-pq{margin:0;padding:0;list-style:none;display:grid;gap:10px}
.fj-pq li{font:400 19px/1.35 var(--mono);color:var(--tinta-2)}
.fj-pq mark{background:none;color:#b4232f;font-weight:700;box-shadow:inset 0 -2px 0 #b4232f}
.fj-fl{position:absolute;top:500px;font:400 56px/1 var(--sans);color:var(--tinta-3)}
.fj-f1{left:762px}.fj-f2{left:1206px}
.fj-juez{left:826px;width:360px;background:var(--ticket);border-radius:10px;padding:24px 26px;box-shadow:0 0 0 1.5px var(--hilo)}
.fj-juez ol{margin:0;padding-left:30px;display:grid;gap:16px;list-style:decimal outside}
.fj-juez li::marker{font:700 20px var(--mono);color:var(--coral-2)}
.fj-juez li{font:400 22px/1.32 var(--sans);color:var(--tinta-2)}
.fj-juez li b{color:var(--tinta)}
.fj-a{margin:22px 0 0;font:400 18px/1.2 var(--mono);color:var(--tinta-3)}
.fj-a kbd{font:700 16px/1 var(--mono);border:1.5px solid var(--tinta-3);border-radius:4px;padding:3px 7px;margin-right:6px}
.fj-out{left:1270px;width:554px}
.fj-cl{margin:0;padding:0;list-style:none}
.fj-cl li{display:grid;grid-template-columns:34px 1fr;align-items:start;padding:12px 0;border-bottom:1px dotted var(--hilo)}
.fj-cl i{font:700 24px/1.1 var(--sans);font-style:normal;color:var(--coral-2)}
.fj-cl li.no i,.fj-cl li.no code{color:#b4232f}
.fj-cl span{display:block;font:400 18px/1.3 var(--sans);color:var(--tinta-3);margin-top:3px}
.fj-cl li.resto span{font-size:19px;color:var(--tinta-2);margin-top:0}
.fj-res{margin:22px 0 0;font:500 24px/1.2 var(--mono);color:var(--tinta-2)}
.fj-res b{font:800 40px/1 var(--display);font-stretch:80%;color:var(--coral);margin-left:4px}
/* el juez de listas, en un caso */
.ljc-in{position:absolute;left:96px;top:270px;width:440px}
.ljc-in .et,.ljc-listas .et,.ljc-out .et{display:block;margin-bottom:12px}
.ljc-in p{font:400 21px/1.38 var(--sans);color:var(--tinta-2);margin:16px 0 0}
.ljc-listas{position:absolute;left:600px;top:270px;width:800px;display:grid;grid-template-columns:1fr 1fr;gap:0 36px}
.lj-l{margin:0;padding:0;list-style:none}
.lj-l li{display:grid;grid-template-columns:62px 1fr 40px;gap:12px;align-items:center;padding:7px 6px;border-bottom:1px dotted var(--hilo)}
.lj-l li.dif{background:#eef1fc}
.lj-l .prod{border:1px solid var(--hilo);background-color:#fff}
.lj-l span{font:400 17px/1.25 var(--mono);color:var(--tinta-2)}
.lj-l i{font:800 22px/1 var(--display);font-style:normal;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;box-shadow:inset 0 0 0 2px currentColor}
.lj-l i.g2{color:var(--coral-2)}.lj-l i.g1{color:var(--tinta-3)}.lj-l i.g0{color:#b4232f}
.lj-s{margin:14px 0 0;font:400 19px/1.4 var(--sans);color:var(--tinta-2)}
.lj-s b{font:800 24px/1 var(--display);color:var(--tinta)}
.lj-s span{display:block;font:500 16px/1.3 var(--mono);color:var(--tinta-3);margin-top:4px}
.ljc-ley{grid-column:1/-1;margin:22px 0 0;font:400 17px/1.4 var(--mono);color:var(--tinta-3)}
.ljc-ley b{color:var(--coral-2)}
.ljc-out{position:absolute;left:1460px;top:270px;width:364px}
.ljc-el{margin:0;font:400 30px/1 var(--sans);color:var(--tinta-2)}
.ljc-el b{font:800 76px/1 var(--display);color:var(--coral);margin-left:6px}
.ljc-why{margin:14px 0 0;font:400 18px/1.4 var(--mono);color:var(--tinta-2)}
.ljc-rev{margin-top:36px;border-top:1px dotted var(--hilo);padding-top:20px}
.ljc-rev p{margin:12px 0 0;font:400 23px/1.3 var(--sans);color:var(--tinta-2)}
.ljc-rev p b{color:var(--tinta)}
/* sin el talón: el resultado, centrado en el alto que queda */
.res-cuerpo{position:absolute;left:96px;right:96px;top:215px;bottom:120px;display:flex;flex-direction:column;justify-content:center}
.res-cuerpo>*{margin-top:0}
.unica .un-der{top:215px;bottom:120px;display:flex;flex-direction:column;justify-content:center}
.res-2.r2n{grid-template-columns:1fr 560px;align-items:center}
.r2n .graf-b{--gb-h:84px;--gb-bar:40px;--gb-et:300px}
.r2n .gb-val{font-size:44px}
.r2n .grande-n>b{font-size:170px}
.r-7.r7n{grid-template-columns:1fr 1fr;gap:110px}
.r7n>div+div{border-left:1px dotted var(--hilo);padding-left:56px;margin-left:-56px}
/* exp 6 · tokens y costo */
.e6c{display:flex;flex-direction:column;gap:46px}
.e6c>div{display:grid;grid-template-columns:1fr 470px;gap:70px;align-items:center}
.e6c-b{--gb-et:360px;--gb-h:64px;--gb-bar:34px}
.e6c-b .gb-val{white-space:nowrap;font-size:40px}
.e6c-b .gb-pista>span{white-space:nowrap}
.e6c-b .gb-et small{display:block;font:400 16px/1.25 var(--mono);color:var(--tinta-3);margin-top:4px}
.e6c-n{margin:0;font:400 25px/1.42 var(--sans);color:var(--tinta-2);padding-left:28px;border-left:3px solid var(--coral)}
.e6c-n b{color:var(--tinta)}
/* los de trámite, de a uno */
.un-nota{margin:30px 0 0;font:400 26px/1.4 var(--sans);color:var(--tinta-2)}
.un-nota b{color:var(--tinta)}
.gb-unica .gb-et small{display:block;font:400 17px/1.25 var(--mono);color:var(--tinta-3);margin-top:4px}
.unica .un-izq{bottom:120px;display:flex;flex-direction:column}
.unica .un-izq .exp-blq{margin-top:auto;margin-bottom:auto}

/* presentacion_experimentos: el coseno sin juez */
.cosg{display:grid;grid-template-columns:1fr 470px;gap:70px;align-items:center}
.cos-b{--gb-et:330px;--gb-h:54px;--gb-bar:24px}
.cos-b .gb-val{font-size:30px;white-space:nowrap}
.cos-n p{margin:0 0 26px;font:400 28px/1.35 var(--sans);color:var(--tinta-2);padding-left:24px;border-left:3px solid var(--coral)}
.cos-n p b{color:var(--tinta)}
.cos-n .cos-p{border:0;padding-left:0;font:400 18px/1.3 var(--mono);color:var(--tinta-3);margin-top:40px}
"""
