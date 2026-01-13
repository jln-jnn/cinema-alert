import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb
import os

CSV_FILE = "watchlist-tchernoalpha.csv"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
tmdb.API_KEY = TMDB_API_KEY

df = pd.read_csv(CSV_FILE)
print("Colonnes détectées dans le CSV :", list(df.columns))

# Créer les colonnes si elles n'existent pas
if "TMDb ID" not in df.columns:
    df["TMDb ID"] = ""
if "Titre FR" not in df.columns:
    df["Titre FR"] = ""

for idx, row in df.iterrows():
    letterboxd_url = row["Letterboxd URI"]
    print(f"\n🎬 Film Letterboxd : {row['Name']}")

    try:
        resp = requests.get(letterboxd_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Chercher le lien IMDb
        imdb_link = soup.find("a", href=lambda h: h and "imdb.com/title" in h)
        if imdb_link:
            imdb_id = imdb_link["href"].split("/")[4]
        else:
            print(f"⚠️ Aucun IMDb ID pour '{row['Name']}', skip")
            continue

        # Chercher le lien TMDb
        tmdb_link = soup.find("a", href=lambda h: h and "themoviedb.org/movie" in h)
        if tmdb_link:
            tmdb_id = tmdb_link["href"].split("/")[-1]
            df.at[idx, "TMDb ID"] = tmdb_id

            # Récupérer le titre français via TMDb
            movie = tmdb.Movies(tmdb_id)
            info = movie.info(language="fr-FR")
            df.at[idx, "Titre FR"] = info.get("title", "")
        else:
            print(f"⚠️ Seulement IMDb trouvé : {imdb_id} (TMDb manquant)")

    except Exception as e:
        print(f"⚠️ Erreur sur {letterboxd_url} : {e}")
        continue

# Sauvegarder définitivement le CSV
df.to_csv(CSV_FILE, index=False)
print(f"\n✅ CSV mis à jour avec titres FR et TMDb ID : {CSV_FILE}")
