# Métricas de amoblai: qué mide cada una, cuánto creerle y cuáles valen más

Actualizado el 2026-11-12, después de la revisión crítica (`docs/REVISION.md`): se rehízo el
ranking, se corrigieron las métricas del generador y se sumaron las diferencias pareadas. Los
números son de la configuración final: catálogo IKEA revisado (819 productos) para lo que tiene
ground truth, 549 consultas con producto anotado en 64 ambientes; y el catálogo IKEA + ABO
(1.502) para lo que se mide sobre ambientes vacíos reales.

## Qué tiene que salir bien

El usuario manda una foto de su ambiente vacío y un pedido. Le sirve el resultado si:

1. los productos son buenos para el pedido y para el ambiente, y combinan entre sí;
2. existen (son del catálogo: se garantiza por construcción, cada id se valida);
3. la imagen muestra esos productos y no otros parecidos;
4. la imagen es su ambiente;
5. sale barato y rápido.

En el esquema de la clase 11 (pregunta, contexto, respuesta, ground truth): la pregunta es la
foto con el pedido; el contexto son los 5 candidatos que trae la búsqueda para cada pieza; la
respuesta es la lista elegida con su porqué, y la imagen.

**No existe ground truth de la tarea real** (foto vacía + pedido → lista ideal). Hay tres
aproximaciones, y cada métrica se apoya en una:

| Ground truth | Qué es | Para qué sirve | Su límite |
|---|---|---|---|
| Productos anotados en fotos de ambientes de IKEA | Qué productos del catálogo hay en cada ambiente (sin posiciones) | Medir el buscador: describir un mueble que se ve y encontrarlo | Es "encontrar un producto conocido", no recomendar. Quien escribe la consulta ve el producto, y consultas y descripciones las escribe el mismo modelo con el mismo molde |
| Un juez LLM que compara dos listas a ciegas, en los dos órdenes | Preferencia entre configuraciones, sobre 11 ambientes vacíos reales | Lo único que mide el flujo entero | n = 11; el juez es el mismo modelo que elige; sin validar contra personas |
| La foto del catálogo de cada producto y la foto original del ambiente | Cómo es cada producto y cómo era el cuarto | Medir la imagen | 8 imágenes |

## El ranking

### Imprescindibles

| # | Métrica | Qué contesta | Valor hoy |
|---|---|---|---|
| 1 | **hit@k** (k = 1, 5, 10) con IC 95% por ambiente, el azar al lado y la **diferencia pareada** entre métodos | ¿El producto anotado está entre los k primeros? hit@5 es el titular: son los 5 candidatos que ve el que elige | búsqueda del flujo (versión 2, híbrida): hit@1 0,605 [0,56–0,65], **hit@5 0,825**, hit@10 0,883; versión 1 (densa): 0,530, 0,790 y 0,863; azar 0,017 y 0,161 |
| 2 | **Juez de listas de a pares** sobre ambientes vacíos (gana / empata, útil por producto) | ¿Qué configuración da mejores listas en la tarea real? | versión 2 contra versión 1: gana 5, empata 6, no pierde (p = 0,06); con búsqueda contra sin búsqueda: 7 a 0 (p = 0,016); IKEA + ABO contra IKEA: 8 a 2 con 1 empate (p = 0,11) |
| 3 | **Acierto de la elección con un VLM**, según cuántos candidatos ve | ¿Suma que un VLM mire las fotos? ¿Cuántos candidatos pasarle? | sobre el top-10: 0,535 → 0,687 (+0,151 [0,115; 0,190]); entre 3: 0,637; entre 5: 0,667; entre 8: 0,689 |
| 4 | **Fidelidad de producto y ambiente preservado**, sobre todas las imágenes | ¿La imagen muestra esos productos, en ese cuarto? | 26 de 52 productos identificados en 8 imágenes (coseno medio 0,48); el control del ambiente rechazó 2 de 3 intentos en un caso |
| 5 | **Tres redactores e IC** | ¿Cuánto cambia el número sin cambiar el sistema? | hit@1 0,604 ± 0,009 según quién escribe las consultas (versión 2); 0,539 ± 0,025 (versión 1) |
| 6 | **Costo por pedido** | ¿Cuánto cuesta cada parte? | plan US$0,06; elección US$0,14 (de 0,05 a 0,43); imagen US$0,08 por intento |
| 7 | **Las cuatro de la clase 11**, rotuladas como lo que son | Lo que pide la cátedra: al menos una del retriever y una del generador | context precision@10 0,63; context recall 0,79 (@3) y 0,93 (@10) por ambiente; faithfulness 0,82; answer relevance 0,69 |

### Útiles

| Métrica | Qué contesta | Valor hoy |
|---|---|---|
| Diagnóstico del flujo sin juez (`amoblai diagnostico-flujo`) | ¿Qué hace de verdad el que elige con los candidatos? | toma el primero de la búsqueda el 41% de las veces; el 20% de lo elegido sale de los puestos 4 y 5; dejó afuera 0 de 75 piezas; el 36% de lo elegido no tiene ninguna medida |
| Relevancia graduada del top-3 (un juez da 2, 1 o 0) | ¿Sirve lo que se trae aunque no sea el producto anotado? | el primero sirve 0,78 y alguno del top-3 0,87 (reponderado a la población) |
| hit@1 por categoría, con su n | ¿Dónde falla el buscador? | sillas 0,84; guardado 0,72; mesas 0,69; lámparas 0,59; deco 0,36; alfombras 0,31 |
| Recall por producto anotado | Comparar con la búsqueda por imagen con la misma unidad | texto 0,55 contra imagen 0,43 (+0,12 [0,04; 0,20]) |
| hit@k por familia | ¿El error es otro mueble, o el mismo modelo en otra medida u otro color? | hit@1 0,689 por familia contra 0,605 exacto (versión 2); 0,623 contra 0,530 (versión 1) |
| MRR@10 | Un solo número para el orden | 0,701 (versión 2); 0,641 (versión 1) |
| IoU de la réplica | ¿El generador pone cada mueble donde se le indica? | 0,20 sin indicar; 0,37 en palabras; 0,40–0,52 con cajas (un cuarto, 3 imágenes por variante) |

### Prescindibles o engañosas (se dejan, rotuladas)

| Métrica | Por qué |
|---|---|
| NDCG@10 y context precision@10 | Bien calculadas (la segunda es la fórmula exacta de la clase), pero con uno o dos relevantes por consulta repiten al MRR: correlación mayor a 0,99 sobre 32 configuraciones. Van en una línea, por la clase |
| "NDCG@3 graduado" | No es el NDCG estándar: usa como ideal las mismas tres notas ordenadas (42 de 150 consultas dan 1,0 sin ningún 2) |
| Pedido ↔ imagen con SigLIP 2 | Sus contrastes son pedidos sin relación ("una cocina blanca"): ganarles no dice nada del estilo |
| "Aceptable" del juez de listas | Satura: 0,97 a 1,00 |
| AUROC del coseno ("¿el primero está bien?") | Se calculaba solo entre consultas con respuesta (0,655). Como detector de "no hay nada así" (con respuesta contra sin) da 0,72: poco para usarlo de umbral |
| Separabilidad del espacio y UMAP | No predice la tarea: BGE separa mejor los kinds y recupera peor. Sirve como figura |
| Piezas inventadas en la imagen | Ruido del detector |
| Las métricas del generador **versión 1** (2026-10-23) | Tenían una fuga y otro contexto. Ver abajo |

## Cada métrica, con sus reparos

### hit@k, MRR y las diferencias pareadas

- **Qué es.** Para cada consulta (la descripción de un mueble que se ve en un ambiente de
  IKEA), si alguno de los k primeros productos es uno de los anotados en ese ambiente del mismo
  grupo. La métrica es permisiva: las anotaciones no dicen cuál mueble es cuál, así que con dos
  sillas distintas en el ambiente, cualquiera de las dos vale. Exigiendo una asignación uno a
  uno, hit@1 baja de 0,536 a 0,519.
- **Diferencias pareadas.** Dos métodos se comparan sobre las mismas consultas: la diferencia
  media y su IC 95% por bootstrap de ambientes (`vs_base` y `vs_anterior` en `metricas.json`).
  Mirar los IC de cada método por separado engaña en los dos sentidos: Qwen3 contra una bolsa
  de palabras "gana" 0,535 a 0,510 pero la diferencia es +0,026 [−0,025; +0,077]; y el filtro
  por kind "está dentro del intervalo" pero pierde 2 puntos de hit@5 con intervalo que no toca
  el cero.
- **Por familia.** `familia_hit@k` cuenta también como acierto cualquier variante del modelo
  anotado (mismo nombre comercial y mismo grupo). El 69% de las consultas busca un producto con
  variantes en el catálogo; una de cada cinco veces que el primero "falla" es una variante.
  Hay tres niveles de correcto, y conviene decirlos juntos: el producto exacto primero (0,53 con
  la versión 1), el mismo modelo primero (0,62) y uno que un juez considera que sirve (0,78).
  El orden entre métodos no cambia por familia.
- **Qué se sostiene y qué no** (hit@1, pareado): descripciones propias contra el texto del
  vendedor, sí (+0,19 con la consulta natural, +0,42 con la ficha); la consulta como ficha contra
  la frase natural, sí (+0,24); Qwen3 contra BGE, sí (+0,057); Qwen3 contra hashing o BM25, no;
  filtro por tipo contra ninguno, no (0,000); 1024 contra 512 dimensiones, no; documento entero
  contra línea por línea alineada, no (+0,022, p = 0,29); híbrida contra densa, sí (+0,075).
- **Cuánto creerle.** Es un banco de "producto conocido": mide bien el índice (qué se describe,
  cómo se escribe la consulta, qué buscador) y no dice cuán buena es la lista para un pedido
  abierto. En los ambientes vacíos las consultas del plan quedan más lejos del catálogo (coseno
  del primero 0,80–0,82 contra 0,875 acá). No hay conjunto apartado: todo se eligió y se reporta
  sobre los mismos 64 ambientes.

### Context precision y context recall (clase 11)

- **Context precision@10**: Σ (Precision@k · v_k) / relevantes en el top-10, la fórmula de la
  clase (`metrics.py`, con el ejemplo de la filmina como test): 0,63.
- **Context recall**: la clase lo define por frases del ground truth atribuibles al contexto.
  Acá el ground truth son productos, así que es por producto y **por ambiente**: de los productos
  anotados que buscan las consultas de un ambiente, cuántos aparecen en la unión de sus top-k.
  0,79 con k = 3 y 0,93 con k = 10. Ojo al compararlo: las demás son por consulta.

### El juez de listas (punta a punta)

- **Qué es.** Sobre un ambiente vacío real, dos variantes del flujo arman su lista (mismo plan);
  el juez (Opus) ve la foto, el pedido y las dos listas con la foto de cada producto, sin saber
  cuál es cuál, y se le pregunta en los dos órdenes. Una variante gana un ambiente solo si gana
  en los dos órdenes.
- **Reparos.** n = 11: 8 a 2 con 1 empate da p = 0,11 en un test de signos. Los 6 ambientes
  públicos (donde gana 6 a 0, p = 0,03) tienen pedidos que escribimos sabiendo qué estilos le
  faltan a IKEA. El juez es el mismo modelo que eligió, y no está validado contra personas. No
  hay corrida repetida (A/A): no sabemos cuántos ambientes da vuelta el ruido solo. Los pedidos
  enumeran las piezas: el pedido abierto no se evalúa.
- **Lo que midió** (`docs/EXPERIMENTOS.md`, T3b y T8): IKEA + ABO contra IKEA, 8 a 2 con 1
  empate; la búsqueda híbrida contra la densa, 5 a 0 con 6 empates (15 votos a 5; p = 0,06); con
  búsqueda contra 5 candidatos al azar del mismo kind, 7 a 0 con los 14 votos (p = 0,016). El
  último es el control del instrumento: cuando la diferencia es grande, el juez la ve siempre.
- **A favor.** En la comparación de catálogos los dos órdenes coinciden en 10 de 11; hay algo de sesgo a la posición A (12 de
  22 votos) y preguntar en los dos órdenes lo cancela. Una métrica sin juez va en el mismo
  sentido: el producto elegido tiene el primer estilo que pidió el plan en 0,42 (IKEA) contra
  0,56 (IKEA + ABO) en los públicos.

### La elección con un VLM y la curva de candidatos

- **Qué es.** Opus recibe la consulta y las fotos del top-10 y las ordena
  (`rerank_candidates_v1`); se mide hit@1 después de reordenar. De ahí sale gratis la curva
  (`amoblai evaluar-candidatos`): si eligiera entre los k primeros, ¿acertaría?
- **Reparo.** Es una **técnica aislada**, no un paso del flujo: el reranker ordena contra la
  consulta, sin ver el ambiente ni el pedido. El paso `choose` del flujo elige una combinación
  para el cuarto, con otra entrada y otro prompt, y no tiene ground truth. El número del flujo
  más cercano es 0,667 (elegir entre 5), y es un sustituto.
- **Control negativo.** Un cross-encoder de texto chico (MiniLM de MS MARCO) empeora: 0,419.

### Las métricas del generador (RAGAS), versión 2

- **Faithfulness**: afirmaciones de hecho del porqué que se infieren del contexto / afirmaciones.
  El juez recibe lo que vio el generador: el pedido, la foto del ambiente y, de cada producto
  elegido, su foto y la línea con su kind, su tipo y su medida (`juez_fidelidad_v2`).
  Sobre las 11 listas de la versión 1 con el catálogo combinado: **0,82** (289 de 351; por lista
  de 0,70 a 0,93). Sobre las listas de la versión 2 no se corrió (US$1,1). Lo que no se
  sostiene: la especie de la madera que el generador afirma sin verla escrita, y medidas.
- **Answer relevance**: un juez que no ve el pedido escribe tres pedidos que la lista contesta
  (`juez_pedidos_v2`); la métrica es el coseno medio con el pedido original (Qwen3): **0,69**.
  Dos varas: los pedidos que el juez escribió para otras listas (0,55; la propia supera a las
  ajenas en 11 de 11) y pedidos sin relación (0,40).
- **Qué pasó con la versión 1.** El prompt del juez de pedidos traía de ejemplo "un living
  nórdico y cálido", que era el pedido evaluado en 3 de 4 corridas: el juez lo copiaba (fuga de
  datos). Su única vara era la de pedidos sin relación; con la cruzada, 0,69–0,73 se comparaba
  con 0,66. Y el juez de fidelidad leía la descripción completa del producto, que el generador
  no ve. Eran 3 respuestas distintas, de una configuración anterior. Sus números (0,89–0,96 y
  0,69–0,73) no se comparan con estos.

### La imagen

- **Fidelidad de producto.** Se detectan los muebles en la imagen generada, se recorta cada uno
  y se compara con las fotos del catálogo (DINOv3): "identificado" si el más parecido de su tipo
  es el de la lista. Sobre las 8 imágenes con métricas: **26 de 52** (por imagen, de 3/8 a 3/4),
  coseno medio 0,48. Con fotos reales de IKEA el mismo reconocimiento da 0,444, pero con otro
  procedimiento (ahí valen todos los recortes; acá cada producto se queda con la detección que
  más se le parece), así que no es una vara pareja.
- **Ambiente preservado.** SSIM fuera de los muebles y puntos SIFT de la foto original
  reencontrados con RANSAC. Discrimina: marcó el caso en que el modelo rehízo el cuarto (SSIM
  0,29, 10 puntos, cámara corrida 7,7%) y rechazó 2 de 3 intentos en otro. El flujo lo usa como
  control (al menos 50 puntos y desplazamiento de hasta 1%, hasta 3 intentos); esos umbrales
  están puestos a mano.
- **n.** 8 imágenes, 4 fotos de ambientes, varias configuraciones mezcladas. Ninguna imagen se
  generó con la configuración final (IKEA + ABO).

### Costo y latencia

Del registro de gastos (`datos/resultados/gastos.jsonl`, cada llamada paga): plan US$0,063 y
elección US$0,138 de media desde el 10/11 (la elección va de 0,05 a 0,43 según cuántas piezas y
de qué catálogo: una foto de ABO pesa unos 1.330 tokens y una de IKEA 385); imagen US$0,08 por
intento. Un pedido típico: unos US$0,28 con un intento de imagen.

## Trampas, dichas en voz alta

- **Fuga por la consulta de evaluación.** El redactor ve el producto que hay que encontrar. Mide
  identificación, no recomendación.
- **El mismo modelo escribe los dos lados** (consultas y descripciones): contar palabras (BM25)
  rinde casi como el embedder. En el flujo real pasa lo mismo (el plan también es Claude), así
  que es representativo del sistema, pero no de un usuario que escribe con otras palabras.
- **Fuga por memoria del modelo.** El dataset de IKEA es público desde 2017.
- **Sin conjunto apartado.** Lo que se elige y lo que se reporta sale de los mismos ambientes.
- **Jueces LLM.** Dos órdenes para el sesgo de posición; el de relevancia está validado contra
  las anotaciones solo para la nota 2 (se la da al anotado el 81% de las veces y a los demás el
  5%); el de listas no está validado contra personas.
- **Lo que no se midió**: cuánto cambia la lista si se corre dos veces el mismo pedido (plan,
  elección, juez e imagen se corrieron una vez).

## Lo que no usamos, y por qué

WER (no hay audio); BLEU, ROUGE y BERTScore (no hay texto de referencia); FID, IS y KID (piden
miles de imágenes y miden realismo, no fidelidad a un producto); Precision@K plana (con uno o
dos relevantes queda clavada abajo); el context recall por frases (el ground truth son
productos); LangSmith (el registro propio de gastos y la carpeta de cada corrida cubren costo,
tokens y traza por paso).

## Cómo se corre

```bash
uv run amoblai evaluar --ablacion datos/configs/ablaciones/camino.yaml    # el camino incremental
uv run amoblai evaluar --ablacion datos/configs/ablaciones/hibrido.yaml   # léxica, foto y fusión
uv run amoblai evaluar --ablacion datos/configs/ablaciones/consulta.yaml  # la consulta, contra no reescribir
uv run amoblai evaluar --ablacion datos/configs/ablaciones/embedders.yaml # embedders, exacto y por familia
uv run amoblai evaluar-punta-a-punta datos/configs/punta_a_punta/hibrida.yaml --pagar       # versión 1 contra versión 2
uv run amoblai evaluar-punta-a-punta datos/configs/punta_a_punta/sin_busqueda.yaml --pagar  # con búsqueda contra sin
uv run amoblai evaluar --ablacion datos/configs/ablaciones/reproducibilidad.yaml --replica r2
uv run amoblai evaluar-candidatos             # la curva de candidatos, desde el rerank ya pago
uv run amoblai diagnostico-flujo              # el flujo real sin juez
uv run amoblai evaluar-graduada               # relevancia graduada
uv run amoblai evaluar-imagen --referencia    # la imagen generada
uv run amoblai evaluar-respuesta <corridas> --juez opus --pagar   # faithfulness y answer relevance
uv run amoblai reporte                        # todo en datos/resultados/reporte/reporte.md
```
