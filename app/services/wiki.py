"""Wikipedia helper — totally free, no API key needed."""
import requests
from urllib.parse import quote
from flask import current_app

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_HTML_BASE = "https://en.wikipedia.org/wiki/"


def _headers():
    return {"User-Agent": current_app.config.get("WIKI_USER_AGENT",
                                                  "AetherAI/1.0")}


def search(query, limit=5):
    """Return a list of {title, snippet, url} results from Wikipedia."""
    try:
        params = {
            "action": "query", "list": "search", "srsearch": query,
            "format": "json", "srlimit": limit, "utf8": 1,
        }
        r = requests.get(WIKI_API, params=params, headers=_headers(), timeout=8)
        r.raise_for_status()
        data = r.json().get("query", {}).get("search", [])
        results = []
        for hit in data:
            title = hit.get("title", "")
            snippet = (hit.get("snippet", "")
                       .replace('<span class="searchmatch">', "")
                       .replace("</span>", ""))
            results.append({
                "title": title,
                "snippet": snippet,
                "url": WIKI_HTML_BASE + quote(title.replace(" ", "_")),
            })
        return results
    except Exception as e:
        return [{"title": "Wikipedia error", "snippet": str(e), "url": "#"}]


def summary(title):
    """Return a clean dict {title, extract, url, thumbnail} for a Wikipedia page."""
    try:
        r = requests.get(WIKI_SUMMARY + quote(title.replace(" ", "_")),
                         headers=_headers(), timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        return {
            "title": d.get("title", title),
            "extract": d.get("extract", ""),
            "url": d.get("content_urls", {}).get("desktop", {}).get("page",
                   WIKI_HTML_BASE + quote(title.replace(" ", "_"))),
            "thumbnail": (d.get("thumbnail") or {}).get("source"),
            "description": d.get("description", ""),
        }
    except Exception:
        return None


def context_for(topic, max_chars=2000):
    """Return a plain-text factual blurb about `topic` to feed the AI."""
    s = summary(topic)
    if s and s.get("extract"):
        return s["extract"][:max_chars]
    hits = search(topic, limit=1)
    if hits and hits[0].get("title") and hits[0]["title"] != "Wikipedia error":
        s = summary(hits[0]["title"])
        if s and s.get("extract"):
            return s["extract"][:max_chars]
    return ""