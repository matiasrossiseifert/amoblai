---
version: scene_prompt_cajas_guia_v1
notes: >
  Ronda 2 de la réplica: la foto del cuarto va limpia (imagen 1) y los rectángulos van en una
  copia aparte, la última imagen: no hay nada que borrar.
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Image {guide} is the same room with numbered colored rectangles drawn on it: rectangle N shows where the product of image N goes and how big it is. Put each product in image 1 at the place and size of its rectangle. Image {guide} is only a guide: do not draw its rectangles or numbers.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
