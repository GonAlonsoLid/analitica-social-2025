"""
Análisis de sentimiento por fuente (NLP + VADER) y generación de gráficas
para estrategias de marketing: word clouds, distribución de sentimiento,
palabras clave por fuente, engagement.
"""
import json
import re
from pathlib import Path
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
OUTPUT_INSIGHTS = PROJECT_ROOT / "output" / "insights"
FIGURES_DIR = OUTPUT_INSIGHTS / "figures"

from src.analysis.stopwords_social import SOCIAL_STOP_WORDS

_URL_RE = re.compile(r"https?://\S+|www\.\S+|\b\w+\.(?:com|org|net)\b", re.I)
_NUMERIC_RE = re.compile(r"^\d+$")

# YouTube: cada video se analiza por separado en gráficas e insights
YOUTUBE_VIDEO_LABELS = {
    "8yh9BPUBbbQ": "Trailer",
    "Cf18Jx4hINk": "Video 2",
}


def _tokenize(text: str) -> List[str]:
    if not text or not isinstance(text, str):
        return []
    text = _URL_RE.sub(" ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return [w for w in words if w not in SOCIAL_STOP_WORDS and not _NUMERIC_RE.match(w)]


def _load_data() -> Dict[str, Any]:
    """Carga datos: primero clean, si no existe usa raw combined."""
    clean_path = DATA_CLEAN / "reviews_f1_clean.json"
    if clean_path.exists():
        with open(clean_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raw_path = DATA_RAW / "reviews_f1_combined.json"
    if raw_path.exists():
        with open(raw_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("No se encontró data/clean/reviews_f1_clean.json ni data/raw/reviews_f1_combined.json")


def _get_engagement(r: Dict) -> int:
    for key in ("likes", "helpful_votes"):
        v = r.get(key)
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                pass
    return 0


def _source_key(r: Dict) -> str:
    """Clave de agrupación: YouTube se separa por video_id (Trailer / Video 2)."""
    src = r.get("source", "Unknown")
    if src == "YouTube" and r.get("video_id"):
        vid = r.get("video_id", "")
        label = YOUTUBE_VIDEO_LABELS.get(vid, vid)
        return f"YouTube - {label}"
    return src


def run_sentiment_by_source(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análisis de sentimiento por fuente: VADER + métricas por fuente.
    Devuelve dict con by_source, total_reviews, y lista de fuentes con datos.
    """
    from src.analysis.sentiment import (
        _get_analyzer,
        add_sentiment_to_reviews,
        label_sentiment,
    )

    reviews = data.get("reviews", [])
    if not reviews:
        return {"error": "No hay reseñas", "by_source": {}}

    analyzer = _get_analyzer()
    if not analyzer:
        return {"error": "Instala vaderSentiment: pip install vaderSentiment", "by_source": {}}

    add_sentiment_to_reviews(reviews, analyzer)

    by_source: Dict[str, Dict[str, Any]] = {}
    for r in reviews:
        src = _source_key(r)
        if src not in by_source:
            by_source[src] = {
                "count": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "compound_sum": 0.0,
                "engagement_sum": 0,
                "compounds": [],
                "word_freq": Counter(),
                "texts_positive": [],
                "texts_negative": [],
                "video_id": r.get("video_id") if r.get("source") == "YouTube" else None,
            }
        sent = r.get("sentiment", {})
        label = sent.get("label", "neutral")
        compound = sent.get("compound", 0.0)
        content = (r.get("content") or "").strip()
        engagement = _get_engagement(r)

        by_source[src]["count"] += 1
        by_source[src][label] = by_source[src].get(label, 0) + 1
        by_source[src]["compound_sum"] += compound
        by_source[src]["compounds"].append(compound)
        by_source[src]["engagement_sum"] += engagement
        for w in _tokenize(content):
            by_source[src]["word_freq"][w] += 1 + engagement
        if content and len(content) > 20:
            if label == "positive":
                by_source[src]["texts_positive"].append(content[:300])
            elif label == "negative":
                by_source[src]["texts_negative"].append(content[:300])

    for src, vals in by_source.items():
        n = vals["count"]
        vals["avg_compound"] = round(vals["compound_sum"] / n, 3) if n else 0
        vals["dominant_label"] = max(
            ["positive", "neutral", "negative"],
            key=lambda L: vals.get(L, 0),
        )
        # Porcentajes de sentimiento (normalizado: no depende del volumen)
        if n:
            vals["pct_positive"] = round(100 * vals.get("positive", 0) / n, 1)
            vals["pct_neutral"] = round(100 * vals.get("neutral", 0) / n, 1)
            vals["pct_negative"] = round(100 * vals.get("negative", 0) / n, 1)
        else:
            vals["pct_positive"] = vals["pct_neutral"] = vals["pct_negative"] = 0
        # Engagement por reseña (normalizado)
        vals["engagement_per_review"] = round(vals["engagement_sum"] / n, 1) if n else 0
        # Top palabras: frecuencia por 100 reseñas para comparar fuentes con distinto n
        vals["top_words"] = [
            {
                "word": w,
                "count": c,
                "per_100_reviews": round(100 * c / n, 1) if n else 0,
            }
            for w, c in vals["word_freq"].most_common(25)
        ]
        del vals["compound_sum"]
        del vals["word_freq"]
        # Limitar textos para JSON
        vals["texts_positive"] = vals["texts_positive"][:5]
        vals["texts_negative"] = vals["texts_negative"][:5]

    return {
        "total_reviews": len(reviews),
        "sources": list(by_source.keys()),
        "by_source": by_source,
    }


def _ensure_figures_dir():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def plot_sentiment_distribution_by_source(by_source: Dict[str, Dict], output_path: Path) -> None:
    """Gráfica de barras: distribución en % (normalizado por fuente)."""
    import matplotlib.pyplot as plt
    import numpy as np

    sources = list(by_source.keys())
    if not sources:
        return
    pos = [by_source[s].get("pct_positive", 0) for s in sources]
    neu = [by_source[s].get("pct_neutral", 0) for s in sources]
    neg = [by_source[s].get("pct_negative", 0) for s in sources]
    x = np.arange(len(sources))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width, pos, width, label="Positivo", color="#2ecc71")
    ax.bar(x, neu, width, label="Neutral", color="#95a5a6")
    ax.bar(x + width, neg, width, label="Negativo", color="#e74c3c")
    ax.set_ylabel("Porcentaje de reseñas (%)")
    ax.set_title("Distribución de sentimiento por fuente (normalizado %)")
    ax.set_ylim(0, 100)
    ax.set_xticks(x)
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_avg_compound_by_source(by_source: Dict[str, Dict], output_path: Path) -> None:
    """Gráfica de barras: puntuación media compound por fuente (-1 a 1)."""
    import matplotlib.pyplot as plt
    import numpy as np

    sources = list(by_source.keys())
    if not sources:
        return
    avgs = [by_source[s].get("avg_compound", 0) for s in sources]
    colors = ["#2ecc71" if a >= 0.05 else "#e74c3c" if a <= -0.05 else "#95a5a6" for a in avgs]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(sources, avgs, color=colors)
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.axhline(y=0.05, color="green", linestyle="--", alpha=0.5, label="Umbral positivo")
    ax.axhline(y=-0.05, color="red", linestyle="--", alpha=0.5, label="Umbral negativo")
    ax.set_ylabel("Compound medio (-1 a 1)")
    ax.set_title("Sentimiento medio por fuente (VADER)")
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_engagement_by_source(by_source: Dict[str, Dict], output_path: Path) -> None:
    """Engagement normalizado (medio por reseña) y total."""
    import matplotlib.pyplot as plt

    sources = list(by_source.keys())
    if not sources:
        return
    per_review = [by_source[s].get("engagement_per_review", 0) for s in sources]
    totals = [by_source[s].get("engagement_sum", 0) for s in sources]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.bar(sources, per_review, color="#9b59b6")
    ax1.set_ylabel("Likes/votos por reseña")
    ax1.set_title("Engagement medio por reseña (comparación justa)")
    ax1.tick_params(axis="x", rotation=15)
    ax2.bar(sources, totals, color="#3498db")
    ax2.set_ylabel("Total likes/votos")
    ax2.set_title("Engagement total (depende del volumen)")
    ax2.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_top_words_by_source(by_source: Dict[str, Dict], output_path: Path, top_n: int = 15) -> None:
    """Gráfica horizontal: top palabras por fuente, normalizado (por 100 reseñas)."""
    import matplotlib.pyplot as plt

    sources = list(by_source.keys())
    if not sources:
        return
    n_sources = len(sources)
    fig, axes = plt.subplots(n_sources, 1, figsize=(10, 4 * n_sources))
    if n_sources == 1:
        axes = [axes]
    for ax, src in zip(axes, sources):
        top = by_source[src].get("top_words", [])[:top_n]
        if not top:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
            ax.set_title(src)
            continue
        words = [t["word"] for t in reversed(top)]
        # Usar frecuencia por 100 reseñas para comparar fuentes con distinto n
        rates = [t.get("per_100_reviews", t["count"]) for t in reversed(top)]
        ax.barh(words, rates, color="#3498db", alpha=0.8)
        ax.set_title(f"Top {top_n} palabras – {src} (n={by_source[src].get('count', 0)})")
        ax.set_xlabel("Frecuencia por 100 reseñas (normalizado)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_wordcloud_per_source(by_source: Dict[str, Dict], output_dir: Path) -> None:
    """Genera una word cloud por fuente."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        return
    import matplotlib.pyplot as plt

    for src in by_source:
        top_words = by_source[src].get("top_words", [])
        if not top_words:
            continue
        freq = {t["word"]: t["count"] for t in top_words}
        wc = WordCloud(
            width=800,
            height=400,
            background_color="white",
            max_words=80,
            colormap="viridis",
        ).generate_from_frequencies(freq)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(f"Palabras más usadas – {src}")
        fig.tight_layout()
        safe_name = re.sub(r"[^\w\-]", "_", src)
        fig.savefig(output_dir / f"wordcloud_{safe_name}.png", dpi=150, bbox_inches="tight")
        plt.close()


def plot_wordcloud_by_sentiment(full_data: Dict[str, Any], output_dir: Path) -> None:
    """Word clouds globales: palabras en comentarios positivos vs negativos (todas las fuentes)."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        return
    import matplotlib.pyplot as plt

    reviews = full_data.get("reviews", [])
    pos_freq: Counter = Counter()
    neg_freq: Counter = Counter()
    for r in reviews:
        content = (r.get("content") or "").strip()
        if not content:
            continue
        label = (r.get("sentiment") or {}).get("label", "neutral")
        wgt = 1 + _get_engagement(r)
        for w in _tokenize(content):
            if label == "positive":
                pos_freq[w] += wgt
            elif label == "negative":
                neg_freq[w] += wgt

    for name, freq, title, fname in [
        ("positive", pos_freq, "Palabras en comentarios POSITIVOS", "wordcloud_global_positive.png"),
        ("negative", neg_freq, "Palabras en comentarios NEGATIVOS", "wordcloud_global_negative.png"),
    ]:
        if not freq:
            continue
        wc = WordCloud(
            width=800,
            height=400,
            background_color="white",
            max_words=60,
            colormap="Greens" if name == "positive" else "Reds",
        ).generate_from_frequencies(dict(freq.most_common(80)))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(output_dir / fname, dpi=150, bbox_inches="tight")
        plt.close()


def plot_compound_boxplot_by_source(by_source: Dict[str, Dict], full_data: Dict[str, Any], output_path: Path) -> None:
    """Boxplot: distribución del compound por fuente (usa sentimiento ya calculado)."""
    import matplotlib.pyplot as plt

    reviews = full_data.get("reviews", [])
    if not reviews:
        return
    by_src_lists: Dict[str, List[float]] = {}
    for r in reviews:
        src = _source_key(r)
        c = r.get("sentiment", {}).get("compound", 0)
        if src not in by_src_lists:
            by_src_lists[src] = []
        by_src_lists[src].append(c)
    if not by_src_lists:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    data = [by_src_lists[s] for s in by_src_lists]
    labels = list(by_src_lists.keys())
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#ecf0f1")
    ax.axhline(y=0.05, color="green", linestyle="--", alpha=0.5)
    ax.axhline(y=-0.05, color="red", linestyle="--", alpha=0.5)
    ax.set_ylabel("Compound (VADER)")
    ax.set_title("Distribución de sentimiento por fuente (boxplot)")
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def write_marketing_insights_report(insights: Dict[str, Any], output_path: Path) -> None:
    """Escribe un reporte en Markdown con insights para marketing."""
    by_source = insights.get("by_source", {})
    if not by_source:
        return
    lines = [
        "# Análisis de sentimiento por fuente – F1 (2025)",
        "",
        "## Resumen",
        f"- **Total de reseñas analizadas:** {insights.get('total_reviews', 0)}",
        f"- **Fuentes:** {', '.join(insights.get('sources', []))}",
        "- Las gráficas y comparaciones usan **métricas normalizadas** (%, por reseña, por 100 reseñas) para que el volumen de datos no penalice a fuentes con menos comentarios.",
        "",
        "## Métricas por fuente",
        "",
    ]
    for src, vals in by_source.items():
        lines.extend([
            f"### {src}",
            f"- Número de reseñas: **{vals.get('count', 0)}**",
            f"- Sentimiento medio (compound): **{vals.get('avg_compound', 0)}** (comparable entre fuentes)",
            f"- Etiqueta dominante: **{vals.get('dominant_label', 'neutral')}**",
            f"- Distribución **normalizada (%):** Positivo {vals.get('pct_positive', 0)}%, Neutral {vals.get('pct_neutral', 0)}%, Negativo {vals.get('pct_negative', 0)}%",
            f"- Engagement total: **{vals.get('engagement_sum', 0)}** | **Por reseña (normalizado):** {vals.get('engagement_per_review', 0)}",
            "",
            "**Palabras más frecuentes (por 100 reseñas, comparable entre fuentes):**",
            "",
        ])
        for w in (vals.get("top_words") or [])[:10]:
            rate = w.get("per_100_reviews", w["count"])
            lines.append(f"- {w['word']} ({rate} por 100 reseñas)")
        lines.append("")
    lines.extend([
        "## Gráficas generadas",
        "",
        "- `figures/sentiment_distribution_by_source.png` – Distribución en % (normalizado)",
        "- `figures/avg_compound_by_source.png` – Sentimiento medio por fuente",
        "- `figures/engagement_by_source.png` – Engagement medio y total (comparación justa)",
        "- `figures/top_words_by_source.png` – Palabras clave (frecuencia por 100 reseñas)",
        "- `figures/compound_boxplot_by_source.png` – Boxplot de sentimiento por fuente",
        "- `figures/wordcloud_*.png` – Nube de palabras por fuente",
        "- `figures/wordcloud_global_positive.png` – Palabras en comentarios positivos (todas las fuentes)",
        "- `figures/wordcloud_global_negative.png` – Palabras en comentarios negativos (todas las fuentes)",
        "",
        "## Recomendaciones para estrategia de marketing",
        "",
    ])
    for src, vals in by_source.items():
        dom = vals.get("dominant_label", "neutral")
        avg = vals.get("avg_compound", 0)
        if dom == "positive" or avg >= 0.05:
            rec = f"**{src}**: El sentimiento es mayormente positivo. Refuerza mensajes que destaquen los aspectos que la audiencia valora (revisar palabras clave) y usa testimonios o citas positivas en campañas."
        elif dom == "negative" or avg <= -0.05:
            rec = f"**{src}**: Hay peso negativo. Prioriza mensajes que aborden objeciones (revisar temas en comentarios negativos) y evita repetir los términos que aparecen en contexto negativo."
        else:
            rec = f"**{src}**: Sentimiento neutro. Oportunidad para educar e informar con contenido que diferencie la película; usa las palabras más usadas en copy para conectar."
        lines.append(f"- {rec}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_full_report() -> Dict[str, Any]:
    """Carga datos, ejecuta análisis por fuente, genera gráficas y reporte."""
    _ensure_figures_dir()
    data = _load_data()
    insights = run_sentiment_by_source(data)
    if "error" in insights:
        print(f"[AVISO] {insights['error']}")
        return insights

    by_source = insights.get("by_source", {})
    if not by_source:
        print("[AVISO] No hay datos por fuente.")
        return insights

    # Guardar JSON de insights por fuente
    out_json = OUTPUT_INSIGHTS / "sentiment_by_source.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    print(f"[OK] Insights por fuente guardados en {out_json}")

    # Gráficas
    plot_sentiment_distribution_by_source(by_source, FIGURES_DIR / "sentiment_distribution_by_source.png")
    plot_avg_compound_by_source(by_source, FIGURES_DIR / "avg_compound_by_source.png")
    plot_engagement_by_source(by_source, FIGURES_DIR / "engagement_by_source.png")
    plot_top_words_by_source(by_source, FIGURES_DIR / "top_words_by_source.png")
    plot_compound_boxplot_by_source(by_source, data, FIGURES_DIR / "compound_boxplot_by_source.png")
    plot_wordcloud_per_source(by_source, FIGURES_DIR)
    plot_wordcloud_by_sentiment(data, FIGURES_DIR)
    print(f"[OK] Graficas guardadas en {FIGURES_DIR}")

    # Reporte marketing
    report_path = OUTPUT_INSIGHTS / "reporte_sentimiento_por_fuente.md"
    write_marketing_insights_report(insights, report_path)
    print(f"[OK] Reporte para marketing en {report_path}")

    return insights


if __name__ == "__main__":
    run_full_report()
