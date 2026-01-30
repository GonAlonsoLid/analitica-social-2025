# Scraper de Reseñas - Película F1 (2025)

Este proyecto permite obtener y almacenar reseñas y comentarios sociales de la película **F1 (2025)** desde **IMDB**, **Rotten Tomatoes**, **Instagram**, **Reddit** y **YouTube**.

## 📋 Requisitos

- Python 3.7 o superior
- Conexión a internet

## 🚀 Instalación

1. Clona o descarga este repositorio

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 💻 Uso

### Ejecutar el scraper completo

Para obtener reseñas de ambas fuentes (IMDB y Rotten Tomatoes):

```bash
python main_scraper.py
```

### Ejecutar scrapers individuales

Si solo quieres reseñas de una fuente específica:

**IMDB:**
```bash
python scraper_imdb.py
```

**Rotten Tomatoes:**
```bash
python scraper_rottentomatoes.py
```

**Instagram (Steady API):**
```bash
export STEADYAPI_AUTH_KEY='tu_api_key'
python scraper_instagram_steady.py
# O con un shortcode específico:
python scraper_instagram_steady.py CvXyZ123Ab
```

**Reddit (Steady API):**
```bash
export STEADYAPI_AUTH_KEY='tu_api_key'
python scraper_reddit_steady.py
# O con otro subreddit:
python scraper_reddit_steady.py formula1
```

**YouTube (YouTube Data API v3):**
```bash
export YOUTUBE_API_KEY='tu_api_key'
python scraper_youtube.py
# O con otra URL o video ID:
python scraper_youtube.py https://www.youtube.com/watch?v=8yh9BPUBbbQ
```

## 📁 Archivos Generados

El script genera los siguientes archivos:

- `reviews_imdb.json` - Reseñas de IMDB
- `reviews_rottentomatoes.json` - Reseñas de Rotten Tomatoes
- `reviews_instagram.json` - Comentarios de Instagram (Steady API)
- `reviews_reddit.json` - Comentarios de Reddit r/F1movie (Steady API)
- `reviews_youtube.json` - Comentarios de YouTube (YouTube Data API)
- `reviews_f1_combined.json` - Todas las reseñas/comentarios combinados
- `reviews_f1.csv` - Reseñas en formato CSV (si pandas está instalado)

## 📸 Instagram y Reddit con Steady API

Instagram y Reddit usan la **misma API key** de [Steady API](https://steadyapi.com):

1. **Registrarte** en [steadyapi.com/register](https://steadyapi.com/register)
2. **Generar un token** en Profile → Personal Access Tokens
3. **Exportar**: `export STEADYAPI_AUTH_KEY='tu_token_aqui'`

**Instagram**: Post por defecto [instagram.com/p/DJ7Kr5XTGtk/](https://www.instagram.com/p/DJ7Kr5XTGtk/). El shortcode está en la URL.

**Reddit**: Subreddit por defecto `r/F1movie`. Puedes cambiar a otro subreddit pasándolo como argumento.

**YouTube**: Usa la [YouTube Data API v3](https://developers.google.com/youtube/v3). Video por defecto: [youtube.com/watch?v=8yh9BPUBbbQ](https://www.youtube.com/watch?v=8yh9BPUBbbQ). Necesitas crear una API key en [Google Cloud Console](https://console.cloud.google.com/) y activar "YouTube Data API v3".

## 📊 Estructura de Datos

Cada reseña contiene la siguiente información:

```json
{
  "source": "IMDB" | "Rotten Tomatoes" | "Instagram" | "Reddit" | "YouTube",
  "title": "Título (solo IMDB/RT)",
  "content": "Contenido de la reseña o comentario",
  "rating": "Calificación (solo IMDB/RT)",
  "author": "Autor o username",
  "date": "Fecha de publicación",
  "helpful_votes": "Votos útiles o likes",
  "post_code": "Shortcode (Instagram)",
  "subreddit": "Subreddit (Reddit)",
  "video_id": "ID del video (YouTube)"
}
```

## ⚠️ Notas Importantes

1. **Rotten Tomatoes**: Algunas páginas de Rotten Tomatoes cargan contenido dinámicamente con JavaScript. Si el scraper no obtiene resultados, puede ser necesario usar Selenium para contenido dinámico.

2. **Rate Limiting**: Los sitios web pueden limitar las solicitudes. El script incluye manejo de errores, pero si experimentas problemas, considera agregar delays entre solicitudes.

3. **Selectores HTML**: Los selectores CSS pueden cambiar si los sitios web actualizan su estructura. Si el scraper deja de funcionar, puede ser necesario actualizar los selectores.

## 🔧 Personalización

### Cambiar el número de reseñas

Edita el parámetro `max_reviews` en los scripts:

```python
reviews = get_imdb_reviews(max_reviews=200)  # Obtener 200 reseñas
```

### Cambiar el ID de la película en IMDB

Si quieres obtener reseñas de otra película, cambia el `movie_id`:

```python
reviews = get_imdb_reviews(movie_id="tt1234567")
```

## 📝 Licencia

Este proyecto es para uso educativo y de investigación. Asegúrate de cumplir con los términos de servicio de IMDB y Rotten Tomatoes al usar este scraper.

## 🐛 Solución de Problemas

**Problema**: No se obtienen reseñas
- Verifica tu conexión a internet
- Los sitios pueden haber cambiado su estructura HTML
- Algunos sitios bloquean scrapers automáticos

**Problema**: Error de importación
- Asegúrate de haber instalado todas las dependencias: `pip install -r requirements.txt`

**Problema**: Rotten Tomatoes no funciona
- Rotten Tomatoes puede requerir JavaScript. Considera usar Selenium:
  ```bash
  pip install selenium
  ```

