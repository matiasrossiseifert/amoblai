---
version: scene_prompt_libre_v2
notes: >
  scene_prompt_libre_v1 más una línea: los muebles que se venden por módulos (bibliotecas,
  estanterías) se pueden repetir uno al lado del otro para llenar una pared, como se arman en la
  tienda. Para que una "biblioteca" no sea un solo mueble chico contra una pared enorme.
---
Image 1 is a photo of a room. Images 2 to {last} are products, one photo each:
{products}

The person asked for this room: "{request}"

Furnish the room in image 1 with these products, as an interior designer would for that request. You decide where each product goes and how the room is arranged. Use every product. Furniture that comes in units, like bookcases and shelves, can be repeated side by side to fill a wall, the way the store sells it; give every piece its real size against the room.

Keep image 1 as it is: the same framing and camera, walls, floor, ceiling, windows and light. Only add the products, each with the design, proportions, colors and materials of its photo, lit like the room. The result must look like a real photograph.
