import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.message import EmailMessage
import os

LETTERBOXD_USER = "TchernoAlpha"
PARIS_CINE_URL = "https://paris-cine.info"
STATE_FILE = "notified.json"

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

def get_french_title_wikidata(title, year):
    query = f"""
    SELECT ?frTitle WHERE {{
      ?film wdt:P31 wd:Q11424;
            rdfs:label "{title}"@en;
            wdt:P577 ?date.
      FILTER(YEAR(?date) = {year})
      OPTIONAL {{ ?film rdfs:label ?frTitle FILTER(LANG(?frTitle) = "fr") }}
    }}
    LIMIT 1
    ""
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    r = requests.get(url, params={"query": query}, headers=headers)
    data = r.json()
    try:
        return data["results"]["bindings"][0]["frTitle"]["value"].lower()
    except (IndexError, KeyError):
        return title.lower()  # fallback → titre anglais


def get_watchlist_from_csv(csv_file="watchlist.csv"):
    """Lit le CSV Letterboxd et retourne un dict anglais → français"""
    df = pd.read_csv(csv_file)
    watchlist = {}
    for _, row in df.iterrows():
        title = str(row['Name']).strip()
        year = int(row['Year']) if not pd.isna(row['Year']) else None
        fr_title = get_french_title_wikidata(title, year)
        print(f"{title} ({year}) → {fr_title}")  # log dans GitHub Actions
        watchlist[title.lower()] = fr_title
    return watchlist



def get_paris_cine_films():
    soup = BeautifulSoup(requests.get(PARIS_CINE_URL).text, "html.parser")
    films = set()
    for h in soup.find_all(["h2", "h3"]):
        films.add(h.text.strip().lower())
    return films

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)

def send_email(films):
    msg = EmailMessage()
    msg["Subject"] = "🎬 Films de ta watchlist en salle à Paris"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(
        "Bonne nouvelle !\n\n" +
        "\n".join(f"• {f.title()}" for f in films) +
        f"\n\nVoir les séances : {PARIS_CINE_URL}"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(EMAIL_FROM, EMAIL_PASSWORD)
        s.send_message(msg)

def main():
    watchlist = get_watchlist_from_csv("watchlist.csv")

    print("WATCHLIST DETECTÉE :", sorted(watchlist)[:10])
    paris = get_paris_cine_films()
    notified = load_state()
    matches = watchlist & paris - notified

    if matches:
        send_email(matches)
        save_state(notified | matches)

main()
