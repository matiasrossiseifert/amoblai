# FUTURO: mejoras fuera del alcance de la v1

Cada idea que surge va acá en lugar de implementarse. Formato: **qué**: por qué vale la pena
(esfuerzo aproximado: S ≈ días, M ≈ 1-2 semanas, L ≈ un mes o más).

## Candidatos para la iteración (Ejercicio 4)

- **Dos fotos del ambiente desde distintos ángulos**: para que el modelo (plan, scene y el
  generador) entienda mejor las dimensiones y la forma del cuarto, mandar una segunda foto del
  mismo ambiente; los muebles se agregan solo en una de las dos. roomrag hoy recibe una foto:
  hay que sumar las vistas extra al contenido de plan/scene y como referencia al generador. (S-M)
- **Filtro por tipo en vez de kind en el retrieve**: en la ablación el filtro por kind resta un
  poco (0,599 vs. 0,618 hit@1 con Qwen3) porque la consulta y el producto discrepan en el kind
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

- **Varias vistas por producto mediante scraping**: mejores descripciones y mejores referencias
  para el generador (hoy hay una foto por SKU y varios SKUs comparten foto). Revisar términos de
  uso del sitio. (M)
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
  hoy la búsqueda exacta sobre 275 vectores alcanza. (S-M)
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
