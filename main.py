import requests
from bs4 import BeautifulSoup
import os
import json
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

DATA_FILE = "data.json"

MAX_PRICE = 3000

KEYWORDS = [
    "europa",
    "rotax",
    "aircraft",
    "microlight",
    "project",
    "kitplane",
    "airframe",
    "permit expired",
    "non flyer",
    "unfinished"
]

GOOD_WORDS = [
    "project",
    "needs",
    "unfinished",
    "non runner",
    "spares",
    "rebuild"
]

BAD_WORDS = [
    "manual",
    "plans",
    "model",
    "toy",
    "fuselage only",
    "frame only"
]

LOCAL_AREAS = [
    "rutland",
    "leicester",
    "nottingham",
    "derby",
    "northampton",
    "peterborough",
    "lincoln",
    "cambridge",
    "bedford",
    "milton keynes"
]

# ---------------- DATA ---------------- #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ---------------- TELEGRAM ---------------- #

def send_alert(msg):

    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram secrets missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=20
        )

    except Exception as e:
        print("Telegram error:", e)

# ---------------- HELPERS ---------------- #

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

# ---------------- PRICE TRACKING ---------------- #

def handle_listing(url, title, price, source, location_text):

    loc = detect_location(location_text or title)
    tag = classify(title, price)

    if url not in data:

        data[url] = {
            "price": price
        }

        save_data(data)

        send_alert(
            f"{loc} {tag} {source}\n\n"
            f"{title}\n"
            f"£{price if price else 'N/A'}\n\n"
            f"{url}"
        )

        return

    old_price = data[url].get("price")

    if (
        price and
        old_price and
        price < old_price
    ):

        drop = old_price - price
        percent = (drop / old_price) * 100

        data[url]["price"] = price

        save_data(data)

        send_alert(
            f"📉 PRICE DROP {source}\n\n"
            f"{title}\n\n"
            f"Was: £{old_price}\n"
            f"Now: £{price}\n"
            f"Drop: £{int(drop)} ({percent:.0f}%)\n\n"
            f"{url}"
        )

# ---------------- EBAY ---------------- #

def check_ebay():

    urls = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for search_url in urls:

        r = requests.get(search_url, headers=headers, timeout=30)

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
                p = float(
                    price.text
                    .replace("£", "")
                    .split()[0]
                    .replace(",", "")
                )

            except:
                continue

            if p > MAX_PRICE:
                continue

            url = link["href"]

            handle_listing(
                url,
                title.text,
                p,
                "EBAY",
                location.text if location else ""
            )

# ---------------- AFORS ---------------- #

def check_afors():

    url = "https://afors.uk/aircraft-for-sale"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)

    soup = BeautifulSoup(r.text, "html.parser")

    for item in soup.select("div.listing"):

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

        handle_listing(
            link,
            title,
            price_val,
            "AFORS",
            text
        )

# ---------------- GUMTREE ---------------- #

def check_gumtree():

    url = "https://www.gumtree.com/search?search_category=all&q=aircraft+project"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)

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

        handle_listing(
            full_link,
            title,
            None,
            "GUMTREE",
            title
        )

# ---------------- APOLLO ---------------- #

def check_apollo():

    url = "https://www.apolloduck.co.uk/aircraft-for-sale"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)

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

        handle_listing(
            link,
            title,
            None,
            "APOLLO",
            title
        )

# ---------------- GOOGLE ---------------- #

def check_google():

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        print("Google API secrets missing")
        return

    queries = [
        "aircraft project UK",
        "europa aircraft project UK",
        "rotax 912 for sale UK"
    ]

    for q in queries:

        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?q={q}"
            f"&key={GOOGLE_API_KEY}"
            f"&cx={GOOGLE_CX}"
        )

        r = requests.get(url, timeout=30)

        data_json = r.json()

        for item in data_json.get("items", []):

            title = item["title"]

            link = item["link"]

            t = title.lower()

            if not any(k in t for k in KEYWORDS):
                continue

            if not is_good(t):
                continue

            handle_listing(
                link,
                title,
                None,
                "GOOGLE",
                title
            )

# ---------------- EUROPA CLUB ---------------- #

def check_europa_club():

    url = "https://www.theeuropaclub.org/the-club/sales--member-adverts"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)

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

        handle_listing(
            url + line[:30],
            line,
            None,
            "EUROPA CLUB",
            line
        )

# ---------------- WINGLIST ---------------- #

def check_winglist():

    url = "https://www.winglist.aero/listings"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)

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

        handle_listing(
            link,
            title,
            None,
            "WINGLIST",
            title
        )

# ---------------- SAFE RUNNER ---------------- #

def safe_run(name, func):

    try:
        print(f"Running {name}")
        func()
        print(f"{name} complete")

    except Exception as e:
        print(f"{name} FAILED:", e)

# ---------------- MAIN ---------------- #

def run():

    safe_run("EBAY", check_ebay)
    safe_run("AFORS", check_afors)
    safe_run("GUMTREE", check_gumtree)
    safe_run("APOLLO", check_apollo)
    safe_run("GOOGLE", check_google)
    safe_run("EUROPA CLUB", check_europa_club)
    safe_run("WINGLIST", check_winglist)

if __name__ == "__main__":
    run()