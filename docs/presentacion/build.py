#!/usr/bin/env python
"""Arma presentacion.html y guion.md de amoblai (TP, 73.69 LLM, ITBA 2026). Versión b2.

    cd /home/fer/tp-llm && uv run python docs/presentacion/build.py

Concepto: «el flujo y la lista». La columna vertebral es el esquema del sistema (foto y pedido →
plan → búsqueda → elección → escena → imagen → control, con el indexing arriba), dibujado en SVG:
aparece en la portada, se recorre fase por fase en la arquitectura (el mapa que avanza: la fase
actual encendida y las vistas marcadas, con el prompt real de cada fase y sus versiones; ver
laminas_recorrido.py y recorrido.py), lleva un pin por experimento (lleno: con lámina propia;
hueco: de trámite) y se ilumina en la etapa que prueba cada uno. Encima, los objetos de la compra: etiquetas de producto, la lista de
compra como ticket y, al final de cada experimento, un talón con la línea de configuración que
deja. Todos los números salen de los archivos de resultados (datos.py). Las fotos van embebidas
como JPEG y las fuentes (Ubuntu Sans y Ubuntu Sans Mono, variables) recortadas en woff2: la
presentación funciona sin conexión.

`presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; `#/12.2`, el paso 2.
"""

from __future__ import annotations

import base64
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from datos import OUT, TRAB, esc, mmss  # noqa: E402
from estilo import CSS, CSS_REV  # noqa: E402
from estilo_recorrido import CSS as CSS_REC  # noqa: E402
from estilo_a import CSS as CSS_A  # noqa: E402
from estilo_b import CSS as CSS_B  # noqa: E402
from estilo_c import CSS as CSS_C  # noqa: E402
from estilo_d import CSS as CSS_D  # noqa: E402
from estilo_anexo import CSS as CSS_ANX  # noqa: E402
import os  # noqa: E402

# SALIDA=ruta.html arma solo ese .html (para pruebas) y no toca el guion
# SIMPLE=1 arma presentacion_simple.html y guion_simple.md: una lámina por experimento (laminas_simple.py)
SIMPLE = bool(os.environ.get("SIMPLE"))
SALIDA = Path(os.environ["SALIDA"]).resolve() if os.environ.get("SALIDA") else OUT / f"presentacion{'_simple' if SIMPLE else ''}.html"
from piezas import IM, defs_svg  # noqa: E402
from registro import LAMINAS  # noqa: E402

# =============================================================================================
# Fuentes embebidas (variables, recortadas a Latin-1 y algunos signos)
# =============================================================================================

UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) + [0x2009, 0x200A, 0x202F]
            + list(range(0x2010, 0x2028)) + list(range(0x2030, 0x203B))
            + [0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x21BA, 0x2212, 0x2248, 0x2260, 0x2264, 0x2265, 0x221A,
               0x2713, 0x2715, 0x2022, 0x25CF, 0x2116, 0x2026])
FUENTES = [
    ("Ubuntu Sans", "/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf", "100 800", "normal", "75% 100%"),
    ("Ubuntu Sans", "/usr/share/fonts/truetype/ubuntu/UbuntuSans-Italic[wdth,wght].ttf", "100 800", "italic", "75% 100%"),
    ("Ubuntu Sans Mono", "/usr/share/fonts/truetype/ubuntu/UbuntuSansMono[wght].ttf", "100 700", "normal", None),
]


def css_fuentes() -> str:
    out = []
    cache = TRAB / "fuentes"
    cache.mkdir(exist_ok=True)
    for fam, path, w, st, stretch in FUENTES:
        dst = cache / (re.sub(r"[\[\],]", "_", Path(path).stem) + ".woff2")
        if not dst.exists():
            from fontTools import subset
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga", "lnum", "tnum", "pnum", "case", "calt", "ccmp", "locl", "mark", "mkmk"]
            opts.name_IDs = ["*"]
            opts.notdef_outline = True
            font = subset.load_font(path, opts)
            sub = subset.Subsetter(opts)
            sub.populate(unicodes=UNICODES)
            sub.subset(font)
            subset.save_font(font, str(dst), opts)
        b = base64.b64encode(dst.read_bytes()).decode()
        st_ = f"font-stretch:{stretch};" if stretch else ""
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};{st_}font-display:block;"
                   f"src:url(data:font/woff2;base64,{b}) format('woff2')}}")
    return "\n".join(out)


# =============================================================================================
# Navegación
# =============================================================================================

JS = r"""
(function(){
  'use strict';
  var $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  var esc=$('#escenario'), slides=$$('#escenario > .slide'), N=slides.length;
  var NOTAS=JSON.parse($('#datos-notas').textContent);
  var TODO=/[?&](all|todo)\b/.test(location.search), PRES=/[?&]presentador/.test(location.search);
  var cur=0, paso=0, otra=null, inicio=null, volver=null;
  var ID={};slides.forEach(function(s,i){ID[s.dataset.id]=i});
  var NP=slides.filter(function(s){return !s.classList.contains('anexo')}).length;
  function focos(s){try{return s.dataset.focos?JSON.parse(s.dataset.focos):null}catch(e){return null}}
  function maxPaso(s){var m=0;$$('[data-paso]',s).forEach(function(e){m=Math.max(m,+e.dataset.paso)});
    $$('[data-en]',s).forEach(function(e){e.dataset.en.split(' ').forEach(function(x){m=Math.max(m,+x)})});
    var f=focos(s);if(f)m=Math.max(m,f.length-1);if(s.dataset.pasos)m=Math.max(m,+s.dataset.pasos);return m}
  function pintar(s,p,todo){
    var mx=maxPaso(s);if(todo)p=mx;
    s.classList.toggle('todo',!!todo);
    $$('[data-paso]',s).forEach(function(e){e.classList.toggle('visto',+e.dataset.paso<=p)});
    $$('[data-hasta]',s).forEach(function(e){e.classList.toggle('oculto',p>=+e.dataset.hasta)});
    $$('[data-en]',s).forEach(function(e){e.classList.toggle('actual',e.dataset.en.split(' ').indexOf(String(p))!==-1)});
    $$('[data-gana]',s).forEach(function(e){e.classList.toggle('gana',p>=+e.dataset.gana)});
    var f=focos(s);
    if(f){var ks=(f[Math.min(p,f.length-1)]||'').split(' ').filter(Boolean);
      $$('.flujo',s).forEach(function(pl){pl.classList.toggle('foco',ks.length>0);
        $$('[data-k]',pl).forEach(function(g){g.classList.toggle('on',g.dataset.k.split(' ').some(function(k){return ks.indexOf(k)!==-1}))})})}
    s.dataset.p=p;
  }
  function escalar(){
    var box=PRES?$('#p-actual').getBoundingClientRect():{left:0,top:0,width:innerWidth,height:innerHeight};
    var k=Math.min(box.width/1920,box.height/1080);
    esc.style.transform='translate('+(box.left+(box.width-1920*k)/2)+'px,'+(box.top+(box.height-1080*k)/2)+'px) scale('+k+')';
    if(PRES)escalarSig();
  }
  function ir(n,p,silencio){
    n=Math.max(0,Math.min(N-1,n));
    slides[cur].classList.remove('activa');
    cur=n;var s=slides[cur];s.classList.add('activa');
    var mx=maxPaso(s);paso=(p==null)?0:(p<0?mx:Math.min(p,mx));
    pintar(s,paso,TODO);
    var tot=mx+1;
    $('#barra').style.width=Math.min(100,(cur+(TODO?1:(paso+1)/tot))/NP*100)+'%';
    $('#hud-sec').textContent=s.dataset.seccion||'';
    $('#hud-n').textContent=s.classList.contains('anexo')?'anexo':(cur+1)+' / '+NP;
    $('#hud').classList.toggle('sobre-clara',s.classList.contains('clara'));
    $('#hud').classList.toggle('oculto',s.classList.contains('sin-hud'));
    $('#notas').innerHTML='<b>'+(cur+1)+'. '+(s.dataset.titulo||'')+'</b> · '+NOTAS[cur].plan+'<br>'+NOTAS[cur].html;
    var h='#/'+(cur+1)+(paso?'.'+paso:'');
    if(location.hash!==h){try{history.replaceState(null,'',location.pathname+location.search+h)}catch(e){}}
    if(PRES)pintarPresentador();
    if(!silencio){var dest=PRES?window.opener:otra;try{if(dest&&!dest.closed)dest.postMessage({amoblai:1,cur:cur,paso:paso},'*')}catch(e){}}
  }
  // A: desde una lámina con anexo, va al anexo; en el anexo, vuelve a esa lámina y a ese paso
  function anexo(){var s=slides[cur];
    if(s.dataset.anexo&&ID[s.dataset.anexo]!=null){volver=[cur,paso];ir(ID[s.dataset.anexo],0);return}
    if(!s.classList.contains('anexo'))return;
    if(volver){var v=volver;volver=null;ir(v[0],v[1]);return}
    var o=slides.filter(function(x){return x.dataset.anexo===s.dataset.id})[0];if(o)ir(slides.indexOf(o),-1)}
  function siguiente(){if(inicio===null)inicio=Date.now();var mx=maxPaso(slides[cur]);if(!TODO&&paso<mx)ir(cur,paso+1);else if(cur<N-1)ir(cur+1,0)}
  function anterior(){if(!TODO&&paso>0)ir(cur,paso-1);else if(cur>0)ir(cur-1,-1)}
  var ind=$('#indice'),grilla=$('#indice-grilla');
  function clon(s){var c=s.cloneNode(true);c.removeAttribute('id');c.classList.add('activa');pintar(c,0,true);return c}
  function abrirIndice(ab){
    ind.classList.toggle('abierto',ab);if(!ab)return;
    if(!grilla.children.length){slides.forEach(function(s,i){var b=document.createElement('button');b.className='mini-l';var v=document.createElement('div');v.className='mini-v';v.appendChild(clon(s));b.appendChild(v);b.appendChild(document.createTextNode((i+1)+'. '+(s.dataset.titulo||'')));b.addEventListener('click',function(){abrirIndice(false);ir(i,0)});grilla.appendChild(b)})}
    $$('.mini-l',ind).forEach(function(b,i){b.classList.toggle('actual',i===cur);var v=$('.mini-v',b);$('.slide',v).style.transform='scale('+(v.clientWidth/1920)+')'});
  }
  function escalarSig(){var v=$('#p-sig'),s=$('.slide',v);if(s)s.style.transform='scale('+(v.clientWidth/1920)+')'}
  function pintarPresentador(){
    var v=$('#p-sig');v.innerHTML='';if(cur<N-1){v.appendChild(clon(slides[cur+1]));escalarSig()}
    var mx=maxPaso(slides[cur]);
    $('#p-plan').textContent=(slides[cur].classList.contains('anexo')?'Anexo':'Lámina '+(cur+1)+' de '+NP)+' · paso '+paso+' de '+mx+' · '+NOTAS[cur].plan;
    $('#p-notas').innerHTML=NOTAS[cur].html;
  }
  function reloj(){var t=inicio===null?0:Math.floor((Date.now()-inicio)/1000);$('#p-reloj').textContent=String(Math.floor(t/60)).padStart(2,'0')+':'+String(t%60).padStart(2,'0')}
  setTimeout(function(){document.body.classList.add('sin-ayuda')},6000);if(TODO)document.body.classList.add('sin-ayuda','modo-todo');
  if(PRES){document.body.classList.add('presentador');document.title='Presentador · '+document.title;setInterval(reloj,1000);try{window.opener&&window.opener.postMessage({amoblai:1,hola:1},'*')}catch(e){}}
  addEventListener('message',function(e){var d=e.data;if(!d||!d.amoblai)return;if(d.hola){otra=e.source;otra.postMessage({amoblai:1,cur:cur,paso:paso},'*');return}if(inicio===null)inicio=Date.now();ir(d.cur,d.paso,true)});
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey)return;var ab=ind.classList.contains('abierto');
    switch(e.key){
      case'ArrowRight':case'ArrowDown':case'PageDown':case' ':case'Enter':if(!ab){siguiente();e.preventDefault()}break;
      case'ArrowLeft':case'ArrowUp':case'PageUp':case'Backspace':if(!ab){anterior();e.preventDefault()}break;
      case'Home':ir(0,0);e.preventDefault();break;
      case'End':ir(NP-1,0);e.preventDefault();break;
      case'f':case'F':if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen().catch(function(){});break;
      case'o':case'O':abrirIndice(!ab);break;
      case'n':case'N':document.body.classList.toggle('con-notas');break;
      case'b':case'B':$('#negro').classList.toggle('abierto');break;
      case'p':case'P':if(!PRES)otra=window.open(location.pathname+'?presentador#/'+(cur+1)+(paso?'.'+paso:''),'amoblai-presentador','width=1500,height=860');break;
      case'r':case'R':inicio=Date.now();break;
      case'a':case'A':if(!ab){anexo();e.preventDefault()}break;
      case'Escape':abrirIndice(false);$('#negro').classList.remove('abierto');break;
    }
  });
  esc.addEventListener('click',function(){if(!PRES)siguiente()});
  var x0=null;addEventListener('touchstart',function(e){x0=e.changedTouches[0].clientX},{passive:true});
  addEventListener('touchend',function(e){if(x0===null)return;var d=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(d)>50){if(d<0)siguiente();else anterior()}},{passive:true});
  addEventListener('resize',function(){escalar();if(ind.classList.contains('abierto'))abrirIndice(true)});
  function desdeHash(){var mm=location.hash.match(/^#\/?(\d+)(?:\.(\d+))?$/);return mm?[+mm[1]-1,mm[2]?+mm[2]:0]:null}
  addEventListener('hashchange',function(){var h=desdeHash();if(h&&(h[0]!==cur||h[1]!==paso))ir(h[0],h[1])});
  var h0=desdeHash();
  escalar();ir(h0?h0[0]:0,h0?h0[1]:0,true);
})();
"""


# =============================================================================================
# Armado
# =============================================================================================

def notas_html(s) -> str:
    n = s["notas"]
    if isinstance(n, list):
        return "".join(f"<p>{'<b>→</b> ' if i else ''}{esc(t)}</p>" for i, t in enumerate(n))
    return f"<p>{esc(n)}</p>"


def armar() -> int:
    t = 0.0
    notas = []
    destinos = {s.get("anexo") for s in LAMINAS}
    for s in LAMINAS:
        s["desde"] = round(t / 5) * 5
        plan = (f"anexo · no se pasa{'; la A vuelve' if s['id'] in destinos else ''}" if s["id"].startswith("anexo-") else f"~{mmss(s['seg'])} · desde el minuto {mmss(s['desde'])}")
        if s.get("anexo"):
            plan += " · A: el prompt completo, en el anexo"
        notas.append({"plan": plan, "html": notas_html(s)})
        t += s["seg_real"]
    t = round(t)
    secs = []
    for i, s in enumerate(LAMINAS):
        attrs = f'data-id="{s["id"]}" data-titulo="{html.escape(s["titulo"])}" data-seccion="{html.escape(s["seccion"])}"'
        if s.get("anexo"):
            attrs += f' data-anexo="{s["anexo"]}"'
        if s["focos"] is not None:
            attrs += f" data-focos='{json.dumps(s['focos'], ensure_ascii=False)}'"
        secs.append(f'<section class="slide {s["clase"]}" id="s{i + 1}" {attrs}>{s["html"]}</section>')
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>amoblai · 73.69 LLM · ITBA</title>
<style>{css_fuentes()}</style>
<style>{CSS}</style>
<style>{CSS_REC}</style>
<style>{CSS_REV}</style>
<style>{CSS_A}{CSS_B}{CSS_C}{CSS_D}{CSS_ANX}{sys.modules["laminas_simple"].CSS + sys.modules["laminas_modelos"].CSS if SIMPLE else ""}</style>
<style>{IM.style()}</style>
</head><body>
{defs_svg()}
<div id="escenario">
{chr(10).join(secs)}
<div id="hud"><span>amoblai · <b id="hud-sec"></b></span><i></i><span id="hud-n"></span></div><div id="barra"></div>
</div>
<div id="p-panel"><div id="p-actual" style="grid-column:1;grid-row:1/3"></div><div id="p-sig"></div><div id="p-info"><div id="p-reloj">00:00</div><div id="p-plan"></div><div id="p-notas"></div></div></div>
<div id="indice"><div id="indice-grilla"></div></div>
<div id="notas"></div><div id="negro"></div>
<div id="ayuda">→ avanza · ← vuelve · F pantalla completa · O índice · N notas · P presentador · B negro · A anexo</div>
<script type="application/json" id="datos-notas">{json.dumps(notas, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{JS}</script>
</body></html>"""
    SALIDA.write_text(doc)
    return t


def _exp_simple(_id: dict) -> list[str]:
    """El párrafo de los experimentos, en la versión simple."""
    return [f"**Los experimentos** van por su ranking (el mapa, en la lámina {_id['hiper']}), una lámina cada uno: el "
            "título y los gráficos, con barras de error (IC 95% por bootstrap de ambientes) y, en azul, lo que queda en el "
            "flujo. Cuando el experimento se repitió de punta a punta en los 11 ambientes vacíos (el 1, el 2, el 5, el 6, el "
            "13 y el 5b), ese panel va a la derecha: los productos útiles de cada lado y el marcador del juez. El camino "
            f"incremental (lámina {_id['s-camino']}) resume los tres primeros; los siete de trámite van del {_id['s9']} al "
            f"{_id['s15']}; al final, el 5b, elegir con texto o con fotos, que se nos ocurrió después de decidir todo lo "
            f"demás ({_id['s5b']}), y el coseno sin juez ({_id['s-cos']}). Las láminas no tienen pasos: se cuenta la "
            "pregunta, se señala cada panel y se dice la decisión.", ""]


def guion(total: int):
    from laminas import PPM
    anexo = [s for s in LAMINAS if s["id"].startswith("anexo-")]
    n = len(LAMINAS) - len(anexo)
    _rec = [i for i, s in enumerate(LAMINAS, 1) if s["id"].startswith("rec-")]
    _id = {s["id"]: i for i, s in enumerate(LAMINAS, 1)}
    dichas = sum(s["palabras"] for s in LAMINAS)
    _palabras = f"{round(dichas, -2):,}".replace(",", ".")
    L = [f"# Guion de la presentación (amoblai, versión {'simple' if SIMPLE else 'b2'})", "",
         f"Generado por `build.py` junto con `{SALIDA.name}`: los números salen de los mismos archivos de resultados que las láminas, "
         f"y los extractos de los prompts, de `src/amoblai/prompts/`. {n} láminas, unos {round(total / 60)} minutos ({mmss(total)}); "
         f"son unas {_palabras} palabras, contadas a {PPM} por minuto.", "",
         "**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve. F: pantalla completa; "
         "O: índice con miniaturas; N: estas notas abajo de la lámina; P: ventana del presentador (lámina actual, la siguiente, "
         "notas y reloj, sincronizadas); B: pantalla negra; A: en la lámina del prompt de la descripción, abre el anexo con el prompt "
         "completo, y en el anexo vuelve. `presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; "
         "`#/12.2` va al paso 2.", "",
         f"**El recorrido** (láminas {_rec[0]} a {_rec[-1]}) sigue un pedido real con la configuración final, un loft de estilo "
         "industrial sobre una foto pública, por las once fases del flujo, con el mapa arriba a la derecha: la fase actual "
         "encendida, las vistas con ✓ y el pin de los experimentos que le hicieron una pregunta a esa fase (lleno: con lámina "
         "propia; hueco: de trámite). En cada fase: qué entra y qué sale, y el prompt tal cual se manda (extracto, en inglés, con "
         "lo importante resaltado) con sus versiones. Ahí no se dan resultados: los números van en cada experimento.", "",
         *(_exp_simple(_id) if SIMPLE else [
         f"**Los experimentos** van por su ranking (el mapa, en la lámina {_id['hiper']}). Cinco tienen dos "
         "láminas: la oscura es la pregunta, con el porqué y el esquema del flujo con la etapa encendida; con la flecha aparece "
         "qué se comparó. **Se cuentan esas dos cosas antes de pasar.** La clara es el resultado: una flecha muestra los "
         "resultados, con la diferencia pareada, y otra la decisión, que se imprime como un talón abajo. Los experimentos 4 y 7, "
         f"que miden al set de evaluación, y el 8, buscar por imagen, van en una sola lámina; el camino incremental (lámina {_id['camino']}) resume los tres "
         f"primeros; y los siete de trámite van de a uno, del {_id['e9']} al {_id['e15']}. Los experimentos 1, 2, 5 y 13 "
         "tienen además una lámina con el mismo cambio de punta a punta en los 11 ambientes vacíos (láminas "
         f"{_id['e1p']}, {_id['e2p']}, {_id['e5p']} y {_id['e13p']}). Al final van el 5b, elegir con texto o con fotos, que "
         f"se nos ocurrió después de decidir todo lo demás (láminas {_id['e5b']} y {_id['e5br']}), y el coseno sin juez "
         f"({_id['cos']}).", ""]),
         f"**El Ejercicio 4** son las láminas {_id['ej4-v1']} a {_id['ej4-res']}: la versión 1 y su limitación, el cambio con la "
         "configuración antes y después, y los resultados en las dos versiones.", "",
         "En el texto, **→** marca dónde se avanza un paso. Si falta tiempo, se pueden pasar rápido las láminas de trámite "
         "(las marcadas con *). Los costos están en el anexo, después de «Gracias».", ""]
    # reparto en tres partes de tiempo parecido
    cortes = []
    for o in (total / 3, 2 * total / 3):
        cortes.append(min(range(n), key=lambda j: abs(LAMINAS[j]["desde"] - o)))
    partes = [(0, cortes[0]), (cortes[0], cortes[1]), (cortes[1], n)]
    L.append("**Reparto sugerido** (a definir entre los tres):")
    for k, (a, b) in enumerate(partes, 1):
        dur = round(sum(s["seg_real"] for s in LAMINAS[a:b]) / 5) * 5
        L.append(f"- Parte {k}: láminas {a + 1} a {b} ({LAMINAS[a]['titulo']} → {LAMINAS[b - 1]['titulo']}), unos {mmss(dur)}.")
    L.append("")
    rapidas = tuple(f"{c}{n}" for n in range(9, 16) for c in "es")
    for i, s in enumerate(LAMINAS[:n], 1):
        L.append(f"## {i}. {re.sub('<[^>]+>', '', s['titulo'])}{' *' if s['id'] in rapidas else ''}")
        L.append(f"*{s['seccion'] or 'Portada'} · ~{mmss(s['seg'])} · desde el minuto {mmss(s['desde'])}*")
        L.append("")
        if isinstance(s["notas"], list):
            L.append(" **→** ".join(s["notas"]))
        else:
            L.append(s["notas"])
        L.append("")
    for s in anexo:
        notas = s["notas"]
        L += [f"## {re.sub('<[^>]+>', '', s['titulo'])}", "*Anexo · no se pasa: se abre con la A desde su lámina*", "",
              " **→** ".join(notas) if isinstance(notas, list) else notas, ""]
    (OUT / f"guion{'_simple' if SIMPLE else ''}.md").write_text("\n".join(L))


if __name__ == "__main__":
    import laminas  # noqa: F401  (registra las láminas)
    total = armar()
    if not os.environ.get("SALIDA"):
        guion(total)
    size = SALIDA.stat().st_size
    from laminas import PPM
    dichas = sum(s["palabras"] for s in LAMINAS)
    print(f"{len(LAMINAS)} láminas · {mmss(total)} · {dichas} palabras a {PPM} por minuto · {size / 1e6:.2f} MB (fotos {IM.bytes / 1e6:.2f} MB)")
    if not 30 * 60 <= total <= 31 * 60:
        print(f"  ojo: el guion dura {mmss(total)}; tiene que quedar entre 30:00 y 31:00")
