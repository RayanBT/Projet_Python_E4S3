import pandas as pd
#import geojson #, geopandas
import json
import webbrowser
import folium

import json
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj

#RECUP GEOJSON SUR INTERNET A METTRE 
# lecture du fichier global
#france = geopandas.read_file("datagouv-communes.geojson")



# Charger le fichier GeoJSON
with open("src/pages/more_complex_page/datagouv-communes.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# Afficher les noms des colonnes (clés principales)
print("Clés principales du GeoJSON:")
for feature in geo_data["features"][:1]:  # Afficher les clés de la première entité
    print(feature.keys())

properties = [feature['properties'] for feature in geo_data['features']]

# Afficher les noms de colonnes (clés) uniques
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



# 1) Charger le fichier CSV

# Définir les types de données pour chaque colonne
dtype_dict = {
    'top': str,
    'tri': float,
    'Npop': int,
    'Ntop': int,
    'dept': str,
    'prev': str,
    'sexe': int,
    'annee': 'Int64',  # Utilisation de 'Int64' pour gérer les valeurs manquantes
    'region': str,
    'cla_age_5': str,
    'patho_niv1': str,
    'patho_niv2': str,
    'patho_niv3': str,
    'libelle_sexe': str,
    'Niveau prioritaire': str,
    'libelle_classe_age': str
}

df = pd.read_csv("data/clean/csv_clean.csv", sep=",", dtype = dtype_dict)   #CHANGER CLEAN POUR QUE SEPARATUER ; 
print(df.columns)

# Afficher les valeurs uniques de la colonne 'region' triées par ordre alphabétique
valeurs_uniques_region = sorted(df['region'].unique())
print(valeurs_uniques_region)

# 2) Filtrer une année, une pathologie, un sexe, une tranche d’âge
df = df[(df['patho_niv1'] == 'Maladies cardioneurovasculaires') & (df['region']!=99)]
#df_sel = df[(df['annee']==2015)
#            & (df['patho_niv3']=="Artériopathie périphérique")
#            & (df['sexe']==2)  # 2 = femmes
#            & (df['cla_age_5']=="45-49")]

# 3) Préparer les données pour la carte : on veut le nombre de malades (Ntop) ou la prévalence (prev) par département
# Par exemple : utiliser prev
data_for_map = df[['Ntop', 'region']].copy()
data_for_map['region'] = data_for_map['region'].astype(int)
valeurs_uniques_region = sorted(data_for_map['region'].unique())
print("datamap : ", valeurs_uniques_region)
#data_for_map.columns = ['code_dept', 'prev']

# 4) Charger le GeoJSON des départements français 
geo_json = "src/pages/more_complex_page/datagouv-communes.geojson"  # chemin vers un fichier GeoJSON des départements  
# Ce fichier doit contenir un champ "code" ou équivalent servant à faire le lien



# Charger le GeoJSON complet
with open("src/pages/more_complex_page/datagouv-communes.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# Garder uniquement les champs essentiels
essential_keys = ["code_insee_region", "commune"]  # à adapter selon ton usage

simplified_features = []

for feature in geo_data["features"]:
    # Conserver uniquement les propriétés essentielles
    properties = {k: feature["properties"][k] for k in essential_keys if k in feature["properties"]}
    
    # Simplifier la géométrie pour réduire la taille (optionnel mais fortement recommandé)
    geom = shape(feature["geometry"])
    
    # Simplification : tolérance à ajuster (en degrés, approx)
    simplified_geom = geom.simplify(0.001, preserve_topology=True)
    
    simplified_features.append({
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(simplified_geom)
    })

# Créer le GeoJSON simplifié
simplified_geojson = {
    "type": "FeatureCollection",
    "features": simplified_features
}

# Sauvegarder dans un nouveau fichier
with open("src/pages/more_complex_page/geo_simplified.json", "w", encoding="utf-8") as f:
    json.dump(simplified_geojson, f)


# 5) Créer la carte
map = folium.Map(location=(46.5, 2.5), zoom_start=6, tiles='OpenStreetMap')

# 6) Ajouter la couche choroplèthe
folium.Choropleth(
    geo_data="src/pages/more_complex_page/geo_simplified.json",
    name='choropleth',
    data=data_for_map,
    columns=['region','Ntop'],
    key_on='feature.properties.code_insee_region',  # adapter selon champ dans le GeoJSON
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Population avec cancer',
    threshold_scale=[0, 20, 30, 50, 300, 1000, 10000000]
).add_to(map)

# 7) Ajouter éventuellement des infobulles
#folium.LayerControl().add_to(map)

# 8) Enregistrer la carte dans un fichier HTML
map.save("src/pages/carte.html")
#webbrowser.open("file:///C:/Users/E/Desktop/e4/python/Projet_Python_E4S3/src/pages/carte.html")


#Large GeoJSON Files in Folium blababl TESTER LES SOLUTIONS SUR PK MEMORY ERROR THAT CAUSE CRASH  
#Au lieu de charger un gros GeoJSON, on peut utiliser des vector tiles ou un autre format plus efficace.
#là on a filtrer pour travailler sur jeo plus petit