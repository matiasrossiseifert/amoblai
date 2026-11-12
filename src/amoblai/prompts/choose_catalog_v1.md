---
version: choose_catalog_v1
notes: >
  The choice without a search (rag.mode: whole_catalog): the comparison "RAG, or the whole
  catalog in the context". The catalog goes first, as text, every product once (the same for
  every request, so it is cached as a prompt prefix); then the room photo and this prompt. Each
  piece lists the ids that pass its hard filters (kind and size): the same products the search
  would rank. No candidate photos: the catalog's don't fit in a prompt. The task, the answer
  and the wording follow choose_combination_v2, so the two differ only in what the model
  chooses from.
---
The text above is our catalog: every product, with its id, its size and its description. Image 1 is a photo of a room. The user asked, in their own words: "{request}".

We are adding {pieces} piece(s) of furniture. For each piece, these are the ids of the catalog products that can be it (the right kind of piece, in a size that fits):
{candidates}

For each piece choose the one product, among its ids, that would look best in this room and does best what the user asked: the right kind of piece, a size that suits its spot, and a style, color and material that go with what is already in the room and with the other pieces you choose. Choose the pieces together, as one look, not each on its own. Judge from the room photo and from the descriptions in the catalog.

Then say how many units of it go in the room ("quantity"). Usually 1. More than one when that is how the piece is used or what the user asked for: chairs around a dining table, a pair of bedside tables or of armchairs, two lamps on either side of a sofa. 0 when none of its products suits this room, or the room is better without it: then it is left out of the list. Don't repeat a piece to fill space when the user asked for one.

Answer with JSON only: {"choices": [{"piece": 1, "id": "<id>", "quantity": 1, "why": "<one sentence>", "ranking": ["<id>", "<id>", "<id>"]}], "why": "<one or two sentences: why these go together in this room>"}

One entry in "choices" for each piece, in the order above. "id": the chosen product, copied exactly from that piece's ids (null when "quantity" is 0). "ranking": that piece's best products, best first, at most three.
