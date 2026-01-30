"""Comentarios de Reddit vía Steady API."""
import os
import json
import requests
from typing import List, Dict, Optional

F1_SUBREDDIT = "F1movie"


def get_reddit_comments(subreddit: str = F1_SUBREDDIT, api_key: Optional[str] = None) -> List[Dict]:
    auth_key = api_key or os.environ.get("STEADYAPI_AUTH_KEY")
    if not auth_key:
        print("⚠ Exporta STEADYAPI_AUTH_KEY. Ver .env.example")
        return []
    url = "https://api.steadyapi.com/v1/reddit/subreddit/comments"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {auth_key}"}, params={"subreddit": subreddit}, timeout=30)
        response.raise_for_status()
        data = response.json()
        comments = _normalize_reddit_response(data.get("body", data), subreddit)
        print(f"✓ Obtenidos {len(comments)} comentarios de Reddit r/{subreddit}")
        return comments
    except Exception as e:
        print(f"Error Reddit API: {e}")
        return []


def _normalize_reddit_response(api_response, subreddit: str) -> List[Dict]:
    items = []
    body = api_response.get("body", api_response) if isinstance(api_response, dict) else api_response
    raw = body.get("comments", body.get("children", [body])) if isinstance(body, dict) else body
    raw = raw if isinstance(raw, list) else [raw]
    for item in raw:
        data = item.get("data", item) if isinstance(item, dict) else item
        if not isinstance(data, dict):
            continue
        content = data.get("body") or data.get("selftext") or data.get("content") or data.get("text") or ""
        if not content or not str(content).strip():
            continue
        items.append({
            "source": "Reddit",
            "content": str(content).strip(),
            "author": data.get("author") or data.get("name") or "Anónimo",
            "date": str(data.get("created_utc") or data.get("created") or ""),
            "rating": None,
            "helpful_votes": str(data.get("score") or data.get("ups") or 0),
            "subreddit": subreddit,
            "post_id": data.get("id"),
            "title": data.get("title"),
        })
    return items


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Guardado: {filename}")


if __name__ == "__main__":
    import sys
    sub = sys.argv[1] if len(sys.argv) > 1 else F1_SUBREDDIT
    comments = get_reddit_comments(subreddit=sub)
    if comments:
        save_comments_to_json(comments, "reviews_reddit.json")
