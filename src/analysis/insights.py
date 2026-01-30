"""
Extracción de insights a partir de los datos limpios.
Puedes extender con: análisis de sentimiento, temas recurrentes, etc.
"""
import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"
OUTPUT_INSIGHTS = PROJECT_ROOT / "output" / "insights"


def load_clean_data() -> Dict[str, Any]:
    """Carga los datos limpios."""
    path = DATA_CLEAN / "reviews_f1_clean.json"
    if not path.exists():
        raise FileNotFoundError(f"Ejecuta primero el pipeline de limpieza. No existe {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def basic_insights(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights básicos: distribución por fuente, longitud media, etc.
    """
    reviews = data.get("reviews", [])
    if not reviews:
        return {"message": "No hay reseñas para analizar"}

    by_source = {}
    for r in reviews:
        src = r.get("source", "Unknown")
        by_source[src] = by_source.get(src, 0) + 1

    lengths = [len(str(r.get("content", ""))) for r in reviews if r.get("content")]
    avg_length = sum(lengths) / len(lengths) if lengths else 0

    return {
        "total_reviews": len(reviews),
        "by_source": by_source,
        "avg_content_length": round(avg_length, 1),
        "min_content_length": min(lengths) if lengths else 0,
        "max_content_length": max(lengths) if lengths else 0,
    }


def run_insights_analysis() -> Dict[str, Any]:
    """Ejecuta el análisis y guarda resultados en output/insights/."""
    OUTPUT_INSIGHTS.mkdir(parents=True, exist_ok=True)
    data = load_clean_data()
    insights = basic_insights(data)
    path = OUTPUT_INSIGHTS / "insights_basicos.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    print(f"✓ Insights guardados en {path}")
    return insights


if __name__ == "__main__":
    run_insights_analysis()
