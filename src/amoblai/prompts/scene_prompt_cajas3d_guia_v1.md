---
version: scene_prompt_cajas3d_guia_v1
notes: >
  Ronda 2 de la réplica: la foto del cuarto va limpia (imagen 1) y las cajas 3D van en una copia
  aparte, la última imagen: no hay nada que borrar.
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Image {guide} is the same room with numbered colored 3D boxes drawn on it. Box N is the space the product of image N takes in the room: where it stands on the floor, which way it faces, and how wide, deep and tall it is. Put each product in image 1 in the place, direction and size of its box. Image {guide} is only a guide: do not draw its boxes or numbers.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
