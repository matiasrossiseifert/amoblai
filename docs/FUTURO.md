# FUTURO: mejoras fuera del alcance de la v1

Cada idea que surge va acá en lugar de implementarse. Formato: **qué**: por qué vale la pena
(esfuerzo aproximado: S ≈ días, M ≈ 1-2 semanas, L ≈ un mes o más).

## Candidatos para la iteración (Ejercicio 4)

- **Que el modelo de imagen ubique los muebles donde se le pide**: en la primera imagen
  (prueba-alvear2) el prompt decía "a mitad del living" y el modelo puso todo cerca de la cámara,
  con el fondo vacío. `src/amoblai/prompts/scene_prompt_v2.md` ancla cada producto a algo visible
  a esa profundidad, da su tamaño en el cuadro y dice que el piso cerca de la cámara queda libre;
  falta probarlo (prueba-alvear2-scene-v2, una imagen). Si no alcanza: una imagen guía con un
  rectángulo dibujado donde va cada producto (Claude da las coordenadas en scene; va al modelo
  como referencia, o se pinta y se pide borrarlo), o un modelo que acepte máscaras. (S-M)
- **Que los productos no se vean pegados**: las fotos del catálogo son de estudio sobre blanco
  (muchas, renders) y v1 pedía cada producto "exactly as in its photo", con lo que el modelo
  copia también la luz pareja del estudio. v2 pide solo el diseño y la luz, el balance de blancos,
  el grano y la nitidez del ambiente. Además: salida en 2K (más cara; confirmar el precio de fal)
  y comparar con gpt-image. (S)
- **Más muebles para ambientes grandes**: un living largo con cuatro piezas queda vacío. Ampliar
  el alcance a guardado (el dataset tiene 49 bibliotecas, estanterías y vitrinas, y 7 muebles
  bajos de TV), iluminación (19 lámparas de pie y de mesa) y pufs o bancos; describirlos con
  subagentes como el resto (gratis) y dejar que el plan complete el ambiente (hasta 6 piezas)
  cuando el pedido lo deja abierto o el lugar lo pide. Accesorios (almohadones, plantas,
  cuadros: también están en el dataset) suman realismo; si no son del catálogo, no van en la
  lista de compra. (M)
- **Una vista del ambiente contra dos**: ya se puede mandar otra foto del mismo ambiente desde
  otro ángulo (`amoblai amoblar --vista`): va a Claude en plan, choose y scene para que entienda
  el tamaño y la forma del cuarto, y los muebles se agregan solo en la foto principal. Falta
  medir si mejora (las mismas corridas con y sin la vista, juzgando ubicación y escala). (S)
- **Fotos propias de ambientes vacíos** (pendiente del equipo, para más adelante): uno o dos
  ambientes, dos ángulos de cada uno y, si se puede, una con un metro extendido en el piso. Son
  las más realistas para probar el sistema y sirven para lo de las medidas (abajo). (S)
- **Medidas del ambiente**: hoy el plan estima a ojo cuánto puede medir cada mueble, y el prompt
  de la imagen da las proporciones relativas a lo que se ve. Con medidas reales el filtro de
  tamaño sería real (un sofá de 2,40 m no entra en una pared de 2 m) y el prompt podría dar la
  escala. Opciones, de menos a más esfuerzo:
  1. **Escribirlas en el pedido o en un formulario** ("la pared de la derecha mide 4 m"): el plan
     ya lee el pedido, así que en parte funciona hoy; falta pedírselo al usuario y decirle al
     prompt del plan que las use para los límites. (S)
  2. **Una referencia en la foto**: un metro extendido en el piso, o cintas a lo largo de las
     paredes (con cuatro alcanza para el contorno). Encaja con las dos fotos: la que tiene las
     cintas para medir y la limpia para amoblar, desde el mismo lugar. Ojo: un VLM lee mal los
     números de una cinta; sirve más un largo conocido (el metro trabado en 2 m) que leer marcas.
     (S-M)
  3. **Profundidad métrica desde la foto** (Depth Pro, Depth Anything V2 métrico): sin pedirle
     nada al usuario, con algo de error; corre local en la RTX 3070. (M)
  4. **AR/LiDAR del celular** (las apps de medición): lo más preciso, pero necesita una app. (L)
  Sin medidas de los asientos en el dataset (ver Catálogo), el filtro solo sirve para mesas y
  alfombras: las dos cosas van juntas.
- **Filtro por tipo en vez de kind en el retrieve**: en la ablación el filtro por kind resta un
  poco (0,616 vs. 0,636 hit@1 con Qwen3) porque la consulta y el producto discrepan en el kind
  fino (mesa auxiliar vs. ratona). Probar tipo, o kind con tipo de respaldo, midiendo de punta a
  punta. (S)
- **Consultas genéricas o de estilo** ("hacelo más acogedor"): que el plan no fije el kind y el
  RAG traiga lo pertinente; el flujo ya lo permite (una pieza sin kinds busca en todo). Falta el
  prompt y ver si sirve. (S)
- **Evaluación con calificaciones** (2 bueno, 1 aceptable, 0 mal) del top-3 para pedidos reales
  sobre ambientes vacíos, como en YouSeeYouBuy (`la evaluación con calificaciones de YouSeeYouBuy`): mide la relevancia para
  el pedido, no solo encontrar el SKU anotado. Requiere calificar a mano (o VLM-as-a-judge,
  pendiente de hablarlo con las profesoras). (M)
- **Descripciones por API vs. por subagentes**: el describer `anthropic_vision` con el mismo
  prompt, para comparar y para describir catálogos nuevos sin intervención. (S)
- **`mode: whole_catalog` vs. `rag`** en el choose: mandarle al LLM todos los productos que pasan
  los filtros en vez del top-3; mide cuánto aporta el ranking. (S)

## Evaluación (lo que quedó afuera de las métricas del 2026-10-23, ver METRICAS.md)

- **Más imágenes generadas**: las métricas de imagen (`evaluar-imagen`) están implementadas y
  probadas en una sola imagen. Con generación habilitada: las mismas corridas con scene v1 y v2,
  y con Nano Banana 2 y gpt-image, para tener n de verdad (cada imagen ≈ US$0,08 + US$0,13 de
  Claude). Gratis: generar a mano con la carpeta `manual/` (ChatGPT o Gemini) y correr
  `evaluar-imagen` sobre esas. (S)
- **Benchmark de reconstrucción con IKEA**: vaciar con inpainting algunas fotos de ambientes IKEA
  (el modelo de imagen saca los muebles), correr el flujo con un pedido escrito desde la foto
  original y comparar contra la foto real: los recortes en el mismo lugar, el embedding global y
  la lista contra los productos anotados (precision/recall de la lista). Es la única forma de
  tener ground truth de punta a punta. Unos US$0,30 por ambiente; 10 ambientes ≈ US$3. (M)
- **Reranking con el VLM sobre el catálogo ampliado**: 367 llamadas sin caché ≈ US$7,5 (hace
  falta subir el tope de Anthropic). (S)
- **Qwen3-Reranker sobre las 552 consultas**: gratis pero ~10 s por par en esta CPU (≈15 h);
  con la RTX 3070 son minutos (`datos/configs/ablaciones/reranking-local.yaml`). (S)
- **Juez por la API en vez de subagentes** (`evaluar-respuesta --juez opus`): reproducible por
  cualquiera con la clave; centavos por corrida. Y medir el acuerdo entre jueces (dos subagentes
  ya discrepan: 0,92 contra 0,96 en la misma respuesta). (S)
- **Evaluación humana** (la clase la menciona): que el equipo y algunos amigos comparen pares de
  imágenes (v1 contra v2) a ciegas; preferencia y acuerdo. (S)

## Escala y geometría

- **Escala métrica**: medidas del ambiente cargadas por el usuario, objetos de referencia en la
  foto (puertas, enchufes) o captura con AR/LiDAR del celular; sin escala no se puede saber si un
  sofá de 2,40 m entra. (L)
- **Proxies 3D y ubicación basada en geometría**: ubicar el modelo 3D del producto a escala antes
  del pase de realismo; es lo que hace YouSeeYouBuy con el mismo núcleo. (L)
- **Verificación de que los muebles entran**: con escala y las medidas del catálogo; hoy los
  límites los estima el plan mirando la foto. (M)

## Catálogo y datos

- **Varias vistas por producto y medidas de los asientos mediante scraping**: mejores
  descripciones y referencias para el generador (hoy hay una foto por SKU, y 7 SKUs se excluyeron
  porque su foto era de otra medida), y las medidas que el dataset no trae (sofás, sillones y
  sillas: ninguno tiene). Revisar términos de uso del sitio. (M)
- **Precios y selección según presupuesto**: el dataset no trae precios; con scraping, un filtro
  duro más. (M)
- **Otras tiendas y catálogos**: un loader por fuente y sus descripciones; el RAG no depende del
  catálogo. YouSeeYouBuy ya tiene 708 productos de otras fuentes. (M por tienda)
- **Más tipos de ambientes**: dormitorios, oficinas, con sus categorías (camas, mesas de luz,
  escritorios). Implica describirlos y sumar kinds. (S-M)
- **Fotos de ambientes vacíos propias** para la evaluación de punta a punta. (S)

## Producto

- **Edición interactiva**: cambiar un solo mueble (otro candidato del top-3, otro color) sin
  rehacer todo; el flujo ya guarda cada paso. (M)
- **Vaciar fotos de ambientes ya amoblados** (inpainting de los muebles existentes). (M)
- **Batch API** para generar muchas imágenes a mitad de precio cuando la latencia no importa. (S)

## Producción

- **Base vectorial administrada** (Chroma en modo servidor, pgvector, Pinecone) cuando el
  catálogo crezca; hoy ChromaDB embebido sobre 268 vectores alcanza. (S-M)
- **Colas de trabajos** para la generación (lenta): API que encola y notifica, reintentos y
  límites de tasa. (M)
- **Monitoreo de costos y calidad**: tablero sobre `datos/resultados/gastos.jsonl`, alertas por tope. (S)

## Si se retoma la v0 (retrieval por imagen, deprecated/)

- Filtro por grupo de asientos (el detector confunde silla ↔ sillón). (S)
- Segmentación por concepto con SAM 3 (detección y máscara en un paso). (S-M)
- Estrategia específica para alfombras tapadas por muebles. (S)
- Fine-tuning de embeddings de imagen con pares recorte ↔ foto de catálogo. (M-L)
- Combinar: retrieval por texto + reranking por similitud de imagen entre el producto y el
  mueble generado. (M)
