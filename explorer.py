import re, time
from urllib.request import urlopen
from flask import Flask, request, render_template_string

RAW = "https://raw.githubusercontent.com/Trac-Systems/awesome-intercom/main/README.md"
CACHE_TTL = 300

app = Flask(__name__)
_cache = {"ts": 0, "items": []}

HTML = """
<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Intercom Explorer</title>
<style>
body{font-family:system-ui;padding:14px}
.top{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input,select{padding:10px;border:1px solid #ddd;border-radius:12px;font-size:14px}
.card{border:1px solid #eee;border-radius:14px;padding:12px;margin:10px 0}
.row{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.tag{font-size:12px;padding:4px 8px;border-radius:999px;background:#f3f3f3;display:inline-block}
.btn{padding:10px 12px;border:1px solid #ddd;border-radius:12px;background:white;text-decoration:none;display:inline-block}
.muted{color:#666;font-size:13px}
</style></head><body>
<h2>Intercom Explorer</h2>
<div class="muted">Source: awesome-intercom README · cache {{ttl}}s · total {{total}}</div>

<form class="top" method="get">
  <input name="q" value="{{q}}" placeholder="Search repo/desc (contoh: bridge, sc, swap)" style="flex:1;min-width:220px;">
  <select name="type">
    <option value="all" {% if typ=='all' %}selected{% endif %}>All</option>
    <option value="intercom" {% if typ=='intercom' %}selected{% endif %}>Intercom</option>
    <option value="swap" {% if typ=='swap' %}selected{% endif %}>IntercomSwap</option>
  </select>
  <select name="sort">
    <option value="repo" {% if sort=='repo' %}selected{% endif %}>Sort: Repo</option>
    <option value="type" {% if sort=='type' %}selected{% endif %}>Sort: Type</option>
  </select>
  <button class="btn" type="submit">Apply</button>
  <a class="btn" href="/refresh">Refresh</a>
</form>

{% for it in items %}
<div class="card">
  <div class="row">
    <div>
      <span class="tag">{{ 'Intercom' if it.kind=='intercom' else 'IntercomSwap' }}</span>
      <strong style="margin-left:8px">{{it.repo}}</strong>
    </div>
    <div><a class="btn" href="{{it.url}}" target="_blank">Open Repo</a></div>
  </div>
  <div class="muted" style="margin-top:8px">{{it.desc}}</div>
  <div class="muted" style="margin-top:6px">{{it.url}}</div>
</div>
{% endfor %}
{% if not items %}<p class="muted">Tidak ada hasil. Coba kata kunci lain.</p>{% endif %}
</body></html>
"""

def fetch_readme():
    with urlopen(RAW) as r:
        return r.read().decode("utf-8", "replace")

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
            m = re.search(r"\*\s+\[?([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\]?\((https:\/\/github\.com\/[^)]+)\)?\s*—\s*(.*)", line)
            if m:
                repo, url, desc = m.group(1), m.group(2), m.group(3).strip()
            else:
                m2 = re.search(r"\*\s+([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\s*—\s*(.*)", line)
                if not m2: 
                    continue
                repo, desc = m2.group(1), m2.group(2).strip()
                url = f"https://github.com/{repo}"
            items.append({"kind": section, "repo": repo, "url": url, "desc": desc})
    return items

def get_items(force=False):
    now = time.time()
    if (not force) and _cache["items"] and (now - _cache["ts"] < CACHE_TTL):
        return _cache["items"]
    items = parse_items(fetch_readme())
    _cache["ts"] = now
    _cache["items"] = items
    return items

@app.get("/")
def index():
    items = get_items()
    q = (request.args.get("q") or "").strip().lower()
    typ = (request.args.get("type") or "all").strip().lower()
    sort = (request.args.get("sort") or "repo").strip().lower()

    filtered = []
    for it in items:
        if typ != "all" and it["kind"] != typ: 
            continue
        if q and q not in (it["repo"] + " " + it["desc"]).lower():
            continue
        filtered.append(it)

    filtered.sort(key=lambda x: ((x["kind"], x["repo"].lower()) if sort=="type" else x["repo"].lower()))
    return render_template_string(HTML, items=filtered, q=request.args.get("q",""), typ=typ, sort=sort, total=len(items), ttl=CACHE_TTL)

@app.get("/refresh")
def refresh():
    get_items(force=True)
    return '<meta http-equiv="refresh" content="0; url=/" />Refreshed.'

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)
