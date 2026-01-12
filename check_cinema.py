import pandas as pd
import requests
from fuzzywuzzy import fuzz
import smtplib
from email.message import EmailMessage
import os
import re
import json

CSV_WATCHLIST = "watchlist-tchernoalpha.csv"
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# -----------------------------
# Scraper ParisCinéInfo : récupère titre FR et VO depuis le JS de la page d'accueil
# -----------------------------
def scrape_pariscine():
    url = "https://paris-cine.info/"
    r = requests.get(url, timeout=10)
    text = r.text

    films = []

    # Chercher tous les objets row = {...} dans le JS
    pattern = r'row\s*=\s*(\{.*?\});'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for m in matches:
        try:
            # Convertir '...' en JSON valide
            row = json.loads(m.replace("'", '"'))
            fr_title = row.get("ti")
            vo_title = row.get("o_ti", fr_title)  # fallback sur FR si absent
            if fr_title:
                films.append((fr_title.strip(), vo_title.strip()))
        except Exception:
            continue

    return films

# -----------------------------
# Envoi email
# -----------------------------
def send_email(matches):
    if not matches:
        print("Aucun match cette semaine.")
        return
    msg = EmailMessage()
    msg["Subject"] = "Films à l'affiche de ta watchlist"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content("Films détectés :\n" + "\n".join(matches))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print(f"Mail envoyé avec {len(matches)} films.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    # Watchlist Letterboxd
    df = pd.read_csv(CSV_WATCHLIST)
    watchlist_titles = [t.strip() for t in df["Name"].tolist()]  # Nom de la colonne Letterboxd

    # ParisCinéInfo
    paris_films = scrape_pariscine()
    
    # DEBUG : vérifier ce qui a été scrappé
    print(f"Nombre de films scrappés sur ParisCinéInfo : {len(paris_films)}")
    for fr, vo in paris_films[:10]:  # affiche seulement les 10 premiers
        print(f"{fr} → {vo}")

    # Fuzzy match avec ta watchlist
    matches = set()
    for lb_title in watchlist_titles:
        for fr_title, vo_title in paris_films:
            ratio = fuzz.token_set_ratio(lb_title.lower(), vo_title.lower())
            if ratio >= 80:  # seuil à ajuster si besoin
                matches.add(fr_title)
    
    if matches:
        send_email(sorted(matches))
    else:
        print("Aucun match cette semaine.")

if __name__ == "__main__":
    main()
