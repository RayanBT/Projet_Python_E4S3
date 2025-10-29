# src/pages/simple_page.py
from dash import html, dcc
import pandas as pd
import json
import folium
import os

def layout():
    """Layout de la page simple avec la carte filtrée."""
    # --- 1) Chargement et simplification du GeoJSON (exécution à chaque appel ou mieux en amont) ---
    input_geo = "src/pages/more_complex_page/datagouv-communes.geojson"
    simplified_geo = "src/pages/more_complex_page/geo_simplified.json"
    if not os.path.exists(simplified_geo):
        with open(input_geo, "r", encoding="utf‑8") as f:
            geo_data = json.load(f)
        # Filtrer les features selon ton critère (ex. régions utiles)
        utile_codes = [1, 2, 3, 4, 6, 11, 24, 27, 28, 32, 44, 52, 53, 75, 76, 84, 93, 94]
        simplified_features = []
        for feat in geo_data["features"]:
            if feat["properties"].get("code_insee_region") in utile_codes:
                # garder seulement les propriétés essentielles
                props = {
                    "code_insee_region": feat["properties"].get("code_insee_region"),
                    "region": feat["properties"].get("region")
                }
                simplified_features.append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": feat["geometry"]
                })
        small_geo = {
            "type": "FeatureCollection",
            "features": simplified_features
        }
        with open(simplified_geo, "w", encoding="utf‑8") as f2:
            json.dump(small_geo, f2)

    # --- 2) Chargement des données CSV ---
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
    df = df[(df['patho_niv1'] == 'Maladies cardioneurovasculaires') & (df['region'] != '99')]
    df['region'] = df['region'].astype(int)  # pour correspondre au code_insee_region
    data_for_map = df[['region', 'Ntop']].copy()

    # --- 3) Création de la carte Folium ---
    m = folium.Map(location=(46.5, 2.5), zoom_start=6, tiles='OpenStreetMap')
    folium.Choropleth(
        geo_data=simplified_geo,
        name='choropleth',
        data=data_for_map,
        columns=['region','Ntop'],
        key_on='feature.properties.code_insee_region',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Nombre de cas'
    ).add_to(m)

    output_html = "src/pages/more_complex_page/carte2.html"
    m.save(output_html)

    # --- 4) Intégration dans l’iframe de Dash ---
    return html.Div(
        children=[
            html.H2("Page Simple avec Carte"),
            html.P("Ceci est une page simple de démonstration avec carte."),
            html.Iframe(
                srcDoc=open(output_html, 'r', encoding='utf‑8').read(),
                style={"width": "100%", "height": "600px", "border": "none"}
            ),
        ],
        style={"padding": "20px"},
    )


layout()