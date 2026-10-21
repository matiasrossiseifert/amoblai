---
version: describe_product_v2
notes: >
  One product's description for the catalog search. The search embeds it and compares it with a
  query written in the same eight lines (the plan step writes it), so: the same fields in the
  same order, short phrases in the words people use, only what helps choose a piece for a room.
  No brand, price or measurements (the filters handle size), and nothing about what it is not
  (embeddings don't read "not"). Short: a long text dilutes what matters. The same prompt for
  the API describers and for the descriptions written ahead in Claude Code.
---
The images are photos of one product sold by a furniture store: a {category} called "{name}", {width_cm} cm wide, {depth_cm} cm deep and {height_cm} cm high. Some photos may be close-ups of a material, a measurement drawing, or the product in a room with other things: describe only this product.

Write its description for a search that matches products to what a person wants for their room. Exactly these eight lines, in this order, in English, short phrases separated by commas, no full sentences:

Type: the common name of what it is, two to six words (e.g. "armless dining chair", "three-seat sofa", "round coffee table", "low TV console").
Use: what it is for, then the rooms it belongs in (e.g. "dining, working at a desk; dining room, home office").
Style: one to three of these, the closest first: Scandinavian, mid-century modern, minimalist, Japandi, industrial, rustic, farmhouse, bohemian, coastal, traditional, classic, art deco, glam, retro, contemporary, modern.
Materials: the main materials and finishes you see (e.g. "solid oak, black powder-coated steel, woven paper cord seat").
Colors: the main color first, then the others, in plain names, with light or dark and warm or cool where it helps (e.g. "light natural wood, black").
Shape: its silhouette and the details that make it recognizable (legs or base, arms, back, edges), and its size and visual weight for its type (e.g. "compact", "oversized", "light and open", "low and bulky").
Feel: two to four words for how it feels in a room (e.g. "warm, calm, airy").
Goes with: the colors, materials and kinds of rooms it suits (e.g. "light wood, white walls, black accents; Scandinavian or Japandi rooms").

60 to 90 words in all. Say only what the photos and the name show. No brand, price, measurements, care or assembly.

Two examples of the format and length (other products):

Type: wishbone dining armchair
Use: dining, working at a desk; dining room, kitchen, home office
Style: Scandinavian, mid-century modern, minimalist
Materials: solid wood frame in a matte black finish, woven paper cord seat
Colors: matte black, charcoal black seat
Shape: curved one-piece top rail that forms the arms, Y-shaped back, woven seat, four round tapered legs with stretchers, open and light, compact
Feel: graphic, calm, crafted, timeless
Goes with: light or dark wood tables, white or grey walls, black accents; Scandinavian, Japandi or modern rooms

Type: upholstered swivel desk chair on casters
Use: working at a desk; home office, study
Style: classic, retro, contemporary
Materials: solid oak frame and base with a wire-brushed limed finish, woven linen-look fabric, black metal swivel mechanism
Colors: honey oak, slate blue-grey fabric, black
Shape: tall curved scoop back framed in exposed wood, armless, padded seat, carved wooden five-star base on casters, medium visual weight
Feel: warm, studious, vintage, comfortable
Goes with: warm wood desks, blue or grey tones, brass or black accents; classic studies, farmhouse or rustic home offices
