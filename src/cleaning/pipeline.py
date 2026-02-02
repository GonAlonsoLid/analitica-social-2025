"""
Pipeline de limpieza de datos.
Carga datos crudos, aplica transformaciones y guarda datos limpios.

IMPORTANTE: El contenido NO se le quitan stop words para preservar negaciones
(not, don't, no) que el análisis de sentimiento (VADER) necesita.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set

# Rutas relativas al proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"

# Stop words (solo para análisis temático / word frequency, NUNCA para sentimiento)
STOP_WORDS: Set[str] = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "pero", "si", "no", "que", "de", "a", "en",
    "the", "a", "an", "and", "or", "but", "if", "of", "in",
    "to", "for", "with", "on", "at", "by", "from", "as",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will",
    "this", "that", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "me", "him", "her",
    "what", "which", "who", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most",
}

# Ruido que no aporta: URLs, fragmentos, spam
URL_PATTERN = re.compile(
    r"https?://[^\s]+|www\.[^\s]+|\[([^\]]+)\]\([^\)]+\)",
    re.IGNORECASE
)
# Timestamps tipo 0:27, 2:23 (comentarios de YouTube)
TIMESTAMP_PATTERN = re.compile(r"\b\d{1,2}:\d{2}\b")
# Palabras/tokens que indican spam o off-topic
NOISE_WORDS = {"lol", "lols", "lmao", "haha", "xd", "omg", "wtf", "idk", "imo", "tbh"}


def load_raw_data() -> Dict[str, Any]:
    """
    Carga todos los JSON crudos de data/raw/.
    Prioridad: archivos individuales por fuente (reviews_youtube.json, etc.).
    Si no hay individuales, usa reviews_f1_combined.json como fallback.
    """
    all_reviews = []
    sources = {}
    individual_files = [
        ("reviews_imdb.json", "IMDB"),
        ("reviews_rottentomatoes.json", "Rotten Tomatoes"),
        ("reviews_instagram.json", "Instagram"),
        ("reviews_reddit.json", "Reddit"),
        ("reviews_youtube.json", "YouTube"),
    ]

    for filename, src_name in individual_files:
        path = DATA_RAW / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reviews = data.get("reviews", data) if isinstance(data, dict) else data
            reviews = reviews if isinstance(reviews, list) else []
            if reviews:
                sources[src_name] = len(reviews)
                all_reviews.extend(reviews)

    # Fallback: si no hay individuales, usar combined
    if not all_reviews:
        combined_path = DATA_RAW / "reviews_f1_combined.json"
        if combined_path.exists():
            with open(combined_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_reviews = data.get("reviews", [])
            sources = data.get("sources", {})

    return {
        "movie": "F1 (2025)",
        "total_reviews": len(all_reviews),
        "sources": sources,
        "reviews": all_reviews,
    }


def _light_clean_for_sentiment(text: str) -> str:
    """
    Limpieza ligera para ANÁLISIS DE SENTIMIENTO.
    Elimina URLs, links markdown, timestamps. NO elimina stop words
    (preserva not, don't, no para que VADER funcione).
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    # Quitar URLs y [texto](url) - dejar solo el texto del link si aplica
    def _replace_url(m):
        if m.lastindex and m.group(1):
            return m.group(1).strip()
        return " "
    text = URL_PATTERN.sub(_replace_url, text)
    # Quitar timestamps tipo 0:27, 2:23
    text = TIMESTAMP_PATTERN.sub(" ", text)
    # Normalizar espacios y saltos de línea
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = text.strip()
    return text


def clean_text(text: str, remove_stopwords: bool = False) -> str:
    """
    Limpia texto. Por defecto NO quita stop words (para sentimiento).
    Si remove_stopwords=True, devuelve texto para análisis temático.
    """
    if not text or not isinstance(text, str):
        return ""
    text = _light_clean_for_sentiment(text)
    if remove_stopwords:
        words = re.findall(r"\b[\w']+\b", text.lower())
        words = [w for w in words if w not in STOP_WORDS and len(w) >= 2]
        text = " ".join(words).strip()
    return text


def clean_review(review: Dict, remove_stopwords: bool = False) -> Dict:
    """
    Limpia una reseña. Content se preserva para sentimiento (sin quitar stop words).
    """
    cleaned = dict(review)
    if "content" in cleaned and cleaned["content"]:
        cleaned["content"] = _light_clean_for_sentiment(str(cleaned["content"]))
    if "title" in cleaned and cleaned.get("title"):
        cleaned["title"] = _light_clean_for_sentiment(str(cleaned["title"]))
    if "author" in cleaned and cleaned.get("author"):
        cleaned["author"] = str(cleaned["author"]).strip()
    return cleaned


def filter_valid_reviews(
    reviews: List[Dict],
    min_content_length: int = 15,
    min_words: int = 3,
) -> List[Dict]:
    """Filtra reseñas con contenido muy corto, inválido o spam."""
    def valid(r):
        c = r.get("content") or ""
        if not c or len(str(c).strip()) < min_content_length:
            return False
        words = re.findall(r"\b[\w']+\b", str(c).lower())
        words = [w for w in words if len(w) >= 2]
        if len(words) < min_words:
            return False
        if len(words) <= 3 and all(w in NOISE_WORDS for w in words):
            return False
        return True
    return [r for r in reviews if valid(r)]


def deduplicate_reviews(reviews: List[Dict]) -> List[Dict]:
    """Elimina reseñas duplicadas por contenido normalizado."""
    seen = set()
    out = []
    for r in reviews:
        c = (r.get("content") or "").strip().lower()
        if len(c) < 25:
            out.append(r)
            continue
        h = hash(c[:500])
        if h in seen:
            continue
        seen.add(h)
        out.append(r)
    return out


def run_cleaning_pipeline(
    min_content_length: int = 15,
    min_words: int = 3,
    remove_stopwords: bool = False,
    deduplicate: bool = True,
    custom_steps: List[callable] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline de limpieza completo.
    
    Args:
        min_content_length: Longitud mínima del contenido (chars).
        min_words: Mínimo de palabras significativas.
        remove_stopwords: Si True, elimina stop words (NO recomendado para sentimiento).
        deduplicate: Si True, elimina reseñas duplicadas.
        custom_steps: Lista opcional de funciones (reviews) -> reviews para pasos extra.
    
    Returns:
        Diccionario con reviews limpios y metadatos.
    """
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)

    data = load_raw_data()
    reviews = data.get("reviews", [])

    # Limpieza: URLs, timestamps, espacios. NO stop words (sentimiento los necesita)
    reviews = [clean_review(r, remove_stopwords=remove_stopwords) for r in reviews]
    reviews = filter_valid_reviews(
        reviews,
        min_content_length=min_content_length,
        min_words=min_words,
    )
    if deduplicate:
        reviews = deduplicate_reviews(reviews)

    # Pasos personalizados
    if custom_steps:
        for step in custom_steps:
            reviews = step(reviews)

    output = {
        "movie": data.get("movie", "F1 (2025)"),
        "total_reviews": len(reviews),
        "sources": {
            src: len([r for r in reviews if r.get("source") == src])
            for src in ["IMDB", "Rotten Tomatoes", "Instagram", "Reddit", "YouTube"]
        },
        "reviews": reviews,
    }

    save_clean_data(output)
    print(f"✓ Limpieza completada: {len(reviews)} reseñas válidas")
    return output


def save_clean_data(data: Dict[str, Any], filename: str = "reviews_f1_clean.json") -> None:
    """Guarda los datos limpios en data/clean/."""
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    path = DATA_CLEAN / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Datos limpios guardados en {path}")


if __name__ == "__main__":
    run_cleaning_pipeline()
