---
version: juez_pedidos_v1
notes: >
  Answer relevance de RAGAS (clase 11) para el flujo: a partir de la respuesta sola (la lista de
  productos elegidos y, si la hay, la foto final del ambiente), el juez escribe los pedidos que
  esa respuesta contesta, sin ver el pedido original (ingeniería inversa). La métrica es el
  coseno medio entre cada pedido generado y el original (Qwen3-Embedding).
---
A furnishing app takes a photo of a room and a request in Spanish ("un living nórdico y cálido", "un comedor para seis") and answers with a shopping list of products and, sometimes, the photo of the room with them.

This is one answer: the products it chose, each with its catalog description:

{products}

{image}

Write {n} different requests, in Spanish, as a person would type them into the app, that this answer fulfils: the kind of room, the style or feel, and the pieces asked for. Do not describe the products in detail; write what the person asked.

Answer with JSON only: {"requests": ["<request>", "<request>", ...]}
