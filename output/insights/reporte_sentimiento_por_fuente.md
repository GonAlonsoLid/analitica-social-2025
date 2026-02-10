# Análisis de sentimiento por fuente – F1 (2025)

## Resumen
- **Total de reseñas analizadas:** 2051
- **Fuentes:** Reddit, YouTube - Trailer, YouTube - Video 2
- Las gráficas y comparaciones usan **métricas normalizadas** (%, por reseña, por 100 reseñas) para que el volumen de datos no penalice a fuentes con menos comentarios.

## Métricas por fuente

### Reddit
- Número de reseñas: **103**
- Sentimiento medio (compound): **0.247** (comparable entre fuentes)
- Etiqueta dominante: **positive**
- Distribución **normalizada (%):** Positivo 50.5%, Neutral 39.8%, Negativo 9.7%
- Engagement total: **386** | **Por reseña (normalizado):** 3.7

**Palabras más frecuentes (por 100 reseñas, comparable entre fuentes):**

- sonny (118.4 por 100 reseñas)
- brad (101.9 por 100 reseñas)
- shot (84.5 por 100 reseñas)
- apx (78.6 por 100 reseñas)
- sequel (71.8 por 100 reseñas)
- tom (69.9 por 100 reseñas)
- scene (63.1 por 100 reseñas)
- time (58.3 por 100 reseñas)
- people (53.4 por 100 reseñas)
- imax (53.4 por 100 reseñas)

### YouTube - Trailer
- Número de reseñas: **912**
- Sentimiento medio (compound): **0.353** (comparable entre fuentes)
- Etiqueta dominante: **positive**
- Distribución **normalizada (%):** Positivo 60.9%, Neutral 30.2%, Negativo 9.0%
- Engagement total: **95538** | **Por reseña (normalizado):** 104.8

**Palabras más frecuentes (por 100 reseñas, comparable entre fuentes):**

- brad (4809.6 por 100 reseñas)
- box (3753.4 por 100 reseñas)
- ferrari (3452.7 por 100 reseñas)
- pitt (2029.8 por 100 reseñas)
- faster (1958.2 por 100 reseñas)
- checking (1957.7 por 100 reseñas)
- radio (1683.6 por 100 reseñas)
- must (1449.5 por 100 reseñas)
- team (1427.6 por 100 reseñas)
- passing (1424.8 por 100 reseñas)

### YouTube - Video 2
- Número de reseñas: **1036**
- Sentimiento medio (compound): **0.382** (comparable entre fuentes)
- Etiqueta dominante: **positive**
- Distribución **normalizada (%):** Positivo 68.7%, Neutral 13.2%, Negativo 18.1%
- Engagement total: **37083** | **Por reseña (normalizado):** 35.8

**Palabras más frecuentes (por 100 reseñas, comparable entre fuentes):**

- top (1409.6 por 100 reseñas)
- gun (1406.5 por 100 reseñas)
- maverick (1307.5 por 100 reseñas)
- director (991.3 por 100 reseñas)
- sold (884.5 por 100 reseñas)
- went (676.9 por 100 reseñas)
- round (631.9 por 100 reseñas)
- much (517.4 por 100 reseñas)
- race (451.2 por 100 reseñas)
- races (442.6 por 100 reseñas)

## Gráficas generadas

- `figures/sentiment_distribution_by_source.png` – Distribución en % (normalizado)
- `figures/avg_compound_by_source.png` – Sentimiento medio por fuente
- `figures/engagement_by_source.png` – Engagement medio y total (comparación justa)
- `figures/top_words_by_source.png` – Palabras clave (frecuencia por 100 reseñas)
- `figures/compound_boxplot_by_source.png` – Boxplot de sentimiento por fuente
- `figures/wordcloud_*.png` – Nube de palabras por fuente
- `figures/wordcloud_global_positive.png` – Palabras en comentarios positivos (todas las fuentes)
- `figures/wordcloud_global_negative.png` – Palabras en comentarios negativos (todas las fuentes)
- `figures/wordcloud_global_bigrams.png` – Bigramas más frecuentes (pares de palabras)

**Notas sobre los wordclouds:**
- Las palabras se filtran con una lista de stopwords (EN/ES + cine); palabras como *about* no deberían aparecer; si ves alguna, puede ser de una ejecución anterior.
- El wordcloud **negativo** muestra palabras que aparecen en *comentarios* etiquetados como negativos por VADER, no palabras «negativas» en sí. Por ejemplo, *leclerc* puede salir ahí porque aparece en comentarios que el modelo puntuó como negativos (críticas, discusiones, etc.).

## Recomendaciones para estrategia de marketing

- **Reddit**: El sentimiento es mayormente positivo. Refuerza mensajes que destaquen los aspectos que la audiencia valora (revisar palabras clave) y usa testimonios o citas positivas en campañas.

- **YouTube - Trailer**: El sentimiento es mayormente positivo. Refuerza mensajes que destaquen los aspectos que la audiencia valora (revisar palabras clave) y usa testimonios o citas positivas en campañas.

- **YouTube - Video 2**: El sentimiento es mayormente positivo. Refuerza mensajes que destaquen los aspectos que la audiencia valora (revisar palabras clave) y usa testimonios o citas positivas en campañas.
