from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Aircraft Deal Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background:#0b0f14; color:white; margin:0; padding:20px; }
        .card { background:#1a2433; padding:15px; margin:10px 0; border-radius:10px; }
        .price { color:#00ff99; font-weight:bold; }
        .tag { background:#2b3b52; padding:3px 8px; border-radius:6px; font-size:12px; }
        a { color:#4da3ff; text-decoration:none; }
        .filters { margin-bottom:15px; }
        button { margin-right:10px; padding:8px; border-radius:8px; border:none; }
    </style>
</head>
<body>

<h2>✈ Aircraft Deal Bot</h2>

<div class="filters">
    <button onclick="load('all')">All</button>
    <button onclick="load('europa')">Europa</button>
    <button onclick="load('rotax')">Rotax</button>
    <button onclick="load('cheap')">Under £20k</button>
</div>

<div id="list"></div>

<script>
async function load(filter) {
    const res = await fetch('/data');
    const data = await res.json();

    let html = '';

    for (let item of data.items) {

        let t = item.title.toLowerCase();

        if (filter === 'europa' && !t.includes('europa')) continue;
        if (filter === 'rotax' && !(t.includes('rotax') || t.includes('912') || t.includes('914'))) continue;
        if (filter === 'cheap' && item.price && item.price > 20000) continue;

        html += `
        <div class="card">
            <div class="tag">${item.source}</div>
            <h3>${item.title}</h3>
            <div class="price">£${item.price || 'N/A'}</div>
            <a href="${item.url}" target="_blank">Open listing</a>
        </div>`;
    }

    document.getElementById('list').innerHTML = html;
}

load('all');
</script>

</body>
</html>
"""

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/data")
def data():
    raw = load_data()

    items = []

    for url, v in raw.items():
        items.append({
            "url": url,
            "title": v.get("title", "Unknown"),
            "price": v.get("price"),
            "source": v.get("source", "BOT")
        })

    return jsonify({"items": items})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)