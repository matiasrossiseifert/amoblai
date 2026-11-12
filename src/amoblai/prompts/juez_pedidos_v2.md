---
version: juez_pedidos_v2
notes: >
  juez_pedidos_v1 sin los pedidos de ejemplo. v1 abría con dos ejemplos de pedido ("un living
  nórdico y cálido", "un comedor para seis") y el primero era, palabra por palabra, el comienzo
  del pedido evaluado en tres de las cuatro corridas: el juez lo copiaba y la answer relevance
  salía inflada (data leakage). v2 no da ningún ejemplo de pedido. Lo demás igual: a partir de la
  respuesta sola, el juez escribe los pedidos que esa respuesta contesta.
---
A furnishing app takes a photo of a room and a request typed by a person in Spanish, and answers with a shopping list of products and, sometimes, the photo of the room with them.

This is one answer: the products it chose, each with its catalog description:

{products}

{image}

Write {n} different requests, in Spanish, as a person would type them into the app, that this answer fulfils: the kind of room, the style or feel, and the pieces asked for. Do not describe the products in detail; write what the person asked.

Answer with JSON only: {"requests": ["<request>", "<request>", ...]}
