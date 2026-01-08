import pandas as pd
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os

# ------------------ CONFIG ------------------
CSV_FILE = "watchlist-tchernoalpha.csv"
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# ------------------ FONCTIONS ------------------

def get_french_title_wikidata(title, year):
    """Récupère le titre français depuis Wikidata, fallback vers titre anglais si erreur"""
    if year is None:
        year = 0  # fallback pour éviter None dans SPARQL
    
    # Échapper les guillemets pour ne pas casser le f-string
    safe_title = title.replace('"', '\\"')
    
    query = f"""
    SELECT ?frTitle WHERE {{
      ?film wdt:P31 wd:Q11424;
            rdfs:label "{safe_title}"@en;
            wdt:P577 ?date.
      FILTER(YEAR(?date) = {year})
      OPTIONAL {{ ?film rdfs:label ?frTitle FILTER(LANG(?frTitle) = "fr") }}
    }}
    LIMIT 1
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    try:
        r = requests.get(url, params={"query": query}, headers=headers, timeout=10)
        r.raise_for_status()  # HTTP != 200 → exception
        data = r.json()
        return data["results"]["bindings"][0]["frTitle"]["value"].lower()
    except Exception as e:
        print(f"⚠️ Impossible de récupérer le titre français pour {title} ({year}): {e}")
        return title.lower()  # fallback → titre anglais

def get_watchlist_from_csv(csv_file=CSV_FILE):
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
    """Scraper ParisCineInfo pour récupérer les films actuellement à l'affiche"""
    url = "https://paris-cine.info/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    films = set()
    # ATTENTION : adapter le select si le HTML change
    for h2 in soup.select("h2.film-title"):
        films.add(h2.text.strip().lower())
    return films

def send_email(matches):
    """Envoie un mail avec la liste des films détectés"""
    if not matches:
        return
    msg = EmailMessage()
    msg["Subject"] = f"Films à l'affiche de ta watchlist"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content("Films détectés :\n" + "\n".join(matches))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ------------------ MAIN ------------------

def main():
    watchlist = get_watchlist_from_csv(CSV_FILE)
    paris = get_paris_cine_films()
    
    matches = set()
    for en_title, fr_title in watchlist.items():
        if fr_title in paris:
            matches.add(en_title)  # tu peux changer en fr_title si tu veux le français dans le mail
    
    if matches:
        send_email(matches)
    else:
        print("Aucun match cette semaine.")

if __name__ == "__main__":
    main()
