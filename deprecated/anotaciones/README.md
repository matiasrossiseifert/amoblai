# Anotaciones

`estricto.jsonl`: set de evaluación estricta del retriever. Cada línea es un
recorte de una foto de ambiente de IKEA con su SKU exacto:

```json
{"room_id": "ikea-...-s4.jpg", "box": [x0, y0, x1, y1], "category": "chair", "sku": "002.115.83", "labeler": "matias", "timestamp": "..."}
```

`sku` puede ser `no_esta` (el mueble no está en el catálogo) o `no_es_mueble`
(detección errónea); esas etiquetas no entran en la métrica.

Se carga con la herramienta `apps/etiquetado.py`. Si una caja se etiqueta dos
veces, vale la última. Solo contiene texto (sin imágenes), así que se commitea.
