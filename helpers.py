"""
Aircraft Deal Bot V2
Helper Functions
"""

import hashlib
import json
import os
import re
import requests

from config import (
    BOT_TOKEN,
    CHAT_ID,
    DATA_FILE,
    HIDDEN_FILE,
    SEARCH_TERMS,
    BAD_WORDS,
    AIRCRAFT_MAX_PRICE,
    ENGINE_MAX_PRICE,
)

# --------------------------------------------------
# DATA
# --------------------------------------------------

def load_json(filename):

    if not os.path.exists(filename):
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {}


def save_json(filename, data):

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


data = load_json(DATA_FILE)

hidden = load_json(HIDDEN_FILE)

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

stats = {}


def start_source(name):

    stats[name] = {
        "found": 0,
        "relevant": 0,
        "new": 0,
        "duplicates": 0,
        "hidden": 0
    }


def found(name):
    stats[name]["found"] += 1


def relevant(name):
    stats[name]["relevant"] += 1


def duplicate(name):
    stats[name]["duplicates"] += 1


def hidden_listing(name):
    stats[name]["hidden"] += 1


def new_listing(name):
    stats[name]["new"] += 1


def print_summary():

    print("\n")
    print("=" * 60)
    print("AIRCRAFT DEAL BOT")
    print("=" * 60)

    for source in stats:

        s = stats[source]

        print(f"\n{source}")

        print(f"  Found      : {s['found']}")
        print(f"  Relevant   : {s['relevant']}")
        print(f"  New        : {s['new']}")
        print(f"  Duplicate  : {s['duplicates']}")
        print(f"  Hidden     : {s['hidden']}")

    print("\nFinished\n")

# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

def telegram(message):

    if not BOT_TOKEN:
        return

    if not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message,
                "disable_web_page_preview": False
            },
            timeout=20
        )

    except Exception as e:

        print("Telegram:", e)

# --------------------------------------------------
# PRICE EXTRACTION
# --------------------------------------------------

price_patterns = [

    r"£\s*([0-9,]+)",

    r"GBP\s*([0-9,]+)",

    r"([0-9,]+)\s*GBP",

    r"£\s*([0-9]+)k",

    r"guide\s*£\s*([0-9,]+)",

    r"offers\s*around\s*£\s*([0-9,]+)"

]


def extract_price(text):

    if not text:
        return None

    t = text.lower()

    for pattern in price_patterns:

        m = re.search(pattern, t, re.IGNORECASE)

        if m:

            value = m.group(1)

            value = value.replace(",", "")

            try:

                if "k" in pattern:
                    return float(value) * 1000

                return float(value)

            except:
                pass

    return None

# --------------------------------------------------
# FILTERING
# --------------------------------------------------

def is_relevant(title, description=""):

    text = f"{title} {description}".lower()

    for word in BAD_WORDS:

        if word in text:
            return False

    for word in SEARCH_TERMS:

        if word in text:
            return True

    return False


def is_engine(text):

    t = text.lower()

    return (
        "rotax" in t
        or "912" in t
        or "914" in t
        or "915" in t
        or "916" in t
    )


def passes_price_limit(title, description, price):

    if price is None:
        return True

    text = f"{title} {description}"

    if is_engine(text):
        return price <= ENGINE_MAX_PRICE

    return price <= AIRCRAFT_MAX_PRICE

# --------------------------------------------------
# UNIQUE ID
# --------------------------------------------------

def listing_id(source, title, price, url):

    text = f"{source}|{title}|{price}|{url}"

    return hashlib.sha1(
        text.encode("utf-8")
    ).hexdigest()

# --------------------------------------------------
# HIDDEN
# --------------------------------------------------

def is_hidden(uid):

    return uid in hidden


def hide(uid):

    hidden[uid] = True

    save_json(HIDDEN_FILE, hidden)

# --------------------------------------------------
# STORAGE
# --------------------------------------------------

def save_listing(source, title, description, price, url):

    uid = listing_id(
        source,
        title,
        price,
        url
    )

    if is_hidden(uid):
        hidden_listing(source)
        return

    if uid in data:

        duplicate(source)

        old_price = data[uid].get("price")

        if (
            old_price
            and price
            and price < old_price
        ):

            data[uid]["price"] = price

            save_json(DATA_FILE, data)

            telegram(
                "📉 PRICE DROP\n\n"
                f"{title}\n\n"
                f"£{old_price} → £{price}\n\n"
                f"{url}"
            )

        return

    data[uid] = {

        "source": source,

        "title": title,

        "description": description,

        "price": price,

        "url": url

    }

    save_json(DATA_FILE, data)

    new_listing(source)

    telegram(

        "✈ NEW LISTING\n\n"

        f"{title}\n\n"

        f"Price: £{price if price else 'N/A'}\n\n"

        f"Source: {source}\n\n"

        f"{url}"

    )

# --------------------------------------------------
# MASTER ENTRY POINT
# --------------------------------------------------

def process_listing(

    source,

    title,

    description,

    price,

    url

):

    found(source)

    if not is_relevant(title, description):
        return

    relevant(source)

    if not passes_price_limit(title, description, price):
        return

    save_listing(

        source,

        title,

        description,

        price,

        url

    )