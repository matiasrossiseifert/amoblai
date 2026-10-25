---
version: scene_prompt_libre_v1
notes: >
  Alternativa a scene_prompt_v1/v2, sin LLM (furnish.scene_llm: false): el modelo de imagen
  recibe la foto del ambiente, las fotos de los productos y el pedido, y decide él dónde va cada
  uno. No se le dice dónde ni cómo ubicar nada.
---
Image 1 is a photo of a room. Images 2 to {last} are products, one photo each:
{products}

The person asked for this room: "{request}"

Furnish the room in image 1 with these products, as an interior designer would for that request. You decide where each product goes and how the room is arranged. Use every product.

Keep image 1 as it is: the same framing and camera, walls, floor, ceiling, windows and light. Only add the products, each with the design, proportions, colors and materials of its photo, lit like the room. The result must look like a real photograph.
