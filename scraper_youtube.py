"""
Script para obtener comentarios de YouTube usando la YouTube Data API v3
(https://developers.google.com/youtube/v3)
"""
import os
import json
import requests
from typing import List, Dict, Optional


# Video por defecto - URL: https://www.youtube.com/watch?v=8yh9BPUBbbQ
F1_VIDEO_ID = "8yh9BPUBbbQ"


def get_youtube_comments(
    video_id: str = F1_VIDEO_ID,
    api_key: Optional[str] = None,
    max_comments: int = 500,
) -> List[Dict]:
    """
    Obtiene comentarios de un video de YouTube usando la YouTube Data API v3.

    Args:
        video_id: ID del video (ej: de youtube.com/watch?v=8yh9BPUBbbQ)
        api_key: Tu API key de Google. Si no se pasa, usa YOUTUBE_API_KEY.
        max_comments: Número máximo de comentarios a obtener (incluye respuestas).

    Returns:
        Lista de diccionarios con los comentarios normalizados
    """
    key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print(
            "⚠ Necesitas configurar tu API key de YouTube Data API v3:\n"
            "  1. Ve a https://console.cloud.google.com/\n"
            "  2. Crea un proyecto y activa 'YouTube Data API v3'\n"
            "  3. Crea credenciales (API key)\n"
            "  4. Exporta: export YOUTUBE_API_KEY='tu_api_key'"
        )
        return []

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    page_token = None

    try:
        while len(comments) < max_comments:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "key": key,
                "maxResults": min(100, max_comments - len(comments)),
                "textFormat": "plainText",
                "order": "relevance",
            }
            if page_token:
                params["pageToken"] = page_token

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                break

            for thread in items:
                snippet = thread.get("snippet", {})
                top_comment = snippet.get("topLevelComment", {})
                top_snippet = top_comment.get("snippet", {})

                # Comentario principal
                comments.append(_format_comment(
                    top_snippet, "YouTube", video_id, top_comment.get("id")
                ))

                # Respuestas
                replies = snippet.get("replies", {}).get("comments", [])
                for reply in replies:
                    if len(comments) >= max_comments:
                        break
                    reply_snippet = reply.get("snippet", {})
                    comments.append(_format_comment(
                        reply_snippet, "YouTube", video_id, reply.get("id")
                    ))

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        print(f"✓ Obtenidos {len(comments)} comentarios de YouTube (video: {video_id})")
        return comments

    except requests.exceptions.HTTPError as e:
        resp = e.response
        if resp.status_code == 403:
            err_body = resp.json() if resp.text else {}
            reason = err_body.get("error", {}).get("errors", [{}])[0].get("reason", "")
            if "commentsDisabled" in str(reason):
                print("Los comentarios están desactivados en este video.")
            elif "quotaExceeded" in str(reason):
                print("Se superó la cuota de la API. Prueba mañana o usa otra API key.")
            else:
                print(f"Error 403: {e}")
        elif resp.status_code == 404:
            print(f"Video no encontrado: {video_id}")
        else:
            print(f"Error HTTP: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con YouTube API: {e}")
        return []
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error procesando respuesta: {e}")
        return []


def _format_comment(
    snippet: dict, source: str, video_id: str, comment_id: Optional[str] = None
) -> Dict:
    """Formatea un comentario al estándar del proyecto."""
    return {
        "source": source,
        "content": snippet.get("textDisplay") or snippet.get("textOriginal", "").strip(),
        "author": snippet.get("authorDisplayName", "Anónimo"),
        "date": snippet.get("publishedAt", ""),
        "rating": None,
        "helpful_votes": str(snippet.get("likeCount", 0)),
        "video_id": video_id,
        "comment_id": comment_id,
    }


def save_comments_to_json(
    comments: List[Dict], filename: str = "reviews_youtube.json"
) -> None:
    """Guarda los comentarios en un archivo JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Comentarios guardados en {filename}")


if __name__ == "__main__":
    import sys

    video_id = sys.argv[1] if len(sys.argv) > 1 else F1_VIDEO_ID
    # Extraer ID de URL completa si el usuario pasa la URL
    if "youtube.com" in video_id or "youtu.be" in video_id:
        if "v=" in video_id:
            video_id = video_id.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in video_id:
            video_id = video_id.split("youtu.be/")[-1].split("?")[0]

    print(f"Obteniendo comentarios de YouTube (video: {video_id})...")
    print()

    comments = get_youtube_comments(video_id=video_id)

    if comments:
        save_comments_to_json(comments)
        print(f"\nTotal de comentarios obtenidos: {len(comments)}")
    else:
        print("No se pudieron obtener comentarios. Verifica tu API key.")
