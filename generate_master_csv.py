import pandas as pd
import requests

INPUT_CSV = "watchlist-tchernoalpha.csv"
OUTPUT_CSV = "watchlist_full.csv"

def get_vo_fr_wikidata(title, year):
    """Récupère le titre original translittéré et le titre français via Wikidata"""
    if year is None:
        year = 0
    safe_title = title.replace('"', '\\"')
    query = f"""
    SELECT ?voTitle ?frTitle WHERE {{
      ?film wdt:P31 wd:Q11424;
            rdfs:label "{safe_title}"@en;
            wdt:P577 ?date.
      FILTER(YEAR(?date) = {year})
      OPTIONAL {{ ?film rdfs:label ?frTitle FILTER(LANG(?frTitle) = "fr") }}
      OPTIONAL {{ ?film rdfs:label ?voTitle FILTER(LANG(?voTitle) = "und") }}
    }}
    LIMIT 1
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    try:
        r = requests.get(url, params={"query": query}, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        vo = data["results"]["bindings"][0]["voTitle"]["value"].lower() if "voTitle" in data["results"]["bindings"][0] else title.lower()
        fr = data["results"]["bindings"][0]["frTitle"]["value"].lower() if "frTitle" in data["results"]["bindings"][0] else title.lower()
        return vo, fr
    except Exception as e:
        print(f"⚠️ Échec Wikidata pour {title} ({year}): {e}")
        return title.lower(), title.lower()

# Lire CSV Letterboxd
df = pd.read_csv(INPUT_CSV)
vos, frs = [], []

for _, row in df.iterrows():
    title = str(row['Name']).strip()
    year = int(row['Year']) if not pd.isna(row['Year']) else None
    vo, fr = get_vo_fr_wikidata(title, year)
    print(f"{title} ({year}) → VO: {vo}, FR: {fr}")
    vos.append(vo)
    frs.append(fr)

df["Title_VO"] = vos
df["Title_FR"] = frs

df.to_csv(OUTPUT_CSV, index=False)
print(f"CSV master sauvegardé : {OUTPUT_CSV}")
