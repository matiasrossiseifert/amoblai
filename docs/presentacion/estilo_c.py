CSS = r"""
/* parte C · experimentos: menos texto, lo que queda más grande */
.variantes span:empty{display:none}
.izq .t.chico{font-size:62px}
.izq .porque{font-size:31px;line-height:1.28;margin-top:26px;color:var(--trazo)}
.izq .exp-blq{margin-top:44px;padding-top:28px}
.izq .exp-blq .et{margin-bottom:22px}
.izq .variantes{gap:22px}
.izq .variantes li{align-items:center}
.izq .variantes b{font-size:34px}
.izq .adv{font-size:19px;margin-top:22px}
.vend{margin-top:30px}
.vend q{font-size:23px}
.unica .porque{font-size:27px;line-height:1.3}
.unica .variantes{gap:16px}
.unica .variantes li{align-items:center}
.unica .variantes b{font-size:30px}
.grande-n span{font-size:24px}
/* E1 */
.res-e1 .graf-b{--gb-et:410px}
/* E2 */
.r2n .grande-n{margin-bottom:34px}
.r2n .grande-n>b{font-size:150px}
/* E3 */
.res-e3 .grande-n p{font-size:26px}
/* E5 */
.r-5{grid-template-columns:600px 1fr;align-items:center;margin-top:40px}
.r5-num{font-size:116px;gap:20px}
.r5-num i{font-size:64px}
.r5-d{font-size:22px;margin-top:14px}
/* E6 */
.rag-q{padding:28px 32px 26px}
.rag-q .tk-cab{margin-bottom:16px}
.rag-q .tk-cab b{font-size:38px}
.rag-q .tk-l{font-size:21px;padding:10px 0}
.rag-q .tk-l.sep{margin-top:12px;padding-top:18px}
/* de trámite */
.tram-tk{margin-top:64px;padding:24px 36px 20px}
.tr-cab,.tr-l{grid-template-columns:50px 280px 640px 1fr}
.tr-cab{font-size:17px}
.tr-l{padding:24px 0 25px}
.tr-l>b{font-size:31px}
.tr-q{font-size:20px;line-height:1.45}
.tr-r{font-size:25px;line-height:1.3}
"""
