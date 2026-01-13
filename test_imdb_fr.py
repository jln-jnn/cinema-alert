import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

CSV_WATCHLIST = "watchlist-tchernoalpha.csv"
MAX_TEST = 10  # nombre de films à tester

def get_imdb_id(imdb_url):
    if pd.isna(imdb_url):
        return None
    return imdb_url.strip("/").split("/")[-1]

def get_imdb_titles(imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"
    headers = {"Accept-Language": "fr-FR,fr;q=0.9"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Titre original (meta)
        original = None
        og = soup.find("meta", property="og:title")
        if og:
            original = og.get("content")

        # Titre FR (balise <h1>)
        h1 = soup.find("h1")
        fr = h1.text.strip() if h1 else None

        return original, fr
    except Exception as e:
        print(f"❌ Erreur IMDb {imdb_id}: {e}")
        return None, None

def main():
    df = pd.read_csv(CSV_WATCHLIST)

    tested = 0
    for _, row in df.iterrows():
        if tested >= MAX_TEST:
            break

        title = row["Name"]
        imdb_id = get_imdb_id(row.get("IMDb ID") or row.get("IMDbID") or row.get("IMDb"))

        if not imdb_id:
            continue

        original, fr = get_imdb_titles(imdb_id)

        print("\n🎬 Film Letterboxd :", title)
        print("🔗 IMDb ID :", imdb_id)
        print("🌍 Titre original IMDb :", original)
        print("🇫🇷 Titre FR IMDb :", fr)

        tested += 1
        time.sleep(1)  # on ralentit pour éviter le blocage IMDb

if __name__ == "__main__":
    main()
