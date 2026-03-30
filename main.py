def run():
    send_alert("✅ Aircraft deal bot is LIVE")

    searches = [
        "https://www.ebay.co.uk/sch/i.html?_nkw=aircraft+project&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=europa+aircraft&_sop=10",
        "https://www.ebay.co.uk/sch/i.html?_nkw=rotax+912&_sop=10"
    ]

    while True:
        for s in searches:
            try:
                check_ebay(s)
            except Exception as e:
                print("Error:", e)

        time.sleep(600)

    # if not is_good(title_text):
    #     continue

MAX_PRICE = 5000