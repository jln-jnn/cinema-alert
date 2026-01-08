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

def get_watchlist():
    import re
    url = f"https://letterboxd.com/{LETTERBOXD_USER}/watchlist/"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    # Cherche tous les titres entre <img ... alt="Titre du film" ...>
    titles = re.findall(r'alt="([^"]+)"', html)
    return set(t.lower() for t in titles)


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
    watchlist = get_watchlist()
    print("WATCHLIST DETECTÉE :", sorted(watchlist)[:10])
    paris = get_paris_cine_films()
    notified = load_state()
    matches = watchlist & paris - notified
    if matches:
        send_email(matches)
        save_state(notified | matches)

main()
