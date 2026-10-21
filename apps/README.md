# Webapps de prueba

```bash
uv run --group apps python apps/amoblar.py      # http://127.0.0.1:7860
```

Foto del ambiente + pedido → cada paso del flujo, a medida que se hace:

1. **plan** (Claude): cómo leyó el ambiente y las piezas, con su kind, sus límites y su consulta.
2. **retrieve**: los candidatos del catálogo de cada pieza (las mismas hojas que ve Claude).
3. **choose** (Claude): los elegidos y por qué (la lista de compra).
4. **scene** (Claude): el prompt para el modelo de imagen.
5. **generate**: la imagen por API (Nano Banana 2 en fal) o a mano: te muestra las imágenes en
   orden y el prompt para pegar en ChatGPT o Gemini, y subís el resultado.

Nada pago sale sin tildar su casilla ("Usar Claude", "Generar la imagen por API"), y siempre
dentro de los topes de `configs/amoblai.yaml`; la app muestra lo gastado por cuenta. Cada corrida
queda en `resultados/amoblar/app-<fecha>/` y se puede seguir ("Seguir esta corrida"): lo ya
hecho no se repite ni se vuelve a pagar.

Las apps de la v0 (retrieval por imagen) están en `deprecated/apps/`.
