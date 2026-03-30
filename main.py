import requests
from bs4 import BeautifulSoup
import time
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"

KEYWORDS = ["europa", "rotax", "aircraft", "microlight", "project"]

MAX_PRICE = 5000  # loosened for testing

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

def check_ebay(search_url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".s-item")

    for item in items:
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one("a")

        if not title or not price or not link:
            continue

        title_text = title.text.lower()

        if not any(k in title_text for k in KEYWORDS):
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

        message = f"""{urgency} DEAL FOUND

{title.text}
£{price_val}
{url}
"""

        send_alert(message)

def run():
    send_alert("✅ Aircraft deal bot is LIVE")

    searches = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10"
    ]

    while True:
        for s in searches:
            try:
                check_ebay(s)
            except Exception as e:
                print("Error:", e)

        time.sleep(600)

run()