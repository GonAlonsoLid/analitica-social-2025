"""
Script principal para obtener y almacenar reseñas de la película F1
desde IMDB y Rotten Tomatoes
"""
import json
import os
from datetime import datetime
from scraper_imdb import get_imdb_reviews, save_reviews_to_json as save_imdb
from scraper_rottentomatoes import get_rottentomatoes_reviews, save_reviews_to_json as save_rt


def combine_reviews(imdb_reviews: list, rt_reviews: list) -> list:
    """
    Combina reseñas de ambas fuentes en una sola lista
    
    Args:
        imdb_reviews: Lista de reseñas de IMDB
        rt_reviews: Lista de reseñas de Rotten Tomatoes
    
    Returns:
        Lista combinada de todas las reseñas
    """
    all_reviews = imdb_reviews + rt_reviews
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
            "Rotten Tomatoes": len([r for r in reviews if r.get("source") == "Rotten Tomatoes"])
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
    
    # Combinar y guardar
    print("3. Combinando reseñas...")
    all_reviews = combine_reviews(imdb_reviews, rt_reviews)
    
    if all_reviews:
        output = save_combined_reviews(all_reviews)
        
        # Intentar guardar en CSV también
        save_to_csv(all_reviews)
        
        print()
        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Total de reseñas obtenidas: {output['total_reviews']}")
        print(f"  - IMDB: {output['sources']['IMDB']}")
        print(f"  - Rotten Tomatoes: {output['sources']['Rotten Tomatoes']}")
        print()
        print("Archivos generados:")
        print("  - reviews_imdb.json")
        print("  - reviews_rottentomatoes.json")
        print("  - reviews_f1_combined.json")
        if os.path.exists("reviews_f1.csv"):
            print("  - reviews_f1.csv")
        print("=" * 60)
    else:
        print("⚠ No se obtuvieron reseñas. Verifica la conexión a internet y los selectores HTML.")


if __name__ == "__main__":
    main()

