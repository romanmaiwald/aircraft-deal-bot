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

MAX_PRICE = 20000

KEYWORDS = [
    "europa",
    "rotax",
    "912",
    "914",
    "jabiru",
    "aircraft",
    "kit aircraft",
    "microlight",
    "homebuilt",
    "experimental",
    "project",
    "kitplane",
    "unfinished",
    "part built",
    "permit expired",
    "barn find",
    "non flyer",
    "rebuild",
    "airframe",
    "aircraft parts"
]

GOOD_WORDS = [
    "project",
    "unfinished",
    "rebuild",
    "spares",
    "non flyer",
    "permit expired",
    "airframe",
    "part built",
    "kit",
    "needs work",
    "repair",
    "damage",
    "dismantled",
    "stored",
    "engine less",
    "incomplete"
]

BAD_WORDS = [
    "manual",
    "plans only",
    "model aircraft",
    "rc plane",
    "radio control",
    "poster",
    "dvd",
    "book",
    "toy",
    "simulator",
    "flight sim"
]

LOCAL_AREAS = [
    "luton",
    "bedford",
    "milton keynes",
    "northampton",
    "cambridge",
    "peterborough",
    "leicester",
    "nottingham",
    "derby",
    "lincoln",
    "oxford",
    "coventry"
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

def is_relevant(title):

    t = title.lower()

    # reject junk
    if any(b in t for b in BAD_WORDS):
        return False

    # ANY europa listing
    if "europa" in t:
        return True

    # ANY rotax listing
    if "rotax" in t or "912" in t or "914" in t:
        return True

    # project keywords
    if any(g in t for g in GOOD_WORDS):
        return True

    return any(k in t for k in KEYWORDS)

def classify(title, price):

    t = title.lower()

    if "europa" in t:
        return "🚨 EUROPA"

    if "rotax" in t or "912" in t or "914" in t:
        return "⚙️ ROTAX"

    if price and price < 3000:
        return "🔥 CHEAP"

    if price and price < 7000:
        return "🔥 PROJECT"

    return "✈️ AIRCRAFT"

def detect_location(text):

    t = text.lower()

    for area in LOCAL_AREAS:

        if area in t:
            return "📍 LOCAL"

    return "🌍 UK"

def extract_price(text):

    match = re.search(r'£\s?([0-9,]+)', text)

    if match:

        try:
            return float(match.group(1).replace(",", ""))

        except:
            return None

    return None

# ---------------- LISTING HANDLER ---------------- #

def handle_listing(url, title, price, source, location_text):

    loc = detect_location(location_text or title)
    tag = classify(title, price)

    if url not in data:

        data[url] = {
            "price": price
        }

        save_data(data)

        send_alert(
            f"{tag} {loc}\n"
            f"{source}\n\n"
            f"{title}\n\n"
            f"💰 £{price if price else 'N/A'}\n\n"
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
            f"📉 PRICE DROP\n\n"
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
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+xs&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+mono&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+914&_sop=10"
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

            title_text = title.text.strip()

            if not is_relevant(title_text):
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
                title_text,
                p,
                "EBAY",
                location.text if location else ""
            )

# ---------------- GOOGLE ---------------- #

def check_google():

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return

    queries = [
        "europa aircraft UK",
        "europa xs UK",
        "europa mono UK",
        "europa trigear UK",
        "europa project UK",
        "rotax 912 for sale UK",
        "rotax 914 for sale UK",
        "homebuilt aircraft project UK",
        "unfinished aircraft project UK"
    ]

    for q in queries:

        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?q={q}"
            f"&key={GOOGLE_API_KEY}"
            f"&cx={GOOGLE_CX}"
        )

        r = requests.get(url, timeout=30)

        results = r.json()

        for item in results.get("items", []):

            title = item["title"]
            link = item["link"]

            if not is_relevant(title):
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

    text = soup.get_text("\n")

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if len(line) < 25:
            continue

        if not is_relevant(line):
            continue

        handle_listing(
            url + "#" + line[:20],
            line,
            extract_price(line),
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

        if not is_relevant(title):
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
    safe_run("GOOGLE", check_google)
    safe_run("EUROPA CLUB", check_europa_club)
    safe_run("WINGLIST", check_winglist)

if __name__ == "__main__":
    run()