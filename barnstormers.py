"""
Aircraft Deal Bot V2
Barnstormers Scraper
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import BARNSTORMERS, HEADERS
from helpers import process_listing, extract_price, start_source

SOURCE = "BARNSTORMERS"


def check_barnstormers():

    start_source(SOURCE)

    try:

        r = requests.get(
            BARNSTORMERS,
            headers=HEADERS,
            timeout=30
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        seen = set()

        #
        # Barnstormers adverts
        #
        for a in soup.find_all("a", href=True):

            href = a.get("href", "").strip()

            if not href:
                continue

            #
            # Ignore navigation
            #
            if "classified" not in href.lower():
                continue

            url = urljoin(BARNSTORMERS, href)

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

                #
                # Title
                #
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

                #
                # Entire advert
                #
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

            except Exception:

                continue

    except Exception as e:

        print(f"{SOURCE}: {e}")