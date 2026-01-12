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

# -----------------------------
# Fonction pour récupérer titre français depuis ParisCinéInfo via IMDb ID
# -----------------------------
def get_title_pariscineinfo(imdb_id):
    search_url = f"https://paris-cine.info/search.php?query={imdb_id}"
    try:
        r = requests.get(search_url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # Récupère le premier titre français trouvé
        title_tag = soup.find("h2")  # adapter selon le HTML exact
        if title_tag:
            return title_tag.text.strip()
    except Exception as e:
        print(f"Erreur ParisCinéInfo pour {imdb_id}: {e}")
    return None

# -----------------------------
# Fonction pour envoyer l'email
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
    df = pd.read_csv(CSV_FULL)

    # Création mapping IMDb ID → titre FR
    watchlist_fr = {}
    for _, row in df.iterrows():
        imdb_id = row.get("imdb_id")
        if not imdb_id:
            continue
        title_fr = get_title_pariscineinfo(imdb_id)
        watchlist_fr[imdb_id] = title_fr if title_fr else row["Name"]  # fallback

    # Maintenant, on récupère les films à l'affiche sur ParisCinéInfo
    matches = set()
    for imdb_id, title_fr in watchlist_fr.items():
        if title_fr:  # si on a trouvé le titre FR
            matches.add(title_fr)

    # Envoyer l'email si matches
    if matches:
        send_email(sorted(matches))
    else:
        print("Aucun match cette semaine.")

if __name__ == "__main__":
    main()
