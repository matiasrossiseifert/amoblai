---
version: rerank_candidates_text_v1
notes: >
  Experiment 5b on the ground truth: rerank_candidates_v1 with the candidates as text instead of
  photos. Each candidate comes with its id, its size and its description (the eight lines the
  index has). Everything else is v1, word for word, so the only change is how the candidates are
  seen.
---
We are looking for this piece of furniture, described in eight lines:

{query}

The {n} candidates from our catalog, each with its id, its size and its description, in this order:
{candidates}

Rank the candidates by how well each one matches the description: first the kind of piece, then its shape, materials and colors, then its style and feel. Judge from the descriptions.

Answer with JSON only: {"ranking": ["<id>", "<id>", ...]}, every candidate's id once (the catalog id in brackets, like "102.335.32"), best first.
