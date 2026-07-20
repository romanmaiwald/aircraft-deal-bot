"""
Aircraft Deal Bot V2
Flask Web Interface

Displays aircraft listings from data.json
Manages hidden adverts through hidden.json
"""

from flask import Flask, request, redirect, url_for, render_template_string

import os

from config import DATA_FILE, HIDDEN_FILE

from helpers import (
    load_json,
    save_json,
    hide,
)

from sources import run_all


# --------------------------------------------------
# APP
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# INITIALISE FILES
# --------------------------------------------------

def ensure_files():

    if not os.path.exists(DATA_FILE):

        save_json(
            DATA_FILE,
            {}
        )

    if not os.path.exists(HIDDEN_FILE):

        save_json(
            HIDDEN_FILE,
            {}
        )


ensure_files()


# --------------------------------------------------
# LOADERS
# --------------------------------------------------

def get_data():

    data = load_json(DATA_FILE)

    if not isinstance(data, dict):

        return {}

    return data



def get_hidden():

    hidden = load_json(HIDDEN_FILE)

    if not isinstance(hidden, dict):

        return {}

    return hidden



def visible_listings():

    data = get_data()

    hidden = get_hidden()

    results = []

    # Reverse insertion order = newest first

    for uid, item in reversed(list(data.items())):

        if uid in hidden:

            continue

        listing = item.copy()

        listing["id"] = uid

        results.append(listing)

    return results



def hidden_listings():

    data = get_data()

    hidden = get_hidden()

    results = []

    for uid, item in data.items():

        if uid in hidden:

            listing = item.copy()

            listing["id"] = uid

            results.append(listing)

    return results



# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

def statistics():

    data = get_data()

    hidden = get_hidden()

    source_counts = {}

    for uid, item in data.items():

        source = item.get(
            "source",
            "Unknown"
        )

        source_counts[source] = (
            source_counts.get(source, 0)
            + 1
        )

    return {

        "total": len(data),

        "hidden": len(hidden),

        "visible": len(data) - len(hidden),

        "sources": source_counts

    }


# --------------------------------------------------
# TEMPLATE
# --------------------------------------------------

PAGE_TEMPLATE = """

<!DOCTYPE html>

<html>

<head>

<title>
Aircraft Deal Bot V2
</title>


<meta name="viewport"
content="width=device-width, initial-scale=1">


<style>


body {

    font-family:
    Arial, Helvetica, sans-serif;

    background:#f4f6f8;

    margin:0;

    padding:20px;

}


.container {

    max-width:1200px;

    margin:auto;

}


.header {

    background:#1f2937;

    color:white;

    padding:20px;

    border-radius:10px;

}


.card {

    background:white;

    padding:20px;

    margin-top:15px;

    border-radius:10px;

    box-shadow:
    0 2px 8px rgba(0,0,0,0.08);

}


.grid {

    display:grid;

    grid-template-columns:
    repeat(auto-fit,minmax(250px,1fr));

    gap:15px;

}


input, select, button {

    padding:10px;

    border-radius:6px;

    border:1px solid #ccc;

}


button {

    background:#2563eb;

    color:white;

    cursor:pointer;

    border:none;

}


button:hover {

    opacity:0.85;

}


.hide {

    background:#dc2626;

}


.restore {

    background:#16a34a;

}


.refresh {

    background:#7c3aed;

}


a {

    color:#2563eb;

    word-break:break-word;

}


.price {

    font-size:18px;

    font-weight:bold;

}


.small {

    color:#666;

    font-size:14px;

}


@media(max-width:600px){

    body {

        padding:10px;

    }

}


</style>


</head>


<body>


<div class="container">


<div class="header">

<h1>
✈ Aircraft Deal Bot V2
</h1>

<p>
Aircraft project and engine listings
</p>


<form method="post"
action="/refresh">

<button class="refresh">

Refresh Sources

</button>

</form>


</div>



<div class="card">


<h2>
Statistics
</h2>


<div class="grid">


<div>
<b>Total adverts</b>
<br>
{{stats.total}}
</div>


<div>
<b>Visible</b>
<br>
{{stats.visible}}
</div>


<div>
<b>Hidden</b>
<br>
{{stats.hidden}}
</div>


</div>



<h3>
Sources
</h3>


<ul>

{% for source,count in stats.sources.items() %}

<li>
{{source}} :
{{count}}
</li>

{% endfor %}

</ul>


</div>



<div class="card">


<form method="get">


<input

type="text"

name="search"

placeholder="Search adverts"

value="{{search}}"


>


<select name="source">


<option value="">
All Sources
</option>


{% for source in sources %}

<option

value="{{source}}"

{% if source == selected_source %}
selected
{% endif %}

>

{{source}}

</option>


{% endfor %}


</select>



<button>

Search

</button>


</form>


<p>

<a href="/hidden">

View Hidden Adverts

</a>

</p>


</div>



{% for item in listings %}


<div class="card">


<h2>

{{item.title}}

</h2>


<p>

<b>
Source:
</b>

{{item.source}}

</p>


<p class="price">

Price:

{% if item.price %}

£{{"{:,.0f}".format(item.price)}}

{% else %}

N/A

{% endif %}

</p>


<p>

{{item.description}}

</p>


<p>

<a href="{{item.url}}"
target="_blank">

Open Advert

</a>

</p>


<form method="post"
action="/hide/{{item.id}}">


<button class="hide">

Hide Advert

</button>


</form>


</div>


{% endfor %}



{% if not listings %}


<div class="card">

<h2>
No adverts found
</h2>

</div>


{% endif %}



</div>


</body>


</html>

"""



# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def index():

    listings = visible_listings()

    search = request.args.get(
        "search",
        ""
    ).lower()


    selected_source = request.args.get(
        "source",
        ""
    )


    if search:

        listings = [

            x for x in listings

            if search in (
                x.get("title","")
                +
                x.get("description","")
            ).lower()

        ]


    if selected_source:

        listings = [

            x for x in listings

            if x.get("source")
            ==
            selected_source

        ]


    sources = sorted(

        list(

            set(

                x.get(
                    "source",
                    "Unknown"
                )

                for x in visible_listings()

            )

        )

    )


    return render_template_string(

        PAGE_TEMPLATE,

        listings=listings,

        stats=statistics(),

        search=search,

        sources=sources,

        selected_source=selected_source

    )



@app.route(
    "/hide/<uid>",
    methods=["POST"]
)

def hide_listing(uid):

    hide(uid)

    return redirect(
        url_for("index")
    )



@app.route("/hidden")
def hidden_page():

    listings = hidden_listings()


    return render_template_string(

        PAGE_TEMPLATE,

        listings=listings,

        stats=statistics(),

        search="",

        sources=[],

        selected_source=""

    )



@app.route(
    "/restore/<uid>",
    methods=["POST"]
)

def restore_listing(uid):

    hidden = get_hidden()


    if uid in hidden:

        del hidden[uid]

        save_json(
            HIDDEN_FILE,
            hidden
        )


    return redirect(
        url_for("hidden_page")
    )



@app.route(
    "/refresh",
    methods=["POST"]
)

def refresh():

    run_all()

    return redirect(
        url_for("index")
    )


# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )