import pandas as pd
import tmdbsimple as tmdb

# ⚠️ Mets ici ta clé TMDb
tmdb.API_KEY = "VOTRE_TMDB_API_KEY"

CSV_FILE = "watchlist-tchernoalpha.csv"

df = pd.read_csv(CSV_FILE)
print(f"Colonnes détectées dans le CSV : {df.columns.tolist()}")

# Créer les colonnes si elles n'existent pas
for col in ["IMDb ID", "TMDb ID", "Title Original", "Title FR"]:
    if col not in df.columns:
        df[col] = None

for idx, row in df.iterrows():
    imdb_id = row.get("IMDb ID")
    if pd.isna(imdb_id):
        print(f"⚠️ Aucun IMDb ID pour '{row['Name']}', skip")
        continue

    try:
        # Cherche le film sur TMDb via l'ID IMDb
        finder = tmdb.Find(imdb_id)
        result = finder.info(external_source='imdb_id')
        movie_data = result['movie_results'][0] if result['movie_results'] else None

        if movie_data:
            tmdb_id = movie_data['id']
            df.at[idx, "TMDb ID"] = tmdb_id
            df.at[idx, "Title Original"] = movie_data['title']

            # Chercher traduction FR
            translations = tmdb.Movies(tmdb_id).translations()['translations']
            title_fr = None
            for t in translations:
                if t['iso_3166_1'] == 'FR':
                    title_fr = t['data'].get('title')
                    break
            df.at[idx, "Title FR"] = title_fr

            print(f"✅ {row['Name']} enrichi : TMDb={tmdb_id}, FR={title_fr}")

        else:
            print(f"⚠️ Aucun résultat TMDb pour {row['Name']}")

    except Exception as e:
        print(f"⚠️ Erreur pour {row['Name']}: {e}")

# Sauvegarde le CSV enrichi
df.to_csv(CSV_FILE, index=False)
print("✅ CSV mis à jour avec titres FR et TMDb ID")
