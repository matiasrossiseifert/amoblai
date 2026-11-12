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
import shutil
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from amoblai.catalog.kinds import KINDS, kinds_text
from amoblai.config import Config
from amoblai.furnish.generate import get_generator
from amoblai.furnish.llm import Answer, image_block, make_llm, parse_json, text_block
from amoblai.furnish.room import preservation
from amoblai.infra.budget import BudgetExceeded, check_spend, ledger_for
from amoblai.infra.http import ProviderError
from amoblai.prompts import PromptTemplate, load_prompt
from amoblai.rag.filters import Filters
from amoblai.rag.index import Index, ensure_index
from amoblai.rag.search import Hit, as_hit, search


def ask(
    cfg: Config, step: str, content: list[dict], llm_params: dict | None = None
) -> tuple[Answer, dict]:
    """One LLM call (`furnish.llm`, or `llm_params`): the paid gate, the call, the ledger;
    (answer, its JSON)."""
    llm = make_llm(llm_params or cfg.furnish.llm, "llm")
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
        text_block(
            tmpl.fill(request=request, kinds=kinds_text(), max_pieces=cfg.furnish.max_pieces)
        ),
    ]
    a, data = ask(cfg, "furnish.plan", content)
    if not data.get("pieces"):
        raise ProviderError("furnish.plan: no pieces in the answer")
    rec = answer_record(a, tmpl, data)
    rec["unknown_kinds"] = [k for p in data["pieces"] for k in check_kinds(p)]
    return with_views(rec, views)


# retrieve --------------------------------------------------------------------------------------


def find_candidates(cfg: Config, piece: dict, index: Index | None = None) -> list[Hit]:
    """The catalog search for one piece: its filters, then its query, `furnish.candidates` hits.
    The size limits get `furnish.size_slack` more. With two kinds, each gets its share of the
    candidates, so the one nearer the query's words can't crowd out the other. No kinds: the
    whole catalog, by the query alone. `index`: the open index (retrieve opens it once)."""
    index = index or ensure_index(cfg)
    kinds = piece.get("kinds") or []
    most = {
        f"max_{a}_cm": round(v * (1 + cfg.furnish.size_slack), 1)
        for a in ("width", "depth", "height")
        if cfg.furnish.size_filter and (v := piece.get(f"max_{a}_cm")) is not None
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
    index = ensure_index(cfg)  # once for every piece
    for piece in pieces:
        hits = find_candidates(cfg, piece, index)
        if not hits:
            empty.append(piece["piece"])
            continue
        if out is not None and cfg.rag.mode != "whole_catalog":  # hundreds: no sheet
            n = len(found) + 1
            contact_sheet(cfg, hits, out / f"2_candidates{'' if n == 1 else f'_{n}'}.jpg")
        found.append(
            {"piece": piece["piece"], "spec": piece, "candidates": [asdict(h) for h in hits]}
        )
    if not found:
        raise ProviderError(f"retrieve: the catalog has nothing for {empty}")
    return {"pieces": found, "empty": empty}


# choose ----------------------------------------------------------------------------------------


def size_text(h: Hit) -> str:
    """The measures the catalog has (a rug or a table top: width and depth only)."""
    d = h.dimensions_cm or {}
    words = (("width", "wide"), ("depth", "deep"), ("height", "high"))
    return ", ".join(f"{d[a]:.0f} cm {w}" for a, w in words if d.get(a)) or "size unknown"


def catalog_text(items: Sequence[dict]) -> str:
    """Every product of the index as text, grouped by kind: what goes whole in the prompt when
    there is no search (rag.mode whole_catalog). The same bytes for the same index, so the
    block can be cached as a prompt prefix."""
    by_kind: dict[str, list[Hit]] = {}
    for it in items:
        h = as_hit(it, None)
        by_kind.setdefault(h.kind or h.category or "other", []).append(h)
    out = [
        f"CATALOG: {len(items)} products, grouped by kind. "
        "Each product: [id] and size, then its description."
    ]
    for kind in sorted(by_kind):
        out.append(f"\n## {kind} ({len(by_kind[kind])} products)")
        out += [f"\n[{h.id}] {size_text(h)}\n{h.description}" for h in by_kind[kind]]
    return "\n".join(out)


def choose(
    cfg: Config,
    room_photo: Path,
    request: str,
    found: list[tuple[dict, list[Hit]]],
    views: Sequence[Path] = (),
) -> dict:
    """The room photo, then every candidate's photo, piece by piece; one product per piece, and
    how many units of it (`quantity`, 1 if the prompt doesn't ask: 0 leaves the piece out).

    With rag.mode whole_catalog there is no search to choose from: the whole catalog goes first,
    as text (cached: it is the same for every request), then the room photo, and each piece
    lists the ids that pass its hard filters. No candidate photos: the catalog's don't fit."""
    if cfg.rag.mode == "whole_catalog":
        tmpl = load_prompt(cfg.furnish.choose_catalog_prompt, cfg.root)
        lines = [
            f"Piece {k}: {piece['piece']}\n  ids: {', '.join(h.id for h in hits)}"
            for k, (piece, hits) in enumerate(found, 1)
        ]
        text = tmpl.fill(request=request, pieces=len(found), candidates="\n".join(lines))
        content = [
            text_block(catalog_text(ensure_index(cfg).items), cfg.furnish.catalog_cache),
            image_block(room_photo, cfg.furnish.photo_max_side),
        ]
        n, step = 1, "furnish.choose_catalog"  # its own line in the ledger: not the flow's cost
    else:
        step = "furnish.choose"
        tmpl = load_prompt(cfg.furnish.choose_prompt, cfg.root)
        lines, content, n = [], [image_block(room_photo, cfg.furnish.photo_max_side)], 1
        for k, (piece, hits) in enumerate(found, 1):
            lines.append(f"Piece {k}: {piece['piece']}")
            for h in hits:
                n += 1
                lines.append(
                    f"  image {n}. {h.id}: {h.kind or h.category}, {type_line(h)}, {size_text(h)}"
                )
                content.append(image_block(photo(cfg, h), cfg.furnish.photo_max_side))
        text = tmpl.fill(request=request, pieces=len(found), images=n, candidates="\n".join(lines))
    content += view_blocks(cfg, views, n + 1)
    content.append(text_block(text))
    a, data = ask(cfg, step, content)
    choices = data.get("choices") or []
    if len(choices) != len(found):
        raise ProviderError(f"furnish.choose: {len(choices)} choices for {len(found)} pieces")
    for (piece, hits), c in zip(found, choices, strict=True):
        c["quantity"] = quantity(c)
        if c["quantity"] and c.get("id") not in {h.id for h in hits}:
            raise ProviderError(
                f"furnish.choose: {c.get('id')!r} is not a candidate for {piece['piece']!r}"
            )
    return with_views(answer_record(a, tmpl, data), views)


def quantity(choice: dict) -> int:
    """How many units of a choice go in the room (1 when the answer doesn't say)."""
    try:
        return max(0, int(choice.get("quantity", 1)))
    except (TypeError, ValueError):
        return 1


def picks(found: dict, choice: dict) -> list[tuple[dict, Hit]]:
    """Each piece that goes in the room (quantity > 0) with its chosen product, from the
    retrieve and choose files; the piece carries its `quantity`."""
    out = []
    for p, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
        if quantity(c):
            hit = next(Hit(**h) for h in p["candidates"] if h["id"] == c["id"])
            out.append(({**p["spec"], "quantity": quantity(c)}, hit))
    return out


def chosen(found: dict, choice: dict) -> list[Hit]:
    """The chosen product of each piece that goes in the room, in order."""
    return [h for _, h in picks(found, choice)]


# scene and generate ----------------------------------------------------------------------------


def units(piece: dict) -> str:
    """What tells the image model a piece goes more than once (", 2 units"), or nothing."""
    q = piece.get("quantity", 1)
    return f", {q} units" if q > 1 else ""


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
    if not cfg.furnish.scene_llm:  # the template alone: the image model places the products
        products = "\n".join(
            f"image {i + 2}: {type_line(h)}, {size_text(h)}{units(p)}"
            for i, (p, h) in enumerate(picks)
        )
        text = tmpl.fill(request=request, products=products, last=len(picks) + 1)
        return {"answer": {"prompt": text}, "model": None, "cost_usd": 0.0, "prompt": tmpl.version}
    lines = [
        f"image {i + 2}. {h.id}: {type_line(h)}, {size_text(h)}{units(p)}; it is the piece: "
        f"{p['piece']}"
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


def room_kept(cfg: Config, room_photo: Path, image: Path) -> dict:
    """Is the image still the room of the photo? SIFT + RANSAC between the two
    (evaluation/image.py): enough points of the original found again, and the camera still."""
    rc = cfg.furnish.room_check
    m = preservation(Image.open(room_photo), Image.open(image), [])
    shift = m.get("sift_desplazamiento_mediano")
    ok = (
        m.get("sift_inliers", 0) >= rc["min_inliers"]
        and shift is not None
        and (shift <= rc["max_shift"])
    )
    keys = ("ssim", "sift_inliers", "sift_reencontrados", "sift_desplazamiento_mediano")
    return {"ok": bool(ok), **{k: m.get(k) for k in keys}}


def generate(cfg: Config, prompt: str, room_photo: Path, picks: list[Hit], out: Path) -> dict:
    """The image model gets the room photo, the chosen products' photos (in that order) and the
    prompt. `pending`: the image is not there yet (the manual generator waits for a person).
    A paid image that is no longer the user's room (room_kept) is kept aside as
    final_intento_N.png and the model tries again (furnish.room_check): the first image that
    keeps the room wins, or, if none does, the one that keeps it best."""
    gen = get_generator(cfg.furnish.generator, cfg)
    images = [room_photo, *(photo(cfg, h) for h in picks)]
    ledger = ledger_for(cfg.budget, gen.account)
    tries = max(1, int(cfg.furnish.room_check["attempts"])) if gen.paid else 1
    attempts: list[dict] = []
    g = None
    for n in range(1, tries + 1):
        try:
            check_spend(
                ledger,
                gen.estimate_cost(images),
                paid=gen.paid,
                allow_paid=cfg.budget.allow_paid,
                what=f"furnish.generate ({gen.name})",
            )
        except BudgetExceeded:
            if not attempts:
                raise
            break  # no room in the cap for another try: the best one so far
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
        if not g.image or not gen.paid:
            break
        kept = Path(out) / f"final_intento_{n}.png"
        shutil.copyfile(g.image, kept)
        attempts.append(
            {"image": kept.name, "cost_usd": g.cost_usd, **room_kept(cfg, room_photo, kept)}
        )
        if attempts[-1]["ok"]:
            break
    best = next((a for a in attempts if a["ok"]), None) or max(
        attempts, key=lambda a: a["sift_inliers"] or 0, default=None
    )
    if best:
        shutil.copyfile(Path(out) / best["image"], g.image)
    return {
        "generator": gen.name,
        "image": g.image and str(Path(g.image).name),
        "pending": g.image is None,
        "model": g.model,
        "cost_usd": round(sum(a["cost_usd"] for a in attempts), 4) if attempts else g.cost_usd,
        "meta": g.meta,
        "attempts": attempts,
        "room_check": {k: v for k, v in best.items() if k != "cost_usd"} if best else None,
    }


def write(path: Path, data: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))
    return data
