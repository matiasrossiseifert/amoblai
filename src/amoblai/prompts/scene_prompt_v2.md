---
version: scene_prompt_v2
notes: >
  The scene step, second version (roomrag's is scene_prompt_v1). The first image of the TP
  (resultados/amoblar/prueba-alvear2) showed two problems. The image model put the whole group
  near the camera, though the prompt said "midway down the room", leaving the back of a long
  room empty. And the products looked pasted in: lit like the catalog photos (studio shots on
  white, many of them renders), not like the room, which is lit from the balcony at the back.
  v2 asks for each position anchored to something visible at that depth, its size as a share of
  the frame and the free floor said out loud; and for the catalog photos to give the design
  only, with the light, white balance, grain and sharpness of the room photo. Same inputs and
  answer as v1.
---
Image 1 is a photo of a room. The user asked, in their own words: "{request}". The room, as read before: {room}

The next images are the products chosen for it, one photo each, in this order:
{products}

Write the prompt for an image-editing model that will receive these same images in this same order and must return image 1 with these products in it. Image-editing models tend to put new furniture close to the camera and to paste catalog photos in as they are: the prompt has to prevent both. It must:
- say that image 1 is the room to edit and that each other image is one product to add, by its number;
- for each product, where it goes (its piece says it), written so it can't be misread: how far into the room, anchored to something visible at that depth (level with the light switch on the right wall, just in front of the balcony door, beside the second window), along which wall, which way it faces, and how big it looks in the frame (about a fifth of the image width); if the floor near the camera stays free, say so;
- keep each product's design exactly as in its photo: the same shape, proportions, colors, materials and details, not a similar one;
- say that the product photos are studio catalog shots, many of them renders, that give the design only: each product must look photographed in this room by this camera, with this room's light (where it comes from and which sides are in shade), its white balance, contrast, grain and sharpness, contact shadows on the floor, and the small creases and wear of real fabric, leather and wood;
- keep everything else in image 1 as it is: the same framing and camera, walls, floor, light and the furniture already there; add nothing but these products;
- ask for a photograph, not a render.

Write it in English, as direct instructions, at most 250 words.

Answer with JSON only: {"prompt": "<the prompt>", "placements": [{"id": "<id>", "where": "<a few words>"}]}
