"""
Script para obtener reseñas de la película F1 desde Rotten Tomatoes
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import re


def get_rottentomatoes_reviews(movie_url: str = None, max_reviews: int = 100) -> List[Dict]:
    """
    Obtiene reseñas de Rotten Tomatoes para la película F1
    
    Args:
        movie_url: URL de la película en Rotten Tomatoes (opcional)
        max_reviews: Número máximo de reseñas a obtener
    
    Returns:
        Lista de diccionarios con las reseñas
    """
    reviews = []
    
    # URL de búsqueda para F1 (2025)
    # Si no se proporciona URL, intentamos buscar
    if not movie_url:
        search_url = "https://www.rottentomatoes.com/search?search=F1%202025"
    else:
        search_url = movie_url
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Primero intentamos obtener la página de la película directamente
        # URL común para F1 (2025) - puede necesitar ajuste
        movie_page_url = "https://www.rottentomatoes.com/m/f1_2025"
        
        response = requests.get(movie_page_url, headers=headers, timeout=10)
        
        # Si no funciona, intentamos con la búsqueda
        if response.status_code != 200:
            response = requests.get(search_url, headers=headers, timeout=10)
        
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar reseñas de críticos
        critic_reviews = soup.find_all('div', class_='review-row')
        
        # También buscar reseñas de audiencia
        audience_reviews = soup.find_all('div', class_='audience-review-row')
        
        all_review_containers = critic_reviews + audience_reviews
        
        for container in all_review_containers[:max_reviews]:
            try:
                # Tipo de reseña (crítico o audiencia)
                review_type = "critic" if container in critic_reviews else "audience"
                
                # Contenido de la reseña
                content_elem = container.find('p', class_='review-text')
                if not content_elem:
                    content_elem = container.find('div', class_='review-text')
                content = content_elem.get_text(strip=True) if content_elem else ""
                
                # Autor
                author_elem = container.find('a', class_='display-name')
                if not author_elem:
                    author_elem = container.find('strong', class_='display-name')
                if not author_elem:
                    author_elem = container.find('span', class_='display-name')
                author = author_elem.get_text(strip=True) if author_elem else "Anónimo"
                
                # Rating (Fresh/Rotten o estrellas)
                rating_elem = container.find('span', class_='icon')
                rating = None
                if rating_elem:
                    if 'fresh' in rating_elem.get('class', []):
                        rating = "Fresh"
                    elif 'rotten' in rating_elem.get('class', []):
                        rating = "Rotten"
                
                # También buscar rating numérico
                rating_num_elem = container.find('span', class_='rating')
                if rating_num_elem:
                    rating_text = rating_num_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = rating_match.group(1)
                
                # Fecha
                date_elem = container.find('span', class_='review-date')
                date = date_elem.get_text(strip=True) if date_elem else ""
                
                # Útil
                helpful_elem = container.find('span', class_='helpful')
                helpful = "0"
                if helpful_elem:
                    helpful_text = helpful_elem.get_text()
                    helpful_match = re.search(r'(\d+)', helpful_text)
                    if helpful_match:
                        helpful = helpful_match.group(1)
                
                if content:  # Solo agregar si hay contenido
                    review = {
                        "source": "Rotten Tomatoes",
                        "review_type": review_type,
                        "content": content,
                        "rating": rating,
                        "author": author,
                        "date": date,
                        "helpful_votes": helpful
                    }
                    reviews.append(review)
                    
            except Exception as e:
                print(f"Error procesando reseña de Rotten Tomatoes: {e}")
                continue
        
        # Si no encontramos reseñas, intentamos método alternativo
        if not reviews:
            # Buscar en diferentes estructuras HTML
            review_sections = soup.find_all(['div', 'section'], class_=re.compile(r'review|comment'))
            for section in review_sections[:max_reviews]:
                try:
                    content = section.get_text(strip=True)
                    if len(content) > 50:  # Filtrar textos muy cortos
                        review = {
                            "source": "Rotten Tomatoes",
                            "review_type": "unknown",
                            "content": content,
                            "rating": None,
                            "author": "Unknown",
                            "date": "",
                            "helpful_votes": "0"
                        }
                        reviews.append(review)
                except:
                    continue
        
        print(f"✓ Obtenidas {len(reviews)} reseñas de Rotten Tomatoes")
        return reviews
        
    except requests.RequestException as e:
        print(f"Error al conectar con Rotten Tomatoes: {e}")
        print("Nota: Rotten Tomatoes puede requerir JavaScript. Considera usar Selenium para scraping dinámico.")
        return []
    except Exception as e:
        print(f"Error inesperado al obtener reseñas de Rotten Tomatoes: {e}")
        return []


def save_reviews_to_json(reviews: List[Dict], filename: str = "reviews_rottentomatoes.json"):
    """Guarda las reseñas en un archivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"✓ Reseñas guardadas en {filename}")


if __name__ == "__main__":
    print("Obteniendo reseñas de Rotten Tomatoes para la película F1...")
    reviews = get_rottentomatoes_reviews()
    
    if reviews:
        save_reviews_to_json(reviews)
        print(f"\nTotal de reseñas obtenidas: {len(reviews)}")
    else:
        print("No se pudieron obtener reseñas de Rotten Tomatoes")
        print("Nota: Puede ser necesario usar Selenium para contenido dinámico")

