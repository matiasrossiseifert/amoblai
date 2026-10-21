"""python -m roomrag <command> --config config.yaml [--set a.b=value ...]

build                       describe and embed the catalog (only what the cache lacks)
search "<query>" [-k N]     the nearest products, no filters (try the index)
run <photo> "<request>"     the whole flow into <runs_dir>/<name> (resumes if it exists);
                            --view <photo>: another photo of the same room (repeatable)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import deep_merge, load_config, parse_override


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="roomrag")
    ap.add_argument("command", choices=["build", "search", "run"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", action="append", default=[], dest="sets")
    ap.add_argument("-k", type=int, default=None)
    ap.add_argument("--name", default=None, help="run folder name (run)")
    ap.add_argument("--view", action="append", default=[], dest="views", help="run: other photo")
    a = ap.parse_args(argv)
    over: dict = {}
    for s in a.sets:
        over = deep_merge(over, parse_override(s))
    cfg = load_config(a.config, over)

    if a.command == "build":
        from .index import build_index

        idx = build_index(cfg)
        print(f"{idx.meta['products']} products, {idx.meta['left_out']} left out: {idx.path}")
    elif a.command == "search":
        from .filters import Filters
        from .index import build_index, index_is_current, open_index
        from .search import search

        if not index_is_current(cfg):
            build_index(cfg)
        if a.k:
            cfg.rag.top_k = a.k
        for h in search(open_index(cfg), a.args[0], Filters(), cfg):
            print(f"{h.score or 0:.3f}  {h.id}  {h.kind or h.category}  {h.name}")
    else:
        from .flow import run_flow

        photo, request = a.args
        out = Path(cfg.runs_dir) / (a.name or Path(photo).stem)
        run_flow(photo, request, cfg, out, views=a.views)
        print(out)


if __name__ == "__main__":
    main()
