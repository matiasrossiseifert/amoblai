# amoblai · la web

La interfaz que haríamos para el producto. Tiene:
- una landing con ejemplos reales;
- "Nuevo ambiente": la foto y el pedido;
- el avance en vivo;
- el resultado, con el antes y después y la lista de compra;
- "Mis ambientes", con las corridas de la web y las de la terminal;
- Ajustes: las claves, el modelo de imagen y los topes de gasto;
- la vista por dentro de cada corrida.

Usa el código, el catálogo y el `.env` de este repo. Desde la raíz:

```bash
uv sync --extra cpu --group apps                       # una vez
uv run --group apps python apps/web/server.py          # http://127.0.0.1:8000
```

Otro puerto: `AMOBLAI_WEB_PORT=8001`. La primera vez tarda más: baja los modelos de la búsqueda.

## Ajustes

- **Claves**: Anthropic (obligatoria), OpenAI (para gpt-image-2) y fal (para Nano Banana 2).
  - Se guardan en el `.env` de la raíz del repo.
  - La página pregunta gratis a cada proveedor si acepta la clave.
- **Imagen**:
  - el modelo, gpt-image-2 o Nano Banana 2;
  - los intentos, si la imagen no conserva el ambiente.
- **Gasto**: lo que lleva gastado la web en cada cuenta, contra un tope que se elige ahí (US$ 5
  por cuenta si no se cambia).
  - Se lleva en `apps/web/gastos.jsonl`, aparte del registro y los topes de la terminal
    (`datos/resultados/gastos.jsonl`).
  - Si una llamada pasaría el tope, la corrida se detiene antes de pagar.

## Qué hace cada corrida

1. Plan, búsqueda y elección, con la configuración final de amoblai (`datos/configs/amoblai.yaml`).
2. En paralelo con la imagen, Claude Sonnet traduce al castellano lo que se muestra: el porqué de
   cada producto y, en la vista por dentro, cómo leyó el ambiente y la idea. Cuesta menos de un centavo.
3. La imagen, con el modelo de Ajustes y el control del ambiente de amoblai. Sin clave para ese
   modelo, se muestra solo la lista.

Cuesta entre US$ 0,20 y US$ 0,80 y tarda de uno a cinco minutos, según los reintentos de la imagen.
Si una corrida se corta, se retoma desde la página: lo pagado no se repite.

## Por dentro

- `/dev/<corrida>`, o "Ver por dentro" desde el resultado. `/dev` lista todas las corridas.
- No está protegida: es otra URL, con el mismo diseño.
- Para cada etapa muestra el modelo, el prompt (con link al texto), el costo, el tiempo y los
  tokens. Además:
  - **Plan**: cómo leyó el ambiente y, de cada pieza, sus tipos, las medidas máximas y la ficha
    que se busca.
  - **Búsqueda**: los 5 candidatos de cada pieza, con foto, medidas, puntaje y descripción.
  - **Elección**: el producto elegido, de qué puesto salió, el orden del modelo y el porqué.
  - **Escena**: el prompt exacto de la imagen.
  - **Imagen**: cada intento, con su control (puntos SIFT, desplazamiento, SSIM y costo).
  - Los JSON crudos de la corrida.
- Mientras la corrida avanza, las etapas van apareciendo.

## Corridas de la terminal

"Mis ambientes" y `/dev` muestran también las corridas de `datos/resultados/amoblar/`, las de
`amoblai amoblar` y las de la interfaz vieja, si llegaron a elegir.
- En las URLs llevan el prefijo `terminal-`.
- No se modifican: su traducción queda en `apps/web/.cache/traducciones/`.
- Se retoman desde la terminal, con el mismo comando.

## Archivos

- `server.py`: la API (FastAPI) y las corridas, de a una por vez.
- `web/`: la página (HTML, CSS y JS, sin build).
  - `web/ejemplos.json` y `web/img/` son los ejemplos de la landing.
- `preparar_ejemplos.py`: arma esos ejemplos con corridas de la configuración final. Se corre una
  vez; traducir cuesta unos centavos.
- Fuera de git:
  - `corridas/`: las corridas;
  - `.cache/`: imágenes achicadas y traducciones;
  - `gastos.jsonl`: el gasto;
  - `ajustes.json`: lo que se elige en Ajustes.
