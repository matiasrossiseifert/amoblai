---
version: scene_prompt_libre_v4
notes: >
  scene_prompt_libre_v3 (no LLM: the image model arranges the products itself) made strict. With
  v3 and nine products, Nano Banana 2 re-imagined the room: it added a window on the left wall
  and moved the bookcase to another wall (experimento-buen-pedido). v4 says it is an edit of the
  client's own photo, not a new picture: the same camera and the same walls, window, ceiling and
  floor, nothing added or opened; and only the products of the reference photos, exactly them,
  nothing else. The generate step checks it (SIFT against the original) and tries again.
---
Edit image 1. It is a photo of the client's own room, and the result must still be that same room, exactly: the same camera position, angle, lens and framing; the same walls, ceiling, floor, light fixture and outlets; the same windows, with the same frames, in the same places. Do not add, remove, move or enlarge any wall, window, door or opening, do not extend, rotate or crop the room, and do not change its light. Wherever no new furniture goes, the result is image 1 unchanged.

Images 2 to {last} are the products to add, one photo each:
{products}

Add exactly these products and nothing else: no other furniture, lamps, plants, rugs or decoration than these (books on the shelves of a bookcase are fine). Each one must be the product of its photo, not a similar one: the same design, proportions, colors and materials. A product listed with "2 units" goes twice.

The client asked: "{request}". Arrange the products as an interior designer would for that, against the walls and on the floor that image 1 shows, each at its real size for this room, lit by this room's light. The result must look like a real photograph of image 1's room.
