---
version: choose_combination_v1
notes: >
  After the catalog search: the LLM sees the room photo and every candidate's photo, piece by
  piece, and picks one product per piece so that together they suit the room and the request
  (the best combination, not the best of each alone). The candidates are listed with the
  catalog's type line and their size, not the store's name. With one piece it is a plain choice
  among candidates.
---
Image 1 is a photo of a room. The user asked, in their own words: "{request}".

We are adding {pieces} piece(s) of furniture. Images 2 to {images} are the candidates from our catalog, one photo each, listed here by piece in the same order:
{candidates}

For each piece choose the one candidate that would look best in this room and does best what the user asked: the right kind of piece, a size that suits its spot, and a style, color and material that go with what is already in the room and with the other pieces you choose. Choose the pieces together, as one look, not each on its own. Judge from the photos.

Answer with JSON only: {"choices": [{"piece": 1, "id": "<id>", "why": "<one sentence>", "ranking": ["<id>", "<id>", "<id>"]}], "why": "<one or two sentences: why these go together in this room>"}

One entry in "choices" for each piece, in the order above. "ranking": that piece's candidates, best first, at most three.
