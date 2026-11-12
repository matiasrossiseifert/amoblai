"""Evaluación del retrieval por texto con el ground truth del dataset IKEA.

Para cada foto de ambiente (los livings y comedores con productos anotados del catálogo), las
consultas de `datos/evaluacion_ikea/consultas.json`: una por producto del alcance que se ve, en
las ocho líneas del catálogo y con su kind (las escribieron subagentes mirando la foto, sin ver
el catálogo ni las anotaciones: primero las de sofás, sillones, sillas, mesas y alfombras, con
`consultas_ambiente_v1`; después las de lo que sumó la ampliación del catálogo, con
`consultas_ambiente_v2`). Cada consulta pasa por la búsqueda (filtros duros, después los
vecinos más cercanos por coseno) y se mira el ranking:

- **relevantes de una consulta**: los SKUs anotados en ese ambiente del mismo grupo que su kind
  (`group_of`): en los muebles, la misma categoría del TP (sofá, sillón, silla, mesa, alfombra,
  estantería...: datos/configs/categories.yaml), la definición de la v0 (retrieval por imagen),
  así que las dos se comparan con el mismo ground truth; en lámparas y decoración, el kind,
  porque la categoría junta cosas que no se reemplazan (un almohadón no responde a una búsqueda
  de florero). Las anotaciones no dicen dónde está cada producto: la métrica es permisiva.
- hit rate@k, MRR@10, context precision@10 (la de RAGAS de la clase 11) y NDCG@10 sobre las
  consultas con al menos un relevante; hit@k por familia (acierta también con otra variante del
  mismo modelo: mismo nombre y grupo), para separar "otro mueble" de "el mismo en otro color";
  context recall@10 por ambiente (de sus productos anotados,
  cuántos trae el contexto de sus consultas) y recall@k por ítem anotado; la curva de hit@k hasta
  k=50 (cuántos candidatos pasarle al reranker); la calibración del score (AUROC de "el primero es
  correcto"); baseline aleatorio sobre lo que deja pasar el filtro; IC 95% por bootstrap de
  ambientes; y cada método contra el primero de la ablación, con la diferencia pareada (las mismas
  consultas) y su IC 95% (`vs_base`).

Un método (las ablaciones de datos/configs/ablaciones/*.yaml) combina:
- `embedder`: hashing, bge, qwen3 (rag.embedders); `bm25`, la búsqueda léxica; o un modelo de
  imagen y texto (siglip2, clip): la consulta en una frase corta contra la foto del producto, sin
  descripción (rag/hybrid.py);
- `fusion`: otros buscadores cuyo puntaje se fusiona con el del embedder ("bm25", "siglip2",
  "bm25+siglip2": búsqueda híbrida), con `fusion_rule` `sum` (z-score, el promedio) o `rrf`;
- `text`, lo que se embebe de cada producto: `description` (nuestras ocho líneas), `seller` (el
  texto del vendedor con nuestra categoría como tipo), `seller-full` (el texto del vendedor con
  su propio tipo, "Easy chair": la línea de base honesta) o `name+description` (el nombre
  comercial adelante);
- `filter`: `kind` (el kind de la consulta), `type` (solo el tipo grueso) o `none`;
- `store`, la base vectorial: `chroma` (ChromaDB, HNSW, los filtros como `where`) o `exact`
  (numpy sobre todos los vectores);
- `query`, cómo se escribe la consulta: `full` (las ocho líneas del catálogo, como las escribe el
  plan: un documento hipotético), `piece` (la frase corta en lenguaje natural con que el redactor
  nombró la pieza, "square pine coffee table": la consulta sin reescribir), `type` (solo la
  línea Type) o `kind` (solo el nombre del kind);
- `drop`: líneas que se sacan de las descripciones y de las consultas antes de embeber
  ("Colors", "Feel+Goes with"): qué parte del documento hace el trabajo;
- `dim`: los vectores truncados a sus primeras `dim` componentes y renormalizados (Qwen3-Embedding
  se entrenó con Matryoshka: la dimensión se elige sin reentrenar);
- `chunks`, cómo se parte cada descripción: `whole` (un documento por producto), `lines-max`
  (cada línea un chunk; el producto puntúa con su mejor línea contra la consulta entera) o
  `lines-aligned` (línea contra línea del mismo rótulo, Colors con Colors...: el promedio);
  partida, la búsqueda es exacta (numpy);
- `rerank`: los `evaluation.rerank_top` primeros reordenados por un VLM que mira las fotos
  (pago) o por un cross-encoder local que lee la consulta y la descripción juntas (gratis,
  `LOCAL_RERANKERS`).
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import platform
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from amoblai.catalog.descriptions import LABELS
from amoblai.catalog.kinds import KINDS
from amoblai.catalog.loader import Product, load_catalog
from amoblai.config import Config
from amoblai.evaluation.metrics import (
    auroc,
    best_f1_threshold,
    bootstrap_ci,
    context_precision_at_k,
    first_relevant_rank,
    hit_at_k,
    ndcg_at_k,
    random_hit_at_k,
    random_mrr,
    reciprocal_rank,
)
from amoblai.evaluation.queries import load_queries
from amoblai.furnish.llm import image_block, text_block
from amoblai.furnish.steps import ask, photo, size_text, type_line
from amoblai.infra.budget import ledger_for
from amoblai.infra.http import ProviderError
from amoblai.prompts import load_prompt
from amoblai.rag.describe import FieldsDescriber
from amoblai.rag.embed import get_embedder
from amoblai.rag.filters import Filters
from amoblai.rag.hybrid import BM25, ImageTextEmbedder, fuse, visual_query
from amoblai.rag.index import Index, ensure_index, vectors_cached
from amoblai.rag.search import as_hit
from amoblai.rag.store import ChromaStore

KS = (1, 3, 5, 10)
LOCAL_RERANKERS = ("minilm-reranker", "qwen3-reranker")  # cross-encoders locales (gratis)
CURVE = (1, 2, 3, 5, 10, 15, 20, 30, 50)  # hit@k: cuántos candidatos le llegan al reranker
DEPTH = max(CURVE)  # cuántos trae la búsqueda; en rankings.jsonl.gz quedan los max(KS) primeros


def seller_full(product: Product) -> str:
    """Todo lo que da el vendedor de un producto: su tipo tal como lo escribe ("Easy chair",
    "Rug, flatwoven"), el nombre, los colores, los materiales y su texto."""
    i = product.info
    lines = [f"Type: {i.get('type_ikea') or i['category'].replace('_', ' ')}", f"Name: {i['name']}"]
    if i.get("colors"):
        lines.append("Colors: " + ", ".join(i["colors"]))
    if i.get("materials"):
        lines.append("Materials: " + ", ".join(i["materials"]))
    if i.get("description"):
        lines.append(i["description"])
    return "\n".join(lines) + "\n"


# Lo que se embebe de cada producto (item del índice, producto del catálogo).
TEXTS: dict[str, Callable[[dict, Product], str]] = {
    "description": lambda it, p: it["description"],  # nuestras ocho líneas
    "name+description": lambda it, p: f"Name: {it['name']}\n{it['description']}",
    "seller": lambda it, p: FieldsDescriber().describe(p).text,  # nombre, colores, texto
    "seller-full": lambda it, p: seller_full(p),  # lo mismo con el tipo que le pone el vendedor
}

# kind (catalog/kinds.py) -> categoría del TP (la de la v0 y de datos/configs/categories.yaml).
# En las categorías que sumó la ampliación, la categoría es el tipo grueso del kind.
EXPANSION = ("desk", "shelf", "cabinet", "dresser", "ottoman", "stool", "bench", "lamp", "deco")
KIND_TO_TP = {
    "sofa": "sofa",
    "sofa bed": "sofa",
    "armchair": "armchair",
    "dining chair": "chair",
    "desk chair": "chair",
    "dining table": "table",
    "coffee table": "table",
    "side table": "table",
    "nightstand": "table",
    "console table": "table",
    "rug": "rug",
    **{k: t for k, t in KINDS.items() if t in EXPANSION},
}
# En lámparas y decoración el grupo de relevancia es el kind, salvo los que una foto no separa.
FINE = ("lamp", "deco")
SAME_GROUP = {
    "ceiling lamp": "pendant lamp",  # colgante o pegada al techo: desde abajo se ven igual
    "desk lamp": "table lamp",  # las dos van sobre un mueble
    "plant pot": "plant",  # la planta se ve con su maceta
    "picture frame": "wall art",  # el cuadro se ve con su marco
}


def family(product: Product) -> tuple[str, str]:
    """El modelo de un producto: su nombre comercial y su grupo de relevancia. Las variantes de
    un mismo modelo (PONG en abedul y en negro, una alfombra en dos medidas) comparten familia."""
    return (str(product.info["name"]).strip().lower(), product_group(product))


def group_of(kind: str) -> str:
    """El grupo de relevancia de un kind: su categoría del TP, o en lámparas y decoración el
    kind mismo (SAME_GROUP junta los que se confunden)."""
    tp = KIND_TO_TP[kind]
    return SAME_GROUP.get(kind, kind) if tp in FINE else tp


def product_group(p: Product) -> str:
    """El grupo de relevancia de un producto del catálogo: el de su categoría del TP (la del
    `type` de IKEA), o el de su kind en lámparas y decoración. Un escritorio que IKEA tipifica
    como mesa (correcciones.yaml) es escritorio."""
    tp = p.info.get("category_tp", p.category)  # ABO no la trae: es la misma categoría
    if p.category == "desk":
        return "desk"
    return group_of(p.kind) if tp in FINE and p.kind in KIND_TO_TP else tp


@dataclass(frozen=True)
class Method:
    embedder: str
    text: str = "description"
    filter: str = "kind"  # kind | type | none
    store: str = "chroma"  # chroma | exact
    query: str = "full"  # full | type | kind
    rerank: str | None = None  # un reranker de evaluation.rerankers
    dim: int | None = None  # truncar los vectores (Matryoshka)
    chunks: str = "whole"  # whole | lines-max | lines-aligned
    drop: str | None = None  # líneas que se sacan de documentos y consultas: "Feel+Goes with"
    fusion: str | None = None  # otros buscadores, fusionados: "bm25", "siglip2", "bm25+siglip2"
    fusion_rule: str = "sum"  # sum (z-score) | rrf

    @property
    def scorers(self) -> list[str]:
        return [self.embedder, *(self.fusion.split("+") if self.fusion else [])]

    @property
    def name(self) -> str:
        name = f"{self.embedder}|{self.text}|filtro-{self.filter}"
        if self.drop:
            name += f"|sin-{self.drop}"
        if self.fusion:
            name += f"|+{self.fusion}"
        if self.fusion_rule != "sum":
            name += f"|fusion-{self.fusion_rule}"
        if self.store != "chroma":
            name += f"|{self.store}"
        if self.query != "full":
            name += f"|consulta-{self.query}"
        if self.dim:
            name += f"|dim-{self.dim}"
        if self.chunks != "whole":
            name += f"|chunks-{self.chunks}"
        if self.rerank:
            name += f"|rerank-{self.rerank}"
        return name

    @property
    def paid(self) -> bool:
        return self.rerank is not None and self.rerank not in LOCAL_RERANKERS


def load_ablation(path: Path) -> tuple[str, list[Method]]:
    """(nombre, métodos) de una ablación: la grilla (producto cartesiano de `grid`) más los
    métodos sueltos de `methods`; los campos que faltan toman el default de Method."""
    spec = yaml.safe_load(Path(path).read_text()) or {}
    grid = spec.get("grid") or {}
    methods = (
        [
            Method(**dict(zip(grid, combo, strict=True)))
            for combo in itertools.product(*grid.values())
        ]
        if grid
        else []
    )
    methods += [Method(**m) for m in spec.get("methods") or []]
    return spec.get("name") or Path(path).stem, list(dict.fromkeys(methods))


@dataclass
class Search:
    room_id: str
    piece: int
    kind: str
    query: str
    relevant: list[str]  # del mismo grupo que el kind
    relevant_any: list[str]  # cualquier producto anotado del catálogo
    prompt: str = "consultas_ambiente_v1"  # la pasada que escribió la consulta
    phrase: str = ""  # la pieza en una frase corta, como la nombró el redactor


def load_searches(queries_path: Path, raw_dir: Path, catalog_ids: dict[str, str]) -> list[Search]:
    """Consultas con sus relevantes, a partir del ground truth del dataset.

    `catalog_ids`: {SKU: grupo de relevancia} de los productos del catálogo (product_group)."""
    from amoblai.dataset.ikea import IkeaDataset

    ds = IkeaDataset.load(raw_dir)
    searches = []
    for room_id, rec in load_queries(queries_path).items():
        gt = sorted(s for s in ds.rooms[room_id].skus if s in catalog_ids)
        for i, p in enumerate(rec["pieces"]):
            kind = p["kinds"][0]
            group = group_of(kind)
            relevant = [s for s in gt if catalog_ids[s] == group]
            searches.append(
                Search(
                    room_id,
                    i,
                    kind,
                    p["query"],
                    relevant,
                    gt,
                    p.get("prompt", Search.prompt),
                    p.get("piece", ""),
                )
            )
    return searches


def filters_for(method: Method, kind: str) -> Filters:
    if method.filter == "kind":
        return Filters(kinds=[kind])
    if method.filter == "type":
        return Filters(categories=[KINDS[kind]])
    return Filters()


# Cómo se escribe la consulta: como la escribe el plan (un documento hipotético en las ocho
# líneas), sin reescribir (la frase corta con que el redactor nombró la pieza), o menos.
QUERIES: dict[str, Callable[[Search], str]] = {
    "full": lambda s: s.query,  # las ocho líneas
    "piece": lambda s: s.phrase or s.kind,  # "square pine coffee table, front center"
    "type": lambda s: s.query.splitlines()[0],  # solo "Type: ..."
    "kind": lambda s: s.kind,  # solo el nombre del kind
}


def without_lines(text: str, drop: str | None) -> str:
    """El texto sin las líneas de esos rótulos ("Feel+Goes with")."""
    if not drop:
        return text
    labels = {x.strip() for x in drop.split("+")}
    return "\n".join(ln for ln in text.splitlines() if ln.split(":", 1)[0].strip() not in labels)


def truncate(vectors: np.ndarray, dim: int) -> np.ndarray:
    """Las primeras `dim` componentes de cada vector, renormalizadas (Matryoshka)."""
    v = vectors[:, :dim]
    return v / np.linalg.norm(v, axis=1, keepdims=True).clip(min=1e-12)


def labeled_lines(text: str) -> dict[str, str]:
    """{rótulo: línea} de un texto en las ocho líneas ("Colors: light oak" va a "Colors")."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line and line.strip():
            out.setdefault(line.split(":", 1)[0].strip(), line.strip())
    return out


def chunk_scores(
    method: Method, doc_texts: list[str], query_texts: list[str], embed: Callable
) -> np.ndarray:
    """(consultas, productos): el score de cada producto con su descripción partida en líneas.
    `embed`: textos -> vectores de largo 1 (en caché).

    - `lines-max`: la consulta entera contra cada línea; el producto vale lo de su mejor línea
      (cada línea es un chunk que apunta a su producto).
    - `lines-aligned`: cada línea de la consulta contra la línea del mismo rótulo del producto
      (Colors con Colors): el promedio sobre los rótulos que tienen los dos."""

    def vectors(texts: list[str]) -> np.ndarray:
        v = embed(texts)
        return truncate(v, method.dim) if method.dim else v

    docs = [labeled_lines(t) for t in doc_texts]
    if method.chunks == "lines-max":
        lines = [ln for d in docs for ln in d.values()]
        sims = vectors(query_texts) @ vectors(lines).T  # (consultas, líneas)
        starts = np.cumsum([0] + [len(d) for d in docs[:-1]])
        return np.maximum.reduceat(sims, starts, axis=1)
    if method.chunks != "lines-aligned":
        raise ValueError(f"chunks {method.chunks!r}: whole, lines-max o lines-aligned")
    queries = [labeled_lines(t) for t in query_texts]
    total = np.zeros((len(queries), len(docs)))
    count = np.zeros((len(queries), len(docs)))
    for label in LABELS:
        d_has = np.array([label in d for d in docs])
        q_has = np.array([label in q for q in queries])
        if not d_has.any() or not q_has.any():
            continue
        dv = vectors([d[label] for d in docs if label in d])
        qv = vectors([q[label] for q in queries if label in q])
        block = np.zeros((len(queries), len(docs)))
        block[np.ix_(q_has, d_has)] = qv @ dv.T
        total += block
        count += np.outer(q_has, d_has)
    return total / count.clip(min=1)


def top_k(scores: np.ndarray, k: int, allowed: np.ndarray) -> list[tuple[int, float]]:
    """Los k mejores (fila, score) entre los permitidos, de mayor a menor."""
    scores = np.where(allowed, scores, -np.inf)
    order = np.argsort(-scores, kind="stable")[:k]
    return [(int(i), float(scores[i])) for i in order if np.isfinite(scores[i])]


def _candidate(answer: str, ids: list[str]) -> str | None:
    """Un id de la respuesta: el id tal cual, o el número de imagen ("image 3", "3")."""
    answer = str(answer).strip()
    if answer in ids:
        return answer
    n = answer.lower().removeprefix("image").strip(" .")
    return ids[int(n) - 1] if n.isdigit() and 1 <= int(n) <= len(ids) else None


def _rerank_request(cfg: Config, reranker: str, query: str, items: list[dict]):
    """Lo que el VLM recibe para reordenar `items` y el archivo de la caché de su respuesta."""
    params = cfg.evaluation.rerankers[reranker]
    tmpl = load_prompt(cfg.evaluation.rerank_prompt, cfg.root)
    hits = [as_hit(it, None) for it in items]
    lines = [
        f"image {n}. {h.id}: {h.kind or h.category}, {type_line(h)}, {size_text(h)}"
        for n, h in enumerate(hits, 1)
    ]
    text = tmpl.fill(query=query, n=len(hits), candidates="\n".join(lines))
    key = {"llm": params, "prompt": tmpl.version, "text": text}
    sha = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    return params, hits, text, Path(cfg.cache_dir) / "rerank" / f"{sha}.json"


class CrossEncoder:
    """Un reranker que lee la consulta y el documento juntos (el cross-encoder de la demo de
    Advanced RAG) y les da un score: `head: classification`, un BERT entrenado para eso (el logit
    de relevancia, MS MARCO); `head: yes_no`, un LLM chico (Qwen3-Reranker, de la familia del
    embedder): la probabilidad de "yes" a "¿el documento cumple la consulta?". Los scores quedan en
    caché por consulta y candidatos."""

    PREFIX = (
        "<|im_start|>system\nJudge whether the Document meets the requirements based on the "
        'Query and the Instruct provided. Note that the answer can only be "yes" or "no".'
        "<|im_end|>\n<|im_start|>user\n"
    )
    SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

    def __init__(self, cfg: Config, params: dict):
        self.cfg = cfg
        self.model_id = params["model"]
        self.instruction = params.get("instruction", "")
        self.batch = int(params.get("batch", 8))
        self.head = params.get("head", "yes_no")
        self._loaded = None

    def _load(self):
        if self._loaded is None and self.head == "classification":
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tok = AutoTokenizer.from_pretrained(self.model_id)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_id).eval()
            self._loaded = tok, model, None, None
        if self._loaded is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            tok = AutoTokenizer.from_pretrained(self.model_id, padding_side="left")
            model = AutoModelForCausalLM.from_pretrained(self.model_id).eval()
            yes, no = tok.convert_tokens_to_ids("yes"), tok.convert_tokens_to_ids("no")
            self._loaded = tok, model, yes, no
        return self._loaded

    def scores(self, query: str, docs: list[str]) -> list[float]:
        key = {"model": self.model_id, "instruction": self.instruction, "q": query, "d": docs}
        if self.head == "classification":
            key = {"model": self.model_id, "q": query, "d": docs}
        sha = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
        f = Path(self.cfg.cache_dir) / "rerank_local" / f"{sha}.json"
        if f.exists():
            return json.loads(f.read_text())
        import torch

        tok, model, yes, no = self._load()
        if self.head == "classification":
            with torch.inference_mode():
                enc = tok(
                    [query] * len(docs),
                    docs,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )
                out = model(**enc).logits[:, 0].float().tolist()
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps([round(x, 6) for x in out]))
            return out
        texts = [
            f"{self.PREFIX}<Instruct>: {self.instruction}\n<Query>: {query}\n<Document>: {d}"
            f"{self.SUFFIX}"
            for d in docs
        ]
        out: list[float] = []
        with torch.inference_mode():
            for i in range(0, len(texts), self.batch):
                enc = tok(texts[i : i + self.batch], padding=True, return_tensors="pt")
                logits = model(**enc).logits[:, -1, :]
                pair = torch.stack([logits[:, no], logits[:, yes]], dim=1).float()
                out += torch.softmax(pair, dim=1)[:, 1].tolist()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps([round(x, 6) for x in out]))
        return out


def rerank(cfg: Config, reranker: str, query: str, items: list[dict]) -> list[str]:
    """Los ids de `items` reordenados por el VLM `reranker` mirando sus fotos (pago; la
    respuesta queda en caché: la misma consulta con los mismos candidatos no se paga dos veces)."""
    params, hits, text, f = _rerank_request(cfg, reranker, query, items)
    if f.exists():
        return json.loads(f.read_text())["ranking"]
    content = [image_block(photo(cfg, h), cfg.furnish.photo_max_side) for h in hits]
    a, data = ask(cfg, "eval.rerank", [*content, text_block(text)], params)
    ids = [h.id for h in hits]
    got = [i for i in dict.fromkeys(_candidate(x, ids) for x in data.get("ranking") or []) if i]
    if not got:
        raise ProviderError(f"eval.rerank: no ranking in the answer: {a.text[:200]!r}")
    ranking = got + [i for i in ids if i not in got]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"ranking": ranking, "model": a.model, "cost_usd": a.cost_usd}))
    return ranking


def rank(
    cfg: Config,
    index: Index,
    method: Method,
    searches: list[Search],
    k: int,
    workers: int = 8,
    estimate: bool = False,
) -> list[dict]:
    """El top-k de cada búsqueda con un método (los vectores se cachean; con `store: chroma`,
    una colección de ChromaDB en memoria con los vectores de ese embedder y ese texto). Con
    `estimate`, en un método con reranking, solo las filas cuyo reranking no está en la caché
    (lo que costaría correrlo)."""
    catalog = {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    texts = [
        without_lines(TEXTS[method.text](it, catalog[it["id"]]), method.drop) for it in index.items
    ]
    query_texts = [without_lines(QUERIES[method.query](s), method.drop) for s in searches]

    def embed(xs: list[str], name: str = method.embedder) -> np.ndarray:
        embedder = get_embedder(name, cfg)
        return vectors_cached(xs, embedder, cfg, ledger_for(cfg.budget, embedder.account))[0]

    def score_matrix(name: str) -> np.ndarray:
        """(consultas, productos): el puntaje de cada producto con un buscador."""
        if name == "bm25":
            return BM25(texts).scores(query_texts)
        params = cfg.rag.embedders.get(name) or {}
        if params.get("kind") == "image_text":  # la consulta corta contra la foto del producto
            model = ImageTextEmbedder(params, name, Path(cfg.cache_dir))
            photos = [cfg.path(it["photos"][0]) for it in index.items]
            queries = model.embed_texts([visual_query(q) for q in query_texts])
            return queries @ model.embed_images(photos).T
        docs, queries = embed(texts, name), embed(query_texts, name)
        if method.dim:
            docs, queries = truncate(docs, method.dim), truncate(queries, method.dim)
        return queries @ docs.T

    def vectorless(name: str) -> bool:
        return name == "bm25" or (cfg.rag.embedders.get(name) or {}).get("kind") == "image_text"

    chunked = fused = None
    if method.chunks != "whole":  # partida: búsqueda exacta sobre los chunks
        chunked = chunk_scores(method, texts, query_texts, embed)
        docs = queries = None
    elif method.fusion or vectorless(method.embedder):  # híbrida: exacta sobre los puntajes
        fused = [score_matrix(name) for name in method.scorers]
        docs = queries = None
    else:
        docs, queries = embed(texts), embed(query_texts)
        if method.dim:
            docs, queries = truncate(docs, method.dim), truncate(queries, method.dim)
        ranked = Index(index.path, index.meta, index.items, docs)
        if method.store == "chroma":
            name = f"eval-{method.embedder}-{method.text}-{method.dim or 'full'}"
            ranked.store = ChromaStore(None, name)
            ranked.store.create(index.items, docs, cfg.rag.hnsw)
    rows = []
    for n, s in enumerate(searches):
        f = filters_for(method, s.kind)
        allowed = np.array([f.allows(it) for it in index.items], bool)
        if chunked is not None:
            hits = top_k(chunked[n], k, allowed)
        elif fused is not None:
            hits = top_k(fuse([m[n] for m in fused], allowed, method.fusion_rule), k, allowed)
        elif method.store == "exact":
            hits = ranked.nearest(queries[n], k, allowed)
        else:
            hits = ranked.query(queries[n], k, f.where())
        ids = [index.items[i]["id"] for i, _ in hits]
        rows.append(
            {
                **asdict(s),
                "method": method.name,
                "ranked": ids,
                "scores": [round(sc, 4) for _, sc in hits],
                "universe": int(allowed.sum()),
                "universe_relevant": sum(
                    1
                    for it, ok in zip(index.items, allowed, strict=True)
                    if ok and it["id"] in s.relevant
                ),
            }
        )
    if method.rerank:
        by_id = {it["id"]: it for it in index.items}
        top = cfg.evaluation.rerank_top
        if estimate:  # sin pagar: cuántas respuestas faltan en la caché
            return [
                r
                for r in rows
                if r["relevant"]
                and not _rerank_request(
                    cfg, method.rerank, r["query"], [by_id[i] for i in r["ranked"][:top]]
                )[3].exists()
            ]

        local = (
            CrossEncoder(cfg, cfg.evaluation.rerankers[method.rerank])
            if method.rerank in LOCAL_RERANKERS
            else None
        )

        def one(row: dict) -> list[str]:
            if not row["relevant"]:  # no entra en las métricas: no se paga
                return row["ranked"]
            head_ids = row["ranked"][:top]
            if local is not None:
                sc = local.scores(row["query"], [by_id[i]["description"] for i in head_ids])
                head = [i for _, i in sorted(zip(sc, head_ids, strict=True), key=lambda t: -t[0])]
            else:
                head = rerank(cfg, method.rerank, row["query"], [by_id[i] for i in head_ids])
            return head + row["ranked"][top:]

        with ThreadPoolExecutor(1 if local else max(1, workers)) as pool:
            for row, new in zip(rows, pool.map(one, rows), strict=True):
                score = dict(zip(row["ranked"], row["scores"], strict=True))
                row["ranked"], row["scores"] = new, [score[i] for i in new]
    for row in rows:
        row["rank"] = first_relevant_rank(row["ranked"], row["relevant"])
        row["rank_any"] = first_relevant_rank(row["ranked"], row["relevant_any"])
        # El mismo modelo en otra medida u otro color (la familia: mismo nombre y mismo grupo)
        # también cuenta: ¿el error es otro mueble, o una variante del correcto?
        families = {family(catalog[i]) for i in row["relevant"]}
        row["rank_family"] = next(
            (n for n, i in enumerate(row["ranked"], 1) if family(catalog[i]) in families), None
        )
    return rows


def metrics(rows: list[dict], n_boot: int = 1000, seed: int = 0) -> dict[str, Any]:
    answerable = [r for r in rows if r["relevant"]]
    groups = [r["room_id"] for r in answerable]
    out: dict[str, Any] = {"searches": len(rows), "answerable": len(answerable)}
    for k in KS:
        vals = [hit_at_k(r["rank"], k) for r in answerable]
        out[f"hit@{k}"] = round(float(np.mean(vals)), 4)
        out[f"hit@{k}_ic95"] = [round(v, 4) for v in bootstrap_ci(vals, groups, n_boot, seed)]
    rr = [reciprocal_rank(r["rank"], max(KS)) for r in answerable]
    out["mrr@10"] = round(float(np.mean(rr)), 4)
    out["mrr@10_ic95"] = [round(v, 4) for v in bootstrap_ci(rr, groups, n_boot, seed)]
    # Las de la clase 11: context precision@K (RAGAS) y NDCG@K (sistemas de recomendación).
    for name, fn in (("context_precision@10", context_precision_at_k), ("ndcg@10", ndcg_at_k)):
        vals = [fn(r["ranked"], r["relevant"], 10) for r in answerable]
        out[name] = round(float(np.mean(vals)), 4)
        out[f"{name}_ic95"] = [round(v, 4) for v in bootstrap_ci(vals, groups, n_boot, seed)]
    # Context recall@K por ambiente: de sus productos anotados que buscan sus consultas, cuántos
    # están en el contexto (la unión de los top-K de sus consultas). K=3 es lo que el flujo le
    # pasa al LLM por pieza (furnish.candidates); K=10, lo que mira el reranker.
    for k in (3, 10):
        gt: dict[str, set] = defaultdict(set)
        ctx: dict[str, set] = defaultdict(set)
        for r in rows:
            gt[r["room_id"]].update(r["relevant"])
            ctx[r["room_id"]].update(r["ranked"][:k])
        rooms = [room for room in gt if gt[room]]
        vals = [len(gt[room] & ctx[room]) / len(gt[room]) for room in rooms]
        out[f"context_recall@{k}"] = round(float(np.mean(vals)), 4) if vals else None
        if vals:
            out[f"context_recall@{k}_ic95"] = [
                round(v, 4) for v in bootstrap_ci(vals, rooms, n_boot, seed)
            ]
    # La curva de hit@k: cuántos candidatos hacen falta para que el correcto llegue al reranker.
    out["curva_hit@k"] = {
        str(k): round(float(np.mean([hit_at_k(r["rank"], k) for r in answerable])), 4)
        for k in CURVE
    }
    # ¿El score dice cuándo el primero está bien? (para avisar "no encontré algo así")
    firsts = [(r["scores"][0], r["rank"] == 1) for r in answerable if r["scores"]]
    if firsts:
        scores, ok = zip(*firsts, strict=True)
        out["confianza_auroc"] = round(auroc(scores, ok), 4)
        out["confianza_umbral_f1"] = {
            k: round(v, 4) for k, v in best_f1_threshold(scores, ok).items()
        }
    # Por familia: acierta si trae el producto anotado o una variante del mismo modelo.
    for k in (1, 5):
        vals = [hit_at_k(r.get("rank_family"), k) for r in answerable]
        out[f"familia_hit@{k}"] = round(float(np.mean(vals)), 4)
        out[f"familia_hit@{k}_ic95"] = [
            round(v, 4) for v in bootstrap_ci(vals, groups, n_boot, seed)
        ]
    out["literal_hit@10"] = round(
        float(np.mean([hit_at_k(r["rank_any"], 10) for r in rows if r["relevant_any"]])), 4
    )
    out["azar_hit@1"] = round(
        float(
            np.mean([random_hit_at_k(r["universe"], r["universe_relevant"], 1) for r in answerable])
        ),
        4,
    )
    out["azar_hit@10"] = round(
        float(
            np.mean(
                [random_hit_at_k(r["universe"], r["universe_relevant"], 10) for r in answerable]
            )
        ),
        4,
    )
    out["azar_mrr@10"] = round(
        float(np.mean([random_mrr(r["universe"], r["universe_relevant"], 10) for r in answerable])),
        4,
    )
    # Recall por ítem: cada SKU anotado (del tipo de alguna consulta del ambiente), ¿alguna
    # consulta del ambiente lo trajo en el top-k?
    best: dict[tuple[str, str], int | None] = {}
    for r in rows:
        for sku in r["relevant"]:
            pos = r["ranked"].index(sku) + 1 if sku in r["ranked"] else None
            key = (r["room_id"], sku)
            prev = best.get(key)
            best[key] = pos if prev is None else (prev if pos is None else min(prev, pos))
    item_groups = [room for room, _ in best]
    for k in (1, 10):
        vals = [hit_at_k(v, k) for v in best.values()]
        out[f"recall_item@{k}"] = round(float(np.mean(vals)), 4) if vals else None
        if vals:
            out[f"recall_item@{k}_ic95"] = [
                round(v, 4) for v in bootstrap_ci(vals, item_groups, n_boot, seed)
            ]
    by_kind: dict[str, list[float]] = defaultdict(list)
    for r in answerable:
        by_kind[KIND_TO_TP[r["kind"]]].append(hit_at_k(r["rank"], 1))
    out["hit@1_por_categoria"] = {
        t: round(float(np.mean(v)), 4) for t, v in sorted(by_kind.items())
    }
    out["consultas_por_categoria"] = dict(Counter(KIND_TO_TP[r["kind"]] for r in answerable))
    by_pass: dict[str, list[dict]] = defaultdict(list)
    for r in answerable:
        by_pass[r.get("prompt", Search.prompt)].append(r)
    out["por_pasada"] = {
        name: {
            "consultas": len(rs),
            "hit@1": round(float(np.mean([hit_at_k(r["rank"], 1) for r in rs])), 4),
            "hit@10": round(float(np.mean([hit_at_k(r["rank"], 10) for r in rs])), 4),
            "mrr@10": round(float(np.mean([reciprocal_rank(r["rank"], max(KS)) for r in rs])), 4),
        }
        for name, rs in sorted(by_pass.items())
    }
    return out


def paired_difference(rows: list[dict], base: list[dict], n_boot: int = 1000) -> dict[str, Any]:
    """Un método contra otro sobre las mismas consultas: la diferencia media de hit@1, hit@5,
    hit@10 y MRR@10 y su IC 95% (bootstrap de ambientes sobre las diferencias). Un intervalo que
    no toca el cero: la diferencia no es ruido del muestreo."""
    pairs = [(r, b) for r, b in zip(rows, base, strict=True) if r["relevant"]]
    groups = [r["room_id"] for r, _ in pairs]
    out: dict[str, Any] = {}
    for name, fn in (
        ("hit@1", lambda r: hit_at_k(r["rank"], 1)),
        ("hit@5", lambda r: hit_at_k(r["rank"], 5)),
        ("hit@10", lambda r: hit_at_k(r["rank"], 10)),
        ("mrr@10", lambda r: reciprocal_rank(r["rank"], max(KS))),
        ("familia_hit@1", lambda r: hit_at_k(r.get("rank_family"), 1)),
    ):
        diffs = [fn(r) - fn(b) for r, b in pairs]
        out[name] = round(float(np.mean(diffs)), 4)
        out[f"{name}_ic95"] = [round(v, 4) for v in bootstrap_ci(diffs, groups, n_boot)]
    return out


def estimate_reranks(
    cfg: Config, queries_path: Path, raw_dir: Path, methods: list[Method]
) -> dict[str, tuple[int, float]]:
    """Por método pago: cuántas llamadas al VLM faltan en la caché y cuánto costarían (según el
    estimate_usd del modelo). No llama a ninguna API."""
    index = ensure_index(cfg)
    catalog_ids = {p.id: product_group(p) for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    searches = load_searches(queries_path, raw_dir, catalog_ids)
    out = {}
    for m in methods:
        if m.paid:
            n = len(rank(cfg, index, m, searches, DEPTH, estimate=True))
            params = cfg.evaluation.rerankers[m.rerank]
            usd = params["models"][params["model"]].get("estimate_usd", 0.0)
            out[m.name] = (n, round(n * usd, 2))
    return out


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def run_eval(
    cfg: Config,
    queries_path: Path,
    raw_dir: Path,
    out_root: Path,
    methods: list[Method],
    name: str = "texto",
    n_boot: int = 1000,
    replica: str | None = None,
) -> Path:
    """Corre todos los métodos y guarda una carpeta con config, métricas y rankings. `replica`:
    las consultas son otra escritura independiente de las mismas (reproducibilidad)."""
    index = ensure_index(cfg)  # las descripciones: el describer `written`
    catalog_ids = {p.id: product_group(p) for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    searches = load_searches(queries_path, raw_dir, catalog_ids)
    started = time.strftime("%Y%m%d-%H%M%S")
    results: dict[str, Any] = {}
    rankings: list[dict] = []
    base: list[dict] | None = None  # las filas del primer método: contra él se compara el resto
    previous: list[dict] | None = None  # y las del anterior: el camino incremental
    for m in methods:  # todo antes de escribir: una corrida que falla no deja nada a medias
        t0 = time.perf_counter()
        rows = rank(cfg, index, m, searches, DEPTH)
        rankings += [  # los primeros max(KS): la curva hasta DEPTH ya está en las métricas
            {**r, "ranked": r["ranked"][: max(KS)], "scores": r["scores"][: max(KS)]} for r in rows
        ]
        results[m.name] = {
            "method": asdict(m),
            **metrics(rows, n_boot),
            "segundos": round(time.perf_counter() - t0, 1),
        }
        if base is None:
            base = rows
        else:
            results[m.name]["vs_base"] = {
                "base": methods[0].name,
                **paired_difference(rows, base, n_boot),
            }
            results[m.name]["vs_anterior"] = paired_difference(rows, previous, n_boot)
        previous = rows
    meta = {
        "name": name,
        "queries": str(queries_path),
        "queries_meta": json.loads(Path(queries_path).read_text()).get("_meta"),
        "rooms": len({s.room_id for s in searches}),
        "replica": replica,
        "catalog": cfg.rag.catalog,
        "index": index.meta,
        "embedders": {
            e: cfg.rag.embedders.get(e, {"kind": e})  # bm25 no es de rag.embedders
            for e in sorted({name for m in methods for name in m.scorers})
        },
        "hnsw": cfg.rag.hnsw,
        "rerankers": {
            r: cfg.evaluation.rerankers[r] for r in sorted({m.rerank for m in methods if m.rerank})
        },
        "git_commit": git_commit(),
        "python": platform.python_version(),
    }
    run_dir = Path(out_root) / f"{started}_{name}"
    run_dir.mkdir(parents=True)
    with gzip.open(run_dir / "rankings.jsonl.gz", "wt") as fh:  # cientos de miles de ids
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rankings)
    (run_dir / "corrida.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str)
    )
    (run_dir / "metricas.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    return run_dir
