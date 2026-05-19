from flask import Flask, render_template_string, request, jsonify
import json
import os
import requests
import base64

app = Flask(__name__)

# ---------------- CONFIG ---------------- #

DATA_FILE = "data.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

HIDDEN_FILE = "hidden.json"
WATCHLIST_FILE = "watchlist.json"

# ---------------- GITHUB STORAGE ---------------- #

def github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def github_get_file(path, default):

    try:

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"

        r = requests.get(url, headers=github_headers())

        if r.status_code != 200:
            return default

        data = r.json()

        content = base64.b64decode(data["content"]).decode()

        return json.loads(content)

    except:
        return default

def github_save_file(path, content_data):

    try:

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"

        # get existing SHA if file exists
        r = requests.get(url, headers=github_headers())

        sha = None

        if r.status_code == 200:
            sha = r.json()["sha"]

        content_encoded = base64.b64encode(
            json.dumps(content_data, indent=2).encode()
        ).decode()

        payload = {
            "message": f"update {path}",
            "content": content_encoded
        }

        if sha:
            payload["sha"] = sha

        requests.put(
            url,
            headers=github_headers(),
            json=payload
        )

    except Exception as e:
        print("GitHub save error:", e)

# ---------------- LOCAL DATA ---------------- #

def load_data():

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
    except:
        pass

    return {}

def load_hidden():
    return set(github_get_file(HIDDEN_FILE, []))

def save_hidden(hidden):
    github_save_file(HIDDEN_FILE, list(hidden))

def load_watchlist():
    return set(github_get_file(WATCHLIST_FILE, []))

def save_watchlist(w):
    github_save_file(WATCHLIST_FILE, list(w))

# ---------------- UI ---------------- #

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aircraft Deal Bot</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

body{
    font-family:Arial;
    background:#0b0f14;
    color:white;
    padding:20px;
}

.card{
    background:#1a2433;
    padding:15px;
    margin-bottom:12px;
    border-radius:10px;
}

.price{
    color:#00ff99;
    font-weight:bold;
}

.tag{
    background:#2b3b52;
    display:inline-block;
    padding:3px 8px;
    border-radius:6px;
    font-size:12px;
    margin-bottom:8px;
}

button{
    padding:7px 12px;
    border:none;
    border-radius:6px;
    margin:3px;
    cursor:pointer;
}

.open{background:#4da3ff;color:white;}
.hide{background:#ff4d4d;color:white;}
.watch{background:#ffaa00;color:black;}

.drop{
    color:#ff8080;
    font-weight:bold;
}

.toolbar{
    margin-bottom:20px;
}

</style>
</head>

<body>

<h2>✈ Aircraft Deal Bot</h2>

<div class="toolbar">

<button onclick="setFilter('all')">All</button>
<button onclick="setFilter('europa')">Europa</button>
<button onclick="setFilter('rotax')">Rotax</button>
<button onclick="setFilter('cheap')">Under £20k</button>
<button onclick="setFilter('watchlist')">Watchlist</button>
<button onclick="showHidden()">Hidden</button>

</div>

<div id="list"></div>

<script>

let currentFilter = 'all';

function setFilter(f){
    currentFilter = f;
    loadData();
}

async function loadData(){

    const res = await fetch('/data');
    const data = await res.json();

    let html = '';

    for(let item of data.items){

        let t = item.title.toLowerCase();

        if(currentFilter === 'europa' &&
           !t.includes('europa'))
            continue;

        if(currentFilter === 'rotax' &&
           !(t.includes('rotax') ||
             t.includes('912') ||
             t.includes('914')))
            continue;

        if(currentFilter === 'cheap' &&
           item.price &&
           item.price > 20000)
            continue;

        if(currentFilter === 'watchlist' &&
           !item.watchlisted)
            continue;

        html += `
        <div class="card">

            <div class="tag">${item.source}</div>

            <h3>${item.title}</h3>

            <div class="price">
                £${item.price || 'N/A'}
            </div>

            ${item.price_drop ?
                '<div class="drop">📉 PRICE DROP</div>' : ''}

            <br><br>

            <button class="open"
                onclick="window.open('${item.url}')">
                Open
            </button>

            <button class="hide"
                onclick="hideItem('${item.url}')">
                Hide
            </button>

            <button class="watch"
                onclick="toggleWatch('${item.url}')">

                ${item.watchlisted ? 'Unwatch' : 'Watch'}

            </button>

        </div>`;
    }

    document.getElementById('list').innerHTML = html;
}

async function hideItem(url){

    await fetch('/hide',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url})
    });

    loadData();
}

async function toggleWatch(url){

    await fetch('/watch',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url})
    });

    loadData();
}

async function showHidden(){

    const res = await fetch('/hidden');
    const data = await res.json();

    let html = '<h3>Hidden Listings</h3>';

    for(let item of data.items){

        html += `
        <div class="card">

            <h3>${item.title}</h3>

            <button onclick="restoreItem('${item.url}')">
                Restore
            </button>

        </div>`;
    }

    document.getElementById('list').innerHTML = html;
}

async function restoreItem(url){

    await fetch('/restore',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url})
    });

    loadData();
}

loadData();

</script>

</body>
</html>
"""

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/data")
def data():

    raw = load_data()

    hidden = load_hidden()
    watchlist = load_watchlist()

    items = []

    for url, v in raw.items():

        if url in hidden:
            continue

        items.append({
            "url": url,
            "title": v.get("title", "Unknown"),
            "price": v.get("price"),
            "source": v.get("source", "BOT"),
            "price_drop": v.get("price_drop", False),
            "watchlisted": url in watchlist
        })

    items.reverse()

    return jsonify({"items": items})

@app.route("/hide", methods=["POST"])
def hide():

    req = request.get_json()

    url = req.get("url")

    hidden = load_hidden()

    hidden.add(url)

    save_hidden(hidden)

    return {"ok": True}

@app.route("/restore", methods=["POST"])
def restore():

    req = request.get_json()

    url = req.get("url")

    hidden = load_hidden()

    if url in hidden:
        hidden.remove(url)

    save_hidden(hidden)

    return {"ok": True}

@app.route("/hidden")
def hidden():

    raw = load_data()

    hidden = load_hidden()

    items = []

    for url in hidden:

        if url in raw:

            items.append({
                "url": url,
                "title": raw[url].get("title", "Unknown")
            })

    return jsonify({"items": items})

@app.route("/watch", methods=["POST"])
def watch():

    req = request.get_json()

    url = req.get("url")

    w = load_watchlist()

    if url in w:
        w.remove(url)
    else:
        w.add(url)

    save_watchlist(w)

    return {"ok": True}

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)