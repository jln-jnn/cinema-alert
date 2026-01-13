import os
import pandas as pd
import requests

# TMDb API key depuis la variable d'environnement
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("Merci de définir la variable d'environnement TMDB_API_KEY.")

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"

CSV_FILE = "watchlist-tchernoalpha.csv"

# Charger le CSV
df = pd.read_csv(CSV_FILE)
print(f"Colonnes détectées dans le CSV : {list(df.columns)}")

# Créer les colonnes si elles n'existent pas
if "TMDb ID" not in df.columns:
    df["TMDb ID"] = ""
if "Titre FR" not in df.columns:
    df["Titre FR"] = ""

for idx, row in df.iterrows():
    if row.get("TMDb ID") and row.get("Titre FR"):
        continue  # déjà rempli, on skip

    film_name = row["Name"]
    year = row.get("Year", "")
    print(f"🎬 Film Letterboxd : {film_name}")

    # Requête TMDb
    params = {
        "api_key": TMDB_API_KEY,
        "query": film_name,
        "year": year if pd.notna(year) else None,
        "language": "fr-FR"
    }
    response = requests.get(TMDB_SEARCH_URL, params=params)
    if response.status_code != 200:
        print(f"⚠️ Erreur TMDb pour '{film_name}' : {response.status_code}")
        continue

    results = response.json().get("results", [])
    if not results:
        print(f"⚠️ Aucun résultat TMDb pour '{film_name}', skip")
        continue

    # On prend le premier résultat
    movie = results[0]
    tmdb_id = movie["id"]
    titre_fr = movie.get("title", film_name)

    df.at[idx, "TMDb ID"] = tmdb_id
    df.at[idx, "Titre FR"] = titre_fr
    print(f"✅ TMDb ID : {tmdb_id}, Titre FR : {titre_fr}")

# Sauvegarder définitivement le CSV
df.to_csv(CSV_FILE, index=False)
print(f"✅ CSV mis à jour avec titres FR et TMDb ID : {CSV_FILE}")
