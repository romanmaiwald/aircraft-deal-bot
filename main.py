import requests
from bs4 import BeautifulSoup
import time
import os
import json
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"

MAX_PRICE = 2000

KEYWORDS = ["europa", "rotax", "aircraft", "microlight", "project"]

GOOD_WORDS = ["project", "needs", "unfinished", "non runner", "spares"]
BAD_WORDS = ["manual", "plans", "model", "toy"]

# Rough "local" area keywords (expandable)
LOCAL_AREAS = [
    "rutland", "leicester", "nottingham", "derby",
    "northampton", "peterborough", "lincoln",
    "cambridge", "bedford", "milton keynes"
]

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

    return any(g in t for g in GOOD_WORDS)

def classify(title, price):
    t = title.lower()

    if "europa" in t:
        return "🚨 EUROPA"
    elif "rotax" in t:
        return "⚙️ ROTAX"
    elif price and price < 1000:
        return "🔥🔥"
    else:
        return "🔥"

def extract_price(text):
    match = re.search(r'£\s?([0-9,]+)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

def detect_location(text):
    t = text.lower()
    for area in LOCAL_AREAS:
        if area in t:
            return "📍 LOCAL"
    return "🌍 UK"

# ---------------- EBAY ---------------- #

def check_ebay(search_url):
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".s-item")

    for item in items:
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one("a")
        location = item.select_one(".s-item__location")

        if not title or not price or not link:
            continue

        title_text = title.text.lower()

        if not any(k in title_text for k in KEYWORDS):
            continue

        if not is_good(title_text):
            continue

        try:
            price_val = float(price.text.replace("£", "").split()[0].replace(",", ""))
        except:
            continue

        if price_val > MAX_PRICE:
            continue

        url = link["href"]

        if url in seen:
            continue

        seen.add(url)
        save_seen(seen)

        location_text = location.text if location else title.text
        loc_tag = detect_location(location_text)

        tag = classify(title.text, price_val)

        send_alert(f"""{loc_tag} {tag} EBAY DEAL

{title.text}
£{price_val}
{url}
""")

# ---------------- AFORS ---------------- #

def check_afors():
    url = "https://afors.uk/aircraft-for-sale"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    listings = soup.select("div.listing")

    for item in listings:
        text = item.get_text(" ", strip=True)
        link_tag = item.find("a", href=True)

        if not link_tag:
            continue

        title = link_tag.text.strip()
        link = "https://afors.uk" + link_tag["href"]

        title_lower = title.lower()

        if not any(k in title_lower for k in KEYWORDS):
            continue

        if not is_good(title_lower):
            continue

        price_val = extract_price(text)

        if price_val and price_val > MAX_PRICE:
            continue

        if link in seen:
            continue

        seen.add(link)
        save_seen(seen)

        loc_tag = detect_location(text)
        tag = classify(title, price_val if price_val else 1500)

        price_text = f"£{price_val}" if price_val else "Price unknown"

        send_alert(f"""{loc_tag} {tag} AFORS DEAL

{title}
{price_text}
{link}
""")

# ---------------- FACEBOOK ---------------- #

def check_facebook():
    url = "https://www.facebook.com/marketplace/search/?query=aircraft%20project"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)

    if "login" in r.url.lower():
        return

    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    for link_tag in links:
        href = link_tag["href"]

        if "/marketplace/item/" not in href:
            continue

        full_link = "https://www.facebook.com" + href

        if full_link in seen:
            continue

        text = link_tag.text.lower()

        if not any(k in text for k in KEYWORDS):
            continue

        if not is_good(text):
            continue

        seen.add(full_link)
        save_seen(seen)

        loc_tag = detect_location(text)

        send_alert(f"""{loc_tag} 📘 FACEBOOK DEAL

{text}
{full_link}
""")

# ---------------- MAIN ---------------- #

def run():
    send_alert("✅ Aircraft deal bot with LOCATION filtering LIVE")

    ebay_searches = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10"
    ]

    while True:
        for s in ebay_searches:
            try:
                check_ebay(s)
            except Exception as e:
                print("EBAY error:", e)

        try:
            check_afors()
        except Exception as e:
            print("AFORS error:", e)

        try:
            check_facebook()
        except Exception as e:
            print("FB error:", e)

        time.sleep(600)

run()