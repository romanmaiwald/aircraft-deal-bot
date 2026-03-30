import requests
from bs4 import BeautifulSoup
import time
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"

KEYWORDS = ["europa", "rotax", "aircraft", "microlight", "project"]
GOOD_WORDS = ["project", "needs", "unfinished", "non runner", "spares"]
BAD_WORDS = ["manual", "plans", "model", "toy"]

MAX_PRICE = 2000

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen = load_seen()

def send_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def is_good(title):
    t = title.lower()

    if any(b in t for b in BAD_WORDS):
        return False

    score = sum(1 for g in GOOD_WORDS if g in t)
    return score >= 1

def check_ebay(search_url):
    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".s-item")

    for item in items:
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one("a")

        if not title or not price:
            continue

        title_text = title.text.lower()

        if not any(k in title_text for k in KEYWORDS):
            continue

        if not is_good(title_text):
            continue

        price_text = price.text.replace("£", "").split()[0]

        try:
            price_val = float(price_text.replace(",", ""))
        except:
            continue

        if price_val > MAX_PRICE:
            continue

        url = link["href"]

        if url in seen:
            continue

        seen.add(url)
        save_seen(seen)

        urgency = "🔥🔥" if price_val < 1000 else "🔥"
        send_alert(f"""{urgency} DEAL FOUND\n\n{title.text}\n£{price_val}\n{url}\n""")

def run():
    send_alert("🚀 TEST MESSAGE FROM RAILWAY")

run()