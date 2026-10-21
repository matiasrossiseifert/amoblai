---
version: scene_prompt_v1
notes: >
  Without 3D the image model places the products itself. The LLM, which has read the room and
  chosen the products, writes the image model's prompt: where each product goes in this photo
  (next to what, along which wall), which way it faces, how big it looks next to what is there,
  and that the room stays as it is. The image model gets the room photo first, then each
  product's photo, in the order of the list. Earlier tests showed that the products' shape is
  what an image model loses first: the prompt asks for each one exactly as in its photo.
---
Image 1 is a photo of a room. The user asked, in their own words: "{request}". The room, as read before: {room}

The next images are the products chosen for it, one photo each, in this order:
{products}

Write the prompt for an image-editing model that will receive these same images in this same order and must return image 1 with these products in it. The prompt must:
- say that image 1 is the room to edit and that each other image is one product to add, by its number;
- for each product, where it goes in this photo, named by what is visible (next to the desk, against the left wall under the window, on the rug in front of the sofa), which way it faces, and how big it looks next to what is already there (its real size is given);
- ask for each product exactly as in its photo: the same shape, proportions, colors, materials and details, not a similar one;
- keep everything else in image 1 as it is: the same framing and camera, walls, floor, light and the furniture already there; only add the products, with the shadows and light this room would give them;
- ask for a photograph, not a render.

Write it in English, as direct instructions, at most 200 words.

Answer with JSON only: {"prompt": "<the prompt>", "placements": [{"id": "<id>", "where": "<a few words>"}]}
