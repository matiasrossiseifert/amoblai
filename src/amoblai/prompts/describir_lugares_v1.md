---
version: describir_lugares_v1
notes: >
  Réplica, variante texto: dónde va cada mueble en palabras, sin cajas. Opus mira la foto real
  (imagen 1) y la vaciada (imagen 2) y escribe, por producto, una o dos frases para ubicarlo en la
  vacía. Es la información de las cajas por otro canal.
---
Image 1 is a photo of a furnished room. Image 2 is the same room, empty.

These are the products in image 1:
{products}

For each product, write one or two short sentences that say where it is, so that someone who only sees image 2 can put it in the same place: which wall or corner it is against or near, where along it (left and right as seen in the photo), which way it faces, how far into the room it comes, and what it is next to, in front of or on. Refer only to what can be seen in image 2 (walls, window, door, floor) and to the other products. Do not describe what the product looks like.

Answer with JSON only, one entry per product id: {"<id>": "<where it is>"}
