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
    "aircraft",
    "kit",
    "project",
    "homebuilt",
    "experimental",
    "unfinished",
    "part built",
    "rebuild",
    "airframe",
    "barn find",
    "permit expired"
]

BAD_WORDS = [
    "rc",
    "model",
    "toy",
    "simulator",
    "book",
    "manual",
    "poster",
    "dvd"
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
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=20)
    except:
        pass

# ---------------- HELPERS ---------------- #

def extract_price(text):
    match = re.search(r'£\s?([0-9,]+)', text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except:
            return None
    return None

def is_relevant(text):
    t = text.lower()

    if any(b in t for b in BAD_WORDS):
        return False

    if "europa" in t:
        return True

    if "rotax" in t or "912" in t or "914" in t:
        return True

    return any(k in t for k in KEYWORDS)

# ---------------- STORAGE ---------------- #

def handle_listing(url, title, price, source):

    if not is_relevant(title):
        return

    if price and price > MAX_PRICE:
        return

    new_item = {
        "title": title,
        "price": price,
        "source": source,
        "url": url
    }

    # NEW ITEM
    if url not in data:
        data[url] = new_item
        save_data(data)

        send_alert(
            f"✈ {source}\n\n"
            f"{title}\n"
            f"£{price if price else 'N/A'}\n\n"
            f"{url}"
        )
        return

    # PRICE DROP CHECK
    old_price = data[url].get("price")

    if price and old_price and price < old_price:
        data[url]["price"] = price
        save_data(data)

        send_alert(
            f"📉 PRICE DROP\n\n"
            f"{title}\n\n"
            f"Was £{old_price}\n"
            f"Now £{price}\n\n"
            f"{url}"
        )

# ---------------- EBAY ---------------- #

def check_ebay():

    urls = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+xs&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+914&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10"
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select(".s-item"):
                title = item.select_one(".s-item__title")
                price = item.select_one(".s-item__price")
                link = item.select_one("a")

                if not title or not price or not link:
                    continue

                title_text = title.text.strip()

                try:
                    p = float(price.text.replace("£", "").split()[0].replace(",", ""))
                except:
                    p = None

                handle_listing(link["href"], title_text, p, "EBAY")

        except:
            continue

# ---------------- GOOGLE ---------------- #

def check_google():

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return

    queries = [
        "europa aircraft UK",
        "rotax 912 for sale UK",
        "rotax 914 for sale UK",
        "homebuilt aircraft project UK"
    ]

    for q in queries:
        try:
            url = (
                "https://www.googleapis.com/customsearch/v1"
                f"?q={q}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
            )

            r = requests.get(url, timeout=30)
            results = r.json()

            for item in results.get("items", []):
                handle_listing(
                    item["link"],
                    item["title"],
                    None,
                    "GOOGLE"
                )

        except:
            continue

# ---------------- EUROPA CLUB ---------------- #

def check_europa_club():

    url = "https://www.theeuropaclub.org/the-club/sales--member-adverts"

    try:
        r = requests.get(url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text("\n")

        for line in text.split("\n"):
            line = line.strip()

            if len(line) < 30:
                continue

            handle_listing(url + "#" + line[:20], line, None, "EUROPA CLUB")

    except:
        pass

# ---------------- WINGLIST ---------------- #

def check_winglist():

    url = "https://www.winglist.aero/listings"

    try:
        r = requests.get(url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a"):
            title = a.text.strip()
            link = a.get("href")

            if not title or not link:
                continue

            if link.startswith("/"):
                link = "https://www.winglist.aero" + link

            handle_listing(link, title, None, "WINGLIST")

    except:
        pass

# ---------------- RUNNER ---------------- #

def run():
    check_ebay()
    check_google()
    check_europa_club()
    check_winglist()

if __name__ == "__main__":
    run()