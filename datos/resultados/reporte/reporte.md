# Retrieval por texto (819 productos, ambientes IKEA)

Corridas: `20261109-235522_ablacion-reranking`, `20261110-003643_ablacion-retrieval`, `20261112-090439_ablacion-camino`, `20261112-092807_ablacion-hibrido`, `20261112-093413_ablacion-consulta`, `20261112-093720_ablacion-reranking-local`.

| método                                                     | corrida                                  | embedder   | texto            | filtro   | base   | consulta   | rerank          |   consultas |   hit@1 | hit@1_ic95     |   hit@3 |   hit@10 |   mrr@10 | mrr@10_ic95    |   recall_item@10 |   context_precision@10 |   ndcg@10 |   context_recall@3 |   context_recall@10 |   azar_hit@1 |
|:-----------------------------------------------------------|:-----------------------------------------|:-----------|:-----------------|:---------|:-------|:-----------|:----------------|------------:|--------:|:---------------|--------:|---------:|---------:|:---------------|-----------------:|-----------------------:|----------:|-------------------:|--------------------:|-------------:|
| qwen3|description|filtro-type|rerank-opus                  | 20261109-235522_ablacion-reranking       | qwen3      | description      | type     | chroma | full       | opus            |         549 |  0.6867 | [0.648, 0.730] |  0.8142 |   0.8925 |   0.7601 | [0.726, 0.795] |           0.9136 |                 0.7323 |    0.7261 |             0.8718 |              0.9267 |       0.0166 |
| hashing|description|filtro-kind                            | 20261110-003643_ablacion-retrieval       | hashing    | description      | kind     | chroma | full       |                 |         549 |  0.5155 | [0.465, 0.568] |  0.7104 |   0.8852 |   0.631  | [0.590, 0.676] |           0.8925 |                 0.6184 |    0.6316 |             0.7424 |              0.9081 |       0.0534 |
| hashing|description|filtro-type                            | 20261110-003643_ablacion-retrieval       | hashing    | description      | type     | chroma | full       |                 |         549 |  0.51   | [0.462, 0.561] |  0.7213 |   0.8925 |   0.6341 | [0.595, 0.675] |           0.8906 |                 0.6185 |    0.639  |             0.751  |              0.9092 |       0.0166 |
| hashing|description|filtro-none                            | 20261110-003643_ablacion-retrieval       | hashing    | description      | none     | chroma | full       |                 |         549 |  0.4954 | [0.445, 0.548] |  0.7067 |   0.8707 |   0.6184 | [0.579, 0.661] |           0.8791 |                 0.6042 |    0.6181 |             0.7446 |              0.9113 |       0.0018 |
| hashing|seller|filtro-kind                                 | 20261110-003643_ablacion-retrieval       | hashing    | seller           | kind     | chroma | full       |                 |         549 |  0.173  | [0.140, 0.207] |  0.3807 |   0.7158 |   0.3217 | [0.292, 0.351] |           0.7102 |                 0.3153 |    0.3753 |             0.3787 |              0.7092 |       0.0534 |
| hashing|seller|filtro-type                                 | 20261110-003643_ablacion-retrieval       | hashing    | seller           | type     | chroma | full       |                 |         549 |  0.1275 | [0.100, 0.156] |  0.286  |   0.5574 |   0.2412 | [0.215, 0.271] |           0.5528 |                 0.2375 |    0.2838 |             0.2983 |              0.5656 |       0.0166 |
| hashing|seller|filtro-none                                 | 20261110-003643_ablacion-retrieval       | hashing    | seller           | none     | chroma | full       |                 |         549 |  0.0765 | [0.057, 0.096] |  0.1694 |   0.3115 |   0.1423 | [0.119, 0.167] |           0.3148 |                 0.1414 |    0.1595 |             0.2045 |              0.3841 |       0.0018 |
| bge|description|filtro-kind                                | 20261110-003643_ablacion-retrieval       | bge        | description      | kind     | chroma | full       |                 |         549 |  0.4754 | [0.427, 0.524] |  0.674  |   0.8488 |   0.5921 | [0.550, 0.633] |           0.8637 |                 0.5771 |    0.5921 |             0.7116 |              0.8884 |       0.0534 |
| bge|description|filtro-type                                | 20261110-003643_ablacion-retrieval       | bge        | description      | type     | chroma | full       |                 |         549 |  0.4791 | [0.433, 0.525] |  0.6867 |   0.8707 |   0.6018 | [0.564, 0.639] |           0.8848 |                 0.5845 |    0.6083 |             0.73   |              0.9081 |       0.0166 |
| bge|description|filtro-none                                | 20261110-003643_ablacion-retrieval       | bge        | description      | none     | chroma | full       |                 |         549 |  0.4791 | [0.433, 0.525] |  0.6794 |   0.8652 |   0.5996 | [0.561, 0.637] |           0.881  |                 0.5842 |    0.6044 |             0.7292 |              0.914  |       0.0018 |
| bge|seller|filtro-kind                                     | 20261110-003643_ablacion-retrieval       | bge        | seller           | kind     | chroma | full       |                 |         549 |  0.1894 | [0.153, 0.228] |  0.3953 |   0.6812 |   0.3267 | [0.287, 0.368] |           0.6622 |                 0.3223 |    0.3721 |             0.4169 |              0.6958 |       0.0534 |
| bge|seller|filtro-type                                     | 20261110-003643_ablacion-retrieval       | bge        | seller           | type     | chroma | full       |                 |         549 |  0.1585 | [0.128, 0.192] |  0.3424 |   0.5556 |   0.2751 | [0.241, 0.313] |           0.5374 |                 0.2713 |    0.3123 |             0.3616 |              0.5757 |       0.0166 |
| bge|seller|filtro-none                                     | 20261110-003643_ablacion-retrieval       | bge        | seller           | none     | chroma | full       |                 |         549 |  0.133  | [0.108, 0.162] |  0.3024 |   0.5118 |   0.2413 | [0.211, 0.275] |           0.5125 |                 0.2378 |    0.282  |             0.3433 |              0.5676 |       0.0018 |
| qwen3|seller|filtro-kind                                   | 20261110-003643_ablacion-retrieval       | qwen3      | seller           | kind     | chroma | full       |                 |         549 |  0.153  | [0.128, 0.182] |  0.3224 |   0.6594 |   0.2808 | [0.251, 0.316] |           0.6507 |                 0.2749 |    0.3371 |             0.3474 |              0.6797 |       0.0534 |
| qwen3|seller|filtro-type                                   | 20261110-003643_ablacion-retrieval       | qwen3      | seller           | type     | chroma | full       |                 |         549 |  0.1257 | [0.102, 0.154] |  0.255  |   0.5537 |   0.2308 | [0.203, 0.262] |           0.5298 |                 0.229  |    0.2777 |             0.2773 |              0.5728 |       0.0166 |
| qwen3|seller|filtro-none                                   | 20261110-003643_ablacion-retrieval       | qwen3      | seller           | none     | chroma | full       |                 |         549 |  0.1202 | [0.097, 0.145] |  0.2332 |   0.4645 |   0.2053 | [0.178, 0.234] |           0.4607 |                 0.204  |    0.2422 |             0.2586 |              0.5118 |       0.0018 |
| bge|name+description|filtro-kind                           | 20261110-003643_ablacion-retrieval       | bge        | name+description | kind     | chroma | full       |                 |         549 |  0.3934 | [0.355, 0.440] |  0.6011 |   0.827  |   0.5214 | [0.486, 0.561] |           0.833  |                 0.5145 |    0.5395 |             0.672  |              0.8578 |       0.0534 |
| qwen3|name+description|filtro-kind                         | 20261110-003643_ablacion-retrieval       | qwen3      | name+description | kind     | chroma | full       |                 |         549 |  0.4208 | [0.376, 0.470] |  0.6776 |   0.8434 |   0.5611 | [0.524, 0.600] |           0.858  |                 0.5448 |    0.568  |             0.7283 |              0.8789 |       0.0534 |
| qwen3|description|filtro-type|exact                        | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | exact  | full       |                 |         549 |  0.5355 | [0.491, 0.577] |  0.7322 |   0.8925 |   0.6536 | [0.617, 0.690] |           0.9136 |                 0.6315 |    0.6539 |             0.7851 |              0.9267 |       0.0166 |
| qwen3|description|filtro-kind|exact                        | 20261110-003643_ablacion-retrieval       | qwen3      | description      | kind     | exact  | full       |                 |         549 |  0.5301 | [0.486, 0.573] |  0.714  |   0.8634 |   0.6407 | [0.602, 0.679] |           0.8848 |                 0.6244 |    0.6308 |             0.7605 |              0.8988 |       0.0534 |
| qwen3|description|filtro-type|consulta-type                | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | type       |                 |         549 |  0.2933 | [0.250, 0.336] |  0.5392 |   0.8106 |   0.4457 | [0.406, 0.485] |           0.8273 |                 0.4297 |    0.4768 |             0.5799 |              0.8424 |       0.0166 |
| qwen3|description|filtro-type|consulta-kind                | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | kind       |                 |         549 |  0.0638 | [0.039, 0.092] |  0.1767 |   0.4044 |   0.1418 | [0.116, 0.172] |           0.334  |                 0.1379 |    0.1707 |             0.1443 |              0.3457 |       0.0166 |
| qwen3|description|filtro-type|dim-32                       | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.4281 | [0.387, 0.472] |  0.6448 |   0.8233 |   0.5553 | [0.520, 0.592] |           0.8503 |                 0.5424 |    0.5626 |             0.6993 |              0.8785 |       0.0166 |
| qwen3|description|filtro-type|dim-64                       | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.4608 | [0.418, 0.504] |  0.6867 |   0.867  |   0.5919 | [0.557, 0.628] |           0.881  |                 0.5749 |    0.6009 |             0.7316 |              0.904  |       0.0166 |
| qwen3|description|filtro-type|dim-128                      | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.5064 | [0.463, 0.547] |  0.714  |   0.8852 |   0.6253 | [0.590, 0.661] |           0.9002 |                 0.6056 |    0.6305 |             0.7657 |              0.9195 |       0.0166 |
| qwen3|description|filtro-type|dim-256                      | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.5155 | [0.473, 0.556] |  0.7013 |   0.8944 |   0.6334 | [0.598, 0.667] |           0.9136 |                 0.6168 |    0.639  |             0.7508 |              0.9232 |       0.0166 |
| qwen3|description|filtro-type|dim-512                      | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.5319 | [0.487, 0.575] |  0.7304 |   0.8925 |   0.649  | [0.613, 0.684] |           0.9136 |                 0.6283 |    0.6493 |             0.7664 |              0.9257 |       0.0166 |
| qwen3|description|filtro-type|chunks-lines-max             | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.2732 | [0.239, 0.309] |  0.5264 |   0.8051 |   0.4335 | [0.407, 0.464] |           0.7927 |                 0.4288 |    0.4733 |             0.5553 |              0.813  |       0.0166 |
| qwen3|description|filtro-type|chunks-lines-aligned         | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.5137 | [0.468, 0.564] |  0.7268 |   0.8907 |   0.6355 | [0.597, 0.675] |           0.9098 |                 0.6181 |    0.6415 |             0.7687 |              0.9252 |       0.0166 |
| qwen3|description|filtro-type|rerank-minilm-reranker       | 20261110-003643_ablacion-retrieval       | qwen3      | description      | type     | chroma | full       | minilm-reranker |         549 |  0.4189 | [0.369, 0.466] |  0.6521 |   0.8925 |   0.5651 | [0.525, 0.606] |           0.9136 |                 0.5453 |    0.591  |             0.6933 |              0.9267 |       0.0166 |
| qwen3|seller-full|filtro-none|consulta-piece               | 20261112-090439_ablacion-camino          | qwen3      | seller-full      | none     | chroma | piece      |                 |         549 |  0.1093 | [0.082, 0.135] |  0.2168 |   0.439  |   0.1937 | [0.170, 0.218] |           0.4568 |                 0.191  |    0.2304 |             0.2504 |              0.4892 |       0.0018 |
| clip|description|filtro-kind                               | 20261112-092807_ablacion-hibrido         | clip       | description      | kind     | chroma | full       |                 |         549 |  0.357  | [0.313, 0.401] |  0.623  |   0.8488 |   0.5116 | [0.471, 0.550] |           0.8637 |                 0.4968 |    0.5267 |             0.6388 |              0.863  |       0.0534 |
| qwen3|description|filtro-kind|+bm25                        | 20261112-092807_ablacion-hibrido         | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.5811 | [0.538, 0.627] |  0.7322 |   0.8761 |   0.674  | [0.637, 0.712] |           0.9002 |                 0.6542 |    0.6577 |             0.7675 |              0.9142 |       0.0534 |
| qwen3|description|filtro-kind|+bm25|fusion-rrf             | 20261112-092807_ablacion-hibrido         | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.5446 | [0.504, 0.584] |  0.7432 |   0.8761 |   0.6555 | [0.621, 0.691] |           0.8983 |                 0.6377 |    0.6446 |             0.7826 |              0.913  |       0.0534 |
| qwen3|description|filtro-kind|+siglip2                     | 20261112-092807_ablacion-hibrido         | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.5847 | [0.538, 0.637] |  0.7596 |   0.8889 |   0.6891 | [0.650, 0.730] |           0.9136 |                 0.6688 |    0.6657 |             0.809  |              0.9261 |       0.0534 |
| qwen3|description|filtro-kind|+bm25+siglip2                | 20261112-092807_ablacion-hibrido         | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.6047 | [0.560, 0.651] |  0.7905 |   0.8834 |   0.7005 | [0.662, 0.739] |           0.904  |                 0.6797 |    0.6768 |             0.8339 |              0.9163 |       0.0534 |
| qwen3|description|filtro-kind|+bm25+siglip2|fusion-rrf     | 20261112-092807_ablacion-hibrido         | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.5902 | [0.543, 0.641] |  0.776  |   0.8871 |   0.6933 | [0.654, 0.734] |           0.9079 |                 0.6734 |    0.6716 |             0.8221 |              0.92   |       0.0534 |
| bm25|description|filtro-kind|+siglip2                      | 20261112-092807_ablacion-hibrido         | bm25       | description      | kind     | chroma | full       |                 |         549 |  0.5974 | [0.551, 0.645] |  0.7559 |   0.8816 |   0.6932 | [0.654, 0.732] |           0.9021 |                 0.6727 |    0.6724 |             0.8041 |              0.9156 |       0.0534 |
| qwen3|description|filtro-type|+bm25+siglip2                | 20261112-092807_ablacion-hibrido         | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.6157 | [0.571, 0.658] |  0.7942 |   0.9199 |   0.7151 | [0.680, 0.750] |           0.9424 |                 0.6863 |    0.7044 |             0.8422 |              0.9514 |       0.0166 |
| qwen3|description|filtro-none|+bm25+siglip2                | 20261112-092807_ablacion-hibrido         | qwen3      | description      | none     | chroma | full       |                 |         549 |  0.6029 | [0.559, 0.647] |  0.7923 |   0.9126 |   0.7074 | [0.673, 0.743] |           0.9367 |                 0.6804 |    0.6979 |             0.8499 |              0.9561 |       0.0018 |
| qwen3|description|filtro-kind                              | 20261112-093413_ablacion-consulta        | qwen3      | description      | kind     | chroma | full       |                 |         549 |  0.5301 | [0.486, 0.573] |  0.714  |   0.8634 |   0.6407 | [0.602, 0.679] |           0.8848 |                 0.6244 |    0.6308 |             0.7605 |              0.8988 |       0.0534 |
| qwen3|description|filtro-kind|consulta-piece               | 20261112-093413_ablacion-consulta        | qwen3      | description      | kind     | chroma | piece      |                 |         549 |  0.3242 | [0.272, 0.382] |  0.5392 |   0.7778 |   0.4599 | [0.414, 0.509] |           0.8119 |                 0.4479 |    0.4781 |             0.5691 |              0.827  |       0.0534 |
| qwen3|description|filtro-kind|consulta-type                | 20261112-093413_ablacion-consulta        | qwen3      | description      | kind     | chroma | type       |                 |         549 |  0.2987 | [0.256, 0.344] |  0.541  |   0.7996 |   0.4458 | [0.406, 0.488] |           0.8215 |                 0.4322 |    0.4709 |             0.5864 |              0.8368 |       0.0534 |
| qwen3|description|filtro-kind|consulta-kind                | 20261112-093413_ablacion-consulta        | qwen3      | description      | kind     | chroma | kind       |                 |         549 |  0.0656 | [0.041, 0.093] |  0.1876 |   0.4645 |   0.1566 | [0.132, 0.187] |           0.405  |                 0.1525 |    0.1949 |             0.1529 |              0.4183 |       0.0534 |
| qwen3|description|filtro-none                              | 20261112-093413_ablacion-consulta        | qwen3      | description      | none     | chroma | full       |                 |         549 |  0.5355 | [0.491, 0.577] |  0.7304 |   0.8852 |   0.652  | [0.616, 0.688] |           0.9079 |                 0.6319 |    0.6493 |             0.7895 |              0.9306 |       0.0018 |
| qwen3|description|filtro-none|consulta-piece               | 20261112-093413_ablacion-consulta        | qwen3      | description      | none     | chroma | piece      |                 |         549 |  0.2969 | [0.246, 0.353] |  0.5082 |   0.7359 |   0.4299 | [0.388, 0.474] |           0.762  |                 0.4174 |    0.4464 |             0.5476 |              0.7837 |       0.0018 |
| bm25|description|filtro-kind                               | 20261112-093413_ablacion-consulta        | bm25       | description      | kind     | chroma | full       |                 |         549 |  0.5173 | [0.475, 0.562] |  0.7086 |   0.8689 |   0.631  | [0.597, 0.669] |           0.8752 |                 0.6143 |    0.6243 |             0.7443 |              0.8948 |       0.0534 |
| bm25|description|filtro-kind|consulta-piece                | 20261112-093413_ablacion-consulta        | bm25       | description      | kind     | chroma | piece      |                 |         549 |  0.3315 | [0.284, 0.382] |  0.5246 |   0.765  |   0.4565 | [0.413, 0.506] |           0.7812 |                 0.4454 |    0.4769 |             0.5501 |              0.7889 |       0.0534 |
| siglip2|description|filtro-kind                            | 20261112-093413_ablacion-consulta        | siglip2    | description      | kind     | chroma | full       |                 |         549 |  0.5082 | [0.454, 0.560] |  0.7195 |   0.8889 |   0.632  | [0.585, 0.676] |           0.906  |                 0.611  |    0.6218 |             0.7465 |              0.9179 |       0.0534 |
| siglip2|description|filtro-kind|consulta-piece             | 20261112-093413_ablacion-consulta        | siglip2    | description      | kind     | chroma | piece      |                 |         549 |  0.4791 | [0.424, 0.533] |  0.674  |   0.8798 |   0.6058 | [0.558, 0.651] |           0.9002 |                 0.5864 |    0.5993 |             0.7123 |              0.9126 |       0.0534 |
| qwen3|description|filtro-kind|+bm25+siglip2|consulta-piece | 20261112-093413_ablacion-consulta        | qwen3      | description      | kind     | chroma | piece      |                 |         549 |  0.4681 | [0.418, 0.521] |  0.6667 |   0.8543 |   0.5921 | [0.549, 0.638] |           0.8791 |                 0.5779 |    0.5899 |             0.7122 |              0.8953 |       0.0534 |
| qwen3|description|filtro-type                              | 20261112-093720_ablacion-reranking-local | qwen3      | description      | type     | chroma | full       |                 |         549 |  0.5355 | [0.491, 0.577] |  0.7322 |   0.8925 |   0.6536 | [0.617, 0.690] |           0.9136 |                 0.6315 |    0.6539 |             0.7851 |              0.9267 |       0.0166 |
| qwen3|description|filtro-type|rerank-qwen3-reranker        | 20261112-093720_ablacion-reranking-local | qwen3      | description      | type     | chroma | full       | qwen3-reranker  |         549 |  0.4736 | [0.431, 0.521] |  0.7031 |   0.8925 |   0.6113 | [0.579, 0.648] |           0.9136 |                 0.5913 |    0.6252 |             0.7626 |              0.9267 |       0.0166 |

## hit@1 por categoría

| método | armchair (18) | bench (4) | cabinet (39) | chair (45) | deco (207) | dresser (1) | lamp (64) | ottoman (6) | rug (45) | shelf (21) | sofa (24) | stool (8) | table (67) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3|description|filtro-type | 0.72 | 1.00 | 0.72 | 0.84 | 0.36 | 1.00 | 0.59 | 1.00 | 0.31 | 0.43 | 0.62 | 0.88 | 0.69 |
| qwen3|description|filtro-type|rerank-qwen3-reranker | 0.61 | 1.00 | 0.51 | 0.62 | 0.34 | 1.00 | 0.52 | 0.83 | 0.40 | 0.43 | 0.50 | 1.00 | 0.60 |

## Por pasada de consultas (v1: muebles del primer alcance; v2: la ampliación)

| método | consultas_ambiente_v1 hit@1 / MRR | consultas_ambiente_v2 hit@1 / MRR |
|---|---|---|
| qwen3|description|filtro-type | 0.633 / 0.736 (199) | 0.480 / 0.607 (350) |
| qwen3|description|filtro-type|rerank-qwen3-reranker | 0.548 / 0.672 (199) | 0.431 / 0.577 (350) |

## Base vectorial y reranking

![avanzado](avanzado.png)

![camino](camino_texto.png)

## ¿Cuántos candidatos? La curva de hit@k

| método | k=1 | k=2 | k=3 | k=5 | k=10 | k=15 | k=20 | k=30 | k=50 |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3, filtro por tipo | 0.535 | 0.674 | 0.732 | 0.812 | 0.892 | 0.933 | 0.958 | 0.980 | 0.995 |
| BGE, filtro por tipo | 0.479 | 0.612 | 0.687 | 0.760 | 0.871 | 0.913 | 0.953 | 0.980 | 0.995 |
| hashing, filtro por tipo | 0.510 | 0.647 | 0.721 | 0.809 | 0.892 | 0.920 | 0.936 | 0.969 | 0.989 |

![curva k](curva_k.png)

## Dimensión del embedding (Matryoshka)

| dimensión | bytes por vector | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|---|
| 32 | 128 | 0.428 | 0.823 | 0.555 |
| 64 | 256 | 0.461 | 0.867 | 0.592 |
| 128 | 512 | 0.506 | 0.885 | 0.625 |
| 256 | 1024 | 0.515 | 0.894 | 0.633 |
| 512 | 2048 | 0.532 | 0.892 | 0.649 |
| 1024 | 4096 | 0.535 | 0.892 | 0.654 |

![dimensión](dimension.png)

## Splitting: ¿un documento por producto o un chunk por línea?

| splitting | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|
| un documento por producto (ChromaDB) | 0.535 [0.49–0.58] | 0.892 | 0.654 |
| cada línea un chunk, el producto vale su mejor línea | 0.273 [0.24–0.31] | 0.805 | 0.433 |
| línea contra línea del mismo rótulo, promedio | 0.514 [0.47–0.56] | 0.891 | 0.635 |

## Reproducibilidad: tres escrituras independientes de las consultas

La búsqueda es determinística: lo que varía es quién escribe la consulta (en el flujo, el paso plan). Las mismas fotos y los mismos prompts, tres subagentes distintos por lote. Promedio ± desvío estándar (n=3) y el rango.

| método | consultas (r1/r2/r3) | hit@1 | MRR@10 | hit@10 |
|---|---|---|---|---|
| bge|description|filtro-type | 549/547/547 | 0.492 ± 0.016 (0.479–0.510) | 0.612 ± 0.010 (0.602–0.622) | 0.872 ± 0.001 (0.871–0.872) |
| bm25|description|filtro-kind | 549/547/547 | 0.502 ± 0.016 (0.486–0.517) | 0.619 ± 0.013 (0.606–0.631) | 0.865 ± 0.010 (0.854–0.872) |
| bm25|description|filtro-kind|+siglip2 | 549/547/547 | 0.584 ± 0.015 (0.569–0.597) | 0.685 ± 0.012 (0.671–0.693) | 0.884 ± 0.008 (0.877–0.892) |
| clip|description|filtro-kind | 549/547/547 | 0.357 ± 0.017 (0.340–0.375) | 0.511 ± 0.012 (0.498–0.522) | 0.844 ± 0.006 (0.837–0.849) |
| hashing|description|filtro-none | 549/547/547 | 0.500 ± 0.027 (0.475–0.528) | 0.621 ± 0.020 (0.602–0.641) | 0.867 ± 0.016 (0.850–0.881) |
| hashing|description|filtro-type | 549/547/547 | 0.516 ± 0.030 (0.490–0.548) | 0.637 ± 0.022 (0.617–0.660) | 0.887 ± 0.010 (0.876–0.892) |
| hashing|seller|filtro-none | 549/547/547 | 0.075 ± 0.002 (0.073–0.076) | 0.140 ± 0.003 (0.137–0.142) | 0.318 ± 0.009 (0.311–0.329) |
| qwen3|description|filtro-kind | 549/547/547 | 0.539 ± 0.025 (0.519–0.567) | 0.643 ± 0.015 (0.629–0.659) | 0.867 ± 0.004 (0.863–0.870) |
| qwen3|description|filtro-kind|+bm25 | 549/547/547 | 0.572 ± 0.019 (0.550–0.585) | 0.671 ± 0.013 (0.657–0.683) | 0.880 ± 0.006 (0.876–0.887) |
| qwen3|description|filtro-kind|+bm25+siglip2 | 549/547/547 | 0.604 ± 0.009 (0.594–0.612) | 0.700 ± 0.009 (0.690–0.709) | 0.889 ± 0.006 (0.883–0.896) |
| qwen3|description|filtro-kind|+bm25+siglip2|fusion-rrf | 549/547/547 | 0.584 ± 0.006 (0.578–0.590) | 0.689 ± 0.007 (0.681–0.693) | 0.893 ± 0.007 (0.887–0.901) |
| qwen3|description|filtro-kind|+bm25|fusion-rrf | 549/547/547 | 0.547 ± 0.028 (0.521–0.576) | 0.656 ± 0.018 (0.638–0.674) | 0.878 ± 0.009 (0.870–0.888) |
| qwen3|description|filtro-kind|+siglip2 | 549/547/547 | 0.572 ± 0.019 (0.550–0.585) | 0.684 ± 0.013 (0.669–0.693) | 0.894 ± 0.005 (0.889–0.899) |
| qwen3|description|filtro-none | 549/547/547 | 0.543 ± 0.027 (0.521–0.574) | 0.654 ± 0.018 (0.637–0.673) | 0.891 ± 0.007 (0.885–0.899) |
| qwen3|description|filtro-none|+bm25+siglip2 | 549/547/547 | 0.600 ± 0.010 (0.589–0.609) | 0.705 ± 0.009 (0.695–0.713) | 0.915 ± 0.011 (0.905–0.927) |
| qwen3|description|filtro-type | 549/547/547 | 0.547 ± 0.027 (0.526–0.578) | 0.657 ± 0.017 (0.642–0.676) | 0.897 ± 0.004 (0.892–0.899) |
| qwen3|description|filtro-type|+bm25+siglip2 | 549/547/547 | 0.609 ± 0.013 (0.594–0.616) | 0.713 ± 0.012 (0.700–0.723) | 0.922 ± 0.009 (0.914–0.932) |
| siglip2|description|filtro-kind | 549/547/547 | 0.494 ± 0.016 (0.477–0.508) | 0.622 ± 0.009 (0.614–0.632) | 0.884 ± 0.006 (0.877–0.889) |

## La imagen generada

Fidelidad: cada producto de la lista buscado en la imagen final (Grounding DINO), recortado y comparado con su foto del catálogo (DINOv3); *identificado* = el más parecido al recorte entre los productos de su tipo es él. Ambiente: SSIM fuera de los muebles y fracción de puntos SIFT de la foto original reencontrados (RANSAC). Pedido: SigLIP 2 entre el pedido y la imagen final, menos lo mismo con la foto vacía; puesto del pedido real entre él y seis pedidos de contraste.

| corrida | generador | detectados | identificados@1 | coseno | inventadas | SSIM fuera | SIFT | pedido Δ (puesto) |
|---|---|---|---|---|---|---|---|---|
| caballito-comedor | nano_banana_2 | 4/4 | 0.5 | 0.4938 | 1 | 0.9718 | 0.4248 | +0.053 (1/7) |
| caballito-living | nano_banana_2 | 7/8 | 0.375 | 0.5493 | 0 | 0.9825 | 0.1857 | +0.025 (2/7) |
| experimento | nano_banana_2 | 6/6 | 0.6667 | 0.5342 | 1 | 0.8291 | 0.1329 | +0.061 (1/7) |
| experimento-buen-pedido | nano_banana_2 | 9/9 | 0.4444 | 0.3649 | 0 | 0.2899 | 0.0065 | +0.085 (1/7) |
| experimento-buen-pedido-estricto | nano_banana_2 | 9/9 | 0.4444 | 0.4291 | 1 | 0.7817 | 0.0759 | +0.063 (1/7) |
| experimento-libre | nano_banana_2 | 6/6 | 0.5 | 0.4561 | 0 | 0.8087 | 0.1008 | +0.075 (1/7) |
| experimento-libre-modular | nano_banana_2 | 6/6 | 0.5 | 0.4655 | 0 | 0.7666 | 0.1126 | +0.090 (1/7) |
| prueba-alvear2 | nano_banana_2 | 4/4 | 0.75 | 0.6824 | 0 | 0.9747 | 0.5521 | +0.077 (1/7) |

### `caballito-comedor` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 002.908.15 | dining table | 2/71 | 0.4886 |
| 003.015.26 | dining chair | 1/78 | 0.5728 |
| 000.379.80 | pendant lamp | 1/101 | 0.7243 |
| 002.809.39 | sideboard | 22/55 | 0.1896 |

### `caballito-living` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 190.114.33 | sofa | 2/37 | 0.7008 |
| 501.637.92 | rug | 11/89 | 0.1885 |
| 902.976.57 | coffee table | no se detectó | None |
| 102.659.24 | TV stand | 3/55 | 0.4721 |
| 202.080.42 | floor lamp | 1/101 | 0.7462 |
| 602.740.06 | cushion | 11/244 | 0.3956 |
| 468.040.05 | plant | 1/244 | 0.6314 |
| 500.460.48 | curtains | 1/244 | 0.7104 |

### `experimento` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 703.233.51 | bookcase | 1/63 | 0.7967 |
| 391.505.88 | armchair | 1/78 | 0.8509 |
| 402.712.59 | rug | 9/89 | 0.1819 |
| 302.865.67 | floor lamp | 1/102 | 0.2782 |
| 102.397.13 | side table | 1/71 | 0.6031 |
| 802.841.94 | curtains | 10/255 | 0.4941 |

### `experimento-buen-pedido` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 802.456.40 | bookcase | 2/54 | 0.2216 |
| 391.505.88 | armchair | 3/78 | 0.6233 |
| 302.865.67 | floor lamp | 1/101 | 0.3698 |
| 802.972.43 | side table | 1/71 | 0.4326 |
| 832.351.10 | rug | 1/89 | 0.3925 |
| 302.006.96 | throw | 60/244 | 0.0908 |
| 503.265.29 | cushion | 25/244 | 0.1644 |
| 802.841.94 | curtains | 9/244 | 0.3017 |
| 001.185.23 | plant | 1/244 | 0.6875 |

### `experimento-buen-pedido-estricto` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 802.456.40 | bookcase | 1/54 | 0.42 |
| 391.505.88 | armchair | 1/78 | 0.6653 |
| 302.865.67 | floor lamp | 2/101 | 0.3725 |
| 802.972.43 | side table | 2/71 | 0.3639 |
| 832.351.10 | rug | 1/89 | 0.5121 |
| 302.006.96 | throw | 142/244 | 0.0458 |
| 503.265.29 | cushion | 23/244 | 0.2299 |
| 802.841.94 | curtains | 5/244 | 0.5744 |
| 001.185.23 | plant | 1/244 | 0.6783 |

### `experimento-libre` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 703.233.51 | bookcase | 3/54 | 0.4892 |
| 391.505.88 | armchair | 1/78 | 0.7 |
| 402.712.59 | rug | 51/89 | 0.0488 |
| 302.865.67 | floor lamp | 1/101 | 0.5495 |
| 102.397.13 | side table | 1/71 | 0.5383 |
| 802.841.94 | curtains | 4/244 | 0.4106 |

### `experimento-libre-modular` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 703.233.51 | bookcase | 1/54 | 0.4612 |
| 391.505.88 | armchair | 1/78 | 0.827 |
| 402.712.59 | rug | 18/89 | 0.0917 |
| 302.865.67 | floor lamp | 1/101 | 0.3085 |
| 102.397.13 | side table | 2/71 | 0.5379 |
| 802.841.94 | curtains | 7/244 | 0.5666 |

### `prueba-alvear2` por producto

| producto | kind | puesto | coseno |
|---|---|---|---|
| 691.249.46 | sofa | 7/37 | 0.6662 |
| 391.505.88 | armchair | 1/78 | 0.8996 |
| 002.852.58 | rug | 1/89 | 0.2853 |
| 302.397.12 | coffee table | 1/71 | 0.8785 |

### La vara: la misma identificación con fotos reales (ambientes IKEA)

545 recortes de 64 ambientes: hit@1 0.444 [0.39–0.50], MRR@10 0.556, coseno medio 0.411.

| grupo | hit@1 | recortes |
|---|---|---|
| armchair | 0.80 | 5 |
| bench | 1.00 | 2 |
| cabinet | 0.62 | 47 |
| chair | 0.75 | 122 |
| curtains | 0.11 | 27 |
| cushion | 0.24 | 95 |
| desk | 0.00 | 1 |
| floor lamp | 0.44 | 18 |
| mirror | 0.33 | 3 |
| ottoman | 0.67 | 3 |
| pendant lamp | 0.44 | 18 |
| plant | 0.10 | 20 |
| rug | 0.30 | 54 |
| shelf | 0.14 | 21 |
| sofa | 0.48 | 29 |
| stool | 0.73 | 11 |
| table | 0.75 | 16 |
| vase | 0.50 | 10 |
| wall art | 0.26 | 43 |

## Relevancia graduada del top-3 (juez)

Método `qwen3|description|filtro-type`. Un juez (subagente) califica cada uno de los tres primeros candidatos contra la pieza que se ve en el ambiente: 2 el mismo o indistinguible, 1 una alternativa aceptable, 0 no sirve. *útil@k*: alguno de los k primeros con 1 o 2.

| consultas | n | nota del 1.º | útil@1 | útil@3 | un 2 en el top-3 | NDCG@3 |
|---|---|---|---|---|---|---|
| todas | 150 | 1.07 | 0.747 [0.68–0.82] | 0.840 [0.78–0.89] | 0.427 | 0.783 |
| con anotado | 75 | 1.41 | 0.867 [0.78–0.94] | 0.947 [0.89–0.99] | 0.693 | 0.884 |
| sin anotado | 75 | 0.73 | 0.627 [0.51–0.73] | 0.733 [0.63–0.83] | 0.160 | 0.682 |

Acuerdo con el ground truth: de 59 productos anotados que aparecen en el top-3, el juez le dio 2 al 81%; a los demás candidatos, al 5%.

## La respuesta en texto: faithfulness y answer relevance, versión 1 de los jueces

**No comparar con la versión 2 (abajo).** Estos jueces (2026-10-23, subagentes de Claude Code) tenían una fuga (el prompt traía de ejemplo el pedido evaluado) y leían la descripción completa de cada producto, que el generador no ve. Faithfulness: de las afirmaciones de hecho del porqué, cuántas se infieren del contexto. Answer relevance: coseno medio (Qwen3) entre el pedido original y tres pedidos que un juez que no lo vio infiere de la respuesta; la vara es el mismo coseno con pedidos sin relación.

| corrida | afirmaciones | faithfulness | answer relevance | vara | no sostenidas |
|---|---|---|---|---|---|
| experimento | 34 | 0.9706 | 0.6038 | 0.3951 | It is the only round rug available |
| prueba-alvear | 27 | 0.8889 | 0.6901 | 0.3743 | The floor is oak; The rug is the largest option; The rug reaches under the sofa's front legs, the table and the armchair |
| prueba-alvear2 | 25 | 0.96 | 0.7261 | 0.3743 | The rug is large enough to sit under the front of both the sofa and the armchair |
| prueba-alvear2-scene-v2 | 26 | 0.9231 | 0.7158 | 0.3743 | The rug is large enough to go under the front of both the sofa and the armchair; The table's size suits a three-seat sofa |

## La respuesta en texto, versión 2 de los jueces (la configuración final)

El juez de faithfulness recibe lo que vio el generador (el pedido, la foto del ambiente y, de cada producto elegido, su foto y la línea con su kind, su tipo y su medida); el de answer relevance no tiene ejemplos de pedido. Vara cruzada: el pedido de cada corrida contra los pedidos que el juez escribió para las otras corridas.

- Faithfulness: **0.8234** (289 de 351 afirmaciones, 11 corridas).
- Answer relevance: **0.6875**; vara cruzada 0.5505 (la propia la supera en 11 corridas); vara de pedidos sin relación 0.4032.

| corrida | afirmaciones | faithfulness | answer relevance |
|---|---|---|---|
| todos__alvear-escritorio | 28 | 0.9286 | 0.7178 |
| todos__alvear-living-comedor | 49 | 0.7347 | 0.6928 |
| todos__caballito-comedor | 20 | 0.85 | 0.7661 |
| todos__caballito-living | 35 | 0.9143 | 0.6238 |
| todos__experimento-lectura | 33 | 0.9091 | 0.7188 |
| todos__publica-comedor-clasico-moderno | 28 | 0.8571 | 0.7135 |
| todos__publica-estudio-sobrio | 32 | 0.8438 | 0.7405 |
| todos__publica-living-bohemio | 37 | 0.7027 | 0.6723 |
| todos__publica-living-clasico | 28 | 0.8929 | 0.6194 |
| todos__publica-living-japandi | 26 | 0.7692 | 0.6197 |
| todos__publica-loft-industrial | 35 | 0.7429 | 0.6775 |

## El espacio de embeddings

855 descripciones. Separabilidad: de cada producto, ¿su vecino más cercano es de su mismo kind / tipo?, y el silhouette por kind (coseno).

| embedder | vecino del mismo kind | vecino del mismo tipo | silhouette por kind |
|---|---|---|---|
| hashing | 0.834 | 0.910 | 0.076 |
| bge | 0.918 | 0.964 | 0.222 |
| qwen3 | 0.894 | 0.961 | 0.179 |

| consulta | mejor coseno | coseno del 10.º | kinds del top-10 |
|---|---|---|---|
| del dominio | 0.833 | 0.751 | armchair, armchair, armchair, ottoman, armchair, sofa, sofa, armchair, armchair, armchair |
| fuera del dominio | 0.318 | 0.283 | floor lamp, desk, desk lamp, rug, rug, desk lamp, armchair, low stool, desk lamp, sofa |

![umap](umap.png)

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

### `20261110-010145_ablacion-catalogo-todos` (1502 productos, consultas + consultas_ambiente_v2)

| método                        |   consultas |   hit@1 |   hit@10 |   mrr@10 |
|:------------------------------|------------:|--------:|---------:|---------:|
| qwen3|description|filtro-type |         549 |  0.5246 |   0.8725 |   0.6367 |

