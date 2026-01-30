"""
Script para obtener comentarios de Reddit sobre la película F1
usando la Steady API (https://steadyapi.com)
"""
import os
import json
import requests
from typing import List, Dict, Optional


# Subreddit por defecto - Película F1
F1_SUBREDDIT = "F1movie"


def get_reddit_comments(
    subreddit: str = F1_SUBREDDIT,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """
    Obtiene comentarios de un subreddit usando la Steady API.

    Args:
        subreddit: Nombre del subreddit (ej: F1movie)
        api_key: Tu API key de Steady. Si no se pasa, usa STEADYAPI_AUTH_KEY.

    Returns:
        Lista de diccionarios con los comentarios normalizados
    """
    auth_key = api_key or os.environ.get("STEADYAPI_AUTH_KEY")
    if not auth_key:
        print(
            "⚠ Necesitas configurar tu API key de Steady API:\n"
            "  export STEADYAPI_AUTH_KEY='tu_token'\n"
            "  (La misma que usas para Instagram)"
        )
        return []

    url = "https://api.steadyapi.com/v1/reddit/subreddit/comments"
    params = {"subreddit": subreddit}
    headers = {"Authorization": f"Bearer {auth_key}"}

    try:
        response = requests.request(
            "GET", url, headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        comments = _normalize_reddit_response(data, subreddit)
        print(f"✓ Obtenidos {len(comments)} comentarios de Reddit (r/{subreddit})")
        return comments

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("Error 401: API key inválida o expirada. Verifica tu token de Steady API.")
        elif response.status_code == 404:
            print(f"Error 404: No se encontró el subreddit r/{subreddit}")
        else:
            print(f"Error HTTP {response.status_code}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con Steady API: {e}")
        return []
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error procesando respuesta de la API: {e}")
        return []


def _normalize_reddit_response(api_response: dict, subreddit: str) -> List[Dict]:
    """
    Normaliza la respuesta de la Steady API al formato estándar del proyecto.
    Reddit puede devolver posts con comentarios o lista de comentarios.
    """
    items = []

    body = api_response.get("body", api_response)
    if isinstance(body, list):
        raw_items = body
    elif isinstance(body, dict):
        raw_items = body.get("comments", body.get("children", [body]))
        if not isinstance(raw_items, list):
            raw_items = [raw_items]
    else:
        raw_items = []

    for item in raw_items:
        # Reddit usa estructura data para cada item
        data = item.get("data", item) if isinstance(item, dict) else item
        if not isinstance(data, dict):
            continue

        content = _extract_reddit_text(data)
        if not content:
            continue

        items.append({
            "source": "Reddit",
            "content": content,
            "author": data.get("author") or data.get("name") or "Anónimo",
            "date": _extract_reddit_date(data),
            "rating": None,
            "helpful_votes": str(data.get("score") or data.get("ups") or 0),
            "subreddit": subreddit,
            "post_id": data.get("id"),
            "title": data.get("title") if data.get("title") else None,
        })

    return items


def _extract_reddit_text(item: dict) -> str:
    """Extrae el texto del post o comentario de Reddit."""
    for key in ("body", "selftext", "content", "text"):
        val = item.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _extract_reddit_date(item: dict) -> str:
    """Extrae la fecha (Reddit usa created_utc)."""
    ts = item.get("created_utc") or item.get("created") or item.get("timestamp")
    return str(ts) if ts else ""


def save_comments_to_json(
    comments: List[Dict], filename: str = "reviews_reddit.json"
) -> None:
    """Guarda los comentarios en un archivo JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Comentarios guardados en {filename}")


if __name__ == "__main__":
    import sys

    subreddit = sys.argv[1] if len(sys.argv) > 1 else F1_SUBREDDIT
    print(f"Obteniendo comentarios de Reddit r/{subreddit} (película F1)...")
    print()

    comments = get_reddit_comments(subreddit=subreddit)

    if comments:
        save_comments_to_json(comments)
        print(f"\nTotal de comentarios obtenidos: {len(comments)}")
    else:
        print("No se pudieron obtener comentarios. Verifica tu API key y el subreddit.")
