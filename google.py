"""
Aircraft Deal Bot V2
Google Custom Search Scraper
"""

import requests

from config import (
    GOOGLE_API_KEY,
    GOOGLE_CX,
    GOOGLE_QUERIES,
)

from helpers import (
    process_listing,
    start_source,
)

SOURCE = "GOOGLE"


def check_google():

    start_source(SOURCE)

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        print(f"{SOURCE}: Google API not configured")
        return

    for query in GOOGLE_QUERIES:

        try:

            url = (
                "https://www.googleapis.com/customsearch/v1"
                f"?key={GOOGLE_API_KEY}"
                f"&cx={GOOGLE_CX}"
                f"&num=10"
                f"&q={query}"
            )

            r = requests.get(
                url,
                timeout=30
            )

            if r.status_code != 200:

                print(
                    f"{SOURCE}: HTTP {r.status_code}"
                )

                continue

            results = r.json()

            for item in results.get("items", []):

                title = item.get("title", "")

                description = item.get(
                    "snippet",
                    ""
                )

                link = item.get(
                    "link",
                    ""
                )

                process_listing(

                    source=SOURCE,

                    title=title,

                    description=description,

                    price=None,

                    url=link

                )

        except Exception as e:

            print(f"{SOURCE}: {e}")