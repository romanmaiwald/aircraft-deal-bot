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
    "dvd",
    "service",
    "insurance",
    "finance"
]

# ---------------- DATA ---------------- #

def load_data():

    if os.path.exists(DATA_FILE):

        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    return {}

def save_data(data):

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ---------------- TELEGRAM ---------------- #

def send_alert(msg):

    if not BOT_TOKEN or not CHAT_ID:
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

        print("TELEGRAM ERROR:", e)

# ---------------- HELPERS ---------------- #

def is_relevant(text):

    if not text:
        return False

    t = text.lower()

    if any(b in t for b in BAD_WORDS):
        return False

    if "europa" in t:
        return True

    if "rotax" in t:
        return True

    if "912" in t or "914" in t:
        return True

    return any(k in t for k in KEYWORDS)

def extract_price(text):

    if not text:
        return None

    match = re.search(r'£\s?([0-9,]+)', text)

    if not match:
        match = re.search(r'\$\s?([0-9,]+)', text)

    if match:

        try:
            return float(
                match.group(1).replace(",", "")
            )

        except:
            return None

    return None

# ---------------- STORAGE + ALERT LOGIC ---------------- #

def handle_listing(url, title, price, source):

    if not url or not title:
        return

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

    if url not in data:

        data[url] = new_item

        save_data(data)

        send_alert(
            f"✈ {source}\n\n"
            f"{title}\n"
            f"£{price if price else 'N/A'}\n\n"
            f"{url}"
        )

        print("NEW:", title)

        return

    old_price = data[url].get("price")

    if (
        price and
        old_price and
        price < old_price
    ):

        data[url]["price"] = price

        save_data(data)

        send_alert(
            f"📉 PRICE DROP\n\n"
            f"{title}\n\n"
            f"Was £{old_price}\n"
            f"Now £{price}\n\n"
            f"{url}"
        )

        print("PRICE DROP:", title)

# ---------------- EBAY ---------------- #

def check_ebay():

    urls = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+xs&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+914&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in urls:

        try:

            r = requests.get(
                url,
                headers=headers,
                timeout=30
            )

            soup = BeautifulSoup(
                r.text,
                "html.parser"
            )

            for item in soup.select(".s-item"):

                title = item.select_one(".s-item__title")
                price = item.select_one(".s-item__price")
                link = item.select_one("a")

                if not title or not link:
                    continue

                title_text = title.text.strip()

                p = None

                if price:

                    try:
                        p = float(
                            price.text
                            .replace("£", "")
                            .split()[0]
                            .replace(",", "")
                        )
                    except:
                        p = None

                handle_listing(
                    link["href"],
                    title_text,
                    p,
                    "EBAY"
                )

        except Exception as e:

            print("EBAY ERROR:", e)

# ---------------- GOOGLE ---------------- #

def check_google():

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return

    queries = [
        "europa aircraft UK",
        "europa xs project UK",
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
                    item.get("link"),
                    item.get("title"),
                    None,
                    "GOOGLE"
                )

        except Exception as e:

            print("GOOGLE ERROR:", e)

# ---------------- EUROPA CLUB ---------------- #

def check_europa_club():

    url = "https://www.theeuropaclub.org/the-club/sales--member-adverts"

    try:

        r = requests.get(url, timeout=30)

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        text = soup.get_text("\n")

        for line in text.split("\n"):

            line = line.strip()

            if len(line) < 30:
                continue

            handle_listing(
                url + "#" + line[:20],
                line,
                None,
                "EUROPA CLUB"
            )

    except Exception as e:

        print("EUROPA CLUB ERROR:", e)

# ---------------- WINGLIST ---------------- #

def check_winglist():

    url = "https://www.winglist.aero/listings"

    try:

        r = requests.get(url, timeout=30)

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        seen = set()

        for a in soup.select("a"):

            title = a.get_text(strip=True)
            link = a.get("href")

            if not title or not link:
                continue

            t = title.lower()

            bad_patterns = [
                "login",
                "register",
                "about",
                "contact",
                "services",
                "advertise",
                "membership",
                "terms",
                "privacy",
                "home",
                "menu"
            ]

            if any(b in t for b in bad_patterns):
                continue

            if len(title) < 15:
                continue

            if link in seen:
                continue

            seen.add(link)

            if link.startswith("/"):
                link = "https://www.winglist.aero" + link

            handle_listing(
                link,
                title,
                None,
                "WINGLIST"
            )

    except Exception as e:

        print("WINGLIST ERROR:", e)

# ---------------- BARNSTORMERS ---------------- #

def check_barnstormers():

    url = "https://www.barnstormers.com/cat.php?mode=latest"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):

            title = a.get_text(strip=True)

            if len(title) < 10:
                continue

            href = a["href"]

            if "classified" not in href:
                continue

            if href.startswith("/"):
                href = "https://www.barnstormers.com" + href

            handle_listing(
                href,
                title,
                None,
                "BARNSTORMERS"
            )

    except Exception as e:

        print("BARNSTORMERS ERROR:", e)

# ---------------- PLANECHECK ---------------- #

def check_planecheck():

    url = "https://www.planecheck.com"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):

            title = a.get_text(strip=True)

            if len(title) < 10:
                continue

            href = a["href"]

            if href.startswith("/"):
                href = "https://www.planecheck.com" + href

            handle_listing(
                href,
                title,
                None,
                "PLANECHECK"
            )

    except Exception as e:

        print("PLANECHECK ERROR:", e)

# ---------------- AIRCRAFT24 ---------------- #

def check_aircraft24():

    url = "https://www.aircraft24.com/en"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):

            title = a.get_text(strip=True)

            if len(title) < 10:
                continue

            href = a["href"]

            if href.startswith("/"):
                href = "https://www.aircraft24.com" + href

            handle_listing(
                href,
                title,
                None,
                "AIRCRAFT24"
            )

    except Exception as e:

        print("AIRCRAFT24 ERROR:", e)

# ---------------- MAIN ---------------- #

def run():

    print("Running Aircraft Deal Bot...")

    check_ebay()
    check_google()
    check_europa_club()
    check_winglist()
    check_barnstormers()
    check_planecheck()
    check_aircraft24()

    print("Finished.")

if __name__ == "__main__":
    run()