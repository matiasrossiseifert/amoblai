CSS = r"""
/* ===== anexo: el prompt completo, en dos columnas (instrucciones | ejemplos) ===== */
.slide .t.anx-t{font-size:56px;margin-top:16px}
.anx-pr{margin-top:24px;box-shadow:0 0 0 1.5px var(--hilo)}
.anx-cols{display:grid;grid-template-columns:1.1fr 1fr}
.anx-pr .pr-tx{font-size:14.5px;line-height:1.42;padding:16px 24px 18px}
.anx-pr .anx-ej{border-left:2px dashed var(--hilo);color:var(--tinta-3)}
/* anexo C: un ticket con lo que cuesta cada opción */
.anx-tk{position:absolute;left:96px;top:270px;width:1120px;padding:32px 40px}
.anx-tk .tk-cab b{font-size:40px}
.anx-tk .tk-cab span{font-size:18px}
.anx-tk .tk-l{font-size:25px;padding:13px 0}
.anx-tk .tk-l b{font-size:30px}
.anx-tag{font:400 17px/1 var(--mono);font-style:normal;color:var(--tinta-3);margin-left:6px}
.anx-sep{border-top:2px dashed var(--hilo);margin:8px 0}
/* anexo D: los créditos de las fotos */
.anx-fotos{list-style:none;margin:56px 0 0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:0 64px;width:1600px}
.anx-fotos li{border-top:1px dotted var(--tinta-3);padding:20px 0 22px}
.anx-fotos b{font:700 30px/1.1 var(--display);font-stretch:85%;color:var(--tinta)}
.anx-fotos span{font:400 22px/1.1 var(--sans);color:var(--tinta-3);margin-left:14px}
.anx-fotos p{margin:8px 0 0;font:400 19px/1.35 var(--mono);color:var(--tinta-2)}
/* anexo E: el prompt del juez, en una columna */
.anx-pj{width:1500px}
.anx-pj .pr-tx{font-size:19px;line-height:1.5;padding:22px 30px 24px;white-space:pre-wrap}
.anx-pl .pr-tx{font-size:17px;line-height:1.42}
"""
