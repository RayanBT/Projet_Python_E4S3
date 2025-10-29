import pandas as pd
import json
import folium
from shapely.geometry import shape, mapping

# --- Charger le GeoJSON ---
with open("src/pages/more_complex_page/datagouv-communes.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# --- Charger le CSV ---
dtype_dict = {
    'top': str,
    'tri': float,
    'Npop': int,
    'Ntop': int,
    'dept': str,
    'prev': str,
    'sexe': int,
    'annee': 'Int64',
    'region': str,
    'cla_age_5': str,
    'patho_niv1': str,
    'patho_niv2': str,
    'patho_niv3': str,
    'libelle_sexe': str,
    'Niveau prioritaire': str,
    'libelle_classe_age': str
}

df = pd.read_csv("data/clean/csv_clean.csv", sep=",", dtype=dtype_dict)

# --- Nettoyage ---
df = df[(df['region'] != '99')]
df['region'] = df['region'].astype(int)

# --- Somme de tous les cas par région ---
data_for_map = df.groupby('region', as_index=False)['Ntop'].sum()

# --- Simplification du GeoJSON ---
essential_keys = ["code_insee_region", "commune"]
simplified_features = []

for feature in geo_data["features"]:
    properties = {k: feature["properties"][k] for k in essential_keys if k in feature["properties"]}
    geom = shape(feature["geometry"]).simplify(0.001, preserve_topology=True)
    simplified_features.append({
        "type": "Feature",
        "properties": properties,git
        "geometry": mapping(geom)
    })

simplified_geojson = {
    "type": "FeatureCollection",
    "features": simplified_features
}

with open("src/pages/more_complex_page/geo_simplified.json", "w", encoding="utf-8") as f:
    json.dump(simplified_geojson, f)

# --- Création de la carte ---
map = folium.Map(location=(46.5, 2.5), zoom_start=6, tiles='OpenStreetMap')

folium.Choropleth(
    geo_data="src/pages/more_complex_page/geo_simplified.json",
    name='choropleth',
    data=data_for_map,
    columns=['region', 'Ntop'],
    key_on='feature.properties.code_insee_region',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Nombre total de cas (toutes pathologies)',
    #threshold_scale=[0, 1000, 5000, 10000, 50000, 100000, 1000000000]
).add_to(map)

map.save("src/pages/carte3.html")

print("Carte générée avec succès : src/pages/carte3.html")
