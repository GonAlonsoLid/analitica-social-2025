"""Scrapers para IMDB, Rotten Tomatoes, Instagram, Reddit y YouTube."""

from src.scrapers.imdb import get_imdb_reviews, save_reviews_to_json as save_imdb
from src.scrapers.rottentomatoes import (
    get_rottentomatoes_reviews,
    save_reviews_to_json as save_rt,
)
from src.scrapers.instagram_steady import (
    get_instagram_comments,
    save_comments_to_json as save_instagram,
    F1_POST_SHORTCODE,
)
from src.scrapers.reddit_steady import (
    get_reddit_comments,
    save_comments_to_json as save_reddit,
    F1_SUBREDDIT,
)
from src.scrapers.youtube import (
    get_youtube_comments,
    save_comments_to_json as save_youtube,
    F1_VIDEO_ID,
)

__all__ = [
    "get_imdb_reviews",
    "save_imdb",
    "get_rottentomatoes_reviews",
    "save_rt",
    "get_instagram_comments",
    "save_instagram",
    "F1_POST_SHORTCODE",
    "get_reddit_comments",
    "save_reddit",
    "F1_SUBREDDIT",
    "get_youtube_comments",
    "save_youtube",
    "F1_VIDEO_ID",
]
