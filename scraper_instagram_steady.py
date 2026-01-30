"""
Script para obtener comentarios de Instagram sobre la película F1
usando la Steady API (https://steadyapi.com)
"""
import os
import json
import requests
from typing import List, Dict, Optional


# Shortcode por defecto - Post de la película F1
# URL: https://www.instagram.com/p/DJ7Kr5XTGtk/
F1_POST_SHORTCODE = "DJ7Kr5XTGtk"


def get_instagram_comments(
    post_code: str = F1_POST_SHORTCODE,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """
    Obtiene comentarios de un post de Instagram usando la Steady API.

    Args:
        post_code: Shortcode del post de Instagram (ej: de instagram.com/p/DESoQn4RgAl/)
        api_key: Tu API key de Steady. Si no se pasa, usa la variable de entorno STEADYAPI_AUTH_KEY.

    Returns:
        Lista de diccionarios con los comentarios normalizados
    """
    auth_key = api_key or os.environ.get("STEADYAPI_AUTH_KEY")
    if not auth_key:
        print(
            "⚠ Necesitas configurar tu API key de Steady API:\n"
            "  1. Regístrate en https://steadyapi.com/register\n"
            "  2. Genera un token en Profile > Personal Access Tokens\n"
            "  3. Exporta: export STEADYAPI_AUTH_KEY='tu_token'\n"
            "     o pásala como parámetro: get_instagram_comments(api_key='tu_token')"
        )
        return []

    url = "https://api.steadyapi.com/v1/instagram/comments"
    params = {"code": post_code}
    headers = {"Authorization": f"Bearer {auth_key}"}

    try:
        response = requests.request(
            "GET", url, headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        comments = _normalize_comments(data, post_code)
        print(f"✓ Obtenidos {len(comments)} comentarios de Instagram (post: {post_code})")
        return comments

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("Error 401: API key inválida o expirada. Verifica tu token de Steady API.")
        elif response.status_code == 404:
            print(f"Error 404: No se encontró el post con shortcode '{post_code}'")
        else:
            print(f"Error HTTP {response.status_code}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con Steady API: {e}")
        return []
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error procesando respuesta de la API: {e}")
        return []


def _normalize_comments(api_response: dict, post_code: str) -> List[Dict]:
    """
    Normaliza la respuesta de la Steady API al formato estándar del proyecto.
    Maneja distintas estructuras posibles de respuesta.
    """
    comments = []

    # La API puede devolver body directamente o anidado en meta/body
    body = api_response.get("body", api_response)
    if isinstance(body, dict) and "comments" in body:
        raw_comments = body["comments"]
    elif isinstance(body, list):
        raw_comments = body
    elif isinstance(body, dict):
        raw_comments = [body]
    else:
        raw_comments = []

    for item in raw_comments:
        if isinstance(item, dict):
            comment = {
                "source": "Instagram",
                "content": _extract_text(item),
                "author": _extract_username(item),
                "date": _extract_date(item),
                "rating": None,
                "helpful_votes": _extract_likes(item),
                "post_code": post_code,
                "comment_id": item.get("id") or item.get("pk"),
            }
            if comment["content"]:
                comments.append(comment)

    return comments


def _extract_text(item: dict) -> str:
    """Extrae el texto del comentario de distintas estructuras."""
    for key in ("text", "comment", "content", "caption"):
        if item.get(key):
            return str(item[key]).strip()
    # Algunas APIs devuelven el texto anidado
    if "node" in item and isinstance(item["node"], dict):
        return _extract_text(item["node"])
    return ""


def _extract_username(item: dict) -> str:
    """Extrae el username del autor."""
    user = item.get("owner") or item.get("user") or item.get("from") or {}
    if isinstance(user, dict):
        return user.get("username") or user.get("name") or "Anónimo"
    return "Anónimo"


def _extract_date(item: dict) -> str:
    """Extrae la fecha del comentario."""
    for key in ("taken_at", "created_at", "timestamp", "date"):
        val = item.get(key)
        if val:
            return str(val)
    return ""


def _extract_likes(item: dict) -> str:
    """Extrae el número de likes del comentario."""
    count = item.get("comment_like_count") or item.get("likes_count") or item.get("like_count") or 0
    return str(count) if count else "0"


def save_comments_to_json(
    comments: List[Dict], filename: str = "reviews_instagram.json"
) -> None:
    """Guarda los comentarios en un archivo JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Comentarios guardados en {filename}")


if __name__ == "__main__":
    import sys

    post_code = sys.argv[1] if len(sys.argv) > 1 else F1_POST_SHORTCODE
    print(f"Obteniendo comentarios de Instagram para la película F1 (post: {post_code})...")
    print()

    comments = get_instagram_comments(post_code=post_code)

    if comments:
        save_comments_to_json(comments)
        print(f"\nTotal de comentarios obtenidos: {len(comments)}")
    else:
        print("No se pudieron obtener comentarios. Verifica tu API key y el shortcode del post.")
