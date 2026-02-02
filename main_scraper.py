"""
Script principal para obtener reseñas de la película F1.
Guarda los datos en data/raw/
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.scrapers import (
    get_imdb_reviews,
    save_imdb,
    get_rottentomatoes_reviews,
    save_rt,
    get_instagram_comments,
    save_instagram,
    F1_POST_SHORTCODE,
    get_reddit_comments,
    save_reddit,
    F1_SUBREDDIT,
    get_youtube_comments_from_videos,
    save_youtube,
    F1_VIDEO_IDS,
)

DATA_DIR = Path(__file__).parent / "data" / "raw"


def combine_reviews(
    imdb_reviews: list,
    rt_reviews: list,
    instagram_comments: Optional[list] = None,
    reddit_comments: Optional[list] = None,
    youtube_comments: Optional[list] = None,
) -> list:
    """Combina reseñas de todas las fuentes."""
    all_reviews = imdb_reviews + rt_reviews
    if instagram_comments:
        all_reviews = all_reviews + instagram_comments
    if reddit_comments:
        all_reviews = all_reviews + reddit_comments
    if youtube_comments:
        all_reviews = all_reviews + youtube_comments
    return all_reviews


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SCRAPER DE RESEÑAS - PELÍCULA F1 (2025)")
    print("=" * 60)
    print()

    # IMDB
    print("1. Obteniendo reseñas de IMDB...")
    imdb_reviews = get_imdb_reviews(max_reviews=100)
    if imdb_reviews:
        save_imdb(imdb_reviews, str(DATA_DIR / "reviews_imdb.json"))
    print()

    # Rotten Tomatoes
    print("2. Obteniendo reseñas de Rotten Tomatoes...")
    rt_reviews = get_rottentomatoes_reviews(max_reviews=100)
    if rt_reviews:
        save_rt(rt_reviews, str(DATA_DIR / "reviews_rottentomatoes.json"))
    print()

    # Instagram
    print("3. Obteniendo comentarios de Instagram (Steady API)...")
    instagram_comments = get_instagram_comments(post_code=F1_POST_SHORTCODE)
    if instagram_comments:
        save_instagram(instagram_comments, str(DATA_DIR / "reviews_instagram.json"))
    else:
        print("  (Omitido: configura STEADYAPI_AUTH_KEY)")
    print()

    # Reddit
    print("4. Obteniendo comentarios de Reddit (Steady API)...")
    reddit_comments = get_reddit_comments(subreddit=F1_SUBREDDIT)
    if reddit_comments:
        save_reddit(reddit_comments, str(DATA_DIR / "reviews_reddit.json"))
    else:
        print("  (Omitido: configura STEADYAPI_AUTH_KEY)")
    print()

    # YouTube (varios vídeos F1 unificados)
    print("5. Obteniendo comentarios de YouTube (vídeos F1)...")
    youtube_comments = get_youtube_comments_from_videos(video_ids=F1_VIDEO_IDS)
    if youtube_comments:
        save_youtube(youtube_comments, str(DATA_DIR / "reviews_youtube.json"))
    else:
        print("  (Omitido: configura YOUTUBE_API_KEY)")
    print()

    # Combinar y guardar
    print("6. Combinando reseñas...")
    all_reviews = combine_reviews(
        imdb_reviews, rt_reviews, instagram_comments, reddit_comments, youtube_comments
    )

    if all_reviews:
        output = {
            "movie": "F1 (2025)",
            "scraping_date": datetime.now().isoformat(),
            "total_reviews": len(all_reviews),
            "sources": {
                "IMDB": len([r for r in all_reviews if r.get("source") == "IMDB"]),
                "Rotten Tomatoes": len([r for r in all_reviews if r.get("source") == "Rotten Tomatoes"]),
                "Instagram": len([r for r in all_reviews if r.get("source") == "Instagram"]),
                "Reddit": len([r for r in all_reviews if r.get("source") == "Reddit"]),
                "YouTube": len([r for r in all_reviews if r.get("source") == "YouTube"]),
            },
            "reviews": all_reviews,
        }
        combined_path = DATA_DIR / "reviews_f1_combined.json"
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✓ Reseñas combinadas guardadas en {combined_path}")

        try:
            import pandas as pd
            csv_path = DATA_DIR / "reviews_f1.csv"
            pd.DataFrame(all_reviews).to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"✓ CSV guardado en {csv_path}")
        except ImportError:
            pass

        print()
        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Total: {output['total_reviews']} reseñas/comentarios")
        for src, count in output["sources"].items():
            print(f"  - {src}: {count}")
        print(f"\nDatos en: {DATA_DIR}")
        print("=" * 60)
    else:
        print("⚠ No se obtuvieron reseñas. Verifica conexión y API keys.")


if __name__ == "__main__":
    main()
