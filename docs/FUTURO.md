# FUTURO: limitaciones y mejoras fuera del alcance de la entrega

Actualizado el 2026-11-12. Lo que está para decidir antes de la entrega (qué es la versión 2, qué
experimentos pagos correr) está en `docs/REVISION.md`; acá queda lo que es trabajo futuro de
verdad. Esfuerzo aproximado: S ≈ días, M ≈ 1-2 semanas, L ≈ un mes o más.

## Limitaciones que hoy tiene el sistema

- **No dice "no hay".** Cuando el catálogo no tiene lo pedido (un sofá de terciopelo mostaza),
  pone lo más parecido sin avisar: en 187 piezas el paso que elige nunca dejó una afuera, aunque
  puede. El coseno no sirve de umbral (como detector de "no hay nada así" da un AUROC de 0,72).
  Falta: que el que elige diga cuándo ningún candidato cumple, y mostrarlo. (S)
- **El tamaño no se puede verificar.** El límite de cada pieza lo estima el plan a ojo desde una
  foto, y solo el 34% de los productos de IKEA tiene alguna medida (ningún sofá ni sillón). El
  72% de lo elegido con IKEA no tiene ninguna medida. Ver "Escala y geometría".
- **El pedido abierto no está evaluado.** Los 11 pedidos de punta a punta enumeran las piezas;
  "un living nórdico y cálido", donde el plan decide qué comprar, no se midió. (S, y unos US$3)
- **El banco de retrieval es de producto conocido.** Mide el índice, no la recomendación; y
  consultas y descripciones las escribe el mismo modelo. Falta un banco escrito por personas:
  mirar solo la foto de 150 productos y escribir en 15 palabras cómo se lo pedirían a un
  vendedor. (S, sin costo)
- **No se sabe cuánto cambia la lista si se corre dos veces el mismo pedido.** (S, US$0,60 por
  ambiente)
- **El generador afirma maderas que no ve.** El 18% de las afirmaciones del porqué no se sostiene
  en lo que el generador recibió, casi siempre la especie de la madera. Pasarle la línea de
  materiales de cada candidato, o pedirle que no afirme lo que no ve. (S)
- **Variantes del mismo modelo entre los candidatos.** Con IKEA, en 40 de 75 piezas dos o más
  de los 5 candidatos son el mismo modelo en otro color o medida (18 de 75 con el catálogo
  combinado). Agrupar por modelo, o MMR, dejaría más variedad para elegir. (S)
- **Sin tope de piezas ni esquema en las respuestas.** Un plan llegó a 15 piezas (76 fotos en la
  elección, US$0,29); las respuestas del LLM se validan campo por campo, sin esquema ni
  reintento. (S)
- **La imagen:** se reconoce como el producto exacto el 41% (31 de 75 en las 11 imágenes de la
  configuración final) y el ambiente se conserva en 7 de 11; cuando no, reintentar con el mismo
  prompt casi nunca lo arregla; el lugar que decide el plan no llega al modelo de imagen; el
  modelo acepta 13 productos; los umbrales del control del ambiente están puestos a mano.

## Mejoras del RAG

- **Fusión con pesos**: la búsqueda híbrida (la versión 2) promedia los tres puntajes con pesos
  iguales, sin ajustar. Ajustarlos pide un conjunto apartado que hoy no hay. (S)
- **Recuperación anclada**: elegir primero la pieza principal (el sofá, la mesa) y reescribir
  las consultas de las demás con sus atributos, para que el conjunto combine. Una llamada más. (M)
- **Filtro por tipo con el kind como preferencia**, en lugar del filtro duro por kind, que hoy
  cuesta 2 puntos de recall cuando la consulta y el catálogo discrepan en el kind fino. (S)
- **Consultas de estilo sin pieza** ("hacelo más acogedor"): que el plan no fije el kind. El
  flujo ya lo permite (una pieza sin kinds busca en todo); falta el prompt y medirlo. (S)
- **Una vista del ambiente contra dos** (`amoblar --vista`): está implementado y nunca se midió
  si cambia la lista. (S)
- **Un modelo más barato para elegir**: la elección con Opus cuesta US$0,14 por pedido. Medir
  cuánto se pierde con Sonnet. (S, unos US$5)

## Escala y geometría

- **Medidas del ambiente**: cargadas por el usuario, con un objeto de referencia en la foto (un
  metro extendido en el piso), con profundidad métrica desde la foto (Depth Pro, ya lo usamos en
  la réplica) o con el LiDAR del celular. Con medidas reales, el filtro de tamaño sería un
  filtro de verdad. (S a L)
- **Cajas 3D para ubicar cada mueble**: en la réplica (un cuarto), indicar el lugar sube el IoU
  con la foto real de 0,20 a 0,40–0,52. Con las medidas del ambiente y del producto, la caja se
  puede calcular. (L)
- **Modelos 3D de los productos**, cuando el catálogo los tenga: ubicarlos a escala antes de
  generar. (L)

## Catálogo y datos

- **Medidas de los asientos y varias vistas por producto**: el dataset de IKEA no las trae. (M)
- **Precios y presupuesto**: con precios, un filtro de metadata más. (M)
- **Más tipos de ambientes**: dormitorios y oficinas, con sus categorías. (S-M)
- **Fotos propias de ambientes vacíos**, con dos ángulos y una referencia de medida. (S)

## Producto y producción

Edición interactiva (cambiar un solo mueble sin rehacer todo; el flujo ya guarda cada paso);
vaciar fotos de ambientes ya amoblados; base vectorial administrada cuando el catálogo crezca;
colas de trabajos para la generación; monitoreo de costos sobre el registro de gastos. El
detalle está en el informe del Ejercicio 3.
