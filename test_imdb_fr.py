import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb

# Lire la clé TMDb depuis la variable d'environnement
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("Merci de définir la variable d'environnement TMDB_API_KEY")
tmdb.API_KEY = TMDB_API_KEY

# Nom du CSV
csv_file = "watchlist-tchernoalpha.csv"

# Lire le CSV
df = pd.read_csv(csv_file)
print(f"Colonnes détectées dans le CSV : {list(df.columns)}")

# Ajouter les colonnes si elles n'existent pas
if 'TMDb ID' not in df.columns:
    df['TMDb ID'] = ""
if 'Titre FR' not in df.columns:
    df['Titre FR'] = ""

# Fonction pour récupérer l'IMDb ID depuis Letterboxd
def get_imdb_id(letterboxd_url):
    try:
        r = requests.get(letterboxd_url, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        link = soup.find("a", href=lambda x: x and "imdb.com/title" in x)
        if link:
            return link['href'].split("/title/")[1].strip("/")
    except Exception as e:
        print(f"⚠️ Erreur sur {letterboxd_url}: {e}")
    return None

# Fonction pour récupérer le TMDb ID et le titre français
def get_tmdb_info(imdb_id):
    try:
        search = tmdb.Find(imdb_id)
        response = search.info(external_source='imdb_id')
        results = response.get('movie_results', [])
        if results:
            movie = results[0]
            tmdb_id = movie.get('id')
            title_fr = movie.get('title')  # TMDb retourne le titre principal (souvent localisé)
            return tmdb_id, title_fr
    except Exception as e:
        print(f"⚠️ Erreur TMDb pour IMDb ID {imdb_id}: {e}")
    return None, None

# Boucle sur chaque film
for idx, row in df.iterrows():
    lb_url = row['Letterboxd URI']
    imdb_id = get_imdb_id(lb_url)
    if not imdb_id:
        print(f"⚠️ Aucun IMDb ID pour '{row['Name']}', skip")
        continue

    tmdb_id, titre_fr = get_tmdb_info(imdb_id)
    if tmdb_id and titre_fr:
        df.at[idx, 'TMDb ID'] = tmdb_id
        df.at[idx, 'Titre FR'] = titre_fr
        print(f"🎬 {row['Name']} => TMDb ID: {tmdb_id}, Titre FR: {titre_fr}")
    else:
        print(f"⚠️ Seulement IMDb trouvé : {imdb_id} (TMDb manquant)")

# Sauvegarder le CSV avec les nouvelles colonnes
df.to_csv(csv_file, index=False)
print(f"✅ CSV mis à jour avec titres FR et TMDb ID : {csv_file}")
