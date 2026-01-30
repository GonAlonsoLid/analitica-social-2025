"""
Script para obtener reseñas de la película F1 desde IMDB
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict


def get_imdb_reviews(movie_id: str = "tt16980178", max_reviews: int = 100) -> List[Dict]:
    """Obtiene reseñas de IMDB para una película específica."""
    reviews = []
    base_url = f"https://www.imdb.com/title/{movie_id}/reviews"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        review_containers = soup.find_all('div', class_='lister-item-content')

        for container in review_containers[:max_reviews]:
            try:
                title_elem = container.find('a', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                content_elem = container.find('div', class_='text')
                content = content_elem.get_text(strip=True) if content_elem else ""
                rating_elem = container.find('span', class_='rating-other-user-rating')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.find('span').get_text(strip=True) if rating_elem.find('span') else ""
                    rating = int(rating_text) if rating_text.isdigit() else None
                author_elem = container.find('span', class_='display-name-link')
                author = author_elem.get_text(strip=True) if author_elem else "Anónimo"
                date_elem = container.find('span', class_='review-date')
                date = date_elem.get_text(strip=True) if date_elem else ""
                helpful_elem = container.find('div', class_='actions')
                helpful = "0"
                if helpful_elem:
                    helpful_match = re.search(r'(\d+)', helpful_elem.get_text())
                    if helpful_match:
                        helpful = helpful_match.group(1)

                if content:
                    reviews.append({
                        "source": "IMDB",
                        "title": title,
                        "content": content,
                        "rating": rating,
                        "author": author,
                        "date": date,
                        "helpful_votes": helpful,
                        "movie_id": movie_id
                    })
            except Exception as e:
                print(f"Error procesando reseña de IMDB: {e}")
                continue

        print(f"✓ Obtenidas {len(reviews)} reseñas de IMDB")
        return reviews
    except requests.RequestException as e:
        print(f"Error al conectar con IMDB: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []


def save_reviews_to_json(reviews: List[Dict], filename: str = "reviews_imdb.json"):
    """Guarda las reseñas en un archivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"✓ Reseñas guardadas en {filename}")


if __name__ == "__main__":
    print("Obteniendo reseñas de IMDB para la película F1...")
    reviews = get_imdb_reviews()
    if reviews:
        save_reviews_to_json(reviews)
        print(f"\nTotal: {len(reviews)} reseñas")
