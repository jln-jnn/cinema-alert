import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb

# -----------------------------
# Initialisation TMDb
# -----------------------------
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("Il faut définir TMDB_API_KEY dans les secrets GitHub.")
tmdb.API_KEY = TMDB_API_KEY

# -----------------------------
# Lire le CSV
# -----------------------------
csv_file = "watchlist-tchernoalpha.csv"
df = pd.read_csv(csv_file)

print(f"Colonnes détectées dans le CSV : {list(df.columns)}")

# -----------------------------
# Ajouter les colonnes si elles n'existent pas
# -----------------------------
if "TMDb ID" not in df.columns:
    df["TMDb ID"] = ""
if "Titre FR" not in df.columns:
    df["Titre FR"] = ""

# -----------------------------
# Fonction pour récupérer l'ID IMDb depuis la page Letterboxd
# -----------------------------
def get_imdb_id(letterboxd_url):
    try:
        resp = requests.get(letterboxd_url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            print(f"⚠️ Erreur sur {letterboxd_url} : {resp.status_code}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        imdb_link = soup.find("a", href=lambda href: href and "imdb.com/title" in href)
        if imdb_link:
            return imdb_link["href"].split("/title/")[1].split("/")[0]
        return None
    except Exception as e:
        print(f"⚠️ Exception sur {letterboxd_url} : {e}")
        return None

# -----------------------------
# Fonction pour récupérer TMDb ID et titre français
# -----------------------------
def get_tmdb_info(imdb_id):
    try:
        search = tmdb.Find(imdb_id)
        response = search.info(external_source="imdb_id")
        results = response.get("movie_results", [])
        if not results:
            return None, None
        movie = results[0]
        tmdb_id = movie.get("id")
        titre_fr = movie.get("title")
        # Chercher le titre français
        details = tmdb.Movies(tmdb_id).info(language="fr-FR")
        titre_fr = details.get("title") or titre_fr
        return tmdb_id, titre_fr
    except Exception as e:
        print(f"⚠️ Erreur TMDb pour IMDb {imdb_id} : {e}")
        return None, None

# -----------------------------
# Boucle sur les films
# -----------------------------
for idx, row in df.iterrows():
    letterboxd_url = row.get("Letterboxd URI")
    if not letterboxd_url:
        continue

    if pd.notna(row["TMDb ID"]) and pd.notna(row["Titre FR"]) and row["TMDb ID"] != "":
        continue  # déjà rempli

    print(f"🎬 Film Letterboxd : {row['Name']}")

    imdb_id = get_imdb_id(letterboxd_url)
    if not imdb_id:
        print(f"⚠️ Aucun IMDb ID pour '{row['Name']}', skip")
        continue

    tmdb_id, titre_fr = get_tmdb_info(imdb_id)
    if not tmdb_id:
        print(f"⚠️ IMDb trouvé ({imdb_id}) mais TMDb manquant pour '{row['Name']}'")
        continue

    df.at[idx, "TMDb ID"] = tmdb_id
    df.at[idx, "Titre FR"] = titre_fr
    print(f"✅ {row['Name']} -> TMDb ID: {tmdb_id}, Titre FR: {titre_fr}")

# -----------------------------
# Écriture définitive du CSV
# -----------------------------
df.to_csv(csv_file, index=False)
print(f"✅ CSV mis à jour avec titres FR et TMDb ID : {csv_file}")
