"""
Aircraft Deal Bot V2
Europa Club Scraper
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import EUROPA_CLUB, HEADERS
from helpers import process_listing, extract_price, start_source

SOURCE = "EUROPA CLUB"


def check_europa_club():

    start_source(SOURCE)

    try:

        r = requests.get(
            EUROPA_CLUB,
            headers=HEADERS,
            timeout=30
        )

        soup = BeautifulSoup(r.text, "html.parser")

        links = set()

        #
        # Find every advert link
        #
        for a in soup.find_all("a", href=True):

            href = a["href"]

            if "/the-club/sales--member-adverts/" not in href:
                continue

            full_url = urljoin(EUROPA_CLUB, href)

            if full_url == EUROPA_CLUB:
                continue

            links.add(full_url)

        #
        # Visit every advert
        #
        for advert in sorted(links):

            try:

                page = requests.get(
                    advert,
                    headers=HEADERS,
                    timeout=30
                )

                psoup = BeautifulSoup(
                    page.text,
                    "html.parser"
                )

                title = ""

                if psoup.title:
                    title = psoup.title.get_text(" ", strip=True)

                if not title:

                    h1 = psoup.find("h1")

                    if h1:
                        title = h1.get_text(" ", strip=True)

                body = psoup.get_text(" ", strip=True)

                price = extract_price(body)

                process_listing(

                    source=SOURCE,

                    title=title,

                    description=body,

                    price=price,

                    url=advert

                )

            except Exception as e:

                print(f"{SOURCE} advert error: {e}")

    except Exception as e:

        print(f"{SOURCE}: {e}")