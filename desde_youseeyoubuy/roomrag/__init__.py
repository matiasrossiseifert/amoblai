"""roomrag: from a room photo and a request, the catalog's products that suit it (RAG), and the
room with them. No 3D: what puts the products in the room is a step named in the config.

The flow (flow.py), one file per step in the run folder, each step done once:

  plan      the LLM reads the photo and the request as an interior designer: which pieces, and
            for each what it is for (a hard filter), the most it may measure, and the ideal
            product written like the catalog's descriptions (the query)
  retrieve  for each piece, the hard filters, then the descriptions nearest to the query
  choose    the LLM looks at the room and the candidates' photos: the best combination
  scene     the LLM writes the image model's prompt: where each product goes, how it faces
  generate  the image model puts the products in the room

YouSeeYouBuy uses the same package with its own last step (its 3D model at true scale, then a
realism pass) instead of scene and generate: `furnish.steps` in its config.

The index (index.py) is built once: each product's description (describe.py: written ahead,
the seller's fields, or a vision LLM) and its vector (embed.py), cached.

  config.py    the YAML config          catalog.py   which products, from where
  kinds.py     what a piece is for      filters.py   type, kind and size limits
  describe.py  the descriptions         embed.py     text -> vector
  index.py     builds and loads it      search.py    filters, then nearest descriptions
  llm.py       Claude, OpenAI-compatible  steps.py   the steps
  generate.py  the image model          flow.py      the run
  evaluate.py  the search test (ok@k, nDCG@k)
  http.py, budget.py, prompts.py: what every paid call uses (retries, the spend cap, templates)
"""
