import pandas as pd
import requests
from fuzzywuzzy import fuzz
import smtplib
from email.message import EmailMessage
import os

CSV_WATCHLIST = "watchlist-tchernoalpha.csv"

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# --------------------------------------------------
# Scrape Paris Ciné Info via l’API JSON officielle
# --------------------------------------------------
def scrape_pariscine():
    url = (
        "https://paris-cine.info/get_pcimovies.php"
        "?selday=week&seldayid=0&selcard=all&selformat=all"
        "&seladdr=&selcine=&selevent=&seltime=all"
        "&sellang=all&init=true&watchtype=&debug="
    )

    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    films = []
    for row in data:
        fr_title = row.get("ti")
        vo_title = row.get("o_ti") or fr_title
        if fr_title:
            films.append((fr_title.strip(), vo_title.strip()))

    print(f"Nombre de films scrappés sur ParisCinéInfo : {len(films)}")

    # DEBUG : afficher quelques films
    for fr, vo in films[:10]:
        print(f"{fr} → {vo}")

    return films


# --------------------------------------------------
# Envoi email
# --------------------------------------------------
def send_email(matches):
    if not matches:
        print("Aucun match cette semaine.")
        return

    msg = EmailMessage()
    msg["Subject"] = "🎬 Films de ta watchlist à l'affiche cette semaine"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content("Films détectés :\n\n" + "\n".join(sorted(matches)))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print(f"Mail envoyé avec {len(matches)} films.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    df = pd.read_csv(CSV_WATCHLIST)
    watchlist_titles = [t.strip() for t in df["Name"].dropna().tolist()]

    paris_films = scrape_pariscine()

    matches = set()
    for lb_title in watchlist_titles:
        for fr_title, vo_title in paris_films:
            score = fuzz.token_set_ratio(lb_title.lower(), vo_title.lower())
            if score >= 80:
                matches.add(fr_title)

    if matches:
        send_email(matches)
    else:
        print("Aucun match cette semaine.")


if __name__ == "__main__":
    main()
