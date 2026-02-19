import os, re, time, math
import requests
from flask import Flask, request, render_template

app = Flask(__name__)

RAW = "https://raw.githubusercontent.com/Trac-Systems/awesome-intercom/main/README.md"
CACHE_TTL = 300  # 5 menit
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()  # optional (naikkan rate limit)

_cache = {"ts": 0, "items": []}

def fetch_readme():
    r = requests.get(RAW, timeout=20)
    r.raise_for_status()
    return r.text

def parse_items(md: str):
    items, section = [], None
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("## Intercom Forks"):
            section = "intercom"; continue
        if s.startswith("## IntercomSwap Forks"):
            section = "swap"; continue
        if s.startswith("## ") and section:
            section = None

        if section and line.lstrip().startswith("*"):
            # * user/repo — desc (kadang pakai link markdown)
            m = re.search(r"\*\s+\[?([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\]?\((https:\/\/github\.com\/[^)]+)\)?\s*—\s*(.*)", line)
            if m:
                repo, url, desc = m.group(1), m.group(2), m.group(3).strip()
            else:
                m2 = re.search(r"\*\s+([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\s*—\s*(.*)", line)
                if not m2:
                    continue
                repo, desc = m2.group(1), m2.group(2).strip()
                url = f"https://github.com/{repo}"
            items.append({
                "kind": section,
                "repo": repo,
                "url": url,
                "desc": desc,
                "stars": None,
                "forks": None,
                "updated_at": None,
            })
    return items

def gh_headers():
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

def enrich_with_github(items, limit=60):
    """
    Ambil metadata GitHub untuk bikin UI terasa "explorer".
    Limit biar nggak kebanyakan request.
    """
    out = []
    for it in items[:limit]:
        try:
            api = f"https://api.github.com/repos/{it['repo']}"
            r = requests.get(api, headers=gh_headers(), timeout=20)
            if r.status_code == 403:
                # rate limit kena
                out.append(it); continue
            r.raise_for_status()
            j = r.json()
            it["stars"] = j.get("stargazers_count")
            it["forks"] = j.get("forks_count")
            it["updated_at"] = j.get("updated_at")
        except Exception:
            pass
        out.append(it)

    # sisanya tetap masuk (tanpa stats)
    out.extend(items[limit:])
    return out

def get_items(force=False):
    now = time.time()
    if (not force) and _cache["items"] and (now - _cache["ts"] < CACHE_TTL):
        return _cache["items"]

    md = fetch_readme()
    items = parse_items(md)
    items = enrich_with_github(items, limit=60)

    _cache["ts"] = now
    _cache["items"] = items
    return items

@app.get("/")
def index():
    items = get_items()

    q = (request.args.get("q") or "").strip().lower()
    typ = (request.args.get("type") or "all").strip().lower()
    sort = (request.args.get("sort") or "stars").strip().lower()
    page = int(request.args.get("page") or 1)
    per_page = int(request.args.get("per_page") or 15)
    per_page = max(5, min(per_page, 50))

    filtered = []
    for it in items:
        if typ != "all" and it["kind"] != typ:
            continue
        hay = (it["repo"] + " " + it["desc"]).lower()
        if q and q not in hay:
            continue
        filtered.append(it)

    def star_key(x):
        return (x["stars"] if isinstance(x["stars"], int) else -1)

    if sort == "repo":
        filtered.sort(key=lambda x: x["repo"].lower())
    elif sort == "updated":
        filtered.sort(key=lambda x: (x["updated_at"] or ""), reverse=True)
    else:  # stars default
        filtered.sort(key=star_key, reverse=True)

    total = len(filtered)
    pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    end = start + per_page
    rows = filtered[start:end]

    total_intercom = sum(1 for x in items if x["kind"] == "intercom")
    total_swap = sum(1 for x in items if x["kind"] == "swap")
    total_stars = sum(x["stars"] for x in items if isinstance(x["stars"], int))

    return render_template(
        "index.html",
        rows=rows,
        q=request.args.get("q", ""),
        typ=typ,
        sort=sort,
        page=page,
        pages=pages,
        per_page=per_page,
        total=total,
        stats=dict(
            total_repos=len(items),
            total_intercom=total_intercom,
            total_swap=total_swap,
            total_stars=total_stars
        ),
        cache_ttl=CACHE_TTL
    )

@app.get("/refresh")
def refresh():
    get_items(force=True)
    return ('<meta http-equiv="refresh" content="0; url=/" />Refreshed.')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)
