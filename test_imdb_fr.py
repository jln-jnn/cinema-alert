import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb

# Récupérer la clé TMDb depuis l'environnement
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY non défini dans les secrets GitHub !")
tmdb.API_KEY = TMDB_API_KEY

CSV_FILE = "watchlist-tchernoalpha.csv"

# Lire le CSV
df = pd.read_csv(CSV_FILE)
print(f"Colonnes détectées dans le CSV : {list(df.columns)}")

# Ajouter les colonnes si elles n'existent pas
if "TMDb ID" not in df.columns:
    df["TMDb ID"] = ""
if "Titre FR" not in df.columns:
    df["Titre FR"] = ""

# Fonction pour récupérer l'IMDb ID depuis Letterboxd
def get_imdb_id(letterboxd_url):
    try:
        resp = requests.get(letterboxd_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        link_imdb = soup.find("a", href=lambda x: x and "imdb.com/title/" in x)
        if link_imdb:
            return link_imdb["href"].split("/title/")[1].split("/")[0]
        return None
    except requests.HTTPError as e:
        print(f"⚠️ Erreur sur {letterboxd_url} : {e}")
        return None

# Fonction pour récupérer TMDb ID et titre français via TMDb
def get_tmdb_info(imdb_id):
    try:
        search = tmdb.Find(imdb_id)
        result = search.info(external_source="imdb_id")
        if result.get("movie_results"):
            movie = result["movie_results"][0]
            tmdb_id = movie["id"]
            # Récupérer le titre FR si disponible
            movie_details = tmdb.Movies(tmdb_id).info(language="fr-FR")
            titre_fr = movie_details.get("title") or movie_details.get("original_title")
            return tmdb_id, titre_fr
        return None, None
    except Exception as e:
        print(f"⚠️ Erreur TMDb pour IMDb {imdb_id} : {e}")
        return None, None

# Parcourir tous les films
for idx, row in df.iterrows():
    lb_url = row.get("Letterboxd URI")
    if not lb_url or pd.isna(lb_url):
        continue

    print(f"\n🎬 Film Letterboxd : {row.get('Name')}")

    imdb_id = get_imdb_id(lb_url)
    if not imdb_id:
        print(f"⚠️ Aucun IMDb ID pour '{row.get('Name')}', skip")
        continue

    tmdb_id, titre_fr = get_tmdb_info(imdb_id)
    if tmdb_id:
        df.at[idx, "TMDb ID"] = tmdb_id
    if titre_fr:
        df.at[idx, "Titre FR"] = titre_fr

# Sauvegarder le CSV mis à jour
df.to_csv(CSV_FILE, index=False)
print(f"\n✅ CSV mis à jour avec titres FR et TMDb ID : {CSV_FILE}")
