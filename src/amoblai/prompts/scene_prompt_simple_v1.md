---
version: scene_prompt_simple_v1
notes: >
  Ronda 2 de la réplica: prompts cortos que dicen qué hacer, iguales en las seis variantes salvo
  en cómo dicen dónde va cada mueble. Esta no lo dice: el modelo los ubica. Para la comparación,
  reemplaza a scene_prompt_libre_v4 (una lista larga de prohibiciones).
---
Add the products of images 2 to {last} to the room in image 1.

The client asked: "{request}"

{products}

Place them where an interior designer would.

Keep the room as it is in image 1: the same camera, walls, floor, windows and light. Add only these products, each exactly like its photo, and nothing else. The result must look like a real photo of this room.
