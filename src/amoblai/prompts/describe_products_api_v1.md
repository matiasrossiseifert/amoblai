---
version: describe_products_api_v1
notes: >
  describe_product_v3 by the API instead of Claude Code subagents, several products per call,
  for a catalog that comes with no descriptions (ABO, catalog/abo.py). The same eight lines,
  rules, style list and length, so its descriptions are comparable with IKEA's. Besides, per
  product: its kind from the catalog's list (the listing's kind is only a guess), and whether it
  belongs in the catalog (a photo that doesn't show the product, or a product that isn't for a
  room of a home, leaves).
---
The images are photos of {n} products sold by a home furnishing store (furniture, lighting, textiles and decoration), one photo each, in this order:
{products}

For each product, three things.

1. "in_scope": true if the photo shows the whole product and it is furniture, lighting, a textile or decoration for a living room, dining room, bedroom or home office. false if the photo is a placeholder ("image coming soon"), a material swatch or a close-up that doesn't show the product, several different products, or the product is for outdoors, a bathroom, a kitchen counter, a child's room or a pet.

2. "kind": what it is: exactly one of the kinds after a colon below, the closest (the word before the colon is only their group, not a kind: "sofa", "armchair" or "cushion", never "chair" or "deco"):
{kinds}

3. "text": its description for a search that matches products to what a person wants for their room. Exactly these eight lines, in this order, in English, short phrases separated by commas, no full sentences:

Type: the common name of what it is, two to six words (e.g. "armless dining chair", "three-seat sofa", "low TV console", "brass pendant lamp", "linen cushion cover", "ceramic table vase").
Use: what it is for, then the rooms it belongs in, and for lighting and decoration where it goes (e.g. "dining, working at a desk; dining room, home office", "light over a dining table; dining room, kitchen", "on a sofa or a bed; living room, bedroom").
Style: one to three of these, the closest first: Scandinavian, mid-century modern, minimalist, Japandi, industrial, rustic, farmhouse, bohemian, coastal, traditional, classic, art deco, glam, retro, contemporary, modern.
Materials: the main materials and finishes you see (e.g. "solid oak, black powder-coated steel, woven paper cord seat", "frosted glass shade, brass", "washed linen, piped edge").
Colors: the main color first, then the others, in plain names, with light or dark and warm or cool where it helps (e.g. "light natural wood, black").
Shape: its silhouette and the details that make it recognizable, and its size and visual weight for its type (e.g. "compact", "oversized", "light and open", "low and bulky"). For furniture: legs or base, arms, back, edges, doors and drawers. For a lamp: the shade, the base or arm, how it hangs or stands. For a textile: its pattern, texture and edges. For a decorative object: its outline and proportions.
Feel: two to four words for how it feels in a room (e.g. "warm, calm, airy").
Goes with: the colors, materials and kinds of rooms it suits (e.g. "light wood, white walls, black accents; Scandinavian or Japandi rooms").

60 to 90 words in all. Say only what the photo and the name show; if the photo shows it in a room, describe only this product. If it is sold as a set (two chairs, three frames), describe one piece and say "set of two" in Type. No brand, product name, price, measurements, care or assembly. A cushion cover is sold without its inner cushion: describe it as the cushion it makes. Write the text even when "in_scope" is false.

An example of the format and length (another product):

Type: wishbone dining armchair
Use: dining, working at a desk; dining room, kitchen, home office
Style: Scandinavian, mid-century modern, minimalist
Materials: solid wood frame in a matte black finish, woven paper cord seat
Colors: matte black, charcoal black seat
Shape: curved one-piece top rail that forms the arms, Y-shaped back, woven seat, four round tapered legs with stretchers, open and light, compact
Feel: graphic, calm, crafted, timeless
Goes with: light or dark wood tables, white or grey walls, black accents; Scandinavian, Japandi or modern rooms

Answer with JSON only, one entry per product in the order above:
{"products": [{"id": "<id>", "in_scope": true, "kind": "<kind>", "text": "Type: ...\nUse: ...\nStyle: ...\nMaterials: ...\nColors: ...\nShape: ...\nFeel: ...\nGoes with: ..."}]}
