"""
Análisis de sentimiento sobre reseñas y comentarios.
Usa VADER, optimizado para texto de redes sociales en inglés.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    HAS_VADER = True
except ImportError:
    HAS_VADER = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"
OUTPUT_INSIGHTS = PROJECT_ROOT / "output" / "insights"

# -1 a 1: negativo a positivo
SENTIMENT_LABELS = {
    "positive": ("compound", 0.05),
    "negative": ("compound", -0.05),
    "neutral": ("compound", None),  # entre -0.05 y 0.05
}


def _get_analyzer():
    """Obtiene el analizador VADER o None si no está instalado."""
    if not HAS_VADER:
        return None
    return SentimentIntensityAnalyzer()


def analyze_sentiment(text: str, analyzer=None) -> Dict[str, float]:
    """
    Analiza el sentimiento de un texto.
    Returns: {'neg': 0-1, 'neu': 0-1, 'pos': 0-1, 'compound': -1 a 1}
    """
    if not text or not isinstance(text, str):
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    if analyzer is None:
        analyzer = _get_analyzer()
    if analyzer is None:
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return analyzer.polarity_scores(text)


def label_sentiment(compound: float) -> str:
    """Etiqueta: positive, neutral o negative según compound."""
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def add_sentiment_to_reviews(reviews: List[Dict], analyzer=None) -> List[Dict]:
    """Añade scores de sentimiento a cada reseña (in-place)."""
    if analyzer is None:
        analyzer = _get_analyzer()
    for r in reviews:
        content = r.get("content") or ""
        scores = analyze_sentiment(content, analyzer)
        r["sentiment"] = {
            "neg": round(scores["neg"], 3),
            "neu": round(scores["neu"], 3),
            "pos": round(scores["pos"], 3),
            "compound": round(scores["compound"], 3),
            "label": label_sentiment(scores["compound"]),
        }
    return reviews


def sentiment_insights(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights de sentimiento: distribución, media por fuente, etc.
    """
    reviews = data.get("reviews", [])
    if not reviews:
        return {"message": "No hay reseñas para analizar"}

    if not HAS_VADER:
        return {
            "error": "Instala vaderSentiment: pip install vaderSentiment",
            "message": "No se pudo ejecutar el análisis de sentimiento.",
        }

    analyzer = _get_analyzer()
    add_sentiment_to_reviews(reviews, analyzer)

    by_label = {"positive": 0, "neutral": 0, "negative": 0}
    compounds = []
    by_source = {}

    for r in reviews:
        sent = r.get("sentiment", {})
        label = sent.get("label", "neutral")
        compound = sent.get("compound", 0.0)

        by_label[label] = by_label.get(label, 0) + 1
        compounds.append(compound)

        src = r.get("source", "Unknown")
        if src not in by_source:
            by_source[src] = {"count": 0, "compound_sum": 0, "positive": 0, "negative": 0, "neutral": 0}
        by_source[src]["count"] += 1
        by_source[src]["compound_sum"] += compound
        by_source[src][label] = by_source[src].get(label, 0) + 1

    # Media compound por fuente
    for src, vals in by_source.items():
        n = vals["count"]
        vals["avg_compound"] = round(vals["compound_sum"] / n, 3) if n else 0
        del vals["compound_sum"]

    avg_compound = sum(compounds) / len(compounds) if compounds else 0

    return {
        "total_reviews": len(reviews),
        "by_label": by_label,
        "avg_compound": round(avg_compound, 3),
        "by_source": by_source,
        "overall_label": label_sentiment(avg_compound),
    }


def run_sentiment_analysis() -> Dict[str, Any]:
    """Ejecuta análisis de sentimiento y guarda resultados."""
    OUTPUT_INSIGHTS.mkdir(parents=True, exist_ok=True)
    path_data = DATA_CLEAN / "reviews_f1_clean.json"
    if not path_data.exists():
        raise FileNotFoundError(f"Ejecuta primero el pipeline de limpieza. No existe {path_data}")

    with open(path_data, "r", encoding="utf-8") as f:
        data = json.load(f)

    insights = sentiment_insights(data)

    if "error" in insights:
        print(f"⚠ {insights['error']}")
        return insights

    # Guardar insights de sentimiento
    path_out = OUTPUT_INSIGHTS / "insights_sentimiento.json"
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    print(f"✓ Insights de sentimiento guardados en {path_out}")

    # Opcional: guardar datos enriquecidos con sentimiento
    path_enriched = OUTPUT_INSIGHTS / "reviews_con_sentimiento.json"
    with open(path_enriched, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Reviews con sentimiento guardados en {path_enriched}")

    return insights


if __name__ == "__main__":
    run_sentiment_analysis()
