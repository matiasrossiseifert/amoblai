"""Las piezas del recorrido por las fases: el mapa que avanza, los extractos de los prompts (se leen
de src/amoblai/prompts tal cual se mandan: si un trozo no está en el archivo, el build falla), la
historia de versiones, y dos cálculos locales que se guardan en _trabajo/ (sift_*.json y
vector_*.json, para no abrir ChromaDB ni correr SIFT en cada build): los puntos SIFT entre la foto
vacía y la imagen generada (el mismo código que el control del flujo) y el vector de Qwen3 de un
producto, leído de una copia de ChromaDB (abrirlo toca su sqlite, que está en git). Si cambia la
corrida de ejemplo se regeneran solos, sin modificar datos/cache/."""

from __future__ import annotations

import json
import re

import yaml

from datos import ROOT, TRAB, esc
from piezas import FASES, TRAMITE, flujo

PROMPTS = ROOT / "src" / "amoblai" / "prompts"


def _partes(nombre: str) -> tuple[dict, str]:
    t = (PROMPTS / nombre).read_text()
    if t.startswith("---"):
        _, fm, cuerpo = t.split("---", 2)
        return yaml.safe_load(fm) or {}, cuerpo.strip("\n")
    return {}, t.strip("\n")


def cuerpo_prompt(nombre: str) -> str:
    """El texto del prompt, sin el front matter (con sus {marcadores} sin llenar)."""
    return _partes(nombre)[1]


def notas_prompt(nombre: str) -> str:
    """Las notas del front matter del prompt (para verificar lo que se dice de cada versión)."""
    return _partes(nombre)[0].get("notes", "")


def _marcar(texto: str, resaltar) -> str:
    h = esc(texto)
    for r in resaltar:
        er = esc(r)
        if er in h:
            h = h.replace(er, f"\x00{er}\x01", 1)
    h = re.sub(r"\{[a-z_]+\}", lambda m: f'<i class="ph">{m.group(0)}</i>', h)
    return h.replace("\x00", '<mark class="hl">').replace("\x01", "</mark>")


def extracto(nombre: str, trozos, resaltar=(), texto: str | None = None) -> str:
    """Trozos literales del prompt: cada (desde, hasta) va desde la primera aparición de `desde`
    hasta el final de `hasta` (None: hasta el final de esa línea). Entre trozos, «…».
    `texto`: otro texto en lugar del archivo (un prompt ya lleno, de una corrida)."""
    t = texto if texto is not None else _partes(nombre)[1]
    partes = []
    for desde, hasta in trozos:
        i = t.index(desde)
        if hasta is None:
            j = t.find("\n", i)
            j = len(t) if j == -1 else j
        else:
            j = t.index(hasta, i) + len(hasta)
        partes.append(t[i:j])
    junto = "\n".join(partes)
    for r in resaltar:
        if r not in junto:
            raise ValueError(f"{nombre}: «{r}» no está en el extracto")
    return '<span class="el">…</span>'.join(_marcar(p, resaltar) for p in partes)


def prompt_tk(nombre: str, trozos, resaltar=(), rotulo: str = "extracto, tal cual se manda", ancho: int | None = None,
              texto: str | None = None, titulo: str | None = None, cls: str = "") -> str:
    st = f' style="width:{ancho}px"' if ancho else ""
    return (f'<div class="pr-tk {cls}"{st}><div class="pr-cab"><b>{titulo or nombre}</b><span>{rotulo}</span></div>'
            f'<pre class="pr-tx">{extracto(nombre, trozos, resaltar, texto)}</pre></div>')


def versiones(items, cls: str = "") -> str:
    """items: (etiqueta, qué cambió, por qué, estado) con estado '' | 'actual' | 'fuera'."""
    filas = "".join(f'<li class="{e}"><em>{v}</em><div><b>{q}</b>{f"<span>{p}</span>" if p else ""}</div></li>'
                    for v, q, p, e in items)
    return f'<ol class="vers {cls}">{filas}</ol>'


def exps(items, cls: str = "") -> str:
    """Los experimentos que le hicieron una pregunta a la fase: (número, qué, detalle). Los de
    trámite van con el pin hueco; «—»: sin experimento."""
    def em(n):
        c = "no" if n == "—" else ("hueco" if n in TRAMITE else "")
        return f'<em{f" class={c}" if c else ""}>{n}</em>'
    filas = "".join(f'<li>{em(n)}<div><b>{t}</b>{f"<span>{d}</span>" if d else ""}</div></li>' for n, t, d in items)
    return f'<ul class="rx {cls}">{filas}</ul>'


def mapa(actual, pines=None, focos=False) -> str:
    """El mapa del recorrido: `actual` son las fases de la lámina (la primera define qué ya se vio);
    las anteriores quedan marcadas como vistas. pines: dict fase -> experimentos.
    Con focos, las fases encendidas las maneja cada paso (data-focos de la lámina)."""
    actual = list(actual)
    i0 = FASES.index(actual[0])
    vistos = FASES[:i0] + (actual[:-1] if focos else [])
    return f'<div class="rmapa">{flujo(ruta=True, on=() if focos else actual, vistos=vistos, pines_en=pines or {})}</div>'


# =============================================================================================
# Cálculos locales, guardados en _trabajo/
# =============================================================================================

def sift_pares(antes, despues, clave: str) -> dict:
    """Los pares SIFT que RANSAC acepta entre la foto original y la generada, con el mismo código
    y los mismos parámetros que furnish/room.py (las dos a 800 px de ancho)."""
    cache = TRAB / f"sift_{clave}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    import numpy as np
    from PIL import Image
    from skimage.feature import SIFT, match_descriptors
    from skimage.measure import ransac
    from skimage.transform import ProjectiveTransform

    before, after = Image.open(antes), Image.open(despues)
    w = 800
    h = round(before.height * w / before.width)
    b = np.asarray(before.convert("L").resize((w, h)), float) / 255
    a = np.asarray(after.convert("L").resize((w, h)), float) / 255
    sb, sa = SIFT(), SIFT()
    sb.detect_and_extract(b)
    sa.detect_and_extract(a)
    m = match_descriptors(sb.descriptors, sa.descriptors, max_ratio=0.8, cross_check=True)
    src = sb.keypoints[m[:, 0]][:, ::-1]
    dst = sa.keypoints[m[:, 1]][:, ::-1]
    _, inl = ransac((src, dst), ProjectiveTransform, min_samples=4, residual_threshold=3, max_trials=2000, rng=0)
    res = {"w": w, "h": h, "puntos": len(sb.keypoints), "matches": len(m), "inliers": int(inl.sum()),
           "pares": [[round(float(x), 1) for x in (*src[i], *dst[i])] for i in np.flatnonzero(inl)]}
    cache.write_text(json.dumps(res))
    return res


def vector_chroma(pid: str, n: int = 64) -> dict:
    """El vector (las primeras n componentes) y la metadata de un producto, tal como están en el
    ChromaDB del flujo (catálogo todos, Qwen3). Se lee de una copia del índice: abrir ChromaDB toca
    su sqlite, y datos/cache/ está en git (y otra corrida puede estar usándolo)."""
    cache = TRAB / f"vector_{pid}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    import shutil

    import chromadb

    src = ROOT / "datos" / "cache" / "rag" / "index" / "todos-written_todos-qwen3" / "chroma"
    tmp = TRAB / "chroma_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp)
    try:
        c = chromadb.PersistentClient(path=str(tmp), settings=chromadb.Settings(anonymized_telemetry=False))
        col = c.get_collection("products")
        r = col.get(ids=[pid], include=["embeddings", "metadatas"])
        v = [float(x) for x in r["embeddings"][0]]
        res = {"dim": len(v), "norma": round(sum(x * x for x in v) ** .5, 4), "v": [round(x, 5) for x in v[:n]],
               "metadata": r["metadatas"][0]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cache.write_text(json.dumps(res))
    return res
