"""
Aircraft Deal Bot V2
Aircraft24 Scraper
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import AIRCRAFT24, HEADERS
from helpers import process_listing, extract_price, start_source

SOURCE = "AIRCRAFT24"


def check_aircraft24():

    start_source(SOURCE)

    try:

        r = requests.get(
            AIRCRAFT24,
            headers=HEADERS,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        seen = set()

        #
        # Find advert links
        #
        for a in soup.find_all("a", href=True):

            href = a.get("href", "").strip()

            if not href:
                continue

            if any(x in href.lower() for x in [
                "login",
                "register",
                "privacy",
                "terms",
                "contact",
                "about"
            ]):
                continue

            if "/en/" not in href:
                continue

            url = urljoin(AIRCRAFT24, href)

            if url in seen:
                continue

            seen.add(url)

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

                title = ""

                if psoup.title:
                    title = psoup.title.get_text(
                        " ",
                        strip=True
                    )

                if not title:

                    h1 = psoup.find("h1")

                    if h1:
                        title = h1.get_text(
                            " ",
                            strip=True
                        )

                body = psoup.get_text(
                    " ",
                    strip=True
                )

                price = extract_price(body)

                process_listing(

                    source=SOURCE,

                    title=title,

                    description=body,

                    price=price,

                    url=url

                )

            except Exception as e:

                print(f"{SOURCE} advert error: {e}")

    except Exception as e:

        print(f"{SOURCE}: {e}")