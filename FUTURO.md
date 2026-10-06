# FUTURO: mejoras fuera del alcance de la v1

Cada idea que surge va acá en lugar de implementarse. Formato: **qué**: por qué
vale la pena (esfuerzo aproximado: S ≈ días, M ≈ 1-2 semanas, L ≈ un mes o más).

## Iteración prevista (Ejercicio 4)

- **Reranking con un VLM (post-retrieval)**: la v1 elige el top-1 del retriever y
  después del generador n.º 1 ya no usa el texto del usuario (colores, estilo); un
  VLM que recibe el recorte, los top-k candidatos y el prompt puede elegir mejor
  entre productos muy parecidos y respetar el pedido. La interfaz `Reranker` ya
  existe (`retrieval/reranker.py`). (S)

## Escala y geometría

- **Escala métrica**: medidas del ambiente cargadas por el usuario, objetos de
  referencia en la foto (puertas, enchufes) o captura con AR/LiDAR del celular;
  sin escala no se puede saber si un sofá de 2,40 m entra. (L)
- **Proxies 3D y ubicación basada en geometría**: estimar el plano del piso y las
  paredes y ubicar cajas 3D del tamaño real del producto antes de generar; da
  perspectiva y proporciones consistentes en vez de confiar en el generador. (L)
- **Verificación de que los muebles entran usando medidas reales**: con escala y
  las medidas del catálogo (`dims_cm`), descartar o advertir productos que no
  caben. Requiere interpretar qué dimensión es cuál según la categoría. (M)

## Catálogo y datos

- **Varias vistas por producto mediante scraping**: el índice ya soporta varias
  imágenes por SKU (una entrada por imagen); más vistas mejoran el retrieval de
  recortes en ángulo. Revisar términos de uso del sitio. (M)
- **Precios y selección según presupuesto**: el dataset no trae precios; con
  scraping se puede filtrar por precio como metadata y armar una lista de compra
  con total. (M)
- **Otras tiendas y catálogos**: el pipeline es independiente del catálogo; hace
  falta un loader por fuente y normalizar categorías. (M por tienda)
- **Más tipos de ambientes y categorías**: dormitorios, oficinas; y categorías
  hoy excluidas del mapeo, como taburetes (Stool, Bar stool), pufs (Pouffe,
  Footstool) y lámparas. Implica sumar etiquetas al detector y revisar el mapeo. (S-M)
- **Fotos de ambientes vacíos sin restricciones de uso** para ampliar la
  evaluación de punta a punta (hoy las saca el grupo). (S)

## Retrieval

- **Filtro por grupo de categorías**: el detector confunde sofá ↔ sillón y
  silla ↔ sillón; con filtro duro, ese error se vuelve un error de retrieval.
  Buscar en "asientos" (sofá + sillón + silla) o en las dos categorías más
  probables del detector. (S)
- **Recuperación híbrida imagen + texto**: usar el prompt del usuario (por ejemplo
  "sofá verde") con los embeddings de texto de CLIP/SigLIP para reordenar o
  filtrar candidatos, además del recorte. (S-M)
- **Fine-tuning de embeddings con recortes en contexto**: entrenar (o adaptar
  con LoRA) el embedder con pares recorte de ambiente ↔ foto de catálogo para
  achicar la brecha de dominio; el dataset trae los pares de forma débil. (M-L)
- **Segmentación por concepto (SAM 3)**: detección y máscara en un solo paso
  con prompts de texto; puede reemplazar detector + SAM y segmentar mejor las
  alfombras tapadas por muebles. Disponible en transformers. (S-M)
- **Estrategia específica para alfombras**: hoy se recortan con los muebles
  encima; probar `skip_categories: [rug]`, inpainting de lo que la tapa o
  recortes de textura. (S)
- **VLM-as-a-judge** para evaluar la imagen final (fidelidad al producto,
  realismo, cumplimiento del prompt). Pendiente de hablarlo con las profesoras. (S)

## Producto

- **Edición interactiva**: cambiar un solo mueble (otro candidato del top-k,
  otro color) sin regenerar todo; el modo `per_item` ya trabaja de a un mueble. (M)
- **Varias fotos por ambiente**: consistencia de los mismos productos entre
  vistas. (L)
- **Vaciar fotos de ambientes ya amoblados** (inpainting de los muebles
  existentes) para aceptar fotos reales del usuario. (M)
- **Batch API para precargar la caché de generación**: enviar el generador n.º 1
  de todos los ambientes en un batch (50% más barato) y que el pipeline lo
  encuentre en la caché. La API soporta `/v1/images/edits` en batch. (S)

## Producción

- **Base vectorial administrada** (Chroma Cloud, pgvector, Pinecone) en lugar de
  Chroma local persistente. (S-M)
- **Colas de trabajos** para las llamadas de generación (son lentas): API que
  encola y notifica, reintentos y límites de tasa. (M)
- **Monitoreo de costos y calidad**: tablero sobre `resultados/gastos.jsonl` y
  las trazas de LangSmith; alertas por presupuesto. (S-M)
