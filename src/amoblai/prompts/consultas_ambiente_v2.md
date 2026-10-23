---
version: consultas_ambiente_v2
notes: >
  La segunda pasada de consultas de evaluación, para lo que sumó la ampliación del catálogo:
  estanterías, muebles de guardado, cómodas, escritorios, pufs, banquetas, bancos, lámparas y
  decoración. Las mismas reglas y el mismo formato que consultas_ambiente_v1 (que hizo sofás,
  sillones, sillas, mesas y alfombras, y no se rehace: sus consultas quedan como estaban). Los
  objetos chicos de decoración entran solo si se ven lo bastante para describir su forma y sus
  colores. El modelo no ve el catálogo ni las anotaciones del ambiente.
---
Image 1 is a photo of a furnished room from a home furnishing store's catalog. Every piece of furniture, lamp and decorative object in it is a product the store sells.

For each product you can see that is one of these, write the search that would find that exact product in the store's catalog:
- shelves and bookcases; storage furniture (sideboards, TV stands, cabinets, chests of drawers); desks;
- ottomans, poufs, stools and benches;
- lamps: pendant, ceiling, floor, table, desk and wall lamps;
- decoration: cushions, throws, curtains, vases, plants and plant pots, picture frames and wall art, mirrors, wall clocks, baskets, candle holders.

Describe the product as it is in the photo: what it is, its shape, materials, colors and the details that make it recognizable.
- One entry per distinct product: several identical cushions or frames are one entry; two different cushions are two.
- Leave out a product when less than half of it is visible, and a small object you can't see well enough to describe its shape and colors.
- Leave out everything else: sofas, armchairs, chairs, tables and rugs (searched separately), beds, books, tableware, kitchen things, flowers in a vase without the vase.

Answer with JSON only:
- "room": one sentence, the room as you read it (what it is, its style and palette).
- "pieces", for each product:
  - "piece": what it is and where it is in the photo, in a few words.
  - "kinds": the one kind of the product, from this list:
{kinds}
  - "query": the product in these eight lines, in this order. English, short phrases separated by commas, no full sentences, no brand, no measurements, nothing about what it is not. The Type line starts with the kind.

Type: the kind, then what it is, two to six words
Use: what it is for, then the rooms it belongs in
Style: one to three of: Scandinavian, mid-century modern, minimalist, Japandi, industrial, rustic, farmhouse, bohemian, coastal, traditional, classic, art deco, glam, retro, contemporary, modern
Materials: the main materials and finishes you see
Colors: the main color first, then the others, in plain names
Shape: silhouette and details (legs or base, doors and drawers, shade, pattern, outline), size and visual weight for its type
Feel: two to four words
Goes with: the colors, materials and kinds of rooms it suits
