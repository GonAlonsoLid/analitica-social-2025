"""
Análisis temático en profundidad: por qué del sentimiento, repeticiones y temas.
Orientado a extraer insights para estrategia de marketing.
"""
import json
import re
from pathlib import Path
from collections import Counter
from typing import Dict, Any, List, Tuple

from src.cleaning.pipeline import load_raw_data
from src.analysis.sentiment import analyze_sentiment, label_sentiment, _get_analyzer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_INSIGHTS = PROJECT_ROOT / "output" / "insights"

from src.analysis.stopwords_social import SOCIAL_STOP_WORDS

# Misma lista que análisis por fuente (word clouds, top words)
THEMATIC_STOP = SOCIAL_STOP_WORDS

# Bigramas que son referencias a películas/series (no indican sentimiento)
NEUTRAL_BIGRAMS = {("top", "gun"), ("brad", "pitt"), ("hans", "zimmer")}

MIN_WORD_LEN = 3
TOP_N_WORDS = 25
TOP_N_BIGRAMS = 20
TOP_N_QUOTES = 5

_URL_RE = re.compile(r"https?://\S+|www\.\S+|\b\w+\.(?:com|org|net)\b", re.I)
_NUMERIC_RE = re.compile(r"^\d+$")


def _preprocess_for_tokenize(text: str) -> str:
    """Quita URLs y fragmentos antes de tokenizar."""
    if not text or not isinstance(text, str):
        return ""
    text = _URL_RE.sub(" ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text


def _tokenize(text: str) -> List[str]:
    """Extrae palabras relevantes (min 3 chars), filtra ruido y URLs."""
    if not text or not isinstance(text, str):
        return []
    text = _preprocess_for_tokenize(text)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return [
        w for w in words
        if w not in THEMATIC_STOP
        and not _NUMERIC_RE.match(w)
        and not w.replace("'", "").isdigit()
    ]


def _bigrams(text: str) -> List[Tuple[str, str]]:
    """Extrae bigramas del texto (excluye ruido conocido)."""
    words = _tokenize(text)
    bigrams = [tuple(words[i:i + 2]) for i in range(len(words) - 1) if len(words) >= 2]
    return [bg for bg in bigrams if bg not in NEUTRAL_BIGRAMS or bg in {("brad", "pitt"), ("hans", "zimmer")}]


def _repr_bigram(bg: Tuple[str, str]) -> str:
    return " ".join(bg)


def _get_engagement(r: Dict) -> int:
    """Obtiene likes/votos de engagement (YouTube: likes, Reddit: helpful_votes)."""
    likes = r.get("likes")
    if likes is not None:
        try:
            return int(likes)
        except (ValueError, TypeError):
            pass
    hv = r.get("helpful_votes")
    if hv is not None:
        try:
            return int(hv)
        except (ValueError, TypeError):
            pass
    return 0


def run_thematic_analysis() -> Dict[str, Any]:
    """
    Análisis en profundidad: temas por categoría de sentimiento,
    repeticiones, citas representativas y recomendaciones para marketing.
    """
    analyzer = _get_analyzer()
    if not analyzer:
        return {"error": "vaderSentiment no instalado"}

    data = load_raw_data()
    reviews = data.get("reviews", [])
    if not reviews:
        return {"error": "No hay reseñas"}

    # Agrupar por sentimiento usando contenido raw (frases completas)
    by_label: Dict[str, List[Dict]] = {"positive": [], "neutral": [], "negative": []}
    for r in reviews:
        content = (r.get("content") or "").strip()
        if not content:
            continue
        scores = analyze_sentiment(content, analyzer)
        label = label_sentiment(scores["compound"])
        r["sentiment"] = {**scores, "label": label}
        by_label[label].append(r)

    # Frecuencias por categoría (raw y ponderada por engagement)
    word_freq: Dict[str, Counter] = {k: Counter() for k in by_label}
    bigram_freq: Dict[str, Counter] = {k: Counter() for k in by_label}
    word_freq_weighted: Dict[str, Counter] = {k: Counter() for k in by_label}
    bigram_freq_weighted: Dict[str, Counter] = {k: Counter() for k in by_label}

    for label, items in by_label.items():
        for r in items:
            txt = (r.get("content") or "")
            wgt = 1 + _get_engagement(r)
            for w in _tokenize(txt):
                word_freq[label][w] += 1
                word_freq_weighted[label][w] += wgt
            for bg in _bigrams(txt):
                bigram_freq[label][bg] += 1
                bigram_freq_weighted[label][bg] += wgt

    def top_items(c: Counter, n: int, format_fn=None):
        format_fn = format_fn or (lambda x: x)
        return [{"term": format_fn(k), "count": v} for k, v in c.most_common(n)]

    # Términos distintivos: más frecuentes en positiva vs negativa
    pos_words = set(w for w, _ in word_freq["positive"].most_common(50))
    neg_words = set(w for w, _ in word_freq["negative"].most_common(50))
    distinctive_positive = pos_words - neg_words
    distinctive_negative = neg_words - pos_words

    # Citas representativas (ordenadas por engagement/likes)
    def pick_quotes(items: List[Dict], n: int) -> List[Dict]:
        sorted_items = sorted(items, key=lambda r: (_get_engagement(r), len(str(r.get("content", "")))), reverse=True)
        return [
            {"content": (r.get("content") or "")[:200], "source": r.get("source"), "likes": _get_engagement(r)}
            for r in sorted_items[:n]
        ]

    # Engagement: total likes por sentimiento
    engagement_by_label = {k: sum(_get_engagement(r) for r in items) for k, items in by_label.items()}
    total_engagement = sum(engagement_by_label.values())

    # Interpretación para marketing
    pos_top = [w for w, _ in word_freq["positive"].most_common(TOP_N_WORDS)]
    neg_top = [w for w, _ in word_freq["negative"].most_common(TOP_N_WORDS)]
    neu_top = [w for w, _ in word_freq["neutral"].most_common(TOP_N_WORDS)]

    def top_weighted(c: Counter, n: int, format_fn=None):
        format_fn = format_fn or (lambda x: x)
        return [{"term": format_fn(k), "count": int(v)} for k, v in c.most_common(n)]

    result = {
        "resumen": {
            "total_analizado": len(reviews),
            "positive": len(by_label["positive"]),
            "neutral": len(by_label["neutral"]),
            "negative": len(by_label["negative"]),
            "porcentaje_positivo": round(100 * len(by_label["positive"]) / len(reviews), 1) if reviews else 0,
            "total_likes": total_engagement,
            "likes_positivo": engagement_by_label["positive"],
            "likes_negativo": engagement_by_label["negative"],
            "likes_neutral": engagement_by_label["neutral"],
            "porcentaje_engagement_positivo": round(100 * engagement_by_label["positive"] / total_engagement, 1) if total_engagement else 0,
        },
        "por_que_positivo": {
            "palabras_mas_frecuentes": top_items(word_freq["positive"], TOP_N_WORDS),
            "palabras_con_mas_impacto": top_weighted(word_freq_weighted["positive"], 15),
            "bigramas_recurrentes": top_items(bigram_freq["positive"], TOP_N_BIGRAMS, _repr_bigram),
            "terminos_distintivos_vs_negativo": sorted(distinctive_positive, key=lambda w: word_freq["positive"][w], reverse=True)[:15],
            "citas_representativas": pick_quotes(by_label["positive"], TOP_N_QUOTES),
            "insight_marketing": _infer_positive_themes(pos_top, [str(b) for b, _ in bigram_freq["positive"].most_common(15)]),
        },
        "por_que_negativo": {
            "palabras_mas_frecuentes": top_items(word_freq["negative"], TOP_N_WORDS),
            "palabras_con_mas_impacto": top_weighted(word_freq_weighted["negative"], 15),
            "bigramas_recurrentes": top_items(bigram_freq["negative"], TOP_N_BIGRAMS, _repr_bigram),
            "terminos_distintivos_vs_positivo": sorted(distinctive_negative, key=lambda w: word_freq["negative"][w], reverse=True)[:15],
            "citas_representativas": pick_quotes(by_label["negative"], TOP_N_QUOTES),
            "insight_marketing": _infer_negative_themes(neg_top, [str(b) for b, _ in bigram_freq["negative"].most_common(15)]),
        },
        "por_que_neutral": {
            "palabras_mas_frecuentes": top_items(word_freq["neutral"], TOP_N_WORDS),
            "bigramas_recurrentes": top_items(bigram_freq["neutral"], TOP_N_BIGRAMS, _repr_bigram),
            "citas_representativas": pick_quotes(by_label["neutral"], TOP_N_QUOTES),
            "insight_marketing": _infer_neutral_themes(neu_top),
        },
        "por_fuente": _by_source_themes(by_label, word_freq, bigram_freq),
    }

    result["recomendaciones_marketing"] = _marketing_recommendations(
        by_label,
        {
            "por_que_positivo": result["por_que_positivo"],
            "por_que_negativo": result["por_que_negativo"],
            "por_que_neutral": result["por_que_neutral"],
            "resumen": result["resumen"],
        },
    )

    OUTPUT_INSIGHTS.mkdir(parents=True, exist_ok=True)
    path_out = OUTPUT_INSIGHTS / "analisis_tematico_marketing.json"
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Generar también un reporte legible en Markdown
    _write_marketing_report(result)

    print(f"✓ Análisis temático guardado en {path_out}")
    print(f"✓ Reporte de marketing en {OUTPUT_INSIGHTS / 'reporte_marketing.md'}")
    return result


def _infer_positive_themes(words: List[str], bigrams: List[str]) -> List[str]:
    """Infiere temas/razones detrás del sentimiento positivo."""
    themes = []
    w = set(w.lower() for w in words)
    bg = " ".join(bigrams).lower()
    if any(x in w or x in bg for x in ["love", "loved", "great", "amazing", "best", "perfect", "phenomenal", "incredible"]):
        themes.append("Valoración emocional muy alta: amor, grandeza, perfección")
    if any(x in w or x in bg for x in ["brad", "pitt", "actor", "performance"]):
        themes.append("Brad Pitt y actuaciones como pilares del éxito")
    if any(x in w or x in bg for x in ["trailer", "edit", "cut", "raise"]):
        themes.append("El trailer y la edición generan hype extremo")
    if any(x in w or x in bg for x in ["hans", "zimmer", "score", "music", "sound"]):
        themes.append("La banda sonora de Hans Zimmer como gancho emocional")
    if any(x in w or x in bg for x in ["top", "gun", "maverick", "director"]):
        themes.append("Asociación con Top Gun: Maverick aumenta expectativas")
    if any(x in w or x in bg for x in ["race", "racing", "f1", "realistic"]):
        themes.append("Realismo y acción de carreras como valor diferencial")
    if any(x in w or x in bg for x in ["theaters", "cinema", "see", "watch"]):
        themes.append("Intención de ver en cines (no streaming)")
    if not themes:
        themes.append("Sentimiento positivo basado en términos genéricos de aprobación")
    return themes


def _infer_negative_themes(words: List[str], bigrams: List[str]) -> List[str]:
    """Infiere temas detrás del sentimiento negativo."""
    themes = []
    w = set(w.lower() for w in words)
    bg = " ".join(bigrams).lower()
    if any(x in w or x in bg for x in ["bad", "worst", "terrible", "boring", "waste"]):
        themes.append("Valoración negativa explícita")
    if any(x in w or x in bg for x in ["quality", "low", "cheap"]):
        themes.append("Percepción de baja calidad")
    if any(x in w or x in bg for x in ["expect", "disappoint", "overhype"]):
        themes.append("Expectativas no cumplidas")
    if any(x in w or x in bg for x in ["story", "plot", "script"]):
        themes.append("Críticas al guion o historia")
    if not themes:
        themes.append("Comentarios negativos breves o de bajo engagement")
    return themes


def _infer_neutral_themes(words: List[str]) -> List[str]:
    """Infiere temas en comentarios neutros."""
    themes = []
    w = set(w.lower() for w in words)
    if any(x in w for x in ["scene", "moment", "reference", "joke"]):
        themes.append("Discusión de escenas o referencias específicas")
    if any(x in w for x in ["character", "sonny", "kate"]):
        themes.append("Debate sobre personajes o relaciones")
    themes.append("Comentarios informativos, memes o referencias sin juicio emocional")
    return themes


def _by_source_themes(
    by_label: Dict[str, List[Dict]],
    word_freq: Dict[str, Counter],
    bigram_freq: Dict[str, Counter],
) -> Dict[str, Any]:
    """Temas por fuente (YouTube, Reddit, etc.)."""
    by_source: Dict[str, Dict[str, List]] = {}
    for label, items in by_label.items():
        for r in items:
            src = r.get("source", "Unknown")
            if src not in by_source:
                by_source[src] = {"positive": [], "neutral": [], "negative": []}
            by_source[src][label].append(r)

    result = {}
    for src, sub in by_source.items():
        all_items = sub["positive"] + sub["neutral"] + sub["negative"]
        if not all_items:
            continue
        c = Counter()
        for r in all_items:
            for w in _tokenize(r.get("content", "")):
                c[w] += 1
        result[src] = {
            "count": len(all_items),
            "positive": len(sub["positive"]),
            "neutral": len(sub["neutral"]),
            "negative": len(sub["negative"]),
            "top_palabras": [{"term": k, "count": v} for k, v in c.most_common(15)],
        }
    return result


def _marketing_recommendations(by_label: Dict[str, List[Dict]], result: Dict) -> List[Dict]:
    """Genera recomendaciones concretas para estrategia de marketing."""
    recs = []
    pos = result.get("por_que_positivo", {})
    neg = result.get("por_que_negativo", {})
    neu = result.get("por_que_neutral", {})
    res = result.get("resumen", {})

    # Aprovechar lo positivo
    for theme in pos.get("insight_marketing", []):
        recs.append({"tipo": "aprovechar", "insight": theme, "accion": "Reforzar en campañas y creativos"})

    # Atacar lo negativo
    for theme in neg.get("insight_marketing", []):
        recs.append({"tipo": "mitigar", "insight": theme, "accion": "Mensajes que desmientan o contextualicen"})

    # Conquistar neutros
    recs.append({
        "tipo": "conversión",
        "insight": "Neutros discuten escenas y personajes sin compromiso emocional",
        "accion": "Contenido que reactive la emoción del trailer (Hans Zimmer, Brad Pitt, acción real)",
    })

    # Datos duros
    pct = res.get("porcentaje_positivo", 0)
    recs.append({
        "tipo": "dato",
        "insight": f"{pct}% sentimiento positivo",
        "accion": "Usar testimonios y citas reales en ads" if pct > 40 else "Priorizar campaña de boca-oreja",
    })

    # Engagement: qué resuena con la audiencia
    pct_eng = res.get("porcentaje_engagement_positivo", 0)
    if res.get("total_likes", 0) > 0:
        recs.append({
            "tipo": "engagement",
            "insight": f"{pct_eng}% del engagement (likes) va a comentarios positivos",
            "accion": "Priorizar citas con muchos likes en creativos; la voz positiva tiene más alcance" if pct_eng > 50 else "Cuidar narrativa: comentarios negativos pueden ganar visibilidad",
        })

    return recs


def _write_marketing_report(data: Dict) -> None:
    """Escribe reporte legible en Markdown para estrategia de marketing."""
    res = data["resumen"]
    lines = [
        "# Análisis en profundidad para estrategia de marketing - F1 (2025)",
        "",
        "## Resumen",
        f"- Total analizado: {res['total_analizado']} comentarios",
        f"- Positivos: {res['positive']} ({res['porcentaje_positivo']}%)",
        f"- Neutros: {res['neutral']} | Negativos: {res['negative']}",
        f"- **Total likes/engagement:** {res.get('total_likes', 0):,}",
        f"- **% engagement en positivos:** {res.get('porcentaje_engagement_positivo', 0)}% (lo que más resuena)",
        "",
        "---",
        "",
        "## Por qué es POSITIVO",
        "",
        "### Palabras más repetidas",
        "",
    ]
    for x in data["por_que_positivo"]["palabras_mas_frecuentes"][:15]:
        lines.append(f"- **{x['term']}** ({x['count']})")
    lines.extend([
        "",
        "### Palabras con más impacto (ponderadas por likes)",
        "",
    ])
    for x in data["por_que_positivo"].get("palabras_con_mas_impacto", [])[:10]:
        lines.append(f"- **{x['term']}** (impacto: {x['count']:,})")
    lines.extend([
        "",
        "### Bigramas recurrentes",
        "",
    ])
    for x in data["por_que_positivo"]["bigramas_recurrentes"][:10]:
        lines.append(f"- {x['term']} ({x['count']})")
    lines.extend([
        "",
        "### Insights para marketing",
        "",
    ])
    for t in data["por_que_positivo"]["insight_marketing"]:
        lines.append(f"- {t}")
    lines.extend([
        "",
        "### Citas representativas (positivas)",
        "",
    ])
    for q in data["por_que_positivo"]["citas_representativas"]:
        likes = q.get("likes", q.get("votes", 0))
        lines.append(f"> \"{q['content'][:150]}...\" — {q.get('source', '')} ❤️ {likes:,}")
        lines.append("")
    lines.extend([
        "---",
        "",
        "## Por qué es NEGATIVO",
        "",
        "### Palabras más repetidas",
        "",
    ])
    for x in data["por_que_negativo"]["palabras_mas_frecuentes"][:15]:
        lines.append(f"- **{x['term']}** ({x['count']})")
    if data["por_que_negativo"].get("palabras_con_mas_impacto"):
        lines.extend(["", "### Palabras negativas con más impacto", ""])
        for x in data["por_que_negativo"]["palabras_con_mas_impacto"][:8]:
            lines.append(f"- **{x['term']}** (impacto: {x['count']:,})")
    lines.extend([
        "",
        "### Insights para marketing",
        "",
    ])
    for t in data["por_que_negativo"]["insight_marketing"]:
        lines.append(f"- {t}")
    lines.extend([
        "",
        "---",
        "",
        "## Por qué es NEUTRAL",
        "",
    ])
    for t in data["por_que_neutral"]["insight_marketing"]:
        lines.append(f"- {t}")
    lines.extend([
        "",
        "---",
        "",
        "## Recomendaciones de marketing",
        "",
    ])
    for r in data["recomendaciones_marketing"]:
        lines.append(f"### [{r['tipo'].upper()}] {r['insight']}")
        lines.append(f"**Acción:** {r['accion']}")
        lines.append("")
    lines.extend([
        "",
        "## Por fuente",
        "",
    ])
    for src, info in data.get("por_fuente", {}).items():
        lines.append(f"### {src}")
        lines.append(f"- Total: {info['count']} | Pos: {info['positive']} | Neu: {info['neutral']} | Neg: {info['negative']}")
        lines.append(f"- Top palabras: {', '.join(x['term'] for x in info['top_palabras'][:8])}")
        lines.append("")

    path_md = OUTPUT_INSIGHTS / "reporte_marketing.md"
    with open(path_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    run_thematic_analysis()
