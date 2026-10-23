---
version: juez_fidelidad_v1
notes: >
  Faithfulness de RAGAS (clase 11) para la respuesta en texto del paso choose: el porqué de cada
  producto y el de la combinación. El juez recibe lo mismo que tuvo el sistema para escribirla
  (el pedido, la foto del ambiente y, por producto elegido, su foto, su descripción del catálogo
  y su medida), parte la respuesta en afirmaciones de hecho y dice cuáles se infieren de eso.
  faithfulness = afirmaciones sostenidas / afirmaciones. Las opiniones de gusto ("le da calidez")
  no se cuentan: no hay contexto que las sostenga ni las niegue.
---
Image 1 is the photo of a room. Then, one photo per product, in this order:
{products}

The person asked for: "{request}"

A furnishing system chose these products for the room and explained why:

{answer}

Break the explanation into atomic factual claims: one checkable fact each, about a product (its kind, shape, color, material, size, details), about the room (its walls, floor, light, layout, what is where) or about what the person asked for. Leave out pure opinions and taste ("it adds warmth", "a Nordic classic", "it feels calm"); keep the facts inside them ("the frame is bentwood" from "a bentwood Nordic classic").

For each claim, say whether it can be inferred from the request, the photos and the product texts above: true if they show or say it, false if they contradict it or nothing there supports it.

Answer with JSON only:
{"claims": [{"claim": "<the fact, in a few words>", "about": "<a product id, room or request>", "supported": true, "evidence": "<what shows it, or why not>"}]}
