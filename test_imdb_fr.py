import pandas as pd
import requests
from bs4 import BeautifulSoup
import tmdbsimple as tmdb

# 🔑 Mets ici ta clé TMDb
tmdb.API_KEY = "TA_CLE_TMDB"

# Charger le CSV
df = pd.read_csv("watchlist-tchernoalpha.csv")
print("Colonnes détectées dans le CSV :", df.columns.tolist())

def get_links_from_letterboxd(url):
    """
    Récupère les liens IMDb et TMDb depuis la page Letterboxd.
    Retourne (imdb_id, tmdb_id)
    """
    try:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        imdb_link = None
        tmdb_link = None

        # Cherche tous les liens externes
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'imdb.com/title/' in href:
                imdb_link = href.split('/')[-2]  # tt1234567
            elif 'themoviedb.org/movie/' in href:
                tmdb_link = href.split('/')[-1]  # 12345

        return imdb_link, tmdb_link
    except Exception as e:
        print(f"⚠️ Erreur sur {url} :", e)
        return None, None

def get_titles_from_tmdb(tmdb_id):
    """
    Récupère le titre original et français depuis TMDb.
    """
    try:
        movie = tmdb.Movies(tmdb_id)
        info = movie.info(language='fr-FR')
        title_fr = info.get('title', None)
        # fallback sur original_title si title_fr est vide
        if not title_fr:
            title_fr = info.get('original_title', None)
        title_original = info.get('original_title', None)
        return title_original, title_fr
    except Exception as e:
        print(f"⚠️ Impossible de récupérer TMDb ID {tmdb_id} :", e)
        return None, None

# Colonnes pour stocker les résultats
df['IMDb ID'] = None
df['TMDb ID'] = None
df['Titre Original'] = None
df['Titre FR'] = None

# Parcourir tous les films
for i, row in df.iterrows():
    name = row['Name']
    lb_url = row['Letterboxd URI']

    print(f"\n🎬 Film Letterboxd : {name}")
    imdb_id, tmdb_id = get_links_from_letterboxd(lb_url)
    df.at[i, 'IMDb ID'] = imdb_id
    df.at[i, 'TMDb ID'] = tmdb_id

    if tmdb_id:
        title_original, title_fr = get_titles_from_tmdb(tmdb_id)
        df.at[i, 'Titre Original'] = title_original
        df.at[i, 'Titre FR'] = title_fr
        print(f"✅ TMDb trouvé : {tmdb_id} | {title_original} / {title_fr}")
    elif imdb_id:
        # Ici tu peux intégrer IMDb comme fallback si nécessaire
        print(f"⚠️ Seulement IMDb trouvé : {imdb_id} (TMDb manquant)")
    else:
        print(f"⚠️ Aucun lien TMDb ou IMDb trouvé pour '{name}', skip")

# Sauvegarde du CSV mis à jour
df.to_csv("films_letterboxd_mis_a_jour.csv", index=False)
print("\n✅ CSV mis à jour avec IMDb/TMDb et titres.")
