"""
Aircraft Deal Bot V2
eBay Scraper
"""

import requests
from bs4 import BeautifulSoup

from config import EBAY_SEARCHES, HEADERS
from helpers import process_listing, extract_price, start_source


SOURCE = "EBAY"


def check_ebay():

    start_source(SOURCE)

    for search_url in EBAY_SEARCHES:

        try:

            r = requests.get(
                search_url,
                headers=HEADERS,
                timeout=30
            )

            soup = BeautifulSoup(
                r.text,
                "html.parser"
            )

            for item in soup.select(".s-item"):

                title = item.select_one(".s-item__title")
                price = item.select_one(".s-item__price")
                link = item.select_one("a.s-item__link")

                if not title or not link:
                    continue

                title_text = title.get_text(" ", strip=True)

                url = link.get("href", "")

                price_value = None

                if price:
                    price_value = extract_price(
                        price.get_text(" ", strip=True)
                    )

                process_listing(

                    source=SOURCE,

                    title=title_text,

                    description="",

                    price=price_value,

                    url=url

                )

        except Exception as e:

            print(f"{SOURCE}: {e}")