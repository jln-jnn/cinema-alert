import requests
from bs4 import BeautifulSoup
import pandas as pd

CSV_WATCHLIST = "watchlist-tchernoalpha.csv"

def get_imdb_id_from_letterboxd(slug):
    url = f"https://letterboxd.com/film/{slug}/"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    imdb_link = soup.find("a", href=lambda x: x and "imdb.com/title" in x)
    if imdb_link:
        return imdb_link["href"].split("/title/")[1].split("/")[0]
    return None

def get_titles_from_imdb(imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # Titre original
    original = soup.find("h1")
    original_title = original.text.strip() if original else None

    # Titre français (s’il existe)
    fr_title = None
    akas = soup.find("a", href=lambda x: x and "releaseinfo" in x)
    if akas:
        fr_title = akas.text.strip()

    return original_title, fr_title

def main():
    df = pd.read_csv(CSV_WATCHLIST)

    # 👉 On teste UNIQUEMENT le premier film
    film = df.iloc[0]
    lb_name = film["Name"]
    lb_slug = film["Name"].lower().replace(" ", "-")

    print(f"🎬 Film Letterboxd : {lb_name}")

    imdb_id = get_imdb_id_from_letterboxd(lb_slug)
    print(f"🔗 IMDb ID : {imdb_id}")

    if not imdb_id:
        print("❌ IMDb ID non trouvé")
        return

    original, fr = get_titles_from_imdb(imdb_id)
    print(f"🌍 Titre original IMDb : {original}")
    print(f"🇫🇷 Titre FR IMDb : {fr}")

if __name__ == "__main__":
    main()
