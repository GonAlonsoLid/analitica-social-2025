"""
Script principal para obtener y almacenar reseñas de la película F1
desde IMDB y Rotten Tomatoes
"""
import json
import os
from datetime import datetime
from typing import Optional
from scraper_imdb import get_imdb_reviews, save_reviews_to_json as save_imdb
from scraper_rottentomatoes import get_rottentomatoes_reviews, save_reviews_to_json as save_rt
from scraper_instagram_steady import (
    get_instagram_comments,
    save_comments_to_json as save_instagram,
    F1_POST_SHORTCODE,
)
from scraper_reddit_steady import (
    get_reddit_comments,
    save_comments_to_json as save_reddit,
    F1_SUBREDDIT,
)
from scraper_youtube import (
    get_youtube_comments,
    save_comments_to_json as save_youtube,
    F1_VIDEO_ID,
)


def combine_reviews(
    imdb_reviews: list,
    rt_reviews: list,
    instagram_comments: Optional[list] = None,
    reddit_comments: Optional[list] = None,
    youtube_comments: Optional[list] = None,
) -> list:
    """
    Combina reseñas de IMDB, Rotten Tomatoes, Instagram, Reddit y YouTube.

    Returns:
        Lista combinada de todas las reseñas/comentarios
    """
    all_reviews = imdb_reviews + rt_reviews
    if instagram_comments:
        all_reviews = all_reviews + instagram_comments
    if reddit_comments:
        all_reviews = all_reviews + reddit_comments
    if youtube_comments:
        all_reviews = all_reviews + youtube_comments
    return all_reviews


def save_combined_reviews(reviews: list, filename: str = "reviews_f1_combined.json"):
    """
    Guarda todas las reseñas combinadas en un archivo JSON
    
    Args:
        reviews: Lista de todas las reseñas
        filename: Nombre del archivo de salida
    """
    output = {
        "movie": "F1 (2025)",
        "scraping_date": datetime.now().isoformat(),
        "total_reviews": len(reviews),
        "sources": {
            "IMDB": len([r for r in reviews if r.get("source") == "IMDB"]),
            "Rotten Tomatoes": len([r for r in reviews if r.get("source") == "Rotten Tomatoes"]),
            "Instagram": len([r for r in reviews if r.get("source") == "Instagram"]),
            "Reddit": len([r for r in reviews if r.get("source") == "Reddit"]),
            "YouTube": len([r for r in reviews if r.get("source") == "YouTube"]),
        },
        "reviews": reviews
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Reseñas combinadas guardadas en {filename}")
    return output


def save_to_csv(reviews: list, filename: str = "reviews_f1.csv"):
    """
    Guarda las reseñas en formato CSV para fácil análisis
    
    Args:
        reviews: Lista de reseñas
        filename: Nombre del archivo CSV
    """
    try:
        import pandas as pd
        
        df = pd.DataFrame(reviews)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✓ Reseñas guardadas en CSV: {filename}")
    except ImportError:
        print("⚠ pandas no está instalado. Instala con: pip install pandas")
        print("  Las reseñas se guardarán solo en JSON.")


def main():
    """Función principal"""
    print("=" * 60)
    print("SCRAPER DE RESEÑAS - PELÍCULA F1 (2025)")
    print("=" * 60)
    print()
    
    # Obtener reseñas de IMDB
    print("1. Obteniendo reseñas de IMDB...")
    imdb_reviews = get_imdb_reviews(max_reviews=100)
    
    if imdb_reviews:
        save_imdb(imdb_reviews, "reviews_imdb.json")
    print()
    
    # Obtener reseñas de Rotten Tomatoes
    print("2. Obteniendo reseñas de Rotten Tomatoes...")
    rt_reviews = get_rottentomatoes_reviews(max_reviews=100)
    
    if rt_reviews:
        save_rt(rt_reviews, "reviews_rottentomatoes.json")
    print()
    
    # Obtener comentarios de Instagram (requiere STEADYAPI_AUTH_KEY)
    print("3. Obteniendo comentarios de Instagram (Steady API)...")
    instagram_comments = get_instagram_comments(post_code=F1_POST_SHORTCODE)
    
    if instagram_comments:
        save_instagram(instagram_comments, "reviews_instagram.json")
    else:
        print("  (Omitido: configura STEADYAPI_AUTH_KEY para incluir Instagram)")
    print()

    # Obtener comentarios de Reddit (Steady API, mismo token que Instagram)
    print("4. Obteniendo comentarios de Reddit (Steady API)...")
    reddit_comments = get_reddit_comments(subreddit=F1_SUBREDDIT)

    if reddit_comments:
        save_reddit(reddit_comments, "reviews_reddit.json")
    else:
        print("  (Omitido: configura STEADYAPI_AUTH_KEY para incluir Reddit)")
    print()

    # Obtener comentarios de YouTube (requiere YOUTUBE_API_KEY)
    print("5. Obteniendo comentarios de YouTube...")
    youtube_comments = get_youtube_comments(video_id=F1_VIDEO_ID)

    if youtube_comments:
        save_youtube(youtube_comments, "reviews_youtube.json")
    else:
        print("  (Omitido: configura YOUTUBE_API_KEY para incluir YouTube)")
    print()

    # Combinar y guardar
    print("6. Combinando reseñas...")
    all_reviews = combine_reviews(
        imdb_reviews, rt_reviews, instagram_comments, reddit_comments, youtube_comments
    )
    
    if all_reviews:
        output = save_combined_reviews(all_reviews)
        
        # Intentar guardar en CSV también
        save_to_csv(all_reviews)
        
        print()
        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Total de reseñas/comentarios obtenidos: {output['total_reviews']}")
        print(f"  - IMDB: {output['sources']['IMDB']}")
        print(f"  - Rotten Tomatoes: {output['sources']['Rotten Tomatoes']}")
        print(f"  - Instagram: {output['sources']['Instagram']}")
        print(f"  - Reddit: {output['sources']['Reddit']}")
        print(f"  - YouTube: {output['sources']['YouTube']}")
        print()
        print("Archivos generados:")
        print("  - reviews_imdb.json")
        print("  - reviews_rottentomatoes.json")
        if output['sources']['Instagram']:
            print("  - reviews_instagram.json")
        if output['sources']['Reddit']:
            print("  - reviews_reddit.json")
        if output['sources']['YouTube']:
            print("  - reviews_youtube.json")
        print("  - reviews_f1_combined.json")
        if os.path.exists("reviews_f1.csv"):
            print("  - reviews_f1.csv")
        print("=" * 60)
    else:
        print("⚠ No se obtuvieron reseñas. Verifica la conexión a internet y los selectores HTML.")


if __name__ == "__main__":
    main()

