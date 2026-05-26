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

    # NEW LISTING
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

    # PRICE DROP
    old_price = data[url].get("price")

    if (
        price and
        old_price and
        price < old_price
    ):

        data[url]["price"] = price
        data[url]["price_drop"] = True

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

# ---------------- AFORS ---------------- #

def check_afors():

    urls = [
        "https://afors.com/aircraftView.php",
        "https://afors.com/engineView.php"
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

            seen = set()

            # AFORS listings are usually inside rows
            rows = soup.find_all("tr")

            for row in rows:

                text = row.get_text(
                    " ",
                    strip=True
                )

                if not text:
                    continue

                if len(text) < 20:
                    continue

                link_tag = row.find(
                    "a",
                    href=True
                )

                if not link_tag:
                    continue

                link = link_tag["href"]

                if "view.php?id=" not in link:
                    continue

                if link.startswith("/"):
                    link = "https://afors.com" + link

                elif not link.startswith("http"):
                    link = "https://afors.com/" + link

                if link in seen:
                    continue

                seen.add(link)

                title = link_tag.get_text(
                    " ",
                    strip=True
                )

                if not title:
                    title = text[:120]

                t = title.lower()

                bad = [
                    "wanted",
                    "insurance",
                    "finance",
                    "instruction",
                    "hangarage",
                    "transport",
                    "trailer service"
                ]

                if any(b in t for b in bad):
                    continue

                price = extract_price(text)

                print("AFORS FOUND:", title, price)

                handle_listing(
                    link,
                    title,
                    price,
                    "AFORS"
                )

        except Exception as e:

            print("AFORS ERROR:", e)

# ---------------- MAIN RUNNER ---------------- #

def run():

    print("Running Aircraft Deal Bot...")

    check_ebay()
    check_google()
    check_europa_club()
    check_winglist()
    check_afors()

    print("Finished.")

if __name__ == "__main__":
    run()