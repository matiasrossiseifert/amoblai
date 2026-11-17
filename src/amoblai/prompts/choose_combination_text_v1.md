---
version: choose_combination_text_v1
notes: >
  Experiment 5b (furnish.candidate_photos false): choose_combination_v2 with the candidates as
  text instead of photos. Each candidate comes with its id, its size and its description, the
  same eight lines the index has. The room photo stays. Everything else is v2, word for word,
  so the only change is how the candidates are seen.
---
Image 1 is a photo of a room. The user asked, in their own words: "{request}".

We are adding {pieces} piece(s) of furniture. The candidates from our catalog are listed here by piece, each with its id, its size and its description:
{candidates}

For each piece choose the one candidate that would look best in this room and does best what the user asked: the right kind of piece, a size that suits its spot, and a style, color and material that go with what is already in the room and with the other pieces you choose. Choose the pieces together, as one look, not each on its own. Judge from the descriptions.

Then say how many units of it go in the room ("quantity"). Usually 1. More than one when that is how the piece is used or what the user asked for: chairs around a dining table, a pair of bedside tables or of armchairs, two lamps on either side of a sofa. 0 when none of its candidates suits this room, or the room is better without it: then it is left out of the list. Don't repeat a piece to fill space when the user asked for one.

Answer with JSON only: {"choices": [{"piece": 1, "id": "<id>", "quantity": 1, "why": "<one sentence>", "ranking": ["<id>", "<id>", "<id>"]}], "why": "<one or two sentences: why these go together in this room>"}

One entry in "choices" for each piece, in the order above. "id": the chosen candidate (null when "quantity" is 0). "ranking": that piece's candidates, best first, at most three.
