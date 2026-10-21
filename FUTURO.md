# FUTURO: mejoras fuera del alcance de la v1

Cada idea que surge va acá en lugar de implementarse. Formato: **qué**: por qué vale la pena
(esfuerzo aproximado: S ≈ días, M ≈ 1-2 semanas, L ≈ un mes o más).

## Candidatos para la iteración (Ejercicio 4)

- **Una vista del ambiente contra dos**: ya se puede mandar otra foto del mismo ambiente desde
  otro ángulo (`amoblai amoblar --vista`): va a Claude en plan, choose y scene para que entienda
  el tamaño y la forma del cuarto, y los muebles se agregan solo en la foto principal. Falta
  medir si mejora (las mismas corridas con y sin la vista, juzgando ubicación y escala). (S)
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
  RAG traiga lo pertinente; roomrag ya lo permite (una pieza sin kinds busca en todo). Falta el
  prompt y ver si sirve. (S)
- **Evaluación con calificaciones** (2 bueno, 1 aceptable, 0 mal) del top-3 para pedidos reales
  sobre ambientes vacíos, como en YouSeeYouBuy (`roomrag/evaluate.py`): mide la relevancia para
  el pedido, no solo encontrar el SKU anotado. Requiere calificar a mano (o VLM-as-a-judge,
  pendiente de hablarlo con las profesoras). (M)
- **Descripciones por API vs. por subagentes**: el describer `anthropic_vision` con el mismo
  prompt, para comparar y para describir catálogos nuevos sin intervención. (S)
- **`mode: whole_catalog` vs. `rag`** en el choose: mandarle al LLM todos los productos que pasan
  los filtros en vez del top-3; mide cuánto aporta el ranking. (S)

## Escala y geometría

- **Escala métrica**: medidas del ambiente cargadas por el usuario, objetos de referencia en la
  foto (puertas, enchufes) o captura con AR/LiDAR del celular; sin escala no se puede saber si un
  sofá de 2,40 m entra. (L)
- **Proxies 3D y ubicación basada en geometría**: ubicar el modelo 3D del producto a escala antes
  del pase de realismo; es lo que hace YouSeeYouBuy con el mismo roomrag. (L)
- **Verificación de que los muebles entran**: con escala y las medidas del catálogo; hoy los
  límites los estima el plan mirando la foto. (M)

## Catálogo y datos

- **Varias vistas por producto y medidas de los asientos mediante scraping**: mejores
  descripciones y referencias para el generador (hoy hay una foto por SKU, y 7 SKUs se excluyeron
  porque su foto era de otra medida), y las medidas que el dataset no trae (sofás, sillones y
  sillas: ninguno tiene). Revisar términos de uso del sitio. (M)
- **Precios y selección según presupuesto**: el dataset no trae precios; con scraping, un filtro
  duro más. (M)
- **Otras tiendas y catálogos**: un loader por fuente y sus descripciones; roomrag no depende del
  catálogo. YouSeeYouBuy ya tiene 708 productos de otras fuentes. (M por tienda)
- **Más tipos de ambientes y categorías**: dormitorios, oficinas; taburetes, pufs, bancos,
  lámparas, aparadores (hoy fuera del alcance aprobado). Implica describirlos y sumar kinds. (S-M)
- **Fotos de ambientes vacíos propias** para la evaluación de punta a punta. (S)

## Producto

- **Edición interactiva**: cambiar un solo mueble (otro candidato del top-3, otro color) sin
  rehacer todo; el flujo ya guarda cada paso. (M)
- **Vaciar fotos de ambientes ya amoblados** (inpainting de los muebles existentes). (M)
- **Batch API** para generar muchas imágenes a mitad de precio cuando la latencia no importa. (S)

## Producción

- **Base vectorial administrada** (pgvector, Pinecone) e índice ANN cuando el catálogo crezca;
  hoy la búsqueda exacta sobre 268 vectores alcanza. (S-M)
- **Colas de trabajos** para la generación (lenta): API que encola y notifica, reintentos y
  límites de tasa. (M)
- **Monitoreo de costos y calidad**: tablero sobre `resultados/gastos.jsonl`, alertas por tope. (S)

## Si se retoma la v0 (retrieval por imagen, deprecated/)

- Filtro por grupo de asientos (el detector confunde silla ↔ sillón). (S)
- Segmentación por concepto con SAM 3 (detección y máscara en un paso). (S-M)
- Estrategia específica para alfombras tapadas por muebles. (S)
- Fine-tuning de embeddings de imagen con pares recorte ↔ foto de catálogo. (M-L)
- Combinar: retrieval por texto + reranking por similitud de imagen entre el producto y el
  mueble generado. (M)
