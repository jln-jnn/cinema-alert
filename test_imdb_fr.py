import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb

# -----------------------------
# Config TMDb avec la clé depuis le secret
# -----------------------------
tmdb_api_key = os.environ.get("TMDB_API_KEY")
if not tmdb_api_key:
    raise ValueError("Clé TMDb manquante ! Mets TMDB_API_KEY dans les secrets GitHub.")
tmdb.API_KEY = tmdb_api_key

# -----------------------------
# Fichier CSV
# -----------------------------
CSV_FILE = "watchlist-tchernoalpha.csv"

# -----------------------------
# Lire le CSV
# -----------------------------
df = pd.read_csv(CSV_FILE)
print("Colonnes détectées dans le CSV :", df.columns.tolist())

# Créer colonnes TMDb ID et titre français si elles n'existent pas
if 'TMDb ID' not in df.columns:
    df['TMDb ID'] = ''
if 'Titre FR' not in df.columns:
    df['Titre FR'] = ''

# -----------------------------
# Fonction pour récupérer les IDs depuis Letterboxd
# -----------------------------
def get_ids_from_letterboxd(url):
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erreur sur {url} : {e}")
        return None, None

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Rechercher le lien IMDb
    imdb_link = soup.find('a', href=lambda x: x and "imdb.com/title" in x)
    imdb_id = imdb_link['href'].split('/')[4] if imdb_link else None

    # Rechercher le lien TMDb
    tmdb_link = soup.find('a', href=lambda x: x and "themoviedb.org/movie" in x)
    tmdb_id = tmdb_link['href'].split('/')[-1] if tmdb_link else None

    return imdb_id, tmdb_id

# -----------------------------
# Fonction pour récupérer le titre français via TMDb
# -----------------------------
def get_fr_title(tmdb_id):
    if not tmdb_id:
        return None
    try:
        movie = tmdb.Movies(tmdb_id).info(language='fr-FR')
        return movie.get('title') or None
    except Exception as e:
        print(f"⚠️ Erreur TMDb pour {tmdb_id} : {e}")
        return None

# -----------------------------
# Parcours des films
# -----------------------------
for idx, row in df.iterrows():
    name = row['Name']
    lb_url = row['Letterboxd URI']
    
    if pd.notna(row['TMDb ID']) and pd.notna(row['Titre FR']):
        # Déjà rempli
        continue

    print(f"\n🎬 Film Letterboxd : {name}")
    imdb_id, tmdb_id = get_ids_from_letterboxd(lb_url)
    
    if not imdb_id and not tmdb_id:
        print(f"⚠️ Aucun lien IMDb ou TMDb trouvé pour '{name}', skip")
        continue

    # Si TMDb ID manquant mais IMDb présent, chercher sur TMDb via IMDb
    if not tmdb_id and imdb_id:
        try:
            search = tmdb.Find(imdb_id).info(external_source='imdb_id')
            results = search.get('movie_results')
            if results:
                tmdb_id = results[0]['id']
        except Exception as e:
            print(f"⚠️ Erreur recherche TMDb via IMDb pour {imdb_id} : {e}")

    # Récupérer le titre français
    titre_fr = get_fr_title(tmdb_id)

    # Mettre à jour le CSV
    df.at[idx, 'TMDb ID'] = tmdb_id or ''
    df.at[idx, 'Titre FR'] = titre_fr or ''

    print(f"✅ TMDb ID : {tmdb_id} | Titre FR : {titre_fr}")

# -----------------------------
# Sauvegarder le CSV mis à jour
# -----------------------------
df.to_csv(CSV_FILE, index=False)
print(f"\n✅ CSV mis à jour avec titres FR et TMDb ID : {CSV_FILE}")
