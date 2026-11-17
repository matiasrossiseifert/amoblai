CSS = r"""
/* ===== parte A · D7–D15: menos texto, lo mismo más grande ===== */
.a-pr{margin-top:30px}
.a-pr .pr-tx{font-size:20px;line-height:1.55}
.a-pr .pr-cab b{font-size:20px}
.rt-banda .a-pr{margin-top:0}
.rt-banda .a-pr.grande{width:1400px}
.a-fl{align-self:center;display:flex;flex-direction:column;align-items:center;gap:6px}
.a-fl i{font:300 64px/1 var(--sans);font-style:normal;color:var(--trazo-2)}
.a-fl b{font:760 26px/1.1 var(--display);font-stretch:84%;color:var(--crema)}
.a-eq{margin-top:58px}

/* D7 · descripción */
.rt-banda.a-rd{top:520px;align-items:center;gap:56px}
.a-ent{width:290px;display:flex;flex-direction:column;align-items:center;gap:10px}
.a-ent .et{align-self:flex-start}
.a-ent .prod{border-radius:6px}
.a-ent b{font:700 22px/1.2 var(--display);font-stretch:88%;color:var(--crema);text-align:center}
.a-sal{width:1140px}
.a-sal .ficha-tk{margin-top:0;padding:20px 26px;border:1px solid var(--hilo)}
.a-sal .ficha{gap:9px}
.a-sal .ficha div{grid-template-columns:150px 1fr;font-size:19px;gap:14px}

/* D8 · índice */
.rt-banda.a-ri{top:575px}
.a-ri .ri-svg .caja-t{stroke:var(--hilo);stroke-width:1.5}

/* D9 · plan */
.a-ped{margin-top:34px;max-width:1100px;font:italic 400 32px/1.3 var(--sans);color:var(--crema);border-left:4px solid var(--coral);padding:4px 0 4px 22px}
.a-plan .rp-pz{font-size:18px;padding:7px 0}
.a-q .ficha-tk{border:1px solid var(--hilo)}
.a-tags{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}
.a-tags span{font:500 17px/1 var(--mono);color:var(--coral);border:1.5px solid var(--coral);border-radius:5px;padding:8px 12px}

/* D10 · prompt del plan */
.a-vers{display:grid;grid-template-columns:repeat(4,1fr);gap:0 28px;margin-top:52px}
.a-vers li{display:flex;flex-direction:column;align-items:flex-start;gap:14px;padding:0;border:0}
.a-vers em{width:92px;font-size:22px;padding:8px 0 7px}
.a-vers b{font-size:26px;line-height:1.15}
.rt-banda.a-rpp{top:530px}

/* D11 · búsqueda */
.rt-banda.a-rb{top:530px;align-items:flex-start;gap:40px}
.a-tres{width:470px;display:flex;flex-direction:column;gap:14px}
.a-tres>div{border-left:4px solid var(--coral);padding:4px 0 4px 16px}
.a-tres>div b{display:block;font:760 30px/1.05 var(--display);font-stretch:84%;color:var(--crema)}
.a-tres>div span{display:block;font:400 19px/1.3 var(--sans);color:var(--trazo);margin-top:3px}
.a-tres p{font:500 18px/1.3 var(--mono);color:var(--coral);margin-top:6px;padding-top:12px;border-top:1px dotted var(--trazo-3)}
.a-rb .a-fl{align-self:flex-start;margin-top:120px}
.a-cands .rb-cands{gap:16px}
.a-c{width:170px;gap:8px}
.a-c em{font-size:34px}
.a-c b{font-size:17px}

/* D12 · elección */
.rt-banda.a-re{top:500px;gap:72px}
.a-filas{width:800px}
.a-fila{padding:10px 0}
.a-dos{align-self:center;display:flex;gap:64px}
.a-dos .rc-n b{font-size:112px}

/* D13 · escena */
.a-cmp{margin-top:40px;display:grid;gap:0;width:900px}
.a-cf{display:grid;grid-template-columns:360px 220px 1fr;align-items:baseline;padding:10px 0;border-top:1px dotted var(--trazo-3)}
.a-cf.cab{border-top:0;padding-bottom:6px}
.a-cf span{font:400 24px/1.2 var(--sans);color:var(--trazo)}
.a-cf b{font:800 52px/1 var(--display);font-stretch:78%;color:var(--trazo-2)}
.a-cf b.si{color:var(--coral)}
.a-cf.cab b{font:700 24px/1.1 var(--display);font-stretch:88%;color:var(--trazo-2)}
.a-cf.cab b.si{color:var(--coral)}
.a-cf small{font:400 18px/1 var(--mono);color:var(--trazo-2);margin-left:6px}
.rt-banda.a-rs{top:515px}
.a-op{margin-top:46px;display:grid;grid-template-columns:1fr 1fr;gap:40px;width:1100px}
.a-op>div{border-top:2px solid var(--trazo-3);padding-top:16px}
.a-op>div.si{border-top-color:var(--coral)}
.a-op b{display:block;font:780 42px/1.05 var(--display);font-stretch:80%;color:var(--trazo-2)}
.a-op .si b{color:var(--coral)}
.a-op p{margin:10px 0 0;font:400 25px/1.3 var(--sans);color:var(--trazo)}
.rt-banda .pr-tk.a-esc{width:100%}
.a-esc .pr-tx{font-size:18px;line-height:1.5}
.pr-cab .ph{font-style:normal;color:var(--coral-2);font-weight:600}

/* D14 · imagen y control */
.a-der{gap:16px}
.a-der .rc-n{margin-top:18px}
.a-der .rc-n b{font-size:96px}

/* D15 · lista */
.a-tk{padding:22px 28px 20px}
.a-l{grid-template-columns:44px 230px 190px 1fr 60px;font-size:17px;padding:5px 0}
.a-l b{font-size:21px}
.a-l .tr{font-size:17px}
.a-l.cab{font:500 14px/1 var(--mono);color:var(--tinta-3);border-top:0;padding:2px 0 6px}
/* D15 · sin el número de arriba: la foto amoblada grande a la izquierda y la lista a la derecha, debajo del mapa */
.rt-banda.a-rl{top:250px;flex-direction:row-reverse;justify-content:flex-end}
.a-rl .rl-fin{width:960px}
.a-rl .rl-tk{width:724px;margin-top:250px}
.a-rl .a-l{grid-template-columns:40px 170px 150px 1fr 44px}
"""
