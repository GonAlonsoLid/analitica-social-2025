"""Comentarios de YouTube vía YouTube Data API v3."""
import os
import json
import requests
from typing import List, Dict, Optional

F1_VIDEO_ID = "8yh9BPUBbbQ"


def get_youtube_comments(video_id: str = F1_VIDEO_ID, api_key: Optional[str] = None, max_comments: int = 500) -> List[Dict]:
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


def _fmt(snippet: dict, video_id: str, comment_id: Optional[str]) -> Dict:
    return {
        "source": "YouTube",
        "content": (snippet.get("textDisplay") or snippet.get("textOriginal") or "").strip(),
        "author": snippet.get("authorDisplayName", "Anónimo"),
        "date": snippet.get("publishedAt", ""),
        "rating": None,
        "helpful_votes": str(snippet.get("likeCount", 0)),
        "video_id": video_id,
        "comment_id": comment_id,
    }


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Guardado: {filename}")


if __name__ == "__main__":
    import sys
    vid = sys.argv[1] if len(sys.argv) > 1 else F1_VIDEO_ID
    if "youtube.com" in vid or "youtu.be" in vid:
        vid = vid.split("v=")[-1].split("&")[0] if "v=" in vid else vid.split("youtu.be/")[-1].split("?")[0]
    comments = get_youtube_comments(video_id=vid)
    if comments:
        save_comments_to_json(comments, "reviews_youtube.json")
