"""Arma presentacion.html y guion.md a partir de los archivos de resultados del repo.

    cd /home/fer/tp-llm && uv run python docs/presentaciones_nuevas/a2/build.py

Ningún número está escrito a mano: todos salen de datos_deck.load(), que lee los archivos de
resultados del repo. El HTML es autocontenido (fuentes recortadas y fotos embebidas) y anda sin
conexión. Al final avisa si el guion no suma entre 30 y 31 minutos, o si alguna lámina pide hablar
más rápido de lo que se puede.

Navegación: → ← espacio PgUp/PgDn (y clic: a la izquierda vuelve), Home/End, F pantalla completa,
O índice, N notas del orador, B pantalla negra, Esc. `?all` muestra cada lámina con todos sus pasos;
`#/12` o `#/12.2` van a una lámina (y a un paso).
"""

from __future__ import annotations

import base64
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import base  # noqa: E402
import datos_deck  # noqa: E402
import fuentes  # noqa: E402
import img  # noqa: E402
import sala  # noqa: E402
from estilo import CSS, JS  # noqa: E402
from estilo_l import CSS_L  # noqa: E402
import planta  # noqa: E402
from laminas_rec import CSS_R  # noqa: E402

OUT = HERE / "presentacion.html"
GUION = HERE / "guion.md"

DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
        '<pattern id="rayado" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="7" height="7" fill="#F4F4F0"/><line x1="0" y1="0" x2="0" y2="7" stroke="#13202C" stroke-width="1.1"/></pattern>'
        '<pattern id="rayado-o" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="7" height="7" fill="#173A78"/><line x1="0" y1="0" x2="0" y2="7" stroke="#CFDCF7" stroke-width="1.1"/></pattern>'
        '</defs></svg>')

MINI_CSS = r"""
.sala.mini *{vector-effect:non-scaling-stroke}
.sala.mini polygon,.sala.mini path,.sala.mini line{stroke-width:.7px}
.sala.mini .grilla,.sala.mini .det,.sala.mini .baranda,.sala.mini .zoc,.sala.mini .hoja.f{display:none}
.sala.mini .corte{fill:var(--hilo-2)}
#pie.sobre-plano .sala.mini{--ink:#E8EFFF;--top:#204A97;--sx:#1C428A;--sy:#183B7D;--wall:#1B4087;--floor:#173A7A;--acc:var(--naranja);--accs:rgba(255,154,61,.4);--accx:rgba(255,154,61,.3);--accy:rgba(255,154,61,.2);--vano:#21498F}
#pie.sobre-plano .sala.mini .corte{fill:#2F5BA8}
#pie.sobre-plano .sala.mini .marco{fill:#CFDCF7}
"""


def fuentes_css() -> str:
    paths = fuentes.build()
    b = lambda k: base64.b64encode(paths[k].read_bytes()).decode()
    return (
        f"@font-face{{font-family:'Ubuntu Sans V';src:url(data:font/woff2;base64,{b('sans')}) format('woff2');"
        "font-weight:100 800;font-stretch:75% 100%;font-style:normal;font-display:block}"
        f"@font-face{{font-family:'Ubuntu Sans V';src:url(data:font/woff2;base64,{b('sans-i')}) format('woff2');"
        "font-weight:100 800;font-stretch:75% 100%;font-style:italic;font-display:block}"
        f"@font-face{{font-family:'Go Mono';src:url(data:font/woff2;base64,{b('mono')}) format('woff2');font-weight:400;font-style:normal;font-display:block}}"
        f"@font-face{{font-family:'Go Mono';src:url(data:font/woff2;base64,{b('mono-b')}) format('woff2');font-weight:700;font-style:normal;font-display:block}}"
    )


def notas_html(notas: list[str]) -> str:
    return "".join(f"<p>{base.md(n)}</p>" for n in notas)


def mmss(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


def palabras(s: dict) -> int:
    """Las palabras que se dicen en una lámina (sus notas, sin las marcas)."""
    return sum(len(n.replace("[paso]", "").replace("**", "").split()) for n in s["notas"])


def guion(slides: list[dict]) -> str:
    main = [s for s in slides if not s["anexo"]]
    tot = sum(s["t"] for s in main)
    dichas = sum(palabras(s) for s in main)
    out = ["# Guion · amoblai", "",
           "TP 3 · 73.69 Large Language Models · ITBA 2026 · Juan Bautista Albertoni Salini, Matias Juan "
           "Rossi Seifert, Junior Rambau", "",
           f"Generado por `build.py` junto con `presentacion.html` ({len(main)} láminas + {len(slides) - len(main)} de anexo): "
           f"los números salen de los mismos archivos de resultados que las láminas. Duración estimada: **{mmss(tot)}** "
           f"(unas {round(dichas, -2):,} palabras, a {round(dichas / tot * 60)} por minuto).".replace(",", "."), "",
           "«▸ paso» marca dónde se aprieta → para mostrar lo siguiente de la lámina. En cada experimento, primero se ve "
           "el porqué; después qué hicimos, los resultados y la decisión. Las notas también se ven en la presentación con "
           "la tecla N; con `presentacion.html?all` cada lámina aparece con todos sus pasos (para revisar o imprimir).", "",
           "Si falta tiempo, se pueden pasar rápido las dos láminas de trámite y la del costo.", "",
           "| # | Lámina | Tiempo | Acumulado |", "|---|---|---|---|"]
    acc = 0
    for i, s in enumerate(main):
        acc += s["t"]
        out.append(f"| {i + 1} | {s['titulo']} | {mmss(s['t'])} | {mmss(acc)} |")
    out.append("")
    cap = None
    acc = 0
    for i, s in enumerate(slides):
        if s["seccion"] != cap:
            cap = s["seccion"]
            out += ["", f"## {cap}", ""]
        if s["anexo"]:
            out.append(f"### Anexo {s['anexo']} · {s['titulo']}")
        else:
            acc += s["t"]
            out.append(f"### {i + 1}. {s['titulo']} · {mmss(s['t'])} (acumulado {mmss(acc)})")
        out.append("")
        for n in s["notas"]:
            n = n.replace("[paso]", "▸ paso:")
            out.append(n)
            out.append("")
    return "\n".join(out).rstrip() + "\n"


# Las referencias a experimentos ({{LAM:E6}}: el número de su lámina; {{IR:E6}}: su índice, para el
# clic) se resuelven al final, cuando ya se sabe en qué lámina quedó cada uno. Los de trámite (E9 a
# E15) no tienen lámina propia: van juntos en dos.
LAM_TITULO = {**{f"E{n}": "De trámite · el índice" for n in (9, 10, 11, 12)},
              **{f"E{n}": "De trámite · filtros" for n in (13, 14, 15)}}


def referencias(secs: str, slides: list[dict]) -> str:
    import re

    def idx(k: str) -> int:
        pre = LAM_TITULO.get(k, f"{k} · ")
        for i, s in enumerate(slides):
            if s["titulo"].startswith(pre) and not s["anexo"]:
                return i
        raise KeyError(f"no hay lámina para {k}")

    secs = re.sub(r"\{\{LAM:(\w+)\}\}", lambda m: str(idx(m.group(1)) + 1), secs)
    return re.sub(r"\{\{IR:(\w+)\}\}", lambda m: str(idx(m.group(1))), secs)


def main() -> None:
    t0 = time.time()
    D = datos_deck.load()
    print(f"datos: {time.time() - t0:.1f} s")
    import laminas_1
    import laminas_2
    import laminas_3
    ctx = laminas_1.build(D)
    laminas_2.build(D, ctx)
    laminas_3.build(D, ctx)

    slides = base.SL
    main_n = sum(1 for s in slides if not s["anexo"])
    secs = "".join(base.section_html(i, s, main_n) for i, s in enumerate(slides))
    minis = "".join(f'<template class="mini-{c}">{sala.mini(base.piezas_hasta(c if c < 8 else 7), base.CAPS[c][1] if c < 8 else ())}</template>'
                    for c in base.CAPS)
    notas = json.dumps([notas_html(s["notas"]) for s in slides], ensure_ascii=False)
    pie = ('<div id="pie"><div class="p-marca">amoblai</div><div class="p-sec" id="p-sec"></div>'
           '<div class="p-planta vacia" id="p-planta"></div>'
           '<div class="p-sala" id="p-sala"></div><div class="p-num" id="p-num"></div></div><div id="barra"></div>')
    minis += f'<template class="llave">{planta.llave()}</template>'
    secs = referencias(secs, slides)
    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>amoblai · TP 3 · 73.69 LLM · ITBA 2026</title>'
        f"<style>{fuentes_css()}{CSS}{CSS_L}{planta.CSS_P}{CSS_R}{MINI_CSS}</style></head><body>{DEFS}"
        f'<div id="escenario">{secs}{pie}</div>{minis}'
        '<div id="indice"><div id="indice-grilla"></div></div><div id="negro"></div><div id="notas"></div>'
        f"<script>window.__NOTAS={notas};</script><script>{JS}</script></body></html>"
    )
    OUT.write_text(html)
    GUION.write_text(guion(slides))
    main_s = [s for s in slides if not s["anexo"]]
    tot = sum(s["t"] for s in main_s)
    dichas = sum(palabras(s) for s in main_s)
    print(f"{main_n} láminas + {len(slides) - main_n} de anexo · {mmss(tot)} · {dichas} palabras ({round(dichas / tot * 60)} por minuto) · "
          f"{OUT.stat().st_size / 1e6:.2f} MB · imágenes {img.STATS['n']} ({img.STATS['bytes'] / 1e6:.2f} MB) · "
          f"{time.time() - t0:.1f} s")
    # el ritmo de cada lámina: avisa si alguna pide hablar más rápido de lo que se puede
    for i, s in enumerate(main_s, 1):
        if s["t"] >= 15 and palabras(s) / s["t"] * 60 > 165:
            print(f"  ojo: la lámina {i} ({s['titulo'][:44]}) tiene {palabras(s)} palabras para {mmss(s['t'])}: "
                  f"{round(palabras(s) / s['t'] * 60)} por minuto")
    if not 30 * 60 <= tot <= 31 * 60:
        print(f"  ojo: el guion dura {mmss(tot)}; tiene que quedar entre 30:00 y 31:00")


if __name__ == "__main__":
    main()
