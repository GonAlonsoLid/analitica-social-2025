# Flujo completo de analítica social – F1 (2025)

Documento para pasar a Chatty (o a un estratega) y que pueda generar **estrategias de marketing** a partir de los datos, gráficas y reportes que produce este código.

---

## 1. Objetivo del proyecto

Analizar **reseñas y comentarios** sobre la película F1 (2025) procedentes de varias fuentes (Reddit, YouTube, IMDB, Rotten Tomatoes, Instagram), para obtener:

- **Sentimiento** por comentario y por fuente (positivo / neutro / negativo).
- **Palabras clave, bigramas y temas** que explican ese sentimiento.
- **Métricas normalizadas** (por fuente, por 100 reseñas, por engagement) para comparar canales con distinto volumen.
- **Gráficas y reportes** listos para presentar y para inspirar estrategias (targeting, contenido, canales, timing).

---

## 2. Flujo de datos (resumen)

```
data/raw/ (scraping)  →  data/clean/ (limpieza)  →  output/insights/ (análisis + figuras + reportes)
         ↑                         ↑                           ↑
   main_scraper.py          run_cleaning.py           run_analysis.py
   (reviews por fuente)     (limpia, filtra,          (4 pasos: insights,
    + combined              deduplica)                 sentiment, temático,
                                                       report por fuente)
```

**Orden de ejecución recomendado:**

1. `python main_scraper.py` → obtiene reseñas y las guarda en `data/raw/`.
2. `python run_cleaning.py` → limpia y guarda en `data/clean/reviews_f1_clean.json`.
3. `python run_analysis.py` → ejecuta los 4 análisis y genera todo en `output/insights/`.

**Dependencias para gráficas:** Para que se generen las **wordclouds** hace falta tener instalada la librería `wordcloud` (`pip install wordcloud`). Si no está instalada, el reporte imprime un aviso y el resto de gráficas (barras, boxplot, etc.) se generan igual; solo faltarán los PNG de nubes de palabras.

---

## 3. Paso a paso del código

### 3.1 Scraping (`main_scraper.py`)

- **Qué hace:** Obtiene reseñas/comentarios de IMDB, Rotten Tomatoes, Instagram (Steady API), Reddit (Steady API), YouTube (por `video_id`).
- **Salida:** Archivos en `data/raw/`:
  - `reviews_imdb.json`, `reviews_rottentomatoes.json`, `reviews_instagram.json`, `reviews_reddit.json`, `reviews_youtube.json`
  - `reviews_f1_combined.json` (combinación de todas las fuentes).
- **Estructura de cada reseña (ejemplo):** `source`, `content`, `author`, `likes` / `helpful_votes`, `video_id` (YouTube), etc.

### 3.2 Limpieza (`run_cleaning.py` → `src/cleaning/pipeline.py`)

- **Qué hace:**
  - **Carga** datos de `data/raw/` (archivos por fuente o `reviews_f1_combined.json`).
  - **Limpieza ligera** del texto: quita URLs, enlaces markdown, timestamps (ej. `0:27`). **No** quita stop words (para que VADER pueda usar negaciones: *not*, *don't*, *no*).
  - **Filtra** reseñas con contenido muy corto (< 15 caracteres), muy pocas palabras (< 3) o solo ruido (lol, lmao, etc.).
  - **Deduplica** por contenido (hash del inicio del texto).
- **Salida:** `data/clean/reviews_f1_clean.json` (lista de `reviews` con campos limpios).

### 3.3 Análisis de insights básicos (`src/analysis/insights.py`)

- **Qué hace:** A partir de datos limpios, calcula:
  - Total de reseñas, distribución por fuente, longitud media del contenido.
  - Engagement total y por fuente (likes / helpful_votes).
- **Salida:** `output/insights/insights_basicos.json`.

### 3.4 Análisis de sentimiento (`src/analysis/sentiment.py`)

- **Qué hace:**
  - Usa **VADER** (Valence Aware Dictionary and sEntiment Reasoner), adaptado a redes sociales y cine.
  - Por cada comentario: scores `neg`, `neu`, `pos`, **compound** (-1 a +1).
  - Etiqueta: **positive** (compound ≥ 0.05), **negative** (≤ -0.05), **neutral** (entre ambos).
  - Ajuste de léxico para cine: *insane*, *crazy*, *fire*, *phenomenal*, etc. se consideran positivos.
- **Salidas:**
  - `output/insights/insights_sentimiento.json`: distribución por etiqueta, media por fuente, engagement por sentimiento, compound ponderado por likes.
  - `output/insights/reviews_con_sentimiento.json`: cada reseña con campo `sentiment` (neg, neu, pos, compound, label).

### 3.5 Análisis temático (`src/analysis/thematic.py`)

- **Qué hace:**
  - Agrupa comentarios por etiqueta de sentimiento (positive / neutral / negative).
  - Calcula **frecuencias de palabras y bigramas** por categoría (con y sin ponderar por engagement).
  - Identifica **términos distintivos** (más en positivos que en negativos y viceversa).
  - Extrae **citas representativas** por categoría (ordenadas por engagement).
  - **Infiere temas** para marketing (p. ej. “Brad Pitt y actuaciones”, “Hans Zimmer y banda sonora”, “Top Gun: Maverick”, “críticas al guion”).
  - Genera **recomendaciones de marketing** a partir de esos temas.
- **Entrada:** `load_raw_data()` (raw o clean según disponibilidad); aplica VADER si no viene ya etiquetado.
- **Salidas:**
  - `output/insights/analisis_tematico_marketing.json`: resumen, por_que_positivo, por_que_negativo, por_que_neutral (palabras, bigramas, citas, insight_marketing), por_fuente, recomendaciones_marketing.
  - `output/insights/reporte_marketing.md`: reporte legible en Markdown.

### 3.6 Reporte por fuente + gráficas (`src/analysis/sentiment_sources_report.py`)

- **Qué hace:**
  - Carga datos de `data/clean/` (o `data/raw/` combined si no hay clean).
  - Añade sentimiento VADER a cada reseña.
  - **Agrupa por fuente;** YouTube se desglosa por video (Trailer / Video 2) mediante `video_id`.
  - Por cada fuente: conteos, % positivo/neutro/negativo, compound medio, engagement total y por reseña, **top palabras** (frecuencia y por 100 reseñas para comparar), textos de ejemplo positivos/negativos.
  - **Tokenización:** palabras ≥ 3 letras, sin URLs, sin **stopwords** (EN/ES/cine + ruido) definidas en `src/analysis/stopwords_social.py`. Palabras como *about* están en esa lista. Nombres que suelen aparecer en contexto negativo (p. ej. *leclerc*) se pueden añadir a las stopwords en ese mismo archivo para que no distorsionen los wordclouds.
  - **Bigramas:** pares de palabras consecutivas (ej. *brad pitt*, *top gun*) para un wordcloud global de bigramas. El archivo `wordcloud_global_bigrams.png` **siempre se genera** (si hay datos de wordclouds); si no hay suficientes bigramas, se guarda una imagen con el mensaje "No hay suficientes bigramas para mostrar".
  - **Wordclouds:** solo se generan si la librería `wordcloud` está instalada; si no, el script muestra un aviso y el resto de gráficas se crea igual.
  - **Gráficas generadas:**
    - `sentiment_distribution_by_source.png` – Distribución % positivo/neutro/negativo por fuente.
    - `avg_compound_by_source.png` – Sentimiento medio (compound) por fuente.
    - `engagement_by_source.png` – Engagement total y por reseña por fuente.
    - `top_words_by_source.png` – Barras horizontales: top palabras (por 100 reseñas) por fuente.
    - `compound_boxplot_by_source.png` – Boxplot del compound por fuente.
    - `wordcloud_<fuente>.png` – Nube de palabras por fuente (ej. Reddit, YouTube, YouTube - Trailer, YouTube - Video 2).
    - `wordcloud_global_positive.png` – Palabras que aparecen en comentarios **etiquetados como positivos** (todas las fuentes).
    - `wordcloud_global_negative.png` – Palabras que aparecen en comentarios **etiquetados como negativos** (no son “palabras malas” en sí; son términos que salen en comentarios que VADER puntuó negativo).
    - `wordcloud_global_bigrams.png` – Bigramas más frecuentes (todas las fuentes); siempre se crea este PNG cuando hay wordclouds.
  - **Reporte:** `output/insights/reporte_sentimiento_por_fuente.md` con métricas por fuente, listado de gráficas, notas sobre wordclouds y recomendaciones por fuente (positivo / negativo / neutro).

**Notas para estrategia:**

- El wordcloud **negativo** muestra **palabras que aparecen en comentarios que VADER puntuó como negativos**, no palabras con carga negativa intrínseca. Para evitar que nombres propios (ej. pilotos) dominen la nube, se pueden añadir a `src/analysis/stopwords_social.py` (p. ej. *leclerc* está ya incluido).
- Las métricas están **normalizadas** (%, por 100 reseñas, por reseña) para que fuentes con menos volumen no queden penalizadas en las comparaciones.

---

## 4. Archivos de salida (qué usar para estrategias)

| Ubicación | Contenido útil para estrategia |
|-----------|---------------------------------|
| `output/insights/insights_basicos.json` | Volumen por fuente, engagement por fuente. |
| `output/insights/insights_sentimiento.json` | Distribución global de sentimiento, compound por fuente, % de likes en comentarios positivos. |
| `output/insights/sentiment_by_source.json` | Por fuente: count, avg_compound, pct_positive/neutral/negative, top_words, textos_positive/texts_negative (muestras). |
| `output/insights/analisis_tematico_marketing.json` | **Por qué** es positivo/negativo/neutro: palabras, bigramas, términos distintivos, citas, insight_marketing, recomendaciones_marketing. |
| `output/insights/reporte_marketing.md` | Resumen temático y recomendaciones en prosa. |
| `output/insights/reporte_sentimiento_por_fuente.md` | Métricas por fuente, recomendaciones por canal, lista de figuras. |
| `output/insights/figures/*.png` | Todas las gráficas anteriores (distribución, compound, engagement, top words, boxplot, wordclouds por fuente, wordclouds globales positivo/negativo, wordcloud bigramas). |
| `output/insights/reviews_con_sentimiento.json` | Cada reseña con sentiment; útil para profundizar en citas o ejemplos. |

---

## 5. Cómo usar esto para generar estrategias (instrucciones para Chatty)

- **Targeting:** Usar `insights_basicos.json` y `sentiment_by_source.json` para ver dónde hay más volumen y engagement, y qué fuentes son más positivas/negativas. Los **top_words** y **wordclouds por fuente** indican lenguaje y temas por canal.
- **Contenido:** Usar `analisis_tematico_marketing.json` (por_que_positivo, por_que_negativo, bigramas, citas_representativas) y los **wordclouds globales** (positivo, negativo, bigramas) para elegir mensajes, testimonios y temas a destacar o a abordar (objeciones).
- **Canales:** Comparar `avg_compound`, `pct_positive/negative` y engagement por fuente en `sentiment_by_source.json` y en `reporte_sentimiento_por_fuente.md` para priorizar canales y tono por canal.
- **Timing y narrativa:** Las **citas representativas** y los **insight_marketing** del análisis temático sirven para secuencias de campaña y copy que conecte con lo que la audiencia ya dice.

Si Chatty tiene acceso a estos JSON y MD (o a un resumen de ellos), puede proponer estrategias concretas de targeting, contenido, canales y timing para la película F1 (2025) a partir de este flujo de analítica social.
