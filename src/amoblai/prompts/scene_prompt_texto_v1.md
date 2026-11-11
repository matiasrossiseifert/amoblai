---
version: scene_prompt_texto_v1
notes: >
  Ronda 2 de la réplica: sin cajas; cada línea de producto trae, después de 'Where:', una o dos
  frases de dónde va (las escribe Opus mirando la foto real y la vaciada: describir_lugares_v1).
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Put each product where its line says, at its real size.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
