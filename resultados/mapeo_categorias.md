# Mapeo de `type` IKEA → categorías del alcance

| Categoría | `type` del dataset | SKUs |
|---|---|---|
| sofá | Three-seat sofa | 12 |
| sofá | Two-seat sofa | 9 |
| sofá | Three-seat sofa-bed | 3 |
| sofá | Two-seat sofa-bed | 2 |
| sofá | Two-seat sofa with chaise longue | 3 |
| sofá | Two-seat sofa w chaise longue left | 2 |
| sofá | Two-seat sofa w chaise longue right | 2 |
| sofá | Two-seat sofa and chaise longue | 1 |
| sofá | 3-seat sofa with 2 chaise longues | 1 |
| sofá | 3-seat sofa with bed | 1 |
| sofá | Chaise longue | 1 |
| **sofá (total)** | | **37** |
| sillón | Armchair | 11 |
| sillón | Armchair with cushion | 1 |
| sillón | Easy chair | 1 |
| sillón | Wing chair | 1 |
| sillón | High-back armchair | 2 |
| sillón | Swivel armchair | 1 |
| sillón | Swivel easy chair | 3 |
| sillón | Rocking-chair | 4 |
| **sillón (total)** | | **24** |
| silla | Chair | 31 |
| silla | Chair with armrests | 4 |
| silla | Chair with long cover | 1 |
| silla | Folding chair | 4 |
| **silla (total)** | | **40** |
| mesa | Table | 23 |
| mesa | Coffee table | 14 |
| mesa | Side table | 11 |
| mesa | Extendable table | 7 |
| mesa | Drop-leaf table | 6 |
| mesa | Gateleg table | 2 |
| mesa | Pedestal table | 2 |
| mesa | Nest of tables, set of 2 | 6 |
| mesa | Console table | 2 |
| mesa | Side table on castors | 2 |
| mesa | Bar table | 1 |
| mesa | Tray table | 1 |
| mesa | Storage table | 2 |
| mesa | Table with drawers | 1 |
| **mesa (total)** | | **80** |
| alfombra | Rug | 8 |
| alfombra | Rug, flatwoven | 42 |
| alfombra | Rug, low pile | 18 |
| alfombra | Rug, high pile | 18 |
| alfombra | Rug, braided | 3 |
| alfombra | Sheepskin | 3 |
| alfombra | Cow hide | 2 |
| **alfombra (total)** | | **94** |

## Excluidos (dudosos)

| `type` | SKUs | Motivo |
|---|---|---|
| Cover two-seat sofa | 1 | se vende la funda, no el sofá |
| Cover for chaise longue | 1 | se vende la funda, no el mueble |
| Swivel chair | 11 | sillas de oficina, fuera de living/comedor |
| Swivel chair with armrests | 2 | sillas de oficina, fuera de living/comedor |
| Junior chair | 5 | silla infantil |
| Stool | 10 | taburete: el detector 'chair' no lo representa (ver FUTURO.md) |
| Bar stool | 1 | taburete (ver FUTURO.md) |
| Bar stool with backrest | 1 | taburete (ver FUTURO.md) |
| Wall-mounted drop-leaf table | 2 | mesa de pared, no es un mueble apoyado |

Resto del catálogo (`other`): 1916 SKUs en 633 valores de `type`.
