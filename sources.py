"""
Aircraft Deal Bot V2
Master Scraper Runner
"""

from ebay import check_ebay
from europaclub import check_europa_club
from winglist import check_winglist
from barnstormers import check_barnstormers
from planecheck import check_planecheck
from aircraft24 import check_aircraft24
from google import check_google

from helpers import print_summary


def run_all():

    print("\n==============================")
    print("Aircraft Deal Bot V2 Starting")
    print("==============================")

    #
    # Aircraft Sources
    #

    check_ebay()

    check_europa_club()

    check_winglist()

    check_barnstormers()

    check_planecheck()

    check_aircraft24()

    #
    # Google Custom Search
    #

    check_google()

    #
    # Print statistics
    #

    print_summary()

    print("==============================")
    print("Aircraft Deal Bot V2 Finished")
    print("==============================\n")