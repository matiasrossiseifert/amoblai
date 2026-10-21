---
version: rerank_candidates_v1
notes: >
  Post-retrieval ablation (evaluation/retrieval.py): a vision LLM reorders the search's top
  candidates for one piece, looking at their photos. It gets the query (the piece in the
  catalog's eight lines, as the plan writes it) and the candidates' photos with their type line
  and size, as the choose step lists them. Not the room photo: in the IKEA rooms the product is
  in the photo, and the task would turn into spotting it.
---
We are looking for this piece of furniture, described in eight lines:

{query}

The {n} images are candidates from our catalog, one photo each, in this order:
{candidates}

Rank the candidates by how well each one matches the description: first the kind of piece, then its shape, materials and colors, then its style and feel. Judge from the photos.

Answer with JSON only: {"ranking": ["<id>", "<id>", ...]}, every candidate's id once (the catalog id after the image number, like "102.335.32"), best first.
