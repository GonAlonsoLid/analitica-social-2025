"""Comentarios de YouTube vía YouTube Data API v3."""
import os
import json
import requests
from typing import List, Dict, Optional, Union

F1_VIDEO_ID = "8yh9BPUBbbQ"
# Vídeos F1 (2025) para análisis unificado
F1_VIDEO_IDS = [
    "8yh9BPUBbbQ",   # Trailer oficial / teaser
    "Cf18Jx4hINk",   # https://www.youtube.com/watch?v=Cf18Jx4hINk
]


def get_youtube_comments(video_id: str = F1_VIDEO_ID, api_key: Optional[str] = None, max_comments: int = 10000) -> List[Dict]:
    key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("⚠ Exporta YOUTUBE_API_KEY. Ver .env.example")
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
            for thread in data.get("items", []):
                snippet = thread.get("snippet", {})
                top = snippet.get("topLevelComment", {})
                top_snip = top.get("snippet", {})
                comments.append(_fmt(top_snip, video_id, top.get("id")))
                for reply in snippet.get("replies", {}).get("comments", []):
                    if len(comments) >= max_comments:
                        break
                    comments.append(_fmt(reply.get("snippet", {}), video_id, reply.get("id")))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        print(f"✓ Obtenidos {len(comments)} comentarios de YouTube")
        return comments
    except requests.exceptions.HTTPError as e:
        print(f"Error YouTube API: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_youtube_comments_from_videos(
    video_ids: Union[List[str], str] = F1_VIDEO_IDS,
    api_key: Optional[str] = None,
    max_per_video: int = 5000,
) -> List[Dict]:
    """
    Obtiene comentarios de varios vídeos y los unifica.
    Args:
        video_ids: Lista de IDs o URL(s), o un solo ID/URL.
        api_key: Clave de YouTube API (o YOUTUBE_API_KEY).
        max_per_video: Máximo de comentarios por vídeo.
    """
    if isinstance(video_ids, str):
        video_ids = [video_ids]
    ids = []
    for v in video_ids:
        if "youtube.com" in v or "youtu.be" in v:
            vid = v.split("v=")[-1].split("&")[0] if "v=" in v else v.split("youtu.be/")[-1].split("?")[0]
        else:
            vid = v
        if vid and vid not in ids:
            ids.append(vid)
    all_comments = []
    for vid in ids:
        comments = get_youtube_comments(video_id=vid, api_key=api_key, max_comments=max_per_video)
        all_comments.extend(comments)
    if all_comments:
        print(f"✓ Total YouTube unificado: {len(all_comments)} comentarios de {len(ids)} vídeo(s)")
    return all_comments


def _fmt(snippet: dict, video_id: str, comment_id: Optional[str]) -> Dict:
    """Formatea comentario según YouTube Data API v3 (snippet.likeCount)."""
    like_count = int(snippet.get("likeCount", 0) or 0)
    return {
        "source": "YouTube",
        "content": (snippet.get("textDisplay") or snippet.get("textOriginal") or "").strip(),
        "author": snippet.get("authorDisplayName", "Anónimo"),
        "date": snippet.get("publishedAt", ""),
        "rating": None,
        "likes": like_count,
        "helpful_votes": str(like_count),
        "video_id": video_id,
        "comment_id": comment_id,
    }


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Guardado: {filename}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        vids = sys.argv[1:]
        comments = get_youtube_comments_from_videos(video_ids=vids)
    else:
        comments = get_youtube_comments_from_videos(video_ids=F1_VIDEO_IDS)
    if comments:
        save_comments_to_json(comments, "reviews_youtube.json")
