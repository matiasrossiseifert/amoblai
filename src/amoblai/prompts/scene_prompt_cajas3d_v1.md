---
version: scene_prompt_cajas3d_v1
notes: >
  scene_prompt_cajas_v1 con cajas 3D: en vez de un rectángulo plano, cada producto tiene dibujado
  un prisma en perspectiva apoyado en el piso, con el lugar, la orientación y el tamaño que ocupa
  en el cuarto (en el experimento de réplica, el volumen de cada mueble en la foto real, sacado de
  la profundidad monocular). El rectángulo plano no dice dónde está el mueble en el piso ni cuánto
  ocupa hacia el fondo; el prisma sí. Mismo pedido de borrar las líneas que v1.
---
Edit image 1. It is a photo of the client's own room, and the result must still be that same room, exactly: the same camera position, angle, lens and framing; the same walls, ceiling, floor, light fixture and outlets; the same windows, with the same frames, in the same places. Do not add, remove, move or enlarge any wall, window, door or opening, do not extend, rotate or crop the room, and do not change its light. Wherever no new furniture goes, the result is image 1 unchanged.

Images 2 to {last} are the products to add, one photo each:
{products}

Image 1 has colored 3D boxes drawn on it in perspective, each a wireframe with a number. The box numbered N is the exact volume the product of image N takes in the room: where it stands on the floor, which way it is turned, and how wide, deep and tall it is. Place that product inside its box, standing on the floor where the bottom of the box is (or lying on it, for a rug, whose box is flat), turned like the box, and as big as the box: its width, depth and height fill the box. Boxes overlap where one product stands in front of another; the rug lies on the floor under the furniture. The boxes and numbers are only guides: remove all of them, so that no line, color or number of them is left in the result.

Add exactly these products and nothing else: no other furniture, lamps, plants, rugs or decoration than these (books on the shelves of a bookcase are fine). Each one must be the product of its photo, not a similar one: the same design, proportions, colors and materials.

The client asked: "{request}". The result must look like a real photograph of image 1's room, with these products where the boxes were.
