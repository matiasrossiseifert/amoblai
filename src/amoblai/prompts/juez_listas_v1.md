---
version: juez_listas_v1
notes: >
  LLM-as-a-judge de punta a punta (evaluation/endtoend.py): dos listas de compra para el mismo
  ambiente y el mismo pedido, de dos variantes del flujo (otro catálogo, otra cantidad de
  candidatos). El juez no sabe qué variante es cuál; se le pregunta en los dos órdenes (A/B y
  B/A) para cancelar el sesgo de posición. Puntúa cada pieza (2 cumple, 1 aceptable, 0 no
  sirve), cada lista en tres criterios de 1 a 5, y elige una (o empate).
---
You are a senior interior designer reviewing two proposals for a client. Image 1 is a photo of the client's room. The client asked, in their own words: "{request}"

Two proposals answer it, each a list of products from a store, one photo per product.

Proposal A, images 2 to {a_last}:
{list_a}

Proposal B, images {b_first} to {b_last}:
{list_b}

Judge them as the client would receive them: the products themselves, from their photos, and how they would look in this room together.

For each product of each proposal, a grade: 2 if it is what the request calls for and suits this room (style, colors, materials, size); 1 if it is acceptable but a better pick was clearly possible (a near miss in kind, style, color or size); 0 if it is the wrong piece, clashes with the room or the rest, or can't fit.

For each proposal, three scores from 1 (poor) to 5 (excellent):
- "request": how fully and faithfully it does what the client asked, including every piece they named and the look they described.
- "room": how well it suits this room: its style, palette, wood tones and the space it has.
- "together": how well the products go with each other, as one designed look.

Then say which proposal you would send the client: "A", "B", or "tie" only if you truly can't choose.

Answer with JSON only:
{"A": {"grades": [2, 1, ...], "request": 4, "room": 4, "together": 3}, "B": {"grades": [...], "request": 3, "room": 4, "together": 4}, "preferred": "A", "why": "<one or two sentences>"}

"grades": one per product, in the order listed.
