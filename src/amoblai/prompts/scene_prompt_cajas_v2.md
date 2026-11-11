---
version: scene_prompt_cajas_v2
notes: >
  Ronda 2 de la réplica: scene_prompt_cajas_v1 corto. Los rectángulos van dibujados sobre la foto
  del cuarto (imagen 1) y hay que borrarlos.
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Image 1 has numbered colored rectangles drawn on it. Put the product of image N inside rectangle N, so that it fills it. Then remove the rectangles and numbers: none may be left in the result.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
