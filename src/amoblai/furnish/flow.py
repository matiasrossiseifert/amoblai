"""One furnishing run: a room photo and a request -> a run folder, the steps of `furnish.steps` in
order. Each step writes its file; a step whose file exists is not done again (nothing is paid
twice), so a run resumes where it stopped.

    room.jpg, request.json
    room_2.jpg ...      other photos of the same room (views), for the LLM only
    1_searches.json     plan: the room as the LLM read it, the pieces and their searches
    2_candidates.json   retrieve: each piece's candidates (+ 2_candidates*.jpg, numbered)
    3_choice.json       choose: one product per piece, and why
    4_scene.json        scene: the image model's prompt
    5_image.json        generate: the image (final.png), or `pending` (manual)

A step is a function step(run: Run) -> dict. Another project adds its own by naming them in
`furnish.steps` as "package.module:function" (e.g. a 3D placement instead of scene and
generate); its file is <function>.json. A record with `pending` stops the run unsaved (to be
resumed); one with `rerun` is not saved, so the step runs every time (it keeps its own files).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageOps

from amoblai.config import Config
from amoblai.furnish import steps as st
from amoblai.furnish.generate import load_attr
from amoblai.rag.search import Hit


@dataclass
class Run:
    cfg: Config
    out: Path
    request: str
    log: Callable[[str], None] = print
    extras: dict = field(default_factory=dict)  # what another project's steps need
    data: dict = field(default_factory=dict)  # each step's record, by step name

    @property
    def room(self) -> Path:
        return self.out / "room.jpg"

    @property
    def views(self) -> list[Path]:
        """The other photos of the room (room_2.jpg, room_3.jpg...), in order."""
        return sorted(self.out.glob("room_*.jpg"), key=lambda p: int(p.stem.split("_")[1]))

    def pieces(self) -> list[dict]:
        return self.data["plan"]["answer"]["pieces"][: self.cfg.furnish.max_pieces]

    def candidates(self) -> list[tuple[dict, list[Hit]]]:
        """Each piece the search found something for, and its candidates."""
        found = self.data["retrieve"]["pieces"]
        return [(f["spec"], [Hit(**h) for h in f["candidates"]]) for f in found]

    def chosen(self) -> list[Hit]:
        """The chosen product of each of those pieces, in the same order."""
        return st.chosen(self.data["retrieve"], self.data["choose"])


def _plan(run: Run) -> dict:
    rec = st.plan(run.cfg, run.room, run.request, run.views)
    run.log(f"pieces: {[p['piece'] for p in rec['answer']['pieces']]}")
    return rec


def _retrieve(run: Run) -> dict:
    rec = st.retrieve(run.cfg, run.pieces(), run.out)
    if rec["empty"]:
        run.log(f"nothing in the catalog for: {rec['empty']}")
    return rec


def _choose(run: Run) -> dict:
    rec = st.choose(run.cfg, run.room, run.request, run.candidates(), run.views)
    for c in rec["answer"]["choices"]:
        q = st.quantity(c)
        run.log(f"chosen: {c['id']} x{q}: {c.get('why')}" if q else f"left out: {c.get('why')}")
    return rec


def _scene(run: Run) -> dict:
    room = run.data["plan"]["answer"].get("room", "")
    picks = st.picks(run.data["retrieve"], run.data["choose"])
    return st.scene(run.cfg, run.room, run.request, room, picks, run.views)


def _generate(run: Run) -> dict:
    rec = st.generate(
        run.cfg, run.data["scene"]["answer"]["prompt"], run.room, run.chosen(), run.out
    )
    run.log(f"image: {rec['image'] or 'pending: ' + str(rec['meta'].get('job'))}")
    return rec


STEPS: dict[str, tuple[str, Callable[[Run], dict]]] = {
    "plan": ("1_searches.json", _plan),
    "retrieve": ("2_candidates.json", _retrieve),
    "choose": ("3_choice.json", _choose),
    "scene": ("4_scene.json", _scene),
    "generate": ("5_image.json", _generate),
}


def step_for(name: str) -> tuple[str, str, Callable[[Run], dict]]:
    """(key, file, function) of a step named in the config."""
    if name in STEPS:
        return name, *STEPS[name]
    key = name.rpartition(":")[2]
    return key, f"{key}.json", load_attr(name)


def run_flow(
    photo: str | Path,
    request: str,
    cfg: Config,
    out: Path,
    log: Callable[[str], None] = print,
    extras: dict | None = None,
    views: Sequence[str | Path] = (),
) -> Run:
    """Runs (or resumes) every step; stops after a step that is `pending`. `views`: other photos
    of the same room, from other angles, for the LLM to understand it (the image model gets
    `photo` alone)."""
    out.mkdir(parents=True, exist_ok=True)
    run = Run(cfg, out, request, log, extras or {})
    copies = {run.room: photo, **{out / f"room_{i}.jpg": v for i, v in enumerate(views, 2)}}
    for dst, src in copies.items():
        if not dst.exists():
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im.save(dst, quality=92)
    info = {"photo": str(photo), "request": request}
    if views:
        info["views"] = [str(v) for v in views]
    (out / "request.json").write_text(
        json.dumps({**info, **(extras or {}).get("request_info", {})})
    )
    for name in cfg.furnish.steps:
        key, file, fn = step_for(name)
        f = out / file
        if f.exists():
            run.data[key] = json.loads(f.read_text())
            continue
        rec = fn(run)
        run.data[key] = rec
        if rec.get("pending"):
            log(f"{key}: waiting; run again when it is done")
            break
        if not rec.get("rerun"):
            st.write(f, rec)
    return run
