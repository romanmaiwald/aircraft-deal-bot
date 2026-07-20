"""
Aircraft Deal Bot V2
Winglist Scraper
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import WINGLIST, HEADERS
from helpers import process_listing, extract_price, start_source

SOURCE = "WINGLIST"


def check_winglist():

    start_source(SOURCE)

    try:

        r = requests.get(
            WINGLIST,
            headers=HEADERS,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        seen = set()

        for a in soup.find_all("a", href=True):

            href = a.get("href", "").strip()

            if not href:
                continue

            url = urljoin(WINGLIST, href)

            if url in seen:
                continue

            seen.add(url)

            title = a.get_text(" ", strip=True)

            if len(title) < 8:
                continue

            t = title.lower()

            # Ignore navigation and site furniture
            if any(x in t for x in [
                "login",
                "register",
                "advertise",
                "membership",
                "contact",
                "about",
                "privacy",
                "terms",
                "cookie",
                "menu",
                "home"
            ]):
                continue

            #
            # Visit advert page
            #

            try:

                page = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=30
                )

                psoup = BeautifulSoup(
                    page.text,
                    "html.parser"
                )

                body = psoup.get_text(" ", strip=True)

                page_title = ""

                if psoup.title:
                    page_title = psoup.title.get_text(
                        " ",
                        strip=True
                    )

                if not page_title:
                    page_title = title

                price = extract_price(body)

                process_listing(

                    source=SOURCE,

                    title=page_title,

                    description=body,

                    price=price,

                    url=url

                )

            except Exception:

                continue

    except Exception as e:

        print(f"{SOURCE}: {e}")