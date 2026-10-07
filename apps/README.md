# Webapps de prueba

Interfaces mínimas en Gradio para probar el sistema. No tienen lógica propia:
llaman al paquete `amoblai` y muestran lo que guarda cada corrida. Correr desde
la raíz del repo:

| App | Comando | Para qué |
|---|---|---|
| Usuario | `uv run --group apps python apps/usuario.py` → http://127.0.0.1:7860 | Foto vacía + pedido → foto amoblada + lista de compra. |
| Flujo completo | `uv run --group apps python apps/flujo.py` → http://127.0.0.1:7861 | Correr con cualquier configuración y ver cada etapa: imagen 1, detecciones, recortes, top-k de IKEA con similitud, elegido, máscara, pasos del generador n.º 2, costos y tiempos. También explora las corridas de evaluación del retriever (ground truth marcado). |
| Etiquetado | `uv run --group apps python apps/etiquetado.py` → http://127.0.0.1:7862 | Armar el set estricto (recorte → SKU exacto) en `anotaciones/estricto.jsonl`. |

## Probar sin gastar

En la app de flujo: generadores en `dry_run` y, como "imagen 1", una foto de
IKEA de la lista. Así se ven la detección, los recortes y el retrieval reales
sin generar nada.

## Paso manual

Con el generador `manual`, la app muestra las imágenes de entrada (en orden), el
prompt para copiar y un lugar para subir la imagen generada a mano en ChatGPT o
Gemini. Al tocar "Continuar" se guarda en la carpeta de trabajo con la app
usada y el pipeline sigue; lo ya hecho se reusa desde la caché.

Las corridas de las apps se guardan en `resultados/corridas/*_app_*`.
