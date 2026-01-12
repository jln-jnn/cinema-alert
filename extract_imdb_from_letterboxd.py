import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

INPUT_CSV = "watchlist-tchernoalpha.csv"
OUTPUT_CSV = "watchlist_full.csv"


def get_imdb_id(letterboxd_url):
    try:
        r = requests.get(letterboxd_url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        imdb_link = soup.find("a", href=lambda x: x and "imdb.com/title" in x)
        if imdb_link:
            return imdb_link["href"].split("/title/")[1].split("/")[0]

    except Exception as e:
        print("Erreur sur", letterboxd_url, e)

    return None


def main():
    df = pd.read_csv(INPUT_CSV)

    imdb_ids = []

    for _, row in df.iterrows():
        url = row["Letterboxd URI"]
        print("Scraping IMDb pour :", url)

        imdb_id = get_imdb_id(url)
        imdb_ids.append(imdb_id)

        time.sleep(1)  # gentil avec Letterboxd

    df["imdb_id"] = imdb_ids
    df.to_csv(OUTPUT_CSV, index=False)

    print("✅ Fichier généré :", OUTPUT_CSV)


if __name__ == "__main__":
    main()
