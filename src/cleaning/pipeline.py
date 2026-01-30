"""
Pipeline de limpieza de datos.
Carga datos crudos, aplica transformaciones y guarda datos limpios.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set

# Rutas relativas al proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"

# Stop words en español e inglés (audiencia internacional F1)
STOP_WORDS: Set[str] = {
    # Español
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "pero", "si", "no", "que", "de", "a", "en",
    "es", "por", "para", "con", "del", "al", "lo", "como",
    "más", "muy", "sin", "sobre", "entre", "hasta", "desde",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "su", "sus", "tu", "tus", "mi", "mis", "se", "le", "les",
    "me", "te", "nos", "os", "ya", "qué", "cuál", "cómo",
    "cuando", "donde", "quien", "porque", "aunque", "mientras",
    "todo", "todos", "toda", "todas", "nada", "algo", "alguien",
    "otro", "otra", "otros", "otras", "poco", "mucho", "poco",
    # Inglés
    "the", "a", "an", "and", "or", "but", "if", "of", "in",
    "to", "for", "with", "on", "at", "by", "from", "as",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must",
    "this", "that", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "our", "their",
    "what", "which", "who", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most",
}


def load_raw_data() -> Dict[str, Any]:
    """
    Carga todos los JSON crudos de data/raw/.
    Espera: reviews_f1_combined.json o los archivos individuales.
    """
    combined_path = DATA_RAW / "reviews_f1_combined.json"
    if combined_path.exists():
        with open(combined_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Cargar individuales y combinar
    all_reviews = []
    sources = {}
    for name in [
        "reviews_imdb.json",
        "reviews_rottentomatoes.json",
        "reviews_instagram.json",
        "reviews_reddit.json",
        "reviews_youtube.json",
    ]:
        path = DATA_RAW / name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reviews = data.get("reviews", data) if isinstance(data, dict) else data
            reviews = reviews if isinstance(reviews, list) else []
            src = "YouTube" if "youtube" in name else "Reddit" if "reddit" in name else "Instagram" if "instagram" in name else "Rotten Tomatoes" if "rottentomatoes" in name else "IMDB"
            sources[src] = len(reviews)
            all_reviews.extend(reviews)

    return {
        "movie": "F1 (2025)",
        "total_reviews": len(all_reviews),
        "sources": sources,
        "reviews": all_reviews,
    }


def clean_text(text: str, remove_stopwords: bool = True) -> str:
    """Limpia texto: espacios extra, caracteres raros y stop words."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if remove_stopwords:
        words = re.findall(r"\b[\w']+\b", text.lower())
        words = [w for w in words if w not in STOP_WORDS]
        text = " ".join(words).strip()
    return text


def clean_review(review: Dict, remove_stopwords: bool = True) -> Dict:
    """Limpia una reseña individual. Por defecto elimina stop words del content."""
    cleaned = dict(review)
    if "content" in cleaned and cleaned["content"]:
        cleaned["content"] = clean_text(cleaned["content"], remove_stopwords=remove_stopwords)
    if "title" in cleaned and cleaned.get("title"):
        cleaned["title"] = clean_text(str(cleaned["title"]), remove_stopwords=remove_stopwords)
    # Author no le quitamos stop words para mantener nombres legibles
    if "author" in cleaned and cleaned.get("author"):
        cleaned["author"] = clean_text(str(cleaned["author"]), remove_stopwords=False)
    return cleaned


def filter_valid_reviews(reviews: List[Dict], min_content_length: int = 3) -> List[Dict]:
    """Filtra reseñas con contenido muy corto o inválido."""
    return [
        r for r in reviews
        if r.get("content") and len(str(r["content"]).strip()) >= min_content_length
    ]


def run_cleaning_pipeline(
    min_content_length: int = 3,
    remove_stopwords: bool = True,
    custom_steps: List[callable] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline de limpieza completo.
    
    Args:
        min_content_length: Longitud mínima del contenido.
        remove_stopwords: Si True, elimina stop words (español e inglés).
        custom_steps: Lista opcional de funciones (reviews) -> reviews para pasos extra.
    
    Returns:
        Diccionario con reviews limpios y metadatos.
    """
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)

    data = load_raw_data()
    reviews = data.get("reviews", [])

    # Limpieza básica + stop words
    reviews = [clean_review(r, remove_stopwords=remove_stopwords) for r in reviews]
    reviews = filter_valid_reviews(reviews, min_content_length=min_content_length)

    # Pasos personalizados (ej: eliminar duplicados, normalizar fechas)
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
