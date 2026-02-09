"""Comentarios y posts de Reddit vía PRAW (API oficial de Reddit, gratuita)."""
import os
import json
from typing import List, Dict, Optional

F1_SUBREDDIT = "F1movie"


def get_reddit_comments_praw(
    subreddit: str = F1_SUBREDDIT,
    limit_posts: int = 50,
    limit_comments_per_post: Optional[int] = 200,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> List[Dict]:
    """
    Obtiene posts y comentarios de un subreddit usando PRAW.
    Necesitas crear una app en https://www.reddit.com/prefs/apps (tipo "script").
    """
    try:
        import praw
    except ImportError:
        print("⚠ Instala PRAW: pip install praw")
        return []

    cid = client_id or os.environ.get("REDDIT_CLIENT_ID")
    secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
    ua = user_agent or os.environ.get("REDDIT_USER_AGENT", "analitica_social_f1/1.0")

    if not cid or not secret:
        print("⚠ Configura REDDIT_CLIENT_ID y REDDIT_CLIENT_SECRET (crea una app en reddit.com/prefs/apps)")
        return []

    reddit = praw.Reddit(
        client_id=cid,
        client_secret=secret,
        user_agent=ua,
    )
    items: List[Dict] = []

    try:
        sub = reddit.subreddit(subreddit)
        # Posts recientes / populares (mezcla hot + new para más contenido)
        for submission in sub.hot(limit=limit_posts):
            # Incluir el texto del post si tiene contenido
            post_body = (getattr(submission, "selftext", None) or "").strip()
            if post_body:
                items.append(_submission_to_review(submission, subreddit, is_post=True))
            # Comentarios del post
            try:
                submission.comment_sort = "top"
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list()[: (limit_comments_per_post or 999)]:
                    if getattr(comment, "body", None) and comment.body.strip():
                        items.append(_comment_to_review(comment, subreddit))
            except Exception:
                continue

        # Añadir también posts "new" para más variedad (evitar duplicados por id)
        seen_ids = {r.get("post_id") for r in items if r.get("post_id")}
        for submission in sub.new(limit=min(25, limit_posts)):
            if submission.id in seen_ids:
                continue
            post_body = (getattr(submission, "selftext", None) or "").strip()
            if post_body:
                items.append(_submission_to_review(submission, subreddit, is_post=True))
            try:
                submission.comment_sort = "top"
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list()[: (limit_comments_per_post or 999)]:
                    if getattr(comment, "body", None) and comment.body.strip():
                        items.append(_comment_to_review(comment, subreddit))
            except Exception:
                continue

        print(f"✓ Obtenidos {len(items)} comentarios/posts de Reddit r/{subreddit} (PRAW)")
        return items
    except Exception as e:
        print(f"Error Reddit PRAW: {e}")
        return []


def _submission_to_review(submission, subreddit: str, is_post: bool = True) -> Dict:
    """Convierte un Submission de PRAW al formato común de review."""
    title = getattr(submission, "title", None) or ""
    body = (getattr(submission, "selftext", None) or "").strip()
    content = f"{title}\n{body}".strip() if title else body
    author = "Anónimo"
    if getattr(submission, "author", None) and submission.author:
        author = getattr(submission.author, "name", None) or str(submission.author)
    created = getattr(submission, "created_utc", None) or getattr(submission, "created", None) or ""
    return {
        "source": "Reddit",
        "content": content,
        "author": author,
        "date": str(created),
        "rating": None,
        "helpful_votes": str(getattr(submission, "score", 0) or 0),
        "subreddit": subreddit,
        "post_id": getattr(submission, "id", None),
        "title": title,
    }


def _comment_to_review(comment, subreddit: str) -> Dict:
    """Convierte un Comment de PRAW al formato común de review."""
    body = (getattr(comment, "body", None) or "").strip()
    author = "Anónimo"
    if getattr(comment, "author", None) and comment.author:
        author = getattr(comment.author, "name", None) or str(comment.author)
    created = getattr(comment, "created_utc", None) or getattr(comment, "created", None) or ""
    return {
        "source": "Reddit",
        "content": body,
        "author": author,
        "date": str(created),
        "rating": None,
        "helpful_votes": str(getattr(comment, "score", 0) or 0),
        "subreddit": subreddit,
        "post_id": getattr(comment, "id", None),
        "title": None,
    }


def save_comments_to_json(comments: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"✓ Guardado: {filename}")


if __name__ == "__main__":
    import sys
    sub = sys.argv[1] if len(sys.argv) > 1 else F1_SUBREDDIT
    comments = get_reddit_comments_praw(subreddit=sub)
    if comments:
        save_comments_to_json(comments, "reviews_reddit.json")
