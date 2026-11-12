# Gastos del proyecto

Generado desde `datos/resultados/gastos.jsonl` (una línea por llamada paga, con su fecha, paso, modelo y costo) con `uv run amoblai gastos --md`. No lo edites a mano: volvé a generarlo.

## Por cuenta

| Cuenta | Llamadas | Gastado (US$) | Tope en la config (US$) |
|---|---|---|---|
| anthropic | 1144 | 38,44 | 50,00 |
| fal | 79 | 6,32 | 8,50 |
| openai | 0 | 0,00 | 0,50 |
| **total** | 1223 | **44,76** | |

## Por uso

| Para qué | Cuenta | Modelo | Llamadas | US$ | US$ por llamada |
|---|---|---|---|---|---|
| El flujo: elección de la lista | anthropic | claude-opus-5-5 | 76 | 12,48 | 0,164 |
| Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | claude-opus-5-5 | 562 | 11,31 | 0,020 |
| Catálogo: descripciones de los productos de ABO | anthropic | claude-opus-5-5 | 80 | 5,63 | 0,070 |
| Evaluación de punta a punta: juez que compara dos listas | anthropic | claude-opus-5-5 | 106 | 4,80 | 0,045 |
| El flujo: imagen del ambiente amoblado | fal | fal-ai/nano-banana-2/edit | 49 | 3,92 | 0,080 |
| Réplica de un ambiente real (ubicación de los muebles) | fal | fal-ai/nano-banana-2/edit | 30 | 2,40 | 0,080 |
| Evaluación del generador: faithfulness | anthropic | claude-opus-5-5 | 22 | 1,90 | 0,086 |
| El flujo: plan (lee la foto y el pedido, escribe las consultas) | anthropic | claude-opus-5-5 | 16 | 0,95 | 0,060 |
| El flujo: prompt de la imagen escrito por el LLM (configuración anterior) | anthropic | claude-opus-5-5 | 18 | 0,86 | 0,048 |
| Evaluación del generador: answer relevance | anthropic | claude-opus-5-5 | 22 | 0,28 | 0,013 |
| Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | claude-haiku-5-5 | 240 | 0,19 | 0,001 |
| Réplica de un ambiente real (ubicación de los muebles) | anthropic | claude-opus-5-5 | 1 | 0,03 | 0,027 |
| Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | claude-sonnet-5-5 | 1 | 0,01 | 0,009 |

## Por día

| Día | Para qué | Cuenta | Llamadas | US$ |
|---|---|---|---|---|
| 2026-10-21 | El flujo: elección de la lista | anthropic | 5 | 0,22 |
| 2026-10-21 | El flujo: imagen del ambiente amoblado | fal | 1 | 0,08 |
| 2026-10-21 | El flujo: plan (lee la foto y el pedido, escribe las consultas) | anthropic | 3 | 0,13 |
| 2026-10-21 | El flujo: prompt de la imagen escrito por el LLM (configuración anterior) | anthropic | 6 | 0,21 |
| 2026-10-21 | Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | 242 | 0,21 |
| 2026-10-22 | Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | 197 | 4,00 |
| 2026-10-25 | El flujo: elección de la lista | anthropic | 2 | 0,14 |
| 2026-10-25 | El flujo: imagen del ambiente amoblado | fal | 5 | 0,40 |
| 2026-10-25 | El flujo: plan (lee la foto y el pedido, escribe las consultas) | anthropic | 2 | 0,13 |
| 2026-10-25 | El flujo: prompt de la imagen escrito por el LLM (configuración anterior) | anthropic | 1 | 0,03 |
| 2026-11-09 | Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | 364 | 7,29 |
| 2026-11-10 | Catálogo: descripciones de los productos de ABO | anthropic | 80 | 5,63 |
| 2026-11-10 | El flujo: elección de la lista | anthropic | 27 | 3,72 |
| 2026-11-10 | El flujo: imagen del ambiente amoblado | fal | 4 | 0,32 |
| 2026-11-10 | El flujo: plan (lee la foto y el pedido, escribe las consultas) | anthropic | 11 | 0,69 |
| 2026-11-10 | Evaluación de punta a punta: juez que compara dos listas | anthropic | 32 | 1,51 |
| 2026-11-10 | Réplica de un ambiente real (ubicación de los muebles) | anthropic | 1 | 0,03 |
| 2026-11-10 | Réplica de un ambiente real (ubicación de los muebles) | fal | 11 | 0,88 |
| 2026-11-11 | Réplica de un ambiente real (ubicación de los muebles) | fal | 19 | 1,52 |
| 2026-11-12 | El flujo: elección de la lista | anthropic | 42 | 8,41 |
| 2026-11-12 | El flujo: imagen del ambiente amoblado | fal | 39 | 3,12 |
| 2026-11-12 | El flujo: prompt de la imagen escrito por el LLM (configuración anterior) | anthropic | 11 | 0,61 |
| 2026-11-12 | Evaluación de punta a punta: juez que compara dos listas | anthropic | 74 | 3,28 |
| 2026-11-12 | Evaluación del generador: answer relevance | anthropic | 22 | 0,28 |
| 2026-11-12 | Evaluación del generador: faithfulness | anthropic | 22 | 1,90 |

| Día | Total (US$) |
|---|---|
| 2026-10-21 | 0,86 |
| 2026-10-22 | 4,00 |
| 2026-10-25 | 0,70 |
| 2026-11-09 | 7,29 |
| 2026-11-10 | 12,78 |
| 2026-11-11 | 1,52 |
| 2026-11-12 | 17,61 |

## Lo que no está en el registro

- El trabajo hecho con subagentes de Claude Code (las descripciones de los productos de IKEA, las consultas de evaluación, los jueces de relevancia graduada): va por la suscripción, no por la API.
- Una imagen de fal del 2026-11-11 (US$0,08) que se pagó y no se guardó porque se llenó el disco.
- Los modelos locales (embeddings, SigLIP 2, detectores, rerankers): corren en CPU, gratis.
