CSS = r"""
/* ===== parte D: Ejercicio 4, costo, limitaciones, futuro y conclusiones, con menos texto ===== */
/* D39 · versión 1 */
.d39-izq{top:286px;width:760px}
.d39-izq>.et{margin-bottom:6px}
.d39-izq .et code{font-size:1em;background:none;padding:0;color:var(--crema)}
.d39-n{border-top:1px dotted var(--trazo-3);padding:34px 0 44px}
.d39-n b{display:block;font:800 132px/.88 var(--display);font-stretch:76%;color:var(--coral);white-space:nowrap}
.d39-n span{display:block;font:500 30px/1.25 var(--sans);color:var(--trazo);margin-top:12px}
.d39-der{top:286px}
.d39-q{display:flex;gap:28px;align-items:center;margin-bottom:40px}
.d39-q .ej-q{margin:0;font-size:28px;flex:1}
.d39-q .ej-q span{font-size:19px;margin-top:10px}
.d39-der>.caso5{gap:18px}
.d39-der>.caso5 .prod{width:152px!important;height:152px!important}
.d39-der>.caso5 .cz span{font-size:17px;margin-top:8px}
.d39-der .ej-c{font-size:28px;margin-top:22px}
/* D40 · versión 2 */
.d40-izq{top:270px;width:800px}
.d40-izq .ej-yaml{margin-bottom:44px}
.d40-izq .ej-yaml .pr-tx{font-size:22px}
.d40-izq>.et{margin-bottom:4px}
.d40-por{display:grid;counter-reset:p}
.d40-por li{counter-increment:p;display:grid;grid-template-columns:48px 1fr;font:700 34px/1.25 var(--display);font-stretch:86%;color:var(--crema);padding:16px 0;border-bottom:1px dotted var(--trazo-3)}
.d40-por li::before{content:counter(p);color:var(--coral);font-weight:800}
.d40-der{top:270px}
.d40-der .ej-c{font-size:26px}
.d40-der .ej-caso2{display:block;margin-top:30px}
.d40-der .ej-caso2 .ej-c{margin:14px 0 0}
.d40-der .ej-caso2 .cz .prod{width:112px!important;height:112px!important}
/* D41 · resultados */
.d41-tk{margin-top:36px;padding:16px 36px 10px}
.d41-tk .v-l{grid-template-columns:1fr 300px 300px 420px;min-height:54px;font-size:27px}
.d41-tk .v-l.v-cab{min-height:44px}
.d41-tk .v-n{color:var(--tinta)}
.d41-tk .v-a,.d41-tk .v-b{font-size:28px}
.d41-tk .v-cab .v-a,.d41-tk .v-cab .v-b,.d41-tk .v-cab .v-d{font-size:18px}
.d41-tk .v-d{font-size:21px}
.d41-tk .v-sec{font-size:18px;padding:16px 0 6px}
/* D42 · costo */
.d42-tk{top:270px;width:820px;padding:32px 40px}
.d42-tk .tk-cab b{font-size:40px}
.d42-tk .tk-cab span{font-size:18px}
.d42-tk .tk-l{font-size:26px;padding:16px 0}
.d42-tk .tk-l b{font-size:42px}
.d42-tk .tk-tot{font-size:22px;margin-top:6px}
.d42-tk .tk-tot span:last-child{font-size:46px}
.d42-der{top:262px;left:1020px;width:804px}
.d42-der .costo-tot{margin-bottom:34px}
.d42-der .costo-tot b{font-size:128px}
.d42-der .costo-tot span{font-size:30px}
/* D43 · limitaciones: una línea por ítem */
.lim-dos.d43{margin-top:84px;gap:80px}
.d43 .et{font-size:20px;margin-bottom:16px}
.d43 .lim2 li{padding:36px 0;align-items:baseline;grid-template-columns:62px 1fr}
.d43 .lim2 li::before{font-size:20px}
.d43 .lim2 li b{font:740 36px/1.15 var(--display);font-stretch:86%;color:var(--crema)}
/* D44 · futuro */
.d44-izq{top:256px;width:820px}
.d44-izq .et{font-size:20px;margin-bottom:10px}
.d44-izq .futl li{padding:19px 0;grid-template-columns:58px 1fr;align-items:baseline}
.d44-izq .futl li::before{font-size:20px}
.d44-izq .futl li b{font:740 34px/1.15 var(--display);font-stretch:86%}
.d44-der{top:256px}
.d44-der .fut-fotos{grid-template-columns:1fr 1fr;gap:24px;margin-top:26px}
.d44-der .fut-fotos figcaption{font-size:17px}
/* D45 · conclusiones: una idea por línea */
.d45-izq{width:1040px}
.conc.d45{gap:0;margin-top:120px}
.conc.d45 li{grid-template-columns:64px 1fr;padding:34px 0 32px}
.conc.d45 em{font-size:44px}
.conc.d45 p{font-size:34px;line-height:1.22;white-space:nowrap}
.d45-der{top:300px}
"""
