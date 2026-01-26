# Scraper de Reseñas - Película F1 (2025)

Este proyecto permite obtener y almacenar reseñas de la película **F1 (2025)** desde **IMDB** y **Rotten Tomatoes**.

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

## 📁 Archivos Generados

El script genera los siguientes archivos:

- `reviews_imdb.json` - Reseñas de IMDB
- `reviews_rottentomatoes.json` - Reseñas de Rotten Tomatoes
- `reviews_f1_combined.json` - Todas las reseñas combinadas con metadatos
- `reviews_f1.csv` - Reseñas en formato CSV (si pandas está instalado)

## 📊 Estructura de Datos

Cada reseña contiene la siguiente información:

```json
{
  "source": "IMDB" o "Rotten Tomatoes",
  "title": "Título de la reseña",
  "content": "Contenido completo de la reseña",
  "rating": "Calificación (número o Fresh/Rotten)",
  "author": "Autor de la reseña",
  "date": "Fecha de publicación",
  "helpful_votes": "Número de votos útiles"
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

