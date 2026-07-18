"""
Aircraft Deal Bot V2
Configuration
"""

import os

# -----------------------------
# TELEGRAM
# -----------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# -----------------------------
# GOOGLE CUSTOM SEARCH
# -----------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CX = os.getenv("GOOGLE_CX", "")

# -----------------------------
# DATA FILES
# -----------------------------

DATA_FILE = "data.json"
HIDDEN_FILE = "hidden.json"

# -----------------------------
# PRICE LIMITS
# -----------------------------

AIRCRAFT_MAX_PRICE = 20000
ENGINE_MAX_PRICE = 8000

# -----------------------------
# SEARCH TERMS
# -----------------------------

SEARCH_TERMS = [

    # Europa
    "europa",
    "europa xs",
    "europa classic",
    "europa mono",
    "europa monowheel",
    "europa trigear",
    "europa kit",
    "europa project",
    "europa aircraft",
    "europa airframe",

    # Rotax
    "rotax",
    "912",
    "912ul",
    "912uls",
    "912is",
    "914",
    "915",
    "915is",
    "916",
    "916is",

    # General
    "kit",
    "project",
    "unfinished",
    "part built",
    "permit expired",
    "homebuilt",
    "experimental",
    "airframe",
    "barn find"
]

# -----------------------------
# WORDS TO IGNORE
# -----------------------------

BAD_WORDS = [

    "model",
    "rc",
    "toy",
    "poster",
    "book",
    "manual",
    "dvd",
    "simulator",
    "insurance",
    "finance",
    "loan",
    "service",
    "advertise",
    "advertising",
    "hosting",
    "domain",
    "web design",
    "membership"
]

# -----------------------------
# USER AGENT
# -----------------------------

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
}

# -----------------------------
# WEBSITE URLS
# -----------------------------

EBAY_SEARCHES = [

    "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",

    "https://www.ebay.co.uk/sch/i.html?_nkw=europa+xs&_sop=10",

    "https://www.ebay.co.uk/sch/i.html?_nkw=europa+project&_sop=10",

    "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10",

    "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+914&_sop=10"

]

EUROPA_CLUB = "https://www.theeuropaclub.org/the-club/sales--member-adverts"

WINGLIST = "https://www.winglist.aero/listings"

BARNSTORMERS = "https://www.barnstormers.com/cat.php?mode=latest"

PLANECHECK = "https://www.planecheck.com"

AIRCRAFT24 = "https://www.aircraft24.com/en"

# -----------------------------
# GOOGLE SEARCHES
# -----------------------------

GOOGLE_QUERIES = [

    "Europa aircraft UK",

    "Europa XS for sale",

    "Europa project",

    "Rotax 912 for sale UK",

    "Rotax 914 for sale UK",

    "Homebuilt aircraft project UK"

]