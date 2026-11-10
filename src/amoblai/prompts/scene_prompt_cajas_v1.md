---
version: scene_prompt_cajas_v1
notes: >
  scene_prompt_libre_v4 con cajas: la foto del ambiente trae dibujado un rectángulo numerado por
  producto, donde va y cuánto ocupa en la foto (en el experimento de réplica, las cajas de los
  muebles en la foto real). El producto tiene que llenar su caja; después no queda ninguna línea.
  Es el primer paso de la idea a futuro: cajas con las medidas reales del producto, en un ambiente
  medido.
---
Edit image 1. It is a photo of the client's own room, and the result must still be that same room, exactly: the same camera position, angle, lens and framing; the same walls, ceiling, floor, light fixture and outlets; the same windows, with the same frames, in the same places. Do not add, remove, move or enlarge any wall, window, door or opening, do not extend, rotate or crop the room, and do not change its light. Wherever no new furniture goes, the result is image 1 unchanged.

Images 2 to {last} are the products to add, one photo each:
{products}

Image 1 has colored rectangles drawn on it, each with a number. The rectangle numbered N marks where the product of image N goes and how much of the photo it takes: place that product so that it fills its rectangle, its visible outline reaching the rectangle's four sides, standing on the floor (or lying on it, for a rug) as a real object would. Rectangles overlap where one product stands in front of another; the rug lies on the floor under the furniture. The rectangles and numbers are only guides: remove all of them, so that no line, color or number of them is left in the result.

Add exactly these products and nothing else: no other furniture, lamps, plants, rugs or decoration than these (books on the shelves of a bookcase are fine). Each one must be the product of its photo, not a similar one: the same design, proportions, colors and materials.

The client asked: "{request}". The result must look like a real photograph of image 1's room, with these products where the rectangles were.
