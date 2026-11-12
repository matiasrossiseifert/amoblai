# Gastos del proyecto

Generado desde `datos/resultados/gastos.jsonl` (una línea por llamada paga, con su fecha, paso, modelo y costo) con `uv run amoblai gastos --md`. No lo edites a mano: volvé a generarlo.

## Por cuenta

| Cuenta | Llamadas | Gastado (US$) | Tope en la config (US$) |
|---|---|---|---|
| anthropic | 1050 | 29,41 | 30,00 |
| fal | 50 | 4,00 | 8,50 |
| openai | 0 | 0,00 | 0,50 |
| **total** | 1100 | **33,41** | |

## Por uso

| Para qué | Cuenta | Modelo | Llamadas | US$ | US$ por llamada |
|---|---|---|---|---|---|
| Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | claude-opus-5-5 | 562 | 11,31 | 0,020 |
| El flujo: elección de la lista | anthropic | claude-opus-5-5 | 54 | 6,89 | 0,128 |
| Catálogo: descripciones de los productos de ABO | anthropic | claude-opus-5-5 | 80 | 5,63 | 0,070 |
| Evaluación de punta a punta: juez que compara dos listas | anthropic | claude-opus-5-5 | 67 | 3,06 | 0,046 |
| Réplica de un ambiente real (ubicación de los muebles) | fal | fal-ai/nano-banana-2/edit | 30 | 2,40 | 0,080 |
| El flujo: imagen del ambiente amoblado | fal | fal-ai/nano-banana-2/edit | 20 | 1,60 | 0,080 |
| Evaluación del generador: faithfulness | anthropic | claude-opus-5-5 | 11 | 0,96 | 0,088 |
| El flujo: plan (lee la foto y el pedido, escribe las consultas) | anthropic | claude-opus-5-5 | 16 | 0,95 | 0,060 |
| El flujo: prompt de la imagen escrito por el LLM (configuración anterior) | anthropic | claude-opus-5-5 | 7 | 0,24 | 0,035 |
| Evaluación: un VLM ordena el top-10 (ground truth de IKEA) | anthropic | claude-haiku-5-5 | 240 | 0,19 | 0,001 |
| Evaluación del generador: answer relevance | anthropic | claude-opus-5-5 | 11 | 0,14 | 0,013 |
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
| 2026-11-12 | El flujo: elección de la lista | anthropic | 20 | 2,82 |
| 2026-11-12 | El flujo: imagen del ambiente amoblado | fal | 10 | 0,80 |
| 2026-11-12 | Evaluación de punta a punta: juez que compara dos listas | anthropic | 35 | 1,54 |
| 2026-11-12 | Evaluación del generador: answer relevance | anthropic | 11 | 0,14 |
| 2026-11-12 | Evaluación del generador: faithfulness | anthropic | 11 | 0,96 |

| Día | Total (US$) |
|---|---|
| 2026-10-21 | 0,86 |
| 2026-10-22 | 4,00 |
| 2026-10-25 | 0,70 |
| 2026-11-09 | 7,29 |
| 2026-11-10 | 12,78 |
| 2026-11-11 | 1,52 |
| 2026-11-12 | 6,26 |

## Lo que no está en el registro

- El trabajo hecho con subagentes de Claude Code (las descripciones de los productos de IKEA, las consultas de evaluación, los jueces de relevancia graduada): va por la suscripción, no por la API.
- Una imagen de fal del 2026-11-11 (US$0,08) que se pagó y no se guardó porque se llenó el disco.
- Los modelos locales (embeddings, SigLIP 2, detectores, rerankers): corren en CPU, gratis.
