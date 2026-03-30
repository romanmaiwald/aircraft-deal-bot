import requests
from bs4 import BeautifulSoup
import time
import os
import json
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

SEEN_FILE = "seen.json"

MAX_PRICE = 2000

KEYWORDS = ["europa", "rotax", "aircraft", "microlight", "project"]

GOOD_WORDS = ["project", "needs", "unfinished", "non runner", "spares"]
BAD_WORDS = ["manual", "plans", "model", "toy"]

LOCAL_AREAS = [
    "rutland","leicester","nottingham","derby",
    "northampton","peterborough","lincoln",
    "cambridge","bedford","milton keynes"
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

def detect_location(text):
    t = text.lower()
    for area in LOCAL_AREAS:
        if area in t:
            return "📍 LOCAL"
    return "🌍 UK"

def extract_price(text):
    match = re.search(r'£\s?([0-9,]+)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

# ---------------- EBAY ---------------- #

def check_ebay():
    urls = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10"
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for search_url in urls:
        r = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select(".s-item"):
            title = item.select_one(".s-item__title")
            price = item.select_one(".s-item__price")
            link = item.select_one("a")
            location = item.select_one(".s-item__location")

            if not title or not price or not link:
                continue

            t = title.text.lower()

            if not any(k in t for k in KEYWORDS):
                continue
            if not is_good(t):
                continue

            try:
                p = float(price.text.replace("£","").split()[0].replace(",",""))
            except:
                continue

            if p > MAX_PRICE:
                continue

            url = link["href"]
            if url in seen:
                continue

            seen.add(url)
            save_seen(seen)

            loc = detect_location(location.text if location else t)
            tag = classify(t, p)

            send_alert(f"{loc} {tag} EBAY\n{title.text}\n£{p}\n{url}")

# ---------------- GUMTREE ---------------- #

def check_gumtree():
    url = "https://www.gumtree.com/search?search_category=all&q=aircraft+project"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for item in soup.select("a[href*='/p/']"):
        title = item.text.strip()
        link = item.get("href")

        if not title:
            continue

        t = title.lower()

        if not any(k in t for k in KEYWORDS):
            continue
        if not is_good(t):
            continue

        full_link = "https://www.gumtree.com" + link

        if full_link in seen:
            continue

        seen.add(full_link)
        save_seen(seen)

        loc = detect_location(title)
        tag = classify(title, None)

        send_alert(f"{loc} {tag} GUMTREE\n{title}\n{full_link}")

# ---------------- APOLLO DUCK ---------------- #

def check_apollo():
    url = "https://www.apolloduck.co.uk/aircraft-for-sale"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for item in soup.select("a"):
        title = item.text.strip()
        link = item.get("href")

        if not title or not link:
            continue

        t = title.lower()

        if not any(k in t for k in KEYWORDS):
            continue
        if not is_good(t):
            continue

        if link.startswith("/"):
            link = "https://www.apolloduck.co.uk" + link

        if link in seen:
            continue

        seen.add(link)
        save_seen(seen)

        loc = detect_location(title)
        tag = classify(title, None)

        send_alert(f"{loc} {tag} APOLLO\n{title}\n{link}")

# ---------------- PLANE SELLING ---------------- #

def check_planeselling():
    url = "https://www.planeselling.co.uk"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for item in soup.find_all("a"):
        title = item.text.strip()
        link = item.get("href")

        if not title or not link:
            continue

        t = title.lower()

        if not any(k in t for k in KEYWORDS):
            continue
        if not is_good(t):
            continue

        if link.startswith("/"):
            link = "https://www.planeselling.co.uk" + link

        if link in seen:
            continue

        seen.add(link)
        save_seen(seen)

        loc = detect_location(title)
        tag = classify(title, None)

        send_alert(f"{loc} {tag} PLANESELLING\n{title}\n{link}")

# ---------------- GOOGLE API ---------------- #

def check_google():
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return

    queries = [
        "aircraft project UK",
        "europa aircraft project UK",
        "rotax 912 for sale UK"
    ]

    for q in queries:
        url = f"https://www.googleapis.com/customsearch/v1?q={q}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"

        r = requests.get(url)
        data = r.json()

        for item in data.get("items", []):
            title = item["title"]
            link = item["link"]

            t = title.lower()

            if not any(k in t for k in KEYWORDS):
                continue
            if not is_good(t):
                continue

            if link in seen:
                continue

            seen.add(link)
            save_seen(seen)

            loc = detect_location(title)
            tag = classify(title, None)

            send_alert(f"{loc} {tag} GOOGLE\n{title}\n{link}")

# ---------------- MAIN ---------------- #

def run():
    send_alert("🚀 FULL DEAL BOT LIVE (ALL SOURCES)")

    while True:
        try: check_ebay()
        except Exception as e: print("EBAY:", e)

        try: check_gumtree()
        except Exception as e: print("GUMTREE:", e)

        try: check_apollo()
        except Exception as e: print("APOLLO:", e)

        try: check_planeselling()
        except Exception as e: print("PLANE:", e)

        try: check_google()
        except Exception as e: print("GOOGLE:", e)

        time.sleep(600)

run()