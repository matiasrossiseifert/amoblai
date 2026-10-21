# Webapps de prueba

Interfaces mínimas en Gradio para probar el sistema. No tienen lógica propia:
llaman al paquete `amoblai` y muestran lo que guarda cada corrida. Correr desde
la raíz del repo:

| App | Comando | Para qué |
|---|---|---|
| Paso a paso (sin API) | `uv run --group apps python apps/paso_a_paso.py` → http://127.0.0.1:7863 | Pedís algo y te da al instante el prompt (y la imagen) para generar la imagen 1 en ChatGPT o Gemini; subís la imagen 1 y te da el prompt y las fotos de producto para la imagen final; subís la final y te da la lista de compra y, si querés, las métricas. |
| Usuario | `uv run --group apps python apps/usuario.py` → http://127.0.0.1:7860 | Foto vacía + pedido → foto amoblada + lista de compra. |
| Flujo completo | `uv run --group apps python apps/flujo.py` → http://127.0.0.1:7861 | Correr con cualquier configuración y ver cada etapa: imagen 1, detecciones, recortes, top-k de IKEA con similitud, elegido, máscara, pasos del generador n.º 2, costos y tiempos. También explora las corridas de evaluación del retriever (ground truth marcado). |
| Etiquetado | `uv run --group apps python apps/etiquetado.py` → http://127.0.0.1:7862 | Armar el set estricto (recorte → SKU exacto) en `anotaciones/estricto.jsonl`. |

## Probar sin API keys: app paso a paso

1. Subí la foto del ambiente vacío y escribí el pedido → **"1 · Darme el prompt de la imagen 1"**.
2. Copiá el prompt, adjuntá la imagen que te da (botón de descarga de la galería) en
   ChatGPT o Gemini y generá. Subí el resultado → **"2 · Listo, siguiente paso"**.
3. La app detecta los muebles, busca los productos y te da el prompt de la imagen
   final con las fotos a adjuntar **en orden** (la 1 es el ambiente). Generá, subí
   el resultado y listo: imagen final, lista de compra y métricas opcionales.

Cada imagen subida queda en `resultados/generaciones/manual/` (caché: el mismo
pedido con la misma foto no te vuelve a pedir la imagen) junto con la app usada.
En "Opciones" se cambian el embedder, el fondo, el umbral y cómo se genera la final.

## Probar sin gastar (ni generar)

En la app de flujo: generadores en `dry_run` y, como "imagen 1", una foto de
IKEA de la lista. Así se ven la detección, los recortes y el retrieval reales
sin generar nada.

## Paso manual

Con el generador `manual`, la app muestra las imágenes de entrada (en orden), el
prompt para copiar y un lugar para subir la imagen generada a mano en ChatGPT o
Gemini. Al tocar "Continuar" se guarda en la carpeta de trabajo con la app
usada y el pipeline sigue; lo ya hecho se reusa desde la caché.

Las corridas de las apps se guardan en `resultados/corridas/*_app_*`.
