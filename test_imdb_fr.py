import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

CSV_WATCHLIST = "watchlist-tchernoalpha.csv"
MAX_TEST = 10  # nombre de films à tester

# ---------- Fonctions ----------

def get_imdb_id(imdb_url):
    """Extrait l'ID IMDb d'une URL"""
    if pd.isna(imdb_url):
        return None
    parts = imdb_url.strip("/").split("/")
    if len(parts) >= 5 and parts[4].startswith("tt"):
        return parts[4]
    return None

def get_imdb_titles(imdb_id):
    """Récupère le titre original et le titre FR depuis IMDb"""
    url = f"https://www.imdb.com/title/{imdb_id}/"
    headers = {"Accept-Language": "fr-FR,fr;q=0.9"}  # pour obtenir le titre FR si dispo
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Titre FR principal
        title_span = soup.select_one('h1[data-testid="hero-title-block__title"]')
        fr_title = title_span.text.strip() if title_span else None

        # Titre original (s'il est différent)
        original_span = soup.select_one('li[data-testid="title-details-origin-title"] span')
        original_title = original_span.text.strip() if original_span else None

        return original_title, fr_title
    except Exception as e:
        print(f"❌ Erreur IMDb {imdb_id}: {e}")
        return None, None

# ---------- Script principal ----------

def main():
    df = pd.read_csv(CSV_WATCHLIST)
    print("Colonnes détectées dans le CSV :", list(df.columns))

    tested = 0
    for _, row in df.iterrows():
        if tested >= MAX_TEST:
            break

        title = row["Name"]
        # Essaye de récupérer IMDb ID depuis plusieurs colonnes possibles
        imdb_id = get_imdb_id(row.get("IMDb ID") or row.get("IMDbID") or row.get("IMDb"))

        if not imdb_id:
            print(f"⚠️ Aucun IMDb ID pour '{title}', skip")
            continue

        original, fr = get_imdb_titles(imdb_id)

        print("\n🎬 Film Letterboxd :", title)
        print("🔗 IMDb ID :", imdb_id)
        print("🌍 Titre original IMDb :", original)
        print("🇫🇷 Titre FR IMDb :", fr)

        tested += 1
        time.sleep(1)  # ralentissement pour éviter blocage IMDb

if __name__ == "__main__":
    main()
