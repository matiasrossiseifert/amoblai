# Retrieval por texto (65 ambientes IKEA)

Corridas: `20261021-161057_ablacion-retrieval`, `20261021-161311_ablacion-reranking`.

| método                                      | corrida                            | embedder   | texto            | filtro   | base   | consulta   | rerank   |   consultas |   hit@1 | hit@1_ic95     |   hit@3 |   hit@10 |   mrr@10 | mrr@10_ic95    |   recall_item@10 |   azar_hit@1 |
|:--------------------------------------------|:-----------------------------------|:-----------|:-----------------|:---------|:-------|:-----------|:---------|------------:|--------:|:---------------|--------:|---------:|---------:|:---------------|-----------------:|-------------:|
| hashing|description|filtro-kind             | 20261021-161057_ablacion-retrieval | hashing    | description      | kind     | chroma | full       |          |         198 |  0.5707 | [0.497, 0.650] |  0.7778 |   0.8939 |   0.6882 | [0.629, 0.754] |           0.8447 |       0.0373 |
| hashing|description|filtro-type             | 20261021-161057_ablacion-retrieval | hashing    | description      | type     | chroma | full       |          |         198 |  0.5859 | [0.515, 0.663] |  0.8283 |   0.9343 |   0.716  | [0.664, 0.776] |           0.8835 |       0.0202 |
| hashing|description|filtro-none             | 20261021-161057_ablacion-retrieval | hashing    | description      | none     | chroma | full       |          |         198 |  0.5859 | [0.515, 0.663] |  0.8131 |   0.9293 |   0.7118 | [0.661, 0.772] |           0.8835 |       0.0049 |
| hashing|seller|filtro-kind                  | 20261021-161057_ablacion-retrieval | hashing    | seller           | kind     | chroma | full       |          |         198 |  0.202  | [0.136, 0.275] |  0.3434 |   0.6869 |   0.3239 | [0.265, 0.386] |           0.6553 |       0.0373 |
| hashing|seller|filtro-type                  | 20261021-161057_ablacion-retrieval | hashing    | seller           | type     | chroma | full       |          |         198 |  0.1566 | [0.102, 0.219] |  0.2727 |   0.5606 |   0.2539 | [0.202, 0.312] |           0.5388 |       0.0202 |
| hashing|seller|filtro-none                  | 20261021-161057_ablacion-retrieval | hashing    | seller           | none     | chroma | full       |          |         198 |  0.1465 | [0.096, 0.207] |  0.2222 |   0.4293 |   0.2124 | [0.161, 0.272] |           0.4175 |       0.0049 |
| bge|description|filtro-kind                 | 20261021-161057_ablacion-retrieval | bge        | description      | kind     | chroma | full       |          |         198 |  0.5152 | [0.446, 0.587] |  0.7222 |   0.8939 |   0.634  | [0.578, 0.691] |           0.8544 |       0.0373 |
| bge|description|filtro-type                 | 20261021-161057_ablacion-retrieval | bge        | description      | type     | chroma | full       |          |         198 |  0.5202 | [0.452, 0.591] |  0.7475 |   0.9192 |   0.6486 | [0.595, 0.703] |           0.8981 |       0.0202 |
| bge|description|filtro-none                 | 20261021-161057_ablacion-retrieval | bge        | description      | none     | chroma | full       |          |         198 |  0.5202 | [0.452, 0.591] |  0.7374 |   0.9192 |   0.6463 | [0.592, 0.701] |           0.8981 |       0.0049 |
| bge|seller|filtro-kind                      | 20261021-161057_ablacion-retrieval | bge        | seller           | kind     | chroma | full       |          |         198 |  0.2424 | [0.173, 0.308] |  0.4242 |   0.6717 |   0.3595 | [0.295, 0.421] |           0.6408 |       0.0373 |
| bge|seller|filtro-type                      | 20261021-161057_ablacion-retrieval | bge        | seller           | type     | chroma | full       |          |         198 |  0.1919 | [0.137, 0.250] |  0.3687 |   0.5859 |   0.3029 | [0.247, 0.362] |           0.5777 |       0.0202 |
| bge|seller|filtro-none                      | 20261021-161057_ablacion-retrieval | bge        | seller           | none     | chroma | full       |          |         198 |  0.1919 | [0.137, 0.250] |  0.3636 |   0.5758 |   0.2998 | [0.244, 0.359] |           0.5728 |       0.0049 |
| qwen3|description|filtro-kind               | 20261021-161057_ablacion-retrieval | qwen3      | description      | kind     | chroma | full       |          |         198 |  0.6162 | [0.553, 0.680] |  0.7727 |   0.8788 |   0.7093 | [0.658, 0.764] |           0.835  |       0.0373 |
| qwen3|description|filtro-none               | 20261021-161057_ablacion-retrieval | qwen3      | description      | none     | chroma | full       |          |         198 |  0.6364 | [0.575, 0.699] |  0.8131 |   0.904  |   0.7353 | [0.686, 0.784] |           0.8835 |       0.0049 |
| qwen3|seller|filtro-kind                    | 20261021-161057_ablacion-retrieval | qwen3      | seller           | kind     | chroma | full       |          |         198 |  0.2121 | [0.158, 0.266] |  0.4091 |   0.6717 |   0.3394 | [0.283, 0.394] |           0.6408 |       0.0373 |
| qwen3|seller|filtro-type                    | 20261021-161057_ablacion-retrieval | qwen3      | seller           | type     | chroma | full       |          |         198 |  0.1667 | [0.118, 0.220] |  0.3182 |   0.6212 |   0.2805 | [0.230, 0.332] |           0.5922 |       0.0202 |
| qwen3|seller|filtro-none                    | 20261021-161057_ablacion-retrieval | qwen3      | seller           | none     | chroma | full       |          |         198 |  0.1667 | [0.118, 0.220] |  0.3182 |   0.601  |   0.2767 | [0.226, 0.330] |           0.5825 |       0.0049 |
| bge|name+description|filtro-kind            | 20261021-161057_ablacion-retrieval | bge        | name+description | kind     | chroma | full       |          |         198 |  0.4848 | [0.419, 0.553] |  0.6919 |   0.8485 |   0.6001 | [0.546, 0.653] |           0.8155 |       0.0373 |
| qwen3|name+description|filtro-kind          | 20261021-161057_ablacion-retrieval | qwen3      | name+description | kind     | chroma | full       |          |         198 |  0.5051 | [0.435, 0.580] |  0.7424 |   0.8384 |   0.6233 | [0.569, 0.681] |           0.801  |       0.0373 |
| qwen3|description|filtro-type|exact         | 20261021-161057_ablacion-retrieval | qwen3      | description      | type     | exact  | full       |          |         198 |  0.6364 | [0.575, 0.699] |  0.8131 |   0.9141 |   0.7374 | [0.689, 0.785] |           0.8932 |       0.0202 |
| qwen3|description|filtro-kind|exact         | 20261021-161057_ablacion-retrieval | qwen3      | description      | kind     | exact  | full       |          |         198 |  0.6162 | [0.553, 0.680] |  0.7727 |   0.8788 |   0.7093 | [0.658, 0.764] |           0.835  |       0.0373 |
| qwen3|description|filtro-type|consulta-type | 20261021-161057_ablacion-retrieval | qwen3      | description      | type     | chroma | type       |          |         198 |  0.3535 | [0.281, 0.432] |  0.6364 |   0.8434 |   0.5098 | [0.454, 0.567] |           0.8204 |       0.0202 |
| qwen3|description|filtro-type|consulta-kind | 20261021-161057_ablacion-retrieval | qwen3      | description      | type     | chroma | kind       |          |         198 |  0.0404 | [0.014, 0.073] |  0.0909 |   0.2374 |   0.082  | [0.053, 0.117] |           0.2136 |       0.0202 |
| qwen3|description|filtro-type               | 20261021-161311_ablacion-reranking | qwen3      | description      | type     | chroma | full       |          |         198 |  0.6364 | [0.575, 0.699] |  0.8131 |   0.9141 |   0.7374 | [0.689, 0.785] |           0.8932 |       0.0202 |
| qwen3|description|filtro-type|rerank-haiku  | 20261021-161311_ablacion-reranking | qwen3      | description      | type     | chroma | full       | haiku    |         198 |  0.7677 | [0.708, 0.829] |  0.8687 |   0.9141 |   0.8228 | [0.775, 0.875] |           0.8932 |       0.0202 |

## Base vectorial, query rewriting y reranking

![avanzado](avanzado.png)

![camino](camino_texto.png)

## Texto vs. imagen

| | consultas | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|---|
| v0 imagen (20261006-231131_retriever_abl-retriever-name-dinov3__method-none__category_filter-true) | 325 recortes | 0.508 | 0.819 | 0.603 |
| v1 texto (qwen3|description|filtro-type|exact) | 198 consultas | 0.636 | 0.914 | 0.737 |

![texto vs imagen](texto_vs_imagen.png)

