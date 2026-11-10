"""Arma presentacion.html y guion.md a partir de los archivos de resultados del repo.

    cd /home/fer/tp-llm && uv run python docs/presentaciones_nuevas/a_desde_cero/build.py

Ningún número de la presentación está escrito a mano: todos salen de datos_deck.load().
Navegación: flechas / espacio / PgUp-PgDn, Home/End, F pantalla completa, O índice, N notas,
B pantalla negra. `?all` muestra cada lámina con todos sus pasos; `#/12` o `#/12.2` van a una
lámina (y a un paso).
"""

from __future__ import annotations

import base64
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import base  # noqa: E402
import componentes  # noqa: E402
import datos_deck  # noqa: E402
import laminas_a  # noqa: E402
import laminas_b  # noqa: E402
from estilo import CSS, JS  # noqa: E402

FONTS = [("Noto Serif Display", "serif-r", 400, "normal"), ("Noto Serif Display", "serif-i", 400, "italic"),
         ("Noto Serif Display", "serif-b", 700, "normal"), ("PT Serif", "texto-i", 400, "italic"),
         ("Cabin", "sans-r", 400, "normal"),
         ("Cabin", "sans-i", 400, "italic"), ("Cabin", "sans-m", 500, "normal"),
         ("Cabin", "sans-sb", 600, "normal"), ("Cabin", "sans-b", 700, "normal"),
         ("Ubuntu Sans Mono", "mono", "100 700", "normal")]

EXTRA_CSS = r"""
:root{--cita:'PT Serif',Georgia,serif}
body.static #hint{display:none}
.quote,.pwhy p,.rq p,.why{font-family:var(--cita)!important;font-style:italic}
.hd.x{display:block;margin-bottom:26px}
.hrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.hd.x .eb{margin-bottom:0}
.hd.x h2.t{max-width:1600px}
.nstep{color:var(--ocre);font-family:var(--mono);font-size:.85em}

/* problema */
.pcards{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;margin-top:40px}
.pc{padding:44px 40px 48px;min-height:400px}
.pc .num{font:400 76px/1 var(--serif);color:var(--terracota);margin-bottom:26px}
.pc h3{font:600 30px/1.25 var(--sans);margin-bottom:16px}
.pc p{font-size:25px}
.pfoot{margin-top:44px;font:400 28px/1.45 var(--sans);color:var(--nogal-2);max-width:1500px;border-left:4px solid var(--terracota);padding-left:28px}
.pfoot b{color:var(--nogal)}

/* producto */
.prod{flex:1;display:grid;grid-template-columns:1000px 1fr;column-gap:56px;min-height:0}
.pq{font-size:25px;line-height:1.45;margin-bottom:34px}
.pphotos{display:flex;align-items:center;gap:0}
.parr{font:400 40px/1 var(--serif);color:var(--terracota);width:60px;text-align:center}
.fgrid{display:grid;gap:22px 20px}
.fgrid.g4{grid-template-columns:repeat(4,126px)}
.fgrid.g5{grid-template-columns:repeat(5,98px);gap:14px}
.pwhy{margin-top:26px;border-top:1px solid var(--hilo);padding-top:16px}
.pwhy p{font:italic 400 21px/1.42 var(--serif);color:var(--nogal-2);margin-top:8px}

/* lo que cumple */
.ptab{display:grid;grid-template-columns:560px 1fr 440px;column-gap:40px;border-top:1px solid var(--hilo)}
.ptab>div{border-bottom:1px solid var(--hilo);padding:27px 0;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.ptab .ph1{font:500 17px/1 var(--mono);color:var(--nogal-3);padding:14px 0}
.ptab .pr1{font:400 31px/1.2 var(--serif);color:var(--nogal)}
.ptab .pr2{font:400 23px/1.4 var(--sans);color:var(--nogal-2)}

/* arquitectura */
.archwrap{flex:1;display:flex;align-items:center;margin-top:-6px}

/* documento y consulta */
.dq{display:grid;grid-template-columns:1fr 1fr;gap:48px}
.dqc{background:var(--papel);border:1px solid var(--hilo);border-radius:6px;padding:20px 26px}
.dqh{display:flex;gap:20px;align-items:center;margin-bottom:12px}
.dqh img{width:96px;height:96px;object-fit:contain;background:#fff;border:1px solid var(--hilo)}
.dqh img.rm{width:128px;height:96px;object-fit:cover}
.dqh .lbl{margin-bottom:6px}
.dqh p{font:400 19px/1.35 var(--sans);color:var(--nogal-2)}
.l8{display:grid;grid-template-columns:118px 1fr;column-gap:14px;padding:5px 0;border-top:1px dashed var(--hilo)}
.l8 .k{font:600 17px/1.4 var(--mono);color:var(--terracota)}
.l8 .v{font:400 19px/1.36 var(--sans);color:var(--nogal)}
.dqs{display:grid;grid-template-columns:420px 1fr;gap:30px;align-items:center;margin-top:20px}
.dqs p{font:400 22px/1.4 var(--sans);color:var(--nogal-2)}
.strip{display:flex;gap:14px;align-items:flex-start}
.cos{font:600 17px/1 var(--mono);color:var(--nogal-2);text-align:center;margin-top:2px}
.ficha.hi .cos{color:var(--terracota)}

/* variantes */
.vt{grid-template-columns:300px 1fr 200px}
.vt>div{min-height:56px;padding:8px 0}
.vt .ex{justify-content:flex-end}

/* línea de tiempo */
.tl{position:relative;flex:1;margin:0 0 10px}
.tl .axis{position:absolute;left:0;right:0;top:50%;height:2px;background:var(--nogal-2)}
.tl .ev{position:absolute;top:50%;width:0;height:0}
.tl .ev .dot{position:absolute;left:-10px;top:-10px;width:20px;height:20px;border-radius:50%;background:var(--lino);border:3px solid var(--nogal);display:block}
.tl .ev .stem{position:absolute;left:-1px;width:2px;height:40px;background:var(--hilo-2);display:block}
.tl .ev.up .stem{bottom:10px}
.tl .ev.dn .stem{top:10px}
.tl .ev .bx{position:absolute;left:-2px;width:330px;padding:0 0 0 18px;border-left:3px solid var(--terracota)}
.tl .ev.up .bx{bottom:50px}
.tl .ev.dn .bx{top:50px}
.tl .ev.v0 .dot{border-color:var(--grafito)}
.tl .ev.v0 .bx{border-left-color:var(--grafito)}
.tl .ev.next .dot{border-style:dashed;border-color:var(--terracota)}
.tl .ev.next .bx{border-left-style:dashed}
.tl .ev .dt{font:600 19px/1 var(--mono);color:var(--terracota);margin-bottom:10px}
.tl .ev.v0 .dt{color:var(--grafito)}
.tl .ev h4{font:600 25px/1.2 var(--sans);color:var(--nogal);margin-bottom:8px}
.tl .ev p{font:400 20px/1.38 var(--sans);color:var(--nogal-2)}

/* ground truth */
.gt{display:grid;grid-template-columns:776px 1fr;column-gap:56px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:40px;margin-top:34px;border-top:1px solid var(--hilo);padding-top:24px}
.stats .big{font-size:64px}

/* métricas */
.mq{display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:baseline;margin-bottom:26px}
.mq .lbl{margin:0;white-space:nowrap}
.mq p{font:400 21px/1.4 var(--sans);color:var(--nogal-2)}
.mq p b{font-family:var(--mono);font-weight:600;font-size:18px;color:var(--terracota)}
.strip.s10{gap:16px}
.mlegend{font:400 19px/1 var(--sans);color:var(--nogal-2);margin:20px 0 40px}
.mlegend i.hi{display:inline-block;width:16px;height:16px;border:3px solid var(--terracota);margin-right:10px;vertical-align:-3px}
.mcards{display:grid;grid-template-columns:repeat(5,1fr);gap:20px}
.mcard{background:var(--papel);border:1px solid var(--hilo);border-radius:6px;padding:24px 24px;display:flex;flex-direction:column;min-height:380px}
.mn{font:600 20px/1.2 var(--mono);color:var(--terracota);margin-bottom:10px}
.mcard p{font:400 22px/1.42 var(--sans);color:var(--nogal-2);flex:1}
.mf{font:500 18px/1.35 var(--mono);color:var(--nogal);margin-top:12px;padding-top:10px;border-top:1px dashed var(--hilo)}
.mv{font:400 54px/1 var(--serif);color:var(--nogal);margin-top:12px}

/* bootstrap */
.boot{flex:1;display:grid;grid-template-columns:620px 1fr;column-gap:72px}
.bootc{padding-top:6px}

/* E5 */
.bign{display:flex;flex-direction:column;gap:44px}
.bign .of{font-size:44px;color:var(--nogal-3)}
.bign .kl{font-size:23px}

/* E7b */
.e7b{flex:1;display:grid;grid-template-columns:920px 1fr;column-gap:64px}
.e7r .note{margin-top:28px;font-size:20px}

/* E11 */
.rg{display:grid;grid-template-columns:250px 1fr 1fr;column-gap:30px;row-gap:22px;align-items:center}
.rg-h{font:500 17px/1.2 var(--mono);color:var(--nogal-3)}
.rg-h span{color:var(--nogal-3)}
.rg-l{font:400 21px/1.25 var(--sans);color:var(--nogal)}
.rg-b{display:grid;grid-template-columns:1fr 64px;column-gap:12px;align-items:center}
.rbar{position:relative;height:24px;background:var(--lino-2)}
.rbar i{position:absolute;left:0;top:0;bottom:0;background:var(--terracota);display:block}
.rbar i.vara{left:0;width:3px!important;background:var(--nogal);top:-6px;bottom:-6px;z-index:2}
.rv{font:600 20px/1 var(--mono);color:var(--nogal)}
.rn{grid-column:1 / span 2;font:400 15px/1 var(--mono);color:var(--nogal-3);margin-top:8px}
.rq{margin-top:30px;border-top:1px solid var(--hilo);padding-top:16px}
.rq p{font:italic 400 21px/1.4 var(--serif);color:var(--nogal-2)}

/* E12 */
.e12a{flex:1;display:grid;grid-template-columns:1fr 1fr;column-gap:64px}
.cmp{display:grid;grid-template-columns:300px 170px 170px;row-gap:0;margin-top:14px}
.cmp>div{padding:14px 0;border-bottom:1px solid var(--hilo);font:400 23px/1.2 var(--sans);color:var(--nogal-2)}
.cmp .ch{font:600 18px/1.2 var(--mono);color:var(--nogal)}
.cmp .cv{font:600 25px/1.2 var(--mono);color:var(--nogal)}
.judge{background:var(--papel);border:1px solid var(--hilo);border-radius:6px;padding:20px 24px;margin:-10px 0 20px}
.jrow{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.jo{font:500 17px/1 var(--mono);color:var(--nogal-3);width:80px}
.jb{font:600 18px/1 var(--mono);padding:9px 12px;border-radius:4px;background:var(--grafito-suave);color:var(--nogal)}
.jb.t{background:var(--terracota-suave);color:var(--terracota)}
.jv{font:500 18px/1 var(--mono);color:var(--nogal-2)}
.judge p{font:400 21px/1.4 var(--sans);color:var(--nogal-2);margin-top:6px}
.defs{display:grid;grid-template-columns:230px 1fr;row-gap:8px;column-gap:16px}
.defs dt{font:600 17px/1.4 var(--mono);color:var(--terracota)}
.defs dd{font:400 21px/1.4 var(--sans);color:var(--nogal-2)}
.e12b{flex:1;display:flex;flex-direction:column;gap:16px}
.e12g{display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:24px}
.e12g .card{padding:18px 22px}
.e12g .card h3{font-size:21px;margin-bottom:8px}
.e12g .card p{font-size:20px}
.e12g .card .sc{font:400 34px/1.2 var(--serif);color:var(--nogal);margin-bottom:6px}
.e12g .card.hi{border-color:var(--terracota);box-shadow:inset 0 0 0 1px var(--terracota)}
.e12g .card.hi .sc{color:var(--terracota)}
.credit{font:400 14px/1.35 var(--mono);color:var(--nogal-3);margin-top:-6px}
.jr .v i.vi,.legend i.vi{background:var(--grafito)}
.jr .v i.vt2,.legend i.vt2{background:var(--terracota)}
.loft{flex:1;display:grid;grid-template-columns:490px 1fr;column-gap:56px}
.lq{font-size:21px;margin-top:20px}
.lst{gap:12px;margin-top:6px}
.lst .ficha .fcap b{font-size:15px}
.lst .ficha .fcap span{font-size:13px}
.glegend{display:flex;gap:22px;margin-top:14px;font:400 17px/1 var(--sans);color:var(--nogal-2)}
.glegend i{display:inline-block;width:22px;height:8px;margin-right:8px;vertical-align:2px;border-radius:2px}
.glegend i.g2{background:var(--salvia)} .glegend i.g1{background:var(--ocre)} .glegend i.g0{background:var(--terracota)}
.why{font:italic 400 20px/1.42 var(--serif);color:var(--nogal-2);margin-top:16px}

/* E13 */
.imet{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto auto;gap:22px}
.imr{display:grid;grid-template-columns:1fr 340px;column-gap:24px;align-items:start}
.imr figure{margin:0}
.imr img{width:340px;height:255px;object-fit:cover;display:block}
.imr figcaption{font:400 15px/1.3 var(--mono);color:var(--nogal-3);margin-top:6px}
.sift2{display:grid;grid-template-columns:540px 1fr;column-gap:20px;margin-top:14px;align-items:end}
.siftimg{width:540px;height:auto;display:block}
.im .sift2 .cap{display:block;font-size:15px;line-height:1.35}
.im .sift2 .th{margin-top:10px;font-size:16px;line-height:1.35}
.im{padding:22px 28px}
.im p{font-size:20px}
.im .note{font-size:18px;margin-top:12px}
.im .th{font:500 17px/1.4 var(--mono);color:var(--terracota);margin-top:10px}
.pairs{display:flex;gap:22px;margin-top:12px}
.pair{display:grid;grid-template-columns:96px 96px;gap:6px}
.pair img{width:96px;height:96px;object-fit:contain;background:#fff;border:1px solid var(--hilo)}
.pair span{grid-column:1 / span 2;font:500 15px/1.2 var(--mono);color:var(--nogal-2)}
.vgrid{display:grid;grid-template-columns:repeat(3,316px);column-gap:22px;row-gap:16px;justify-content:end}
.vrow-l{grid-column:1 / span 3;font:500 17px/1 var(--mono);color:var(--nogal-3);border-bottom:1px solid var(--hilo);padding:6px 0}
.vt3{margin:0}
.vimg{position:relative;aspect-ratio:4/3;background:#fff;padding:5px;box-shadow:0 14px 26px -18px rgba(43,33,27,.6)}
.vimg img{width:100%;height:100%;object-fit:cover}
.vimg .badge,.aimg .badge{position:absolute;left:12px;top:12px;font:600 15px/1 var(--mono);padding:6px 9px;border-radius:3px;color:#fff;background:var(--terracota)}
.aimg .badge.ok{background:var(--salvia)}
.vt3 figcaption{margin-top:6px;display:flex;flex-direction:column;gap:2px}
.vt3 figcaption b{font:600 17px/1.2 var(--sans);color:var(--nogal)}
.vt3 figcaption span{font:400 15px/1.25 var(--mono);color:var(--nogal-2)}
.atts{display:grid;grid-template-columns:repeat(4,1fr);gap:26px;margin-top:6px}
.at{margin:0}
.aimg{position:relative;aspect-ratio:4/3;background:#fff;padding:7px;box-shadow:0 18px 30px -20px rgba(43,33,27,.6)}
.aimg img{width:100%;height:100%;object-fit:cover}
.at figcaption{margin-top:12px;display:flex;flex-direction:column;gap:4px}
.at figcaption b{font:600 22px/1.2 var(--sans);color:var(--nogal)}
.at figcaption span{font:400 18px/1.3 var(--mono);color:var(--nogal-2)}

/* T4 */
.t4tag{display:flex;align-items:center;gap:22px;margin:-6px 0 22px}
.t4{display:grid;grid-template-columns:80px 1.1fr 1.5fr 280px 280px;border-top:1px solid var(--hilo)}
.t4>div{border-bottom:1px solid var(--hilo);padding:14px 16px 14px 0}
.t4h{font:500 17px/1 var(--mono);color:var(--nogal-3)}
.t4c{font:400 21px/1.38 var(--sans);color:var(--nogal-2)}
.t4c.b{font:600 22px/1.2 var(--mono);color:var(--terracota)}
.t4c.m{font:400 19px/1.38 var(--mono);color:var(--nogal)}
.t4tot{margin-top:22px;font:400 23px/1.45 var(--sans);color:var(--nogal-2)}
.t4tot b{color:var(--nogal)}

/* cierre */
.path{flex:1;display:flex;flex-direction:column;justify-content:center}
.cost{flex:1;display:grid;grid-template-columns:640px 1fr;column-gap:80px}
.cbar{display:flex;gap:4px;margin-top:20px;height:86px}
.cb{background:var(--terracota);color:#fff;padding:12px 14px;display:flex;flex-direction:column;justify-content:space-between;min-width:110px}
.cb:nth-child(2){background:#8F3F20}
.cb:nth-child(3){background:var(--nogal-2)}
.cb b{font:600 19px/1 var(--sans)}
.cb span{font:600 19px/1 var(--mono)}
.learn{flex:1;display:grid;grid-template-columns:1fr 1fr;column-gap:72px}
.li{display:grid;grid-template-columns:60px 1fr;padding:26px 0;border-top:1px solid var(--hilo)}
.ln{font:400 40px/1 var(--serif);color:var(--terracota)}
.li p{font:400 27px/1.45 var(--sans);color:var(--nogal-2)}
.li p strong{color:var(--nogal)}
.lim .ln{color:var(--nogal-3)}
.lim .lbl{color:var(--nogal-2)}
h1.gr{font-size:160px}

/* apéndice */
.rai{display:grid;grid-template-columns:320px 1fr 1.4fr;column-gap:36px;border-top:1px solid var(--hilo)}
.rai>div{border-bottom:1px solid var(--hilo);padding:14px 0}
.rh{font:500 17px/1 var(--mono);color:var(--nogal-3)}
.r1{font:600 23px/1.3 var(--sans);color:var(--nogal)}
.r2,.r3{font:400 20px/1.4 var(--sans);color:var(--nogal-2)}
.abl{display:grid;grid-template-columns:1fr 1fr;column-gap:48px}
.abt{display:grid;grid-template-columns:1fr 78px 78px 86px 90px 70px;column-gap:8px}
.abt>div{padding:5px 0;border-bottom:1px solid var(--hilo)}
.abh{font:500 15px/1.2 var(--mono);color:var(--nogal-3)}
.ab1{font:400 16px/1.25 var(--mono);color:var(--nogal)}
.ab2{font:500 16px/1.25 var(--mono);color:var(--nogal-2);text-align:right}

/* E14 réplica y pasos a futuro */
.rgrid{display:grid;grid-template-columns:repeat(3,1fr);column-gap:20px;row-gap:14px}
.rgrid.g2{grid-template-columns:repeat(2,1fr);column-gap:18px;row-gap:12px}
.rt{margin:0}
.rimg{position:relative;aspect-ratio:1300/816;background:#fff;padding:5px;box-shadow:0 14px 26px -18px rgba(43,33,27,.6)}
.rimg img{width:100%;height:100%;object-fit:cover;display:block}
.rbadge{position:absolute;left:12px;top:12px;font:600 15px/1 var(--mono);padding:6px 9px;border-radius:3px;color:#fff;background:var(--terracota)}
.rbadge.ok{background:var(--salvia)}
.rt figcaption{margin-top:6px;display:flex;flex-direction:column;gap:2px}
.rt figcaption b{font:600 17px/1.2 var(--sans);color:var(--nogal)}
.rt figcaption span{font:400 15px/1.25 var(--mono);color:var(--nogal-2)}
.rk{display:grid;grid-template-columns:auto 1fr;column-gap:14px;row-gap:10px;align-content:center;padding:0 6px}
.rkn{font:400 40px/1 var(--serif);color:var(--nogal)}
.rkn.t{color:var(--terracota)}
.rkl{font:400 17px/1.25 var(--sans);color:var(--nogal-2);align-self:center}
.fx{flex:1;display:grid;grid-template-columns:1fr 780px;column-gap:56px;min-height:0}
.fxl{display:flex;flex-direction:column}
.fxl .blk{margin-bottom:22px}
.fxr{display:flex;flex-direction:column;gap:18px}
.fxk{display:grid;grid-template-columns:repeat(3,1fr);column-gap:24px;border-top:1px solid var(--hilo);padding-top:14px}
.fxk>div{display:flex;flex-direction:column;gap:4px}
.fxn{font:400 34px/1.05 var(--serif);color:var(--nogal-2)}
.fxn b{font-weight:400;color:var(--terracota)}
.fxl2{font:400 16px/1.25 var(--sans);color:var(--nogal-2)}
.ppl{display:flex;flex-direction:column;gap:7px;margin-top:6px}
.pp{display:grid;grid-template-columns:130px 1fr 52px 1fr 52px;column-gap:10px;align-items:center}
.pn{font:500 18px/1.2 var(--sans);color:var(--nogal)}
.pb{height:14px;background:var(--hilo);position:relative}
.pb i{position:absolute;left:0;top:0;bottom:0}
.pb i.a{background:var(--grafito-suave,#9AA0A6)}
.pb i.b{background:var(--terracota)}
.pv{font:500 16px/1 var(--mono);color:var(--nogal-2)}
.pv.t{color:var(--terracota)}
.fcs{display:grid;grid-template-columns:1fr 1fr 1.35fr 1fr;column-gap:22px;margin-top:6px}
.fc{border-top:3px solid var(--terracota);background:rgba(255,255,255,.45);padding:20px 22px 22px;display:flex;flex-direction:column;gap:10px}
.fcn{font:400 46px/1 var(--serif);color:var(--terracota)}
.fct{font:600 25px/1.2 var(--sans);color:var(--nogal)}
.fc p{font:400 21px/1.42 var(--sans);color:var(--nogal-2)}
.fc strong{color:var(--nogal)}
.fo{font:400 20px/1.4 var(--sans);color:var(--nogal-2);border-left:2px solid var(--hilo-2);padding-left:12px}
.fo b{font:600 20px/1 var(--mono);color:var(--terracota);margin-right:4px}
.fo strong{color:var(--nogal)}
.f3{margin-top:26px;background:var(--noche);color:var(--noche-tx);border-radius:4px;padding:22px 32px;display:grid;grid-template-columns:170px 1fr;column-gap:24px;align-items:baseline}
.f3k{font:600 18px/1.3 var(--mono);color:var(--ocre)}
.f3 p{font:400 24px/1.42 var(--sans)}
.f3 p strong{color:#fff}
.fnote{margin-top:10px;font:400 19px/1.4 var(--sans);color:var(--nogal-3)}
.fnow{margin-top:28px;display:grid;grid-template-columns:auto 1fr;column-gap:56px;align-items:start}
.fth{display:flex;align-items:center;gap:14px;margin-top:8px}
.fth img{width:300px;height:188px;object-fit:cover;background:#fff;padding:4px;box-shadow:0 12px 22px -16px rgba(43,33,27,.6)}
.fa{font:400 34px/1 var(--serif);color:var(--terracota)}
.fn2 ul{list-style:none;display:flex;flex-direction:column;gap:10px;margin-top:10px}
.fn2 li{font:400 22px/1.4 var(--sans);color:var(--nogal-2);padding-left:26px;position:relative}
.fn2 li::before{content:"";position:absolute;left:2px;top:15px;width:12px;height:1.6px;background:var(--terracota)}
"""


def font_css() -> str:
    out = []
    for fam, fn, w, st in FONTS:
        b64 = base64.b64encode((HERE / "_trabajo/cache" / f"{fn}.woff2").read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');"
                   f"font-weight:{w};font-style:{st};font-display:block}}")
    return "\n".join(out)


def notes_html(paras: list[str]) -> str:
    return "".join(f"<p>{base.md_to_html(p)}</p>" for p in paras)


def mmss(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


def main() -> None:
    t0 = time.time()
    D = datos_deck.load()
    laminas_a.build(D)
    laminas_b.build(D)
    S = base.SL
    sections = []
    for i, s in enumerate(S):
        attrs = f'class="slide {s["cls"]}" data-sec="{base.esc(s["sec"])}" data-title="{base.esc(s["title"])}"'
        if s["phases"]:
            attrs += f' data-phases="{s["phases"]}"'
        sections.append(f'<section {attrs}>{s["body"]}</section>')
    import json

    notes = [notes_html(s["notes"]) for s in S]
    html = (
        "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>amoblai · presentación final</title>"
        f"<style>{font_css()}\n{CSS}\n{EXTRA_CSS}</style></head><body>"
        "<div id=\"stage\">" + "".join(sections)
        + '<div id="hud"><span class="sec" id="hud-sec"></span><span class="rule" id="hud-rule">'
          '<i class="ln"></i><i class="fill" id="hud-fill"></i></span><span class="num" id="hud-num"></span></div>'
        + "</div>"
        '<div id="notes"></div><div id="ov"><div class="grid" id="ov-grid"></div></div><div id="black"></div>'
        '<div id="hint">→ / espacio avanzar · F pantalla completa · O índice · N notas</div>'
        f"<script>window.__NOTES={json.dumps(notes, ensure_ascii=False)};</script>"
        f"<script>{JS}</script></body></html>"
    )
    out = HERE / "presentacion.html"
    out.write_text(html)

    # ---------------------------------------------------------------- guion
    total = sum(s["t"] for s in S)
    g = ["# amoblai · guion de la presentación final", "",
         "TP 3 · 73.69 Large Language Models · ITBA 2026 · Juan Bautista Albertoni Salini, Matias Juan "
         "Rossi Seifert, Junior Rambau", "",
         f"Duración estimada: **{mmss(total)}** ({len([s for s in S if s['t']])} láminas con tiempo, "
         f"más {len([s for s in S if not s['t']])} de apéndice para las preguntas). Los números salen de "
         "los mismos archivos de resultados que la presentación (build.py los lee); si se regenera, "
         "el guion se actualiza con ellos.", "",
         "Cómo leerlo: cada bloque es una lámina, en orden, con su tiempo y el acumulado. "
         "«▸ paso» marca dónde avanzar dentro de la lámina (flecha o espacio). En cada experimento el "
         "orden es siempre el mismo: por qué, qué hicimos, resultados, decisión; los resultados no "
         "aparecen hasta el tercer paso. En la presentación, la tecla N muestra estas mismas notas.", "",
         "| # | Lámina | Tiempo | Acumulado |", "|---|---|---|---|"]
    acc = 0
    for i, s in enumerate(S):
        acc += s["t"]
        g.append(f"| {i + 1} | {s['title']} | {mmss(s['t']) if s['t'] else '—'} | {mmss(acc) if s['t'] else '—'} |")
    g.append("")
    acc = 0
    cur_sec = None
    for i, s in enumerate(S):
        if s["sec"] != cur_sec:
            cur_sec = s["sec"]
            g += [f"## {cur_sec}", ""]
        acc += s["t"]
        tt = f"{mmss(s['t'])} · acumulado {mmss(acc)}" if s["t"] else "respaldo, sin tiempo"
        g.append(f"### {i + 1} · {s['title']} ({tt})")
        g.append("")
        for p in s["notes"]:
            g.append(re.sub(r"\[(paso|clic)\]", r"▸ \1:", p))
            g.append("")
    (HERE / "guion.md").write_text("\n".join(g))

    size = out.stat().st_size
    print(f"{len(S)} láminas · {size / 1e6:.2f} MB · {componentes.STATS['n']} imágenes "
          f"({componentes.STATS['bytes'] / 1e6:.2f} MB en base64) · guion {mmss(total)} · {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
