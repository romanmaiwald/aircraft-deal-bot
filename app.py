from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"
HIDDEN_FILE = "hidden.json"
WATCHLIST_FILE = "watchlist.json"

# ---------------- SAFE JSON ---------------- #

def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except:
        pass
    return default

def safe_save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except:
        pass

def load_data():
    return safe_load_json(DATA_FILE, {})

def load_hidden():
    return set(safe_load_json(HIDDEN_FILE, []))

def save_hidden(hidden):
    safe_save_json(HIDDEN_FILE, list(hidden))

def load_watchlist():
    return set(safe_load_json(WATCHLIST_FILE, []))

def save_watchlist(w):
    safe_save_json(WATCHLIST_FILE, list(w))

# auto-create files
for f in [HIDDEN_FILE, WATCHLIST_FILE]:
    if not os.path.exists(f):
        safe_save_json(f, [])

# ---------------- UI ---------------- #

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Aircraft Deal Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

body {
    font-family: Arial;
    background:#0b0f14;
    color:white;
    margin:0;
    padding:20px;
}

.card {
    background:#1a2433;
    padding:15px;
    margin:10px 0;
    border-radius:10px;
}

.price {
    color:#00ff99;
    font-weight:bold;
}

.tag {
    background:#2b3b52;
    padding:3px 8px;
    border-radius:6px;
    font-size:12px;
    display:inline-block;
    margin-bottom:8px;
}

button {
    padding:6px 10px;
    border:none;
    border-radius:6px;
    margin:3px;
    cursor:pointer;
}

.open { background:#4da3ff; color:white; }
.hide { background:#ff4d4d; color:white; }
.watch { background:#ffaa00; color:black; }

.toolbar {
    margin-bottom:20px;
}

.drop {
    color:#ff8080;
    font-weight:bold;
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

function setFilter(f) {
    currentFilter = f;
    loadData();
}

async function loadData() {

    const res = await fetch('/data');
    const data = await res.json();

    let html = '';

    for (let item of data.items) {

        let t = item.title.toLowerCase();

        if (currentFilter === 'europa' && !t.includes('europa'))
            continue;

        if (currentFilter === 'rotax' &&
            !(t.includes('rotax') || t.includes('912') || t.includes('914')))
            continue;

        if (currentFilter === 'cheap' &&
            item.price &&
            item.price > 20000)
            continue;

        if (currentFilter === 'watchlist' &&
            !item.watchlisted)
            continue;

        html += `
        <div class="card">

            <div class="tag">${item.source}</div>

            <h3>${item.title}</h3>

            <div class="price">
                £${item.price || 'N/A'}
            </div>

            ${item.price_drop ? '<div class="drop">📉 PRICE DROP</div>' : ''}

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

async function hideItem(url) {

    await fetch('/hide', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url})
    });

    loadData();
}

async function toggleWatch(url) {

    await fetch('/watch', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url})
    });

    loadData();
}

async function showHidden() {

    const res = await fetch('/hidden');
    const data = await res.json();

    let html = '<h3>Hidden Listings</h3>';

    for (let item of data.items) {

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

async function restoreItem(url) {

    await fetch('/restore', {
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