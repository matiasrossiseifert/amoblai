---
version: scene_prompt_cajas3d_v2
notes: >
  Ronda 2 de la réplica: scene_prompt_cajas3d_v1 corto. Las cajas 3D van dibujadas sobre la foto
  del cuarto (imagen 1) y hay que borrarlas.
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Image 1 has numbered colored 3D boxes drawn on it. Box N is the space the product of image N takes in the room: where it stands on the floor, which way it faces, and how wide, deep and tall it is. Put each product inside its box, so that it fills it. Then remove the boxes and numbers: none may be left in the result.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
