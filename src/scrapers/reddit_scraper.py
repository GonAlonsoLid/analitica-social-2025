"""
Scraper de Reddit sin API: obtiene posts y comentarios vía URLs .json.
No requiere API key ni PRAW. Usa requests + User-Agent.
"""
import json
import time
import requests
from typing import List, Dict, Any, Optional

F1_SUBREDDIT = "F1movie"

# Reddit pide un User-Agent identificable; si no, puede devolver 429
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) analitica-social-f1/1.0 (educational)"
REQUEST_DELAY = 1.5  # segundos entre requests para no saturar


def get_reddit_comments_scraper(
    subreddit: str = F1_SUBREDDIT,
    limit_posts: int = 30,
    limit_comments_per_post: Optional[int] = 150,
    sort: str = "hot",
) -> List[Dict]:
    """
    Obtiene posts y comentarios de un subreddit por scraping (URLs .json).
    Sin API key. Respeta un delay entre peticiones.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    items: List[Dict] = []

    # 1) Listado de posts del subreddit
    listing_url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit_posts, 100), "raw_json": 1}
    try:
        r = session.get(listing_url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error obteniendo listado r/{subreddit}: {e}")
        return []

    children = (data.get("data") or {}).get("children") or []
    post_ids = []
    for child in children:
        d = (child.get("data") or {}) if isinstance(child, dict) else {}
        post_id = d.get("id")
        if not post_id:
            continue
        post_ids.append(post_id)
        # Incluir el post si tiene texto (selftext) o al menos título (links)
        selftext = (d.get("selftext") or "").strip()
        title = (d.get("title") or "").strip()
        if selftext or title:
            items.append(_thing_to_review(d, subreddit, is_post=True))
        if len(post_ids) >= limit_posts:
            break

    # 2) Por cada post, pedir la página de comentarios (post + thread de comentarios)
    for i, post_id in enumerate(post_ids):
        time.sleep(REQUEST_DELAY)
        comments_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        try:
            r = session.get(comments_url, params={"raw_json": 1}, timeout=15)
            r.raise_for_status()
            thread = r.json()
        except Exception as e:
            print(f"  Warning: comentarios de {post_id}: {e}")
            continue

        # thread es una lista: [post listing, comments listing]
        if not isinstance(thread, list) or len(thread) < 2:
            continue
        comments_listing = thread[1]
        comment_children = (comments_listing.get("data") or {}).get("children") or []
        collected = 0
        for comment in _flatten_comments(comment_children, limit_comments_per_post or 999):
            if comment is None:
                continue
            items.append(_thing_to_review(comment, subreddit, is_post=False))
            collected += 1
            if limit_comments_per_post and collected >= limit_comments_per_post:
                break

    print(f"[OK] Obtenidos {len(items)} comentarios/posts de Reddit r/{subreddit} (scraping)")
    return items


def _flatten_comments(children: List[Any], limit: int) -> List[Dict]:
    """Extrae comentarios de forma recursiva (solo primer nivel de replies para no hacer más requests)."""
    out: List[Dict] = []
    for c in children:
        if len(out) >= limit:
            break
        data = (c.get("data") or {}) if isinstance(c, dict) else {}
        kind = c.get("kind") if isinstance(c, dict) else ""
        if kind == "t1":  # comentario
            body = (data.get("body") or "").strip()
            if body and data.get("id"):
                out.append(data)
            # Replies: pueden ser lista de comentarios o "MoreComments"
            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_children = (replies.get("data") or {}).get("children") or []
                out.extend(_flatten_comments(reply_children, limit - len(out)))
    return out


def _thing_to_review(data: Dict, subreddit: str, is_post: bool = False) -> Dict:
    """Convierte un nodo data de Reddit (post o comentario) al formato común."""
    if is_post:
        title = data.get("title") or ""
        selftext = (data.get("selftext") or "").strip()
        content = f"{title}\n{selftext}".strip() if title else selftext
    else:
        content = (data.get("body") or "").strip()
    author = data.get("author") or "Anónimo"
    if author == "[deleted]":
        author = "Anónimo"
    created = data.get("created_utc") or data.get("created") or ""
    return {
        "source": "Reddit",
        "content": content,
        "author": author,
        "date": str(created),
        "rating": None,
        "helpful_votes": str(data.get("score") or data.get("ups") or 0),
        "subreddit": subreddit,
        "post_id": data.get("id"),
        "title": data.get("title") if is_post else None,
    }


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado: {filename}")


if __name__ == "__main__":
    import sys
    sub = sys.argv[1] if len(sys.argv) > 1 else F1_SUBREDDIT
    comments = get_reddit_comments_scraper(subreddit=sub)
    if comments:
        save_comments_to_json(comments, "reviews_reddit.json")
