import pandas as pd
import json
import folium
from shapely.geometry import shape, mapping
from typing import List, Dict, Any, Tuple


def load_geojson(path: str) -> Dict[str, Any]:
    """Charge un fichier GeoJSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: str, dtype_dict: Dict[str, Any] = None) -> pd.DataFrame:
    """Charge un fichier CSV (avec types spécifiques si besoin)."""
    df: pd.DataFrame = pd.read_csv(path, sep=",", dtype=dtype_dict) #MODIF POUR QUE ; !!!!!!!!!
    # Nettoyage de base 
    df = df[df['region'] != '99'] #On filtre le code COG (de l'INSEE) 99 qui désigne les territoires étrangers (hors France métropolitaine/DOM‑COM) car ce n'es pas cartographiable (le code n'est pas présent dans le geojson)
    df['region'] = df['region'].astype(int)#A VERIFIER UTILITE !!!!!!!
    return df


def data_for_map(df: pd.DataFrame, group_col: str='region', agg_col: str='Ntop') -> pd.DataFrame:
    """Fait la somme du nombre de pathologies (ou autre colonne numérique) par région (ou autre colonne)."""
    return df.groupby(group_col, as_index=False)[agg_col].sum()


def simplify_geojson(
    geo_data: Dict[str, Any],
    essential_keys: List[str],
    output_path: str,
    tolerance: float=0.002
) -> None:
    """Simplifie le GeoJSON (conserve les propriétés utiles et simplifie les géométries)"""
    simplified_features: List[Dict[str, Any]] = []
    for feature in geo_data["features"]:
        # Garde uniquement les propriétés essentielles
        properties: Dict[str, Any] = {k: feature["properties"][k] for k in essential_keys if k in feature["properties"]}
        # Simplifie la géométrie
        geom = shape(feature["geometry"]).simplify(tolerance, preserve_topology=True)
        # Crée la nouvelle feature simplifiée
        simplified_features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": mapping(geom)
        })
    # Crée le GeoJSON simplifié
    simplified_geojson: Dict[str, Any] = {"type": "FeatureCollection", "features": simplified_features}
    # Enregistre le GeoJSON simplifié
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(simplified_geojson, f)


def create_choropleth_map(
    geojson_path: str,
    data: pd.DataFrame,
    output_path: str,
    key_on: str,
    columns: List[str],
    location: Tuple[float, float]=(46.5, 2.5),
    zoom_start: int=6
) -> folium.Map:
    """Crée une carte choroplèthe avec Folium et la sauvegarde."""
    map_obj: folium.Map = folium.Map(location=location, zoom_start=zoom_start, tiles='OpenStreetMap')
    folium.Choropleth(
        geo_data=geojson_path,
        name='choropleth',
        data=data,
        columns=columns,
        key_on=key_on,
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Nombre total de cas (toutes pathologies)'
    ).add_to(map_obj)
    #Enregistre la carte dans la page html
    map_obj.save(output_path)
    print(f"Carte générée avec succès : {output_path}")
    return map_obj


def main():
    geojson_path = "src/pages/more_complex_page/datagouv-communes.geojson"
    csv_path = "data/clean/csv_clean.csv"
    simplified_geojson_path = "src/pages/more_complex_page/geo_simplified.json"
    output_map_path = "src/pages/carte3.html"

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

    geo_data = load_geojson(geojson_path)
    df = load_csv(csv_path, dtype_dict)
    data_for_map_df = data_for_map(df, 'region', 'Ntop')

    essential_keys = ["code_insee_region", "commune"]
    simplify_geojson(geo_data, essential_keys, simplified_geojson_path)

    create_choropleth_map(
        geojson_path=simplified_geojson_path,
        data=data_for_map_df,
        columns=['region', 'Ntop'],
        key_on='feature.properties.code_insee_region',
        output_path=output_map_path
    )
