"""
Análisis de sentimiento sobre reseñas y comentarios.

¿QUÉ HACE ESTE MÓDULO?

1. Usa VADER (Valence Aware Dictionary and sEntiment Reasoner), un modelo de
   léxico diseñado para texto de redes sociales (emojis, mayúsculas, "!!!", etc.).

2. Por cada comentario obtiene 4 scores:
   - neg: proporción de palabras negativas (0-1)
   - neu: proporción neutras
   - pos: proporción positivas
   - compound: score global de -1 (muy negativo) a +1 (muy positivo)

3. Etiqueta cada comentario: positive (compound >= 0.05), negative (<= -0.05),
   neutral (entre -0.05 y 0.05).

4. Ajuste de léxico para cine: palabras como "insane", "crazy", "fire" que en
   contexto de películas son positivas se añaden al léxico de VADER.

5. NO se quitan stop words del texto antes del análisis (el pipeline conserva
   "not", "don't", "no") porque VADER necesita las negaciones para invertir
   el sentimiento correctamente.

Salida: insights_sentimiento.json (distribución, media por fuente) y
       reviews_con_sentimiento.json (cada reseña con su score).
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

# Palabras que en contexto de cine/hype suelen ser positivas (VADER las marca neutras/negativas)
# Valor típico VADER: 2.x = positivo fuerte, 1.x = positivo suave
MOVIE_HYPE_LEXICON = {
    "insane": 2.2, "crazy": 1.8, "wild": 1.5, "fire": 2.0, "hype": 1.8,
    "hypebeast": 1.0, "goosebumps": 2.0, "chills": 1.5, "seated": 2.0,
    "phenomenal": 2.5, "incredible": 2.3, "unreal": 2.0, "mental": 1.5,
}

SENTIMENT_LABELS = {
    "positive": ("compound", 0.05),
    "negative": ("compound", -0.05),
    "neutral": ("compound", None),
}

_analyzer_instance = None


def _get_analyzer():
    """Obtiene el analizador VADER con lexicon ajustado para cine/redes sociales."""
    global _analyzer_instance
    if not HAS_VADER:
        return None
    if _analyzer_instance is None:
        _analyzer_instance = SentimentIntensityAnalyzer()
        _analyzer_instance.lexicon.update(MOVIE_HYPE_LEXICON)
    return _analyzer_instance


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


def _get_engagement(r: Dict) -> int:
    """Likes o helpful_votes para ponderar por engagement."""
    for key in ("likes", "helpful_votes"):
        v = r.get(key)
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                pass
    return 0


def sentiment_insights(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights de sentimiento: distribución, media por fuente,
    sentimiento ponderado por engagement (likes).
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
    weighted_sum = 0.0
    weight_total = 0.0
    engagement_by_label = {"positive": 0, "neutral": 0, "negative": 0}

    for r in reviews:
        sent = r.get("sentiment", {})
        label = sent.get("label", "neutral")
        compound = sent.get("compound", 0.0)
        wgt = 1 + _get_engagement(r)

        by_label[label] = by_label.get(label, 0) + 1
        compounds.append(compound)
        weighted_sum += compound * wgt
        weight_total += wgt
        engagement_by_label[label] += _get_engagement(r)

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
    avg_compound_weighted = weighted_sum / weight_total if weight_total > 0 else avg_compound
    total_engagement = sum(engagement_by_label.values())
    pct_eng_pos = round(100 * engagement_by_label["positive"] / total_engagement, 1) if total_engagement else 0

    result = {
        "total_reviews": len(reviews),
        "by_label": by_label,
        "avg_compound": round(avg_compound, 3),
        "by_source": by_source,
        "overall_label": label_sentiment(avg_compound),
    }
    if total_engagement > 0:
        result["engagement"] = {
            "total_likes": total_engagement,
            "likes_por_sentimiento": engagement_by_label,
            "avg_compound_ponderado_likes": round(avg_compound_weighted, 3),
            "porcentaje_likes_positivos": pct_eng_pos,
            "interpretacion": "Sentimiento de los comentarios con más alcance (likes)" if pct_eng_pos > 50 else "Los comentarios negativos concentran parte relevante del engagement",
        }
    return result


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
