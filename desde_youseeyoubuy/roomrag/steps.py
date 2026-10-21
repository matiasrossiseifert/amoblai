"""The furnishing steps (flow.py runs them in order, each once, into the run folder):

    plan      the LLM reads the room photo and the request as an interior designer: which pieces,
              and for each its kinds (a filter), its size limits and the ideal product written in
              the catalog's eight lines (the query)
    retrieve  the catalog search for each piece: `furnish.candidates` products
    choose    the LLM sees the room and every candidate's photo and picks one per piece: the best
              combination, not the best of each alone
    scene     the LLM writes the image model's prompt (where each product goes, how it faces)
    generate  the image model (generate.py) puts the products in the room

Every LLM call goes through the paid gate and the spend ledger. Other photos of the same room
(`views`, other angles) go to plan, choose and scene after the step's own images, only for the
LLM to understand the room; the room photo is still image 1, and the image model gets it alone.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .budget import check_spend, ledger_for
from .config import Config
from .filters import Filters
from .generate import get_generator
from .http import ProviderError
from .index import build_index, index_is_current, open_index
from .kinds import KINDS, kinds_text
from .llm import Answer, image_block, make_llm, parse_json, text_block
from .prompts import PromptTemplate, load_prompt
from .search import Hit, search


def ask(cfg: Config, step: str, content: list[dict]) -> tuple[Answer, dict]:
    """One LLM call: the paid gate, the call, the ledger; (answer, its JSON)."""
    llm = make_llm(cfg.furnish.llm, "llm")
    ledger = ledger_for(cfg.budget, llm.account)
    check_spend(
        ledger,
        llm.estimate_cost(),
        paid=llm.paid,
        allow_paid=cfg.budget.allow_paid or step in cfg.budget.allow_paid_steps,
        what=f"{step} ({llm.model})",
    )
    a = llm.ask(content)
    ledger.record(
        step=step,
        provider=llm.account,
        model=a.model,
        cost_usd=a.cost_usd,
        cost_source=a.cost_source,
        cached=False,
    )
    if not a.complete:
        raise ProviderError(f"{step}: the LLM stopped early ({a.meta.get('stop_reason')})")
    return a, parse_json(a.text)


def answer_record(a: Answer, prompt: PromptTemplate, data: dict) -> dict:
    return {
        "answer": data,
        "model": a.model,
        "cost_usd": a.cost_usd,
        "prompt": prompt.version,
        "meta": a.meta,
        "text": a.text,
    }


def photo(cfg: Config, hit: Hit) -> Path:
    return cfg.path(hit.photos[0])


def view_blocks(cfg: Config, views: Sequence[Path], first: int, for_scene: bool = False) -> list:
    """The other photos of the room, numbered from `first`, and what they are for. None: []."""
    if not views:
        return []
    last = first + len(views) - 1
    which = (
        f"Image {first} is another photo"
        if first == last
        else f"Images {first} to {last} are other photos"
    )
    note = (
        f"{which} of this same room, from another angle, only to understand the room: its size, "
        "its layout and what image 1 leaves out of frame. Image 1 is the photo that gets the "
        "furniture: place everything in image 1, as its camera sees the room."
    )
    if for_scene:
        note += (
            " The image model will get image 1 and the products' photos only: do not mention"
            " these other photos in its prompt."
        )
    blocks = [image_block(v, cfg.furnish.photo_max_side) for v in views]
    return [*blocks, text_block(note)]


def with_views(rec: dict, views: Sequence[Path]) -> dict:
    if views:
        rec["views"] = len(views)
    return rec


# plan ------------------------------------------------------------------------------------------


def check_kinds(piece: dict) -> list[str]:
    """Keeps the piece's kinds that exist (any case), drops the others and returns them: an
    unknown kind would filter out the whole catalog."""
    known = {k.lower(): k for k in KINDS}
    asked = piece.get("kinds") or []
    piece["kinds"] = [known[k.lower()] for k in asked if k.lower() in known]
    return [k for k in asked if k.lower() not in known]


def plan(cfg: Config, room_photo: Path, request: str, views: Sequence[Path] = ()) -> dict:
    """Which pieces the request needs in this room, and one search for each."""
    tmpl = load_prompt(cfg.furnish.query_prompt, cfg.root)
    content = [
        image_block(room_photo, cfg.furnish.photo_max_side),
        *view_blocks(cfg, views, 2),
        text_block(tmpl.fill(request=request, kinds=kinds_text())),
    ]
    a, data = ask(cfg, "furnish.plan", content)
    if not data.get("pieces"):
        raise ProviderError("furnish.plan: no pieces in the answer")
    rec = answer_record(a, tmpl, data)
    rec["unknown_kinds"] = [k for p in data["pieces"] for k in check_kinds(p)]
    return with_views(rec, views)


# retrieve --------------------------------------------------------------------------------------


def find_candidates(cfg: Config, piece: dict) -> list[Hit]:
    """The catalog search for one piece: its filters, then its query, `furnish.candidates` hits.
    The size limits get `furnish.size_slack` more. With two kinds, each gets its share of the
    candidates, so the one nearer the query's words can't crowd out the other. No kinds: the
    whole catalog, by the query alone."""
    if not index_is_current(cfg):
        build_index(cfg, log=lambda _: None)
    index = open_index(cfg)
    kinds = piece.get("kinds") or []
    most = {
        f"max_{a}_cm": round(v * (1 + cfg.furnish.size_slack), 1)
        for a in ("width", "depth", "height")
        if (v := piece.get(f"max_{a}_cm")) is not None
    }
    hits: list[Hit] = []
    for i, group in enumerate([[k] for k in kinds] or [[]]):
        filters = Filters(categories=piece.get("categories") or [], kinds=group, **most)
        c = cfg.model_copy(deep=True)
        share = cfg.furnish.candidates // max(1, len(kinds))
        c.rag.top_k = cfg.furnish.candidates - len(hits) if i == len(kinds) - 1 else share
        hits += search(index, piece["query"], filters, c)
    return sorted(hits, key=lambda h: -(h.score or 0.0))


def type_line(hit: Hit) -> str:
    first = hit.description.splitlines()[0] if hit.description else ""
    return first.removeprefix("Type:").strip() or hit.category


def contact_sheet(cfg: Config, hits: list[Hit], out: Path, first: int = 1, cell: int = 300) -> None:
    """The candidates side by side, numbered as the LLM sees them."""
    cols = min(5, len(hits))
    rows = (len(hits) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 44)), "white")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(13)
    for i, h in enumerate(hits):
        im = Image.open(photo(cfg, h)).convert("RGB")
        im.thumbnail((cell - 10, cell - 10))
        x, y = (i % cols) * cell, (i // cols) * (cell + 44)
        sheet.paste(im, (x + (cell - im.width) // 2, y + 5))
        d.text((x + 6, y + cell + 2), f"{first + i}. {h.id}", fill=(30, 30, 30), font=font)
        d.text((x + 6, y + cell + 20), type_line(h)[:38], fill=(110, 110, 110), font=font)
    sheet.save(out, quality=88)


def retrieve(cfg: Config, pieces: list[dict], out: Path | None = None) -> dict:
    """The candidates of each piece (`spec`: the plan's piece); a piece the catalog has nothing
    for goes to `empty` and the flow goes on without it. With `out`, a contact sheet per piece
    (2_candidates.jpg, 2_candidates_2.jpg...)."""
    found, empty = [], []
    for piece in pieces:
        hits = find_candidates(cfg, piece)
        if not hits:
            empty.append(piece["piece"])
            continue
        if out is not None:
            n = len(found) + 1
            contact_sheet(cfg, hits, out / f"2_candidates{'' if n == 1 else f'_{n}'}.jpg")
        found.append(
            {"piece": piece["piece"], "spec": piece, "candidates": [asdict(h) for h in hits]}
        )
    if not found:
        raise ProviderError(f"retrieve: the catalog has nothing for {empty}")
    return {"pieces": found, "empty": empty}


# choose ----------------------------------------------------------------------------------------


def _size(h: Hit) -> str:
    """The measures the catalog has (a rug or a table top: width and depth only)."""
    d = h.dimensions_cm or {}
    words = (("width", "wide"), ("depth", "deep"), ("height", "high"))
    return ", ".join(f"{d[a]:.0f} cm {w}" for a, w in words if d.get(a)) or "size unknown"


def choose(
    cfg: Config,
    room_photo: Path,
    request: str,
    found: list[tuple[dict, list[Hit]]],
    views: Sequence[Path] = (),
) -> dict:
    """The room photo, then every candidate's photo, piece by piece; one product per piece."""
    tmpl = load_prompt(cfg.furnish.choose_prompt, cfg.root)
    lines, content, n = [], [image_block(room_photo, cfg.furnish.photo_max_side)], 1
    for k, (piece, hits) in enumerate(found, 1):
        lines.append(f"Piece {k}: {piece['piece']}")
        for h in hits:
            n += 1
            lines.append(f"  image {n}. {h.id}: {h.kind or h.category}, {type_line(h)}, {_size(h)}")
            content.append(image_block(photo(cfg, h), cfg.furnish.photo_max_side))
    text = tmpl.fill(request=request, pieces=len(found), images=n, candidates="\n".join(lines))
    content += view_blocks(cfg, views, n + 1)
    content.append(text_block(text))
    a, data = ask(cfg, "furnish.choose", content)
    choices = data.get("choices") or []
    if len(choices) != len(found):
        raise ProviderError(f"furnish.choose: {len(choices)} choices for {len(found)} pieces")
    for (piece, hits), c in zip(found, choices, strict=True):
        if c.get("id") not in {h.id for h in hits}:
            raise ProviderError(
                f"furnish.choose: {c.get('id')!r} is not a candidate for {piece['piece']!r}"
            )
    return with_views(answer_record(a, tmpl, data), views)


def chosen(found: dict, choice: dict) -> list[Hit]:
    """The chosen product of each piece, from the retrieve and choose files."""
    out = []
    for p, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
        out.append(next(Hit(**h) for h in p["candidates"] if h["id"] == c["id"]))
    return out


# scene and generate ----------------------------------------------------------------------------


def scene(
    cfg: Config,
    room_photo: Path,
    request: str,
    room: str,
    picks: list[tuple[dict, Hit]],
    views: Sequence[Path] = (),
) -> dict:
    """The LLM writes the image model's prompt from the room, each piece and its chosen
    product's photo: where each one goes and how it faces."""
    tmpl = load_prompt(cfg.furnish.scene_prompt, cfg.root)
    lines = [
        f"image {i + 2}. {h.id}: {type_line(h)}, {_size(h)}; it is the piece: {p['piece']}"
        for i, (p, h) in enumerate(picks)
    ]
    content = [image_block(room_photo, cfg.furnish.photo_max_side)]
    content += [image_block(photo(cfg, h), cfg.furnish.photo_max_side) for _, h in picks]
    content += view_blocks(cfg, views, len(picks) + 2, for_scene=True)
    content.append(text_block(tmpl.fill(request=request, room=room, products="\n".join(lines))))
    a, data = ask(cfg, "furnish.scene", content)
    if not data.get("prompt"):
        raise ProviderError("furnish.scene: no prompt in the answer")
    return with_views(answer_record(a, tmpl, data), views)


def generate(cfg: Config, prompt: str, room_photo: Path, picks: list[Hit], out: Path) -> dict:
    """The image model gets the room photo, the chosen products' photos (in that order) and the
    prompt. `pending`: the image is not there yet (the manual generator waits for a person)."""
    gen = get_generator(cfg.furnish.generator, cfg)
    images = [room_photo, *(photo(cfg, h) for h in picks)]
    ledger = ledger_for(cfg.budget, gen.account)
    check_spend(
        ledger,
        gen.estimate_cost(images),
        paid=gen.paid,
        allow_paid=cfg.budget.allow_paid,
        what=f"furnish.generate ({gen.name})",
    )
    g = gen.generate(prompt, images, out)
    if gen.paid:
        ledger.record(
            step="furnish.generate",
            provider=gen.name,
            model=g.model,
            cost_usd=g.cost_usd,
            cost_source=g.cost_source,
            cached=False,
        )
    return {
        "generator": gen.name,
        "image": g.image and str(Path(g.image).name),
        "pending": g.image is None,
        "model": g.model,
        "cost_usd": g.cost_usd,
        "meta": g.meta,
    }


def write(path: Path, data: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))
    return data
