"""
Script para obtener reseñas de la película F1 desde Rotten Tomatoes
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict


def get_rottentomatoes_reviews(movie_url: str = None, max_reviews: int = 100) -> List[Dict]:
    """Obtiene reseñas de Rotten Tomatoes para la película F1."""
    reviews = []
    search_url = movie_url or "https://www.rottentomatoes.com/search?search=F1%202025"
    movie_page_url = "https://www.rottentomatoes.com/m/f1_2025"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(movie_page_url, headers=headers, timeout=10)
        if response.status_code != 200:
            response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        critic_reviews = soup.find_all('div', class_='review-row')
        audience_reviews = soup.find_all('div', class_='audience-review-row')
        all_review_containers = critic_reviews + audience_reviews

        for container in all_review_containers[:max_reviews]:
            try:
                review_type = "critic" if container in critic_reviews else "audience"
                content_elem = container.find('p', class_='review-text') or container.find('div', class_='review-text')
                content = content_elem.get_text(strip=True) if content_elem else ""
                author_elem = (
                    container.find('a', class_='display-name')
                    or container.find('strong', class_='display-name')
                    or container.find('span', class_='display-name')
                )
                author = author_elem.get_text(strip=True) if author_elem else "Anónimo"
                rating_elem = container.find('span', class_='icon')
                rating = "Fresh" if rating_elem and 'fresh' in rating_elem.get('class', []) else None
                if rating_elem and 'rotten' in rating_elem.get('class', []):
                    rating = "Rotten"
                rating_num = container.find('span', class_='rating')
                if rating_num:
                    match = re.search(r'(\d+\.?\d*)', rating_num.get_text())
                    if match:
                        rating = match.group(1)
                date_elem = container.find('span', class_='review-date')
                date = date_elem.get_text(strip=True) if date_elem else ""
                helpful_elem = container.find('span', class_='helpful')
                helpful = re.search(r'(\d+)', helpful_elem.get_text()).group(1) if helpful_elem else "0"

                if content:
                    reviews.append({
                        "source": "Rotten Tomatoes",
                        "review_type": review_type,
                        "content": content,
                        "rating": rating,
                        "author": author,
                        "date": date,
                        "helpful_votes": helpful
                    })
            except Exception as e:
                print(f"Error procesando reseña: {e}")
                continue

        if not reviews:
            review_sections = soup.find_all(['div', 'section'], class_=re.compile(r'review|comment'))
            for section in review_sections[:max_reviews]:
                try:
                    content = section.get_text(strip=True)
                    if len(content) > 50:
                        reviews.append({
                            "source": "Rotten Tomatoes",
                            "review_type": "unknown",
                            "content": content,
                            "rating": None,
                            "author": "Unknown",
                            "date": "",
                            "helpful_votes": "0"
                        })
                except Exception:
                    continue

        print(f"✓ Obtenidas {len(reviews)} reseñas de Rotten Tomatoes")
        return reviews
    except requests.RequestException as e:
        print(f"Error al conectar con Rotten Tomatoes: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []


def save_reviews_to_json(reviews: List[Dict], filename: str = "reviews_rottentomatoes.json"):
    """Guarda las reseñas en un archivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"✓ Reseñas guardadas en {filename}")


if __name__ == "__main__":
    print("Obteniendo reseñas de Rotten Tomatoes...")
    reviews = get_rottentomatoes_reviews()
    if reviews:
        save_reviews_to_json(reviews)
        print(f"\nTotal: {len(reviews)} reseñas")
