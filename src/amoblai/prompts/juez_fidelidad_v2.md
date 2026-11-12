---
version: juez_fidelidad_v2
notes: >
  juez_fidelidad_v1 con el contexto que de verdad tuvo el generador. En v1 el juez leía la
  descripción completa de ocho líneas de cada producto, que el paso choose nunca recibe: choose ve
  la foto del ambiente, la foto de cada candidato y una línea con su kind, su tipo y su medida.
  Así, "patas de abedul" quedaba sostenida por un texto que el generador no leyó, y la métrica
  medía si el porqué coincide con la ficha, no si se infiere del contexto (la faithfulness de la
  clase 11). v2 le da al juez exactamente lo que vio choose de cada producto elegido: su foto y
  esa línea. Lo demás igual: afirmaciones de hecho, sostenidas / afirmaciones.
---
Image 1 is the photo of a room. Then, one photo per product, in this order, with all the text the system had about it:
{products}

The person asked for: "{request}"

A furnishing system chose these products for the room and explained why:

{answer}

Break the explanation into atomic factual claims: one checkable fact each, about a product (its kind, shape, color, material, size, details), about the room (its walls, floor, light, layout, what is where) or about what the person asked for. Leave out pure opinions and taste ("it adds warmth", "a Nordic classic", "it feels calm"); keep the facts inside them ("the frame is bentwood" from "a bentwood Nordic classic").

For each claim, say whether it can be inferred from the request, the photos and the product lines above: true if they show or say it, false if they contradict it or nothing there supports it. A measure the line does not give is not supported, even if it looks plausible in the photo.

Answer with JSON only:
{"claims": [{"claim": "<the fact, in a few words>", "about": "<a product id, room or request>", "supported": true, "evidence": "<what shows it, or why not>"}]}
