import pandas as pd
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os

CSV_FULL = "watchlist_full.csv"
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def get_paris_cine_vo():
    """Scraper ParisCinéInfo et récupérer VO translittérée et titre FR"""
    url = "https://paris-cine.info/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    films = []
    # Adapter selon le HTML réel
    for film_div in soup.select("div.film-entry"):
        fr_tag = film_div.select_one("h2.film-title")
        orig_tag = film_div.select_one("span.original-title")
        if fr_tag and orig_tag:
            fr_title = fr_tag.text.strip().lower()
            vo_title = orig_tag.text.strip().lower()
            films.append((vo_title, fr_title))
    return films

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

def main():
    df = pd.read_csv(CSV_FULL)
    watchlist_vo = {row["Title_VO"].lower(): row["Title_FR"] for _, row in df.iterrows()}
    paris = get_paris_cine_vo()
    
    matches = set()
    paris_vo_set = {vo: fr for vo, fr in paris}
    
    for vo_csv, fr_csv in watchlist_vo.items():
        if vo_csv in paris_vo_set:
            matches.add(fr_csv)
    
    if matches:
        send_email(sorted(matches))
    else:
        print("Aucun match cette semaine.")

if __name__ == "__main__":
    main()
