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

MAX_PRICE = 3000

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

        t = title.lower()

        if not any(k in t for k in KEYWORDS):
            continue
        if not is_good(t):
            continue

        price_val = extract_price(text)
        if price_val and price_val > MAX_PRICE:
            continue

        if link in seen:
            continue

        seen.add(link)
        save_seen(seen)

        loc = detect_location(text)
        tag = classify(title, price_val if price_val else 1500)

        price_text = f"£{price_val}" if price_val else "Price unknown"

        send_alert(f"{loc} {tag} AFORS\n{title}\n{price_text}\n{link}")

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

# ---------------- FACEBOOK ---------------- #

def check_facebook():
    url = "https://www.facebook.com/marketplace/search/?query=aircraft%20project"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)

    if "login" in r.url.lower():
        return

    soup = BeautifulSoup(r.text, "html.parser")

    for link_tag in soup.find_all("a", href=True):
        href = link_tag["href"]

        if not any(x in href for x in ["/marketplace/item/", "/groups/", "/share/"]):
            continue

        full_link = "https://www.facebook.com" + href

        if full_link in seen:
            continue

        text = (link_tag.text or "").lower()

        if not text:
            text = href.lower()

        if not any(k in text for k in KEYWORDS):
            continue

        seen.add(full_link)
        save_seen(seen)

        loc = detect_location(text)

        send_alert(f"{loc} 📘 FACEBOOK\n{text}\n{full_link}")
        
# ---------------- GOOGLE ---------------- #

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

# ---------------- EUROPA CLUB ---------------- #

def check_europa_club():
    url = "https://www.theeuropaclub.org/the-club/sales--member-adverts"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    lines = soup.get_text("\n").split("\n")

    for line in lines:
        line = line.strip()

        if len(line) < 20:
            continue

        t = line.lower()

        if not any(k in t for k in KEYWORDS):
            continue
        if not is_good(t):
            continue

        if line in seen:
            continue

        seen.add(line)
        save_seen(seen)

        loc = detect_location(line)

        send_alert(f"{loc} 🚨 EUROPA CLUB\n{line}\n{url}")

# ---------------- WINGLIST ---------------- #

def check_winglist():
    url = "https://www.winglist.aero/listings"
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
            link = "https://www.winglist.aero" + link

        if link in seen:
            continue

        seen.add(link)
        save_seen(seen)

        loc = detect_location(title)
        tag = classify(title, None)

        send_alert(f"{loc} {tag} WINGLIST\n{title}\n{link}")

# ---------------- MAIN ---------------- #

def run():
    send_alert("🚀 DEAL BOT FULLY LIVE (ALL SOURCES)")

    while True:
        try: check_ebay()
        except Exception as e: print("EBAY:", e)

        try: check_afors()
        except Exception as e: print("AFORS:", e)

        try: check_gumtree()
        except Exception as e: print("GUMTREE:", e)

        try: check_apollo()
        except Exception as e: print("APOLLO:", e)

        try: check_planeselling()
        except Exception as e: print("PLANE:", e)

        try: check_facebook()
        except Exception as e: print("FACEBOOK:", e)

        try: check_google()
        except Exception as e: print("GOOGLE:", e)

        try: check_europa_club()
        except Exception as e: print("EUROPA:", e)

        try: check_winglist()
        except Exception as e: print("WINGLIST:", e)

        time.sleep(600)

run()