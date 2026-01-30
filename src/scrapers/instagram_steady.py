"""Comentarios de Instagram vía Steady API."""
import os
import json
import requests
from typing import List, Dict, Optional

F1_POST_SHORTCODE = "DJ7Kr5XTGtk"


def get_instagram_comments(post_code: str = F1_POST_SHORTCODE, api_key: Optional[str] = None) -> List[Dict]:
    auth_key = api_key or os.environ.get("STEADYAPI_AUTH_KEY")
    if not auth_key:
        print("⚠ Exporta STEADYAPI_AUTH_KEY. Ver .env.example")
        return []
    url = "https://api.steadyapi.com/v1/instagram/comments"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {auth_key}"}, params={"code": post_code}, timeout=30)
        response.raise_for_status()
        data = response.json()
        comments = _normalize_comments(data.get("body", data), post_code)
        print(f"✓ Obtenidos {len(comments)} comentarios de Instagram")
        return comments
    except Exception as e:
        print(f"Error Instagram API: {e}")
        return []


def _normalize_comments(body, post_code: str) -> List[Dict]:
    comments = []
    raw = body.get("comments", body) if isinstance(body, dict) else body
    raw = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    for item in raw:
        if isinstance(item, dict):
            text = item.get("text") or item.get("comment") or item.get("content") or ""
            user = item.get("owner") or item.get("user") or {}
            user = user if isinstance(user, dict) else {}
            comments.append({
                "source": "Instagram",
                "content": str(text).strip(),
                "author": user.get("username") or user.get("name") or "Anónimo",
                "date": str(item.get("taken_at") or item.get("created_at") or ""),
                "rating": None,
                "helpful_votes": str(item.get("comment_like_count") or item.get("like_count") or 0),
                "post_code": post_code,
                "comment_id": item.get("id") or item.get("pk"),
            })
    return [c for c in comments if c["content"]]


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Guardado: {filename}")


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else F1_POST_SHORTCODE
    comments = get_instagram_comments(post_code=code)
    if comments:
        save_comments_to_json(comments, "reviews_instagram.json")
