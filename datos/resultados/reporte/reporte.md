# Retrieval por texto (855 productos, ambientes IKEA)

Corridas: `20261022-213008_ablacion-retrieval`.

| método                                      | corrida                            | embedder   | texto            | filtro   | base   | consulta   | rerank   |   consultas |   hit@1 | hit@1_ic95     |   hit@3 |   hit@10 |   mrr@10 | mrr@10_ic95    |   recall_item@10 |   azar_hit@1 |
|:--------------------------------------------|:-----------------------------------|:-----------|:-----------------|:---------|:-------|:-----------|:---------|------------:|--------:|:---------------|--------:|---------:|---------:|:---------------|-----------------:|-------------:|
| hashing|description|filtro-kind             | 20261022-213008_ablacion-retrieval | hashing    | description      | kind     | chroma | full       |          |         552 |  0.5127 | [0.464, 0.563] |  0.7101 |   0.8841 |   0.6286 | [0.588, 0.672] |           0.8916 |       0.0523 |
| hashing|description|filtro-type             | 20261022-213008_ablacion-retrieval | hashing    | description      | type     | chroma | full       |          |         552 |  0.5091 | [0.462, 0.559] |  0.7228 |   0.8931 |   0.6333 | [0.595, 0.674] |           0.8897 |       0.016  |
| hashing|description|filtro-none             | 20261022-213008_ablacion-retrieval | hashing    | description      | none     | chroma | full       |          |         552 |  0.4928 | [0.442, 0.544] |  0.7065 |   0.8696 |   0.6161 | [0.577, 0.657] |           0.8764 |       0.0017 |
| hashing|seller|filtro-kind                  | 20261022-213008_ablacion-retrieval | hashing    | seller           | kind     | chroma | full       |          |         552 |  0.1775 | [0.145, 0.211] |  0.3804 |   0.712  |   0.3229 | [0.295, 0.353] |           0.7072 |       0.0523 |
| hashing|seller|filtro-type                  | 20261022-213008_ablacion-retrieval | hashing    | seller           | type     | chroma | full       |          |         552 |  0.1322 | [0.106, 0.158] |  0.2826 |   0.5616 |   0.2428 | [0.216, 0.270] |           0.557  |       0.016  |
| hashing|seller|filtro-none                  | 20261022-213008_ablacion-retrieval | hashing    | seller           | none     | chroma | full       |          |         552 |  0.0761 | [0.057, 0.096] |  0.1703 |   0.3188 |   0.1427 | [0.121, 0.167] |           0.3213 |       0.0017 |
| bge|description|filtro-kind                 | 20261022-213008_ablacion-retrieval | bge        | description      | kind     | chroma | full       |          |         552 |  0.4728 | [0.425, 0.520] |  0.6703 |   0.846  |   0.5889 | [0.548, 0.629] |           0.8612 |       0.0523 |
| bge|description|filtro-type                 | 20261022-213008_ablacion-retrieval | bge        | description      | type     | chroma | full       |          |         552 |  0.4764 | [0.431, 0.522] |  0.6848 |   0.8714 |   0.5994 | [0.562, 0.636] |           0.884  |       0.016  |
| bge|description|filtro-none                 | 20261022-213008_ablacion-retrieval | bge        | description      | none     | chroma | full       |          |         552 |  0.4764 | [0.431, 0.522] |  0.6775 |   0.8659 |   0.5972 | [0.560, 0.634] |           0.8802 |       0.0017 |
| bge|seller|filtro-kind                      | 20261022-213008_ablacion-retrieval | bge        | seller           | kind     | chroma | full       |          |         552 |  0.1866 | [0.151, 0.225] |  0.3967 |   0.6812 |   0.3243 | [0.286, 0.367] |           0.6635 |       0.0523 |
| bge|seller|filtro-type                      | 20261022-213008_ablacion-retrieval | bge        | seller           | type     | chroma | full       |          |         552 |  0.1558 | [0.126, 0.189] |  0.3442 |   0.5598 |   0.2736 | [0.240, 0.312] |           0.5399 |       0.016  |
| bge|seller|filtro-none                      | 20261022-213008_ablacion-retrieval | bge        | seller           | none     | chroma | full       |          |         552 |  0.1322 | [0.107, 0.162] |  0.3025 |   0.5145 |   0.241  | [0.209, 0.276] |           0.5133 |       0.0017 |
| qwen3|description|filtro-kind               | 20261022-213008_ablacion-retrieval | qwen3      | description      | kind     | chroma | full       |          |         552 |  0.5254 | [0.480, 0.568] |  0.7083 |   0.8641 |   0.637  | [0.599, 0.676] |           0.8859 |       0.0523 |
| qwen3|description|filtro-type               | 20261022-213008_ablacion-retrieval | qwen3      | description      | type     | chroma | full       |          |         552 |  0.5326 | [0.490, 0.574] |  0.7283 |   0.8949 |   0.6515 | [0.617, 0.688] |           0.9144 |       0.016  |
| qwen3|description|filtro-none               | 20261022-213008_ablacion-retrieval | qwen3      | description      | none     | chroma | full       |          |         552 |  0.5326 | [0.490, 0.574] |  0.7264 |   0.8877 |   0.65   | [0.615, 0.686] |           0.9087 |       0.0017 |
| qwen3|seller|filtro-kind                    | 20261022-213008_ablacion-retrieval | qwen3      | seller           | kind     | chroma | full       |          |         552 |  0.1504 | [0.126, 0.179] |  0.3188 |   0.6486 |   0.2769 | [0.248, 0.311] |           0.6369 |       0.0523 |
| qwen3|seller|filtro-type                    | 20261022-213008_ablacion-retrieval | qwen3      | seller           | type     | chroma | full       |          |         552 |  0.1232 | [0.100, 0.150] |  0.2554 |   0.5399 |   0.2276 | [0.199, 0.258] |           0.5152 |       0.016  |
| qwen3|seller|filtro-none                    | 20261022-213008_ablacion-retrieval | qwen3      | seller           | none     | chroma | full       |          |         552 |  0.1178 | [0.094, 0.142] |  0.2319 |   0.4601 |   0.2032 | [0.176, 0.231] |           0.4582 |       0.0017 |
| bge|name+description|filtro-kind            | 20261022-213008_ablacion-retrieval | bge        | name+description | kind     | chroma | full       |          |         552 |  0.3931 | [0.355, 0.437] |  0.5978 |   0.8188 |   0.5188 | [0.484, 0.556] |           0.8289 |       0.0523 |
| qwen3|name+description|filtro-kind          | 20261022-213008_ablacion-retrieval | qwen3      | name+description | kind     | chroma | full       |          |         552 |  0.4185 | [0.373, 0.467] |  0.6757 |   0.8424 |   0.5593 | [0.522, 0.597] |           0.8574 |       0.0523 |
| qwen3|description|filtro-type|exact         | 20261022-213008_ablacion-retrieval | qwen3      | description      | type     | exact  | full       |          |         552 |  0.5326 | [0.490, 0.574] |  0.7283 |   0.8949 |   0.6515 | [0.617, 0.688] |           0.9144 |       0.016  |
| qwen3|description|filtro-kind|exact         | 20261022-213008_ablacion-retrieval | qwen3      | description      | kind     | exact  | full       |          |         552 |  0.5254 | [0.480, 0.568] |  0.7083 |   0.8641 |   0.637  | [0.599, 0.676] |           0.8859 |       0.0523 |
| qwen3|description|filtro-type|consulta-type | 20261022-213008_ablacion-retrieval | qwen3      | description      | type     | chroma | type       |          |         552 |  0.2917 | [0.249, 0.335] |  0.5344 |   0.8098 |   0.4435 | [0.404, 0.483] |           0.8251 |       0.016  |
| qwen3|description|filtro-type|consulta-kind | 20261022-213008_ablacion-retrieval | qwen3      | description      | type     | chroma | kind       |          |         552 |  0.0634 | [0.039, 0.091] |  0.1739 |   0.404  |   0.1403 | [0.115, 0.172] |           0.3308 |       0.016  |

## hit@1 por categoría

| método | armchair (18) | bench (4) | cabinet (41) | chair (45) | deco (208) | dresser (1) | lamp (64) | ottoman (6) | rug (45) | shelf (21) | sofa (24) | stool (8) | table (67) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hashing|description|filtro-kind | 0.67 | 1.00 | 0.71 | 0.67 | 0.34 | 1.00 | 0.67 | 0.83 | 0.36 | 0.48 | 0.38 | 1.00 | 0.69 |
| hashing|description|filtro-type | 0.67 | 1.00 | 0.78 | 0.67 | 0.33 | 1.00 | 0.58 | 0.83 | 0.36 | 0.48 | 0.38 | 1.00 | 0.73 |
| hashing|description|filtro-none | 0.67 | 0.75 | 0.76 | 0.67 | 0.32 | 0.00 | 0.56 | 0.67 | 0.36 | 0.43 | 0.33 | 0.88 | 0.73 |
| hashing|seller|filtro-kind | 0.17 | 0.25 | 0.24 | 0.22 | 0.15 | 0.00 | 0.11 | 0.33 | 0.07 | 0.19 | 0.25 | 0.38 | 0.27 |
| hashing|seller|filtro-type | 0.11 | 0.25 | 0.20 | 0.22 | 0.11 | 0.00 | 0.06 | 0.33 | 0.07 | 0.14 | 0.21 | 0.12 | 0.16 |
| hashing|seller|filtro-none | 0.06 | 0.00 | 0.07 | 0.20 | 0.06 | 0.00 | 0.05 | 0.00 | 0.07 | 0.05 | 0.08 | 0.12 | 0.10 |
| bge|description|filtro-kind | 0.56 | 1.00 | 0.56 | 0.62 | 0.34 | 1.00 | 0.61 | 0.67 | 0.18 | 0.43 | 0.54 | 1.00 | 0.64 |
| bge|description|filtro-type | 0.50 | 1.00 | 0.59 | 0.62 | 0.34 | 1.00 | 0.61 | 0.67 | 0.18 | 0.43 | 0.54 | 1.00 | 0.67 |
| bge|description|filtro-none | 0.50 | 1.00 | 0.59 | 0.62 | 0.34 | 1.00 | 0.61 | 0.67 | 0.18 | 0.43 | 0.54 | 1.00 | 0.67 |
| bge|seller|filtro-kind | 0.17 | 0.75 | 0.17 | 0.33 | 0.14 | 0.00 | 0.12 | 0.00 | 0.07 | 0.10 | 0.25 | 0.62 | 0.31 |
| bge|seller|filtro-type | 0.11 | 0.75 | 0.17 | 0.29 | 0.13 | 0.00 | 0.08 | 0.00 | 0.07 | 0.10 | 0.21 | 0.38 | 0.22 |
| bge|seller|filtro-none | 0.11 | 0.25 | 0.15 | 0.29 | 0.10 | 0.00 | 0.08 | 0.00 | 0.07 | 0.10 | 0.21 | 0.38 | 0.19 |
| qwen3|description|filtro-kind | 0.72 | 1.00 | 0.68 | 0.84 | 0.36 | 1.00 | 0.61 | 1.00 | 0.31 | 0.43 | 0.58 | 0.88 | 0.64 |
| qwen3|description|filtro-type | 0.72 | 1.00 | 0.73 | 0.84 | 0.35 | 1.00 | 0.59 | 1.00 | 0.31 | 0.43 | 0.62 | 0.88 | 0.69 |
| qwen3|description|filtro-none | 0.72 | 1.00 | 0.73 | 0.84 | 0.35 | 1.00 | 0.59 | 1.00 | 0.31 | 0.43 | 0.62 | 0.88 | 0.69 |
| qwen3|seller|filtro-kind | 0.11 | 0.75 | 0.10 | 0.44 | 0.08 | 1.00 | 0.14 | 0.00 | 0.04 | 0.24 | 0.17 | 0.25 | 0.21 |
| qwen3|seller|filtro-type | 0.11 | 0.75 | 0.12 | 0.38 | 0.08 | 1.00 | 0.06 | 0.00 | 0.04 | 0.19 | 0.12 | 0.12 | 0.13 |
| qwen3|seller|filtro-none | 0.11 | 0.75 | 0.12 | 0.38 | 0.08 | 1.00 | 0.06 | 0.00 | 0.04 | 0.14 | 0.12 | 0.00 | 0.13 |
| bge|name+description|filtro-kind | 0.39 | 1.00 | 0.41 | 0.58 | 0.26 | 1.00 | 0.42 | 0.83 | 0.22 | 0.24 | 0.46 | 0.88 | 0.63 |
| qwen3|name+description|filtro-kind | 0.72 | 0.50 | 0.39 | 0.64 | 0.32 | 1.00 | 0.44 | 0.67 | 0.22 | 0.33 | 0.46 | 0.88 | 0.55 |
| qwen3|description|filtro-type|exact | 0.72 | 1.00 | 0.73 | 0.84 | 0.35 | 1.00 | 0.59 | 1.00 | 0.31 | 0.43 | 0.62 | 0.88 | 0.69 |
| qwen3|description|filtro-kind|exact | 0.72 | 1.00 | 0.68 | 0.84 | 0.36 | 1.00 | 0.61 | 1.00 | 0.31 | 0.43 | 0.58 | 0.88 | 0.64 |
| qwen3|description|filtro-type|consulta-type | 0.22 | 0.50 | 0.24 | 0.69 | 0.23 | 0.00 | 0.27 | 0.50 | 0.13 | 0.29 | 0.17 | 0.75 | 0.36 |
| qwen3|description|filtro-type|consulta-kind | 0.06 | 0.00 | 0.05 | 0.07 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.25 | 0.06 |

## Por pasada de consultas (v1: muebles del primer alcance; v2: la ampliación)

| método | consultas_ambiente_v1 hit@1 / MRR | consultas_ambiente_v2 hit@1 / MRR |
|---|---|---|
| hashing|description|filtro-kind | 0.568 / 0.687 (199) | 0.482 / 0.596 (353) |
| hashing|description|filtro-type | 0.583 / 0.715 (199) | 0.467 / 0.587 (353) |
| hashing|description|filtro-none | 0.578 / 0.703 (199) | 0.445 / 0.567 (353) |
| hashing|seller|filtro-kind | 0.201 / 0.323 (199) | 0.164 / 0.323 (353) |
| hashing|seller|filtro-type | 0.156 / 0.252 (199) | 0.119 / 0.238 (353) |
| hashing|seller|filtro-none | 0.111 / 0.163 (199) | 0.057 / 0.131 (353) |
| bge|description|filtro-kind | 0.513 / 0.632 (199) | 0.450 / 0.564 (353) |
| bge|description|filtro-type | 0.518 / 0.647 (199) | 0.453 / 0.573 (353) |
| bge|description|filtro-none | 0.518 / 0.643 (199) | 0.453 / 0.571 (353) |
| bge|seller|filtro-kind | 0.241 / 0.358 (199) | 0.156 / 0.305 (353) |
| bge|seller|filtro-type | 0.191 / 0.295 (199) | 0.136 / 0.262 (353) |
| bge|seller|filtro-none | 0.181 / 0.282 (199) | 0.105 / 0.218 (353) |
| qwen3|description|filtro-kind | 0.613 / 0.708 (199) | 0.476 / 0.597 (353) |
| qwen3|description|filtro-type | 0.633 / 0.736 (199) | 0.476 / 0.604 (353) |
| qwen3|description|filtro-none | 0.633 / 0.733 (199) | 0.476 / 0.603 (353) |
| qwen3|seller|filtro-kind | 0.211 / 0.339 (199) | 0.116 / 0.242 (353) |
| qwen3|seller|filtro-type | 0.166 / 0.279 (199) | 0.099 / 0.199 (353) |
| qwen3|seller|filtro-none | 0.166 / 0.269 (199) | 0.091 / 0.166 (353) |
| bge|name+description|filtro-kind | 0.482 / 0.598 (199) | 0.343 / 0.474 (353) |
| qwen3|name+description|filtro-kind | 0.502 / 0.623 (199) | 0.371 / 0.523 (353) |
| qwen3|description|filtro-type|exact | 0.633 / 0.736 (199) | 0.476 / 0.604 (353) |
| qwen3|description|filtro-kind|exact | 0.613 / 0.708 (199) | 0.476 / 0.597 (353) |
| qwen3|description|filtro-type|consulta-type | 0.347 / 0.503 (199) | 0.261 / 0.410 (353) |
| qwen3|description|filtro-type|consulta-kind | 0.040 / 0.081 (199) | 0.076 / 0.174 (353) |

## Base vectorial, query rewriting y reranking

![avanzado](avanzado.png)

![camino](camino_texto.png)

## Texto vs. imagen

| | consultas | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|---|
| v0 imagen (20261006-231131_retriever_abl-retriever-name-dinov3__method-none__category_filter-true) | 325 recortes | 0.508 | 0.819 | 0.603 |
| v1 texto (qwen3|description|filtro-type) | 207 consultas | 0.618 | 0.908 | 0.717 |

![texto vs imagen](texto_vs_imagen.png)

## Corridas anteriores (otro catálogo u otras consultas)

No se mezclan con las de arriba: cambian el universo de búsqueda o las consultas.

### `20261021-133226_ablacion-texto` (275 productos)

| método                             |   consultas |   hit@1 |   hit@10 |   mrr@10 |
|:-----------------------------------|------------:|--------:|---------:|---------:|
| hashing|description|filtro-kind    |         207 |  0.5459 |   0.8937 |   0.6698 |
| hashing|description|filtro-type    |         207 |  0.5604 |   0.9324 |   0.6963 |
| hashing|description|filtro-none    |         207 |  0.5604 |   0.9275 |   0.6924 |
| hashing|seller|filtro-kind         |         207 |  0.1932 |   0.6957 |   0.3144 |
| hashing|seller|filtro-type         |         207 |  0.1546 |   0.5604 |   0.2469 |
| hashing|seller|filtro-none         |         207 |  0.1449 |   0.4396 |   0.2083 |
| bge|description|filtro-kind        |         207 |  0.4976 |   0.8937 |   0.6197 |
| bge|description|filtro-type        |         207 |  0.5024 |   0.9179 |   0.6337 |
| bge|description|filtro-none        |         207 |  0.5024 |   0.9179 |   0.6315 |
| bge|seller|filtro-kind             |         207 |  0.2367 |   0.6473 |   0.3476 |
| bge|seller|filtro-type             |         207 |  0.1884 |   0.5749 |   0.2946 |
| bge|seller|filtro-none             |         207 |  0.1884 |   0.5556 |   0.2905 |
| qwen3|description|filtro-kind      |         207 |  0.599  |   0.8744 |   0.6903 |
| qwen3|description|filtro-type      |         207 |  0.6184 |   0.9082 |   0.7172 |
| qwen3|description|filtro-none      |         207 |  0.6184 |   0.8986 |   0.7152 |
| qwen3|seller|filtro-kind           |         207 |  0.2077 |   0.657  |   0.3277 |
| qwen3|seller|filtro-type           |         207 |  0.1643 |   0.5894 |   0.2686 |
| qwen3|seller|filtro-none           |         207 |  0.1643 |   0.5749 |   0.2655 |
| bge|name+description|filtro-kind   |         207 |  0.4589 |   0.8502 |   0.5814 |
| qwen3|name+description|filtro-kind |         207 |  0.4831 |   0.8406 |   0.6031 |

### `20261021-141030_ablacion-texto-268` (268 productos)

| método                             |   consultas |   hit@1 |   hit@10 |   mrr@10 |
|:-----------------------------------|------------:|--------:|---------:|---------:|
| hashing|description|filtro-kind    |         198 |  0.5707 |   0.8939 |   0.6882 |
| hashing|description|filtro-type    |         198 |  0.5859 |   0.9343 |   0.716  |
| hashing|description|filtro-none    |         198 |  0.5859 |   0.9293 |   0.7118 |
| hashing|seller|filtro-kind         |         198 |  0.202  |   0.6869 |   0.324  |
| hashing|seller|filtro-type         |         198 |  0.1566 |   0.5505 |   0.2532 |
| hashing|seller|filtro-none         |         198 |  0.1465 |   0.4343 |   0.213  |
| bge|description|filtro-kind        |         198 |  0.5152 |   0.8939 |   0.634  |
| bge|description|filtro-type        |         198 |  0.5202 |   0.9192 |   0.6486 |
| bge|description|filtro-none        |         198 |  0.5202 |   0.9192 |   0.6463 |
| bge|seller|filtro-kind             |         198 |  0.2424 |   0.6667 |   0.3589 |
| bge|seller|filtro-type             |         198 |  0.1919 |   0.5909 |   0.3034 |
| bge|seller|filtro-none             |         198 |  0.1919 |   0.5707 |   0.2992 |
| qwen3|description|filtro-kind      |         198 |  0.6162 |   0.8788 |   0.7093 |
| qwen3|description|filtro-type      |         198 |  0.6364 |   0.9141 |   0.7374 |
| qwen3|description|filtro-none      |         198 |  0.6364 |   0.904  |   0.7353 |
| qwen3|seller|filtro-kind           |         198 |  0.2121 |   0.6768 |   0.3398 |
| qwen3|seller|filtro-type           |         198 |  0.1667 |   0.6212 |   0.2805 |
| qwen3|seller|filtro-none           |         198 |  0.1667 |   0.6061 |   0.2772 |
| bge|name+description|filtro-kind   |         198 |  0.4848 |   0.8485 |   0.6001 |
| qwen3|name+description|filtro-kind |         198 |  0.5051 |   0.8384 |   0.6233 |

### `20261022-175001_ablacion-reranking` (268 productos)

| método                                    |   consultas |   hit@1 |   hit@10 |   mrr@10 |
|:------------------------------------------|------------:|--------:|---------:|---------:|
| qwen3|description|filtro-type             |         198 |  0.6364 |   0.9141 |   0.7374 |
| qwen3|description|filtro-type|rerank-opus |         198 |  0.803  |   0.9141 |   0.8474 |

