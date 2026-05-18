from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"
HIDDEN_FILE = "hidden.json"

# ---------------- SAFE FILE HANDLING ---------------- #

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

# ensure file exists at startup
if not os.path.exists(HIDDEN_FILE):
    save_hidden(set())

# ---------------- UI ---------------- #

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Aircraft Deal Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        body { font-family: Arial; background:#0b0f14; color:white; margin:0; padding:20px; }

        .card {
            background:#1a2433;
            padding:15px;
            margin:10px 0;
            border-radius:10px;
        }

        .price { color:#00ff99; font-weight:bold; }

        .tag {
            background:#2b3b52;
            padding:3px 8px;
            border-radius:6px;
            font-size:12px;
        }

        button {
            padding:6px 10px;
            border-radius:6px;
            border:none;
            margin-right:8px;
            cursor:pointer;
        }

        .hide { background:#ff4d4d; color:white; }
        .open { background:#4da3ff; color:white; }
    </style>
</head>

<body>

<h2>✈ Aircraft Deal Bot</h2>

<button onclick="loadData()">Refresh</button>

<div id="list"></div>

<script>

async function loadData() {
    const res = await fetch('/data');
    const data = await res.json();

    let html = '';

    for (let item of data.items) {

        html += `
        <div class="card">
            <div class="tag">${item.source}</div>
            <h3>${item.title}</h3>
            <div class="price">£${item.price || 'N/A'}</div>

            <button class="open" onclick="window.open('${item.url}')">
                Open
            </button>

            <button class="hide" onclick="hideItem('${item.url}')">
                Hide
            </button>
        </div>`;
    }

    document.getElementById('list').innerHTML = html;
}

async function hideItem(url) {
    await fetch('/hide', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url})
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

    items = []

    for url, v in raw.items():
        if url in hidden:
            continue

        items.append({
            "url": url,
            "title": v.get("title", "Unknown"),
            "price": v.get("price"),
            "source": v.get("source", "BOT")
        })

    return jsonify({"items": items})

@app.route("/hide", methods=["POST"])
def hide():
    req = request.get_json()
    url = req.get("url")

    if not url:
        return {"ok": False}

    hidden = load_hidden()
    hidden.add(url)
    save_hidden(hidden)

    return {"ok": True}

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)