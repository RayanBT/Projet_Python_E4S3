# tests/test_my_module.py

import os
import json
import pandas as pd
import pytest

from page_specific_component_carte import (
    load_geojson,
    load_csv,
    data_for_map,
    simplify_geojson,
    create_choropleth_map,
)

@pytest.fixture
def sample_csv_path(tmp_path): #A FAIRE
    # Création d’un CSV temporaire
    file = tmp_path / "sample.csv"
    file.write_text(
        "region,Ntop,other\n"
        "1,10,x\n"
        "99,5,y\n"
        "2,20,z\n"
    )
    return str(file)

@pytest.fixture
def sample_geojson_path(tmp_path): #A FAIRE
    # Création d’un GeoJSON temporaire minimal
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"code_insee_region": 1, "commune": "A"},
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "type": "Feature",
                "properties": {"code_insee_region": 2, "commune": "B"},
                "geometry": {"type": "Point", "coordinates": [1, 1]},
            },
        ],
    }
    file = tmp_path / "sample.geojson"
    with open(file, "w", encoding="utf‑8") as f:
        json.dump(geojson, f)
    return str(file)

def test_load_csv_filters_region_99(sample_csv_path):
    df = load_csv(sample_csv_path, dtype_dict={"region", "Ntop"})
    # On s’attend à ce que la ligne avec region == '99' soit supprimée
    assert all(df["region"] != 99)
    # Afficher les valeurs uniques de la colonne 'region' triées par ordre alphabétique
    valeurs_uniques_region = sorted(df['region'].unique())
    print(valeurs_uniques_region)

def test_load_geojson(sample_geojson_path):
    geo_data = load_geojson(sample_geojson_path)
    # Afficher les noms des clés principales 
    print("Clés principales du GeoJSON:")
    for feature in geo_data["features"][:1]: # Affiche les clés de la première entité
        print(feature.keys())
    # Afficher les noms de colonnes (clés) uniques
    properties = [feature['properties'] for feature in geo_data['features']]
    columns = set()
    for prop in properties:
        columns.update(prop.keys())
    print("Colonnes disponibles :", columns)
    #Colonnes disponibles : {'code_ancienne_region', 'departement', 'code_commune', 'geo_point', 'code_departement', 'commune', 'region', 'epci', 'ancienne_region', 'intitule_commune', 'code_insee_region', 'code_epci'}

    # Afficher les valeurs distinctes de 'feature.properties.code_commune'
    codes_commune = set()
    for feature in geo_data["features"]:
        codes_commune.add(feature["properties"].get("code_insee_region"))
    print("\nValeurs distinctes de 'code_insee_region' :")
    print(sorted(codes_commune))

def test_data_for_map_simple():
    # Préparer un DataFrame simple
    df = pd.DataFrame({
        "region": [1, 1, 2],
        "Ntop": [10, 5, 20],
        "patho": ['cancer', 'cancer', 'cancer']
    })
    result = data_for_map(df, group_col="region", agg_col="Ntop")
    # On s’attend à un Dataframe de 2 lignes 2 colones 

def test_simplify_geojson_creates_file(sample_geojson_path, tmp_path):
    output_file = tmp_path / "out.geojson"
    simplify_geojson(
        geo_data=load_geojson(sample_geojson_path),
        essential_keys=["code_insee_region"],
        output_path=str(output_file),
        tolerance=0.1
    )
    # Le fichier doit exister après appel
    assert output_file.exists()
    # Le contenu doit être un GeoJSON valide
    with open(output_file, "r", encoding="utf‑8") as f:
        data = json.load(f)
    assert data["type"] == "FeatureCollection"
    # Vérifier que chaque feature conserve la propriété « code_insee_region »
    for feat in data["features"]:
        assert "code_insee_region" in feat["properties"]

def test_create_choropleth_map_creates_html(tmp_path, sample_geojson_path):
    # Préparer un DataFrame simple
    df = pd.DataFrame({
        "region": [1, 2],
        "Ntop": [15, 20]
    })
    output_html = tmp_path / "map.html"
    map_obj = create_choropleth_map(
        geojson_path=sample_geojson_path,
        data=df,
        output_path=str(output_html),
        key_on='feature.properties.code_insee_region',
        columns=['region', 'Ntop'],
        location=(0, 0),
        zoom_start=2
    )
    # Vérifier que l’objet retourné est bien un folium.Map
    assert hasattr(map_obj, "save")
    # Vérifier que le fichier html est créé
    assert output_html.exists()
