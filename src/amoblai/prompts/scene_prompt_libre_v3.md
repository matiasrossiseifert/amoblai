---
version: scene_prompt_libre_v3
notes: >
  scene_prompt_libre_v1 (no LLM: the image model arranges the products itself) with the
  quantities of choose_combination_v2: a product listed with N units goes N times in the room.
  Without libre_v2's line about repeating modular furniture: how many units of each is decided
  in choose, and the shopping list says it.
---
Image 1 is a photo of a room. Images 2 to {last} are products, one photo each:
{products}

The person asked for this room: "{request}"

Furnish the room in image 1 with these products, as an interior designer would for that request. You decide where each product goes and how the room is arranged. Use every product: one of each, or as many as its line says ("2 units": two of it).

Keep image 1 as it is: the same framing and camera, walls, floor, ceiling, windows and light. Only add the products, each with the design, proportions, colors and materials of its photo, at its real size against the room, lit like the room. The result must look like a real photograph.
