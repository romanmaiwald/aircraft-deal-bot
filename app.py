from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"
HIDDEN_FILE = "hidden.json"

# ---------------- DATA ---------------- #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def load_hidden():
    if os.path.exists(HIDDEN_FILE):
        with open(HIDDEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_hidden(hidden):
    with open(HIDDEN_FILE, "w") as f:
        json.dump(list(hidden), f)

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
            display:inline-block;
            margin-bottom:8px;
        }

        a, button {
            margin-right:10px;
        }

        button {
            padding:6px 10px;
            border-radius:6px;
            border:none;
            cursor:pointer;
        }

        .hide-btn {
            background:#ff4d4d;
            color:white;
        }

        .open-btn {
            background:#4da3ff;
            color:white;
        }

        .topbar {
            margin-bottom:15px;
        }
    </style>
</head>

<body>

<h2>✈ Aircraft Deal Bot</h2>

<div class="topbar">
    <button onclick="loadData()">Refresh</button>
</div>

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

            <a class="open-btn" href="${item.url}" target="_blank">Open</a>

            <button class="hide-btn" onclick="hideItem('${item.url}')">
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
    data_req = request.get_json()
    url = data_req.get("url")

    if not url:
        return {"ok": False}

    hidden = load_hidden()
    hidden.add(url)
    save_hidden(hidden)

    return {"ok": True}

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)