"""Page dediee a la carte choroplethe des pathologies."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import folium
import pandas as pd
from dash import Input, Output, callback, dcc, html

from src.utils.db_queries import get_liste_pathologies, get_pathologies_par_region, get_pathologies_par_departement
from src.utils.geo_reference import get_dept_to_region_mapping, get_all_regions

# Nouveaux fichiers GeoJSON simplifiés (légers et performants)
GEOJSON_REGIONS_PATH = Path("data/geolocalisation/regions-version-simplifiee.geojson")
GEOJSON_DEPARTEMENTS_PATH = Path("data/geolocalisation/departements-version-simplifiee.geojson")
FRANCE_CENTER: Tuple[float, float] = (46.603354, 1.888334)
FRANCE_ZOOM: int = 6  # Zoom optimal pour voir toute la France


def _format_int(value: int | float) -> str:
    """Formate un entier avec des espaces comme séparateurs de milliers."""
    return f"{int(round(value)):,}".replace(",", " ")


def _format_rate(value: float) -> str:
    """Formate un taux en pourcentage avec 2 décimales."""
    return f"{float(value):.2f} %"


@lru_cache(maxsize=2)
def _load_geojson_by_level(level: str) -> dict | None:
    """
    Charge le GeoJSON selon le niveau géographique demandé.
    
    Args:
        level: "region" ou "departement"
    
    Returns:
        dict: GeoJSON ou None en cas d'erreur
    """
    try:
        if level == "region":
            # Charger le fichier régions simplifié (220 Ko, 13 régions)
            if GEOJSON_REGIONS_PATH.exists():
                print(f"✅ Chargement des RÉGIONS (fichier simplifié)")
                with GEOJSON_REGIONS_PATH.open("r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"❌ Fichier régions introuvable : {GEOJSON_REGIONS_PATH}")
                return None
        
        elif level == "departement":
            # Charger le fichier départements simplifié (556 Ko, 96 départements)
            if GEOJSON_DEPARTEMENTS_PATH.exists():
                print(f"✅ Chargement des DÉPARTEMENTS (fichier simplifié)")
                with GEOJSON_DEPARTEMENTS_PATH.open("r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"❌ Fichier départements introuvable : {GEOJSON_DEPARTEMENTS_PATH}")
                return None
        
        return None
    
    except Exception as e:
        print(f"❌ Erreur chargement GeoJSON niveau {level}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_choropleth_html(
    annee: int, 
    pathologie: str | None, 
    niveau_geo: str = "region",
    indicateur: str = "prevalence"
) -> tuple[str, pd.DataFrame]:
    """Crée une carte choroplèthe Folium et retourne le HTML + DataFrame.
    
    Args:
        annee: Année des données
        pathologie: Pathologie à filtrer (None = toutes)
        niveau_geo: "region" ou "departement"
        indicateur: "prevalence" ou "total_cas"
    """
    
    try:
        # Récupération des données selon le niveau géographique
        try:
            if niveau_geo == "region":
                df = get_pathologies_par_region(annee, pathologie)
                geo_column = "region"
                geo_key = "code"  # Les nouveaux GeoJSON utilisent "code"
                label_field = "nom"  # Les nouveaux GeoJSON utilisent "nom"
            else:  # departement
                df = get_pathologies_par_departement(annee, pathologie)
                geo_column = "dept"
                geo_key = "code"  # Les nouveaux GeoJSON utilisent "code"
                label_field = "nom"  # Les nouveaux GeoJSON utilisent "nom"
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de base de données</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Impossible de récupérer les données depuis la base de données.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
                <p style='font-size: 14px; margin-top: 20px;'>Vérifiez que le fichier <code>data/effectifs.sqlite3</code> existe et est accessible.</p>
            </div>
            """
            return error_html, pd.DataFrame()
        
        if df.empty:
            return (
                (
                    "<div style='font-family: Arial; color: #e67e22; text-align: center; padding: 40px; background-color: #fef5e7; border: 2px solid #f39c12; border-radius: 10px; margin: 20px;'>"
                    "<h2 style='color: #d68910;'>⚠️ Aucune donnée disponible</h2>"
                    "<p style='font-size: 16px;'>Il n'y a pas de données pour l'année et la pathologie sélectionnées.</p>"
                    "<p style='font-size: 14px; margin-top: 10px;'>Essayez de changer les filtres ci-dessus.</p>"
                    "</div>"
                ),
                df,
            )

        # Préparation des données
        try:
            df = df.copy()
            df[geo_column] = df[geo_column].astype(str)
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de traitement des données</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Les données récupérées ne sont pas au format attendu.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
            </div>
            """
            return error_html, pd.DataFrame()

        # Chargement du GeoJSON selon le niveau
        try:
            geo_data = _load_geojson_by_level(niveau_geo)
            
            if geo_data is None:
                error_html = """
                <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                    <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de chargement GeoJSON</h2>
                    <p style='font-size: 16px; margin-bottom: 10px;'>Impossible de charger ou d'agréger le fichier GeoJSON des communes.</p>
                    <p style='font-size: 14px; margin-top: 20px;'><strong>Vérifications à effectuer :</strong></p>
                    <ul style='text-align: left; display: inline-block; font-size: 14px; color: #7f8c8d;'>
                        <li>Le fichier <code>data/geolocalisation/datagouv-communes.geojson</code> existe</li>
                        <li>Le fichier GeoJSON est valide (format JSON correct)</li>
                        <li>Le fichier contient les propriétés <code>code_insee_region</code> et <code>region</code></li>
                    </ul>
                    <p style='font-size: 14px; margin-top: 20px; color: #e67e22;'>Consultez la console pour plus de détails.</p>
                </div>
                """
                return error_html, df
                
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur critique GeoJSON</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Une erreur inattendue s'est produite lors du chargement du GeoJSON.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
            </div>
            """
            return error_html, df

        # Création de la carte Folium
        try:
            fmap = folium.Map(
                location=FRANCE_CENTER, 
                zoom_start=FRANCE_ZOOM,  # Zoom optimal pour voir toute la France
                tiles="CartoDB positron", 
                control_scale=True,
                zoom_control=True,
                scrollWheelZoom=True,
                dragging=True,
                max_bounds=True  # Limite le déplacement pour garder la France visible
            )
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de création de la carte</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Impossible de créer l'objet carte Folium.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
                <p style='font-size: 14px; margin-top: 20px;'>Vérifiez que le module <code>folium</code> est correctement installé.</p>
            </div>
            """
            return error_html, df

        # Création de la carte choroplèthe
        try:
            # Déterminer le nom de la légende selon l'indicateur
            if indicateur == "prevalence":
                legend_name = "Prévalence (%)"
            else:
                legend_name = "Nombre de cas"
            
            # Calculer les limites min/max pour l'échelle de couleurs
            # Cela force Folium à recalculer l'échelle pour chaque carte
            valeur_min = df[indicateur].min()
            valeur_max = df[indicateur].max()
            
            # ⚡ UTILISER LES QUANTILES au lieu d'intervalles égaux
            # Les quantiles répartissent équitablement les données dans chaque classe
            # C'est essentiel quand les valeurs sont proches (ex: prévalence 2.5%-4.3%)
            import numpy as np
            threshold_scale = [
                valeur_min,
                df[indicateur].quantile(0.2),
                df[indicateur].quantile(0.4),
                df[indicateur].quantile(0.6),
                df[indicateur].quantile(0.8),
                valeur_max
            ]
            
            print(f"📊 Échelle de couleurs pour {indicateur} (QUANTILES):")
            print(f"   Min: {valeur_min:.2f}, Max: {valeur_max:.2f}")
            print(f"   Paliers: {[f'{x:.2f}' for x in threshold_scale]}")
            print(f"   Méthode: Quantiles (20% des données par classe)")
            
            choropleth = folium.Choropleth(
                geo_data=geo_data,
                data=df,
                columns=(geo_column, indicateur),  # Utiliser l'indicateur choisi
                key_on=f"feature.properties.{geo_key}",
                fill_color="YlOrRd",
                fill_opacity=0.7,
                line_opacity=0.5,  # Lignes plus visibles
                line_weight=1.5,   # Bordures plus épaisses
                nan_fill_color="#d9d9d9",
                legend_name=None,  # Désactiver la légende auto (on va créer la nôtre)
                threshold_scale=threshold_scale,  # Forcer l'échelle basée sur les données actuelles
                highlight=True,
                smooth_factor=1.0  # Lissage des contours
            )
            choropleth.add_to(fmap)
            
            # 🎨 Créer une légende personnalisée avec des labels formatés lisiblement
            # Les couleurs correspondent à la palette YlOrRd de Folium
            colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']
            
            # Formater les labels selon l'indicateur
            if indicateur == "prevalence":
                # Pour la prévalence: afficher en %
                labels = [
                    f"{threshold_scale[0]:.2f}% - {threshold_scale[1]:.2f}%",
                    f"{threshold_scale[1]:.2f}% - {threshold_scale[2]:.2f}%",
                    f"{threshold_scale[2]:.2f}% - {threshold_scale[3]:.2f}%",
                    f"{threshold_scale[3]:.2f}% - {threshold_scale[4]:.2f}%",
                    f"{threshold_scale[4]:.2f}% - {threshold_scale[5]:.2f}%",
                ]
            else:
                # Pour le nombre de cas: formater avec des espaces (ex: 1 234 567)
                def format_nombre(n):
                    if n >= 1_000_000:
                        return f"{n/1_000_000:.1f}M"  # Millions
                    elif n >= 1_000:
                        return f"{n/1_000:.0f}K"  # Milliers
                    else:
                        return f"{int(n)}"
                
                labels = [
                    f"{format_nombre(threshold_scale[0])} - {format_nombre(threshold_scale[1])}",
                    f"{format_nombre(threshold_scale[1])} - {format_nombre(threshold_scale[2])}",
                    f"{format_nombre(threshold_scale[2])} - {format_nombre(threshold_scale[3])}",
                    f"{format_nombre(threshold_scale[3])} - {format_nombre(threshold_scale[4])}",
                    f"{format_nombre(threshold_scale[4])} - {format_nombre(threshold_scale[5])}",
                ]
            
            # HTML de la légende personnalisée
            legend_html = f'''
            <div style="
                position: fixed; 
                bottom: 50px; 
                right: 50px; 
                width: 180px; 
                background-color: white; 
                border: 2px solid grey; 
                border-radius: 5px; 
                z-index: 9999; 
                font-size: 13px;
                padding: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            ">
                <p style="margin: 0 0 8px 0; font-weight: bold; font-size: 14px;">{legend_name}</p>
            '''
            
            for color, label in zip(colors, labels):
                legend_html += f'''
                <p style="margin: 4px 0; line-height: 18px;">
                    <span style="
                        display: inline-block; 
                        width: 20px; 
                        height: 12px; 
                        background-color: {color}; 
                        border: 1px solid #999;
                        margin-right: 5px;
                        vertical-align: middle;
                    "></span>
                    <span style="vertical-align: middle; font-size: 12px;">{label}</span>
                </p>
                '''
            
            legend_html += '</div>'
            
            # Ajouter la légende personnalisée à la carte
            fmap.get_root().html.add_child(folium.Element(legend_html))
            
            # 🗑️ Supprimer la légende automatique de Folium (classe 'legend')
            # Même avec legend_name=None, Folium peut créer une légende vide
            remove_folium_legend = """
            <script>
                // Attendre que la page soit chargée
                document.addEventListener('DOMContentLoaded', function() {
                    // Supprimer toutes les légendes automatiques de Folium
                    var legends = document.getElementsByClassName('legend');
                    while(legends.length > 0) {
                        legends[0].parentNode.removeChild(legends[0]);
                    }
                    
                    // Alternative : cibler les divs avec la classe 'leaflet-control'
                    var controls = document.querySelectorAll('.leaflet-control.leaflet-control-colorbar');
                    controls.forEach(function(control) {
                        control.style.display = 'none';
                    });
                });
            </script>
            """
            fmap.get_root().html.add_child(folium.Element(remove_folium_legend))
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de création choroplèthe</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Impossible de créer la carte choroplèthe.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
                <p style='font-size: 14px; margin-top: 20px;'><strong>Causes possibles :</strong></p>
                <ul style='text-align: left; display: inline-block; font-size: 14px; color: #7f8c8d;'>
                    <li>Incompatibilité entre les codes région de la BDD et du GeoJSON</li>
                    <li>Colonne 'region' ou 'prevalence' manquante dans les données</li>
                    <li>Propriété 'code_insee_region' manquante dans le GeoJSON</li>
                </ul>
            </div>
            """
            return error_html, df

        # Ajout des tooltips
        try:
            folium.features.GeoJsonTooltip(
                fields=[label_field, geo_key],
                aliases=["Nom :", "Code :"],
                sticky=False,
                labels=True,
                localize=True,
                style=(
                    "background-color: white; color: #333333; font-family: Arial;"
                    " font-size: 14px; padding: 10px 14px; border-radius: 5px;"
                    " box-shadow: 0 2px 6px rgba(0,0,0,0.3);"
                ),
            ).add_to(choropleth.geojson)
        except Exception as e:
            print(f"⚠️ Impossible d'ajouter les tooltips : {e}")
            # Ne pas arrêter pour les tooltips, la carte fonctionne quand même

        # Ne PAS ajuster automatiquement les limites pour garder le zoom France
        # La carte reste centrée sur la France avec le zoom défini
        try:
            # Optionnel : définir des limites strictes
            fmap.fit_bounds([[41.0, -5.5], [51.5, 10.0]])  # Cadre France + marges
        except Exception as e:
            print(f"⚠️ Impossible de définir les limites : {e}")
            # La carte s'affiche quand même avec le zoom par défaut

        # Génération du HTML
        try:
            html_output = fmap.get_root().render()
            
            # ⚡ AJOUT: Injecter un identifiant unique pour forcer le rafraîchissement du cache
            # Sans cela, le navigateur peut réutiliser l'ancienne carte avec l'ancienne échelle
            import time
            import hashlib
            unique_id = hashlib.md5(f"{niveau_geo}-{annee}-{pathologie}-{indicateur}-{time.time()}".encode()).hexdigest()[:8]
            html_output = html_output.replace('<head>', f'<head><meta name="cache-id" content="{unique_id}">')
            print(f"🔑 ID unique de carte: {unique_id}")
            
            return html_output, df
        except Exception as e:
            error_html = f"""
            <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
                <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur de rendu HTML</h2>
                <p style='font-size: 16px; margin-bottom: 10px;'>Impossible de générer le code HTML de la carte.</p>
                <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
            </div>
            """
            return error_html, df
    
    except Exception as e:
        # Erreur générale non capturée
        import traceback
        traceback.print_exc()
        
        error_html = f"""
        <div style='font-family: Arial; color: #e74c3c; text-align: center; padding: 40px; background-color: #fadbd8; border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>
            <h2 style='color: #c0392b; margin-bottom: 20px;'>❌ Erreur inattendue</h2>
            <p style='font-size: 16px; margin-bottom: 10px;'>Une erreur inattendue s'est produite lors de la création de la carte.</p>
            <p style='font-size: 14px; color: #7f8c8d;'><strong>Détails :</strong> {str(e)}</p>
            <p style='font-size: 14px; margin-top: 20px;'>Consultez la console pour la trace complète de l'erreur.</p>
        </div>
        """
        return error_html, pd.DataFrame()


def _build_stats_content(df, niveau_geo="region", indicateur="prevalence"):
    """Construit le panneau de statistiques selon le niveau géographique et l'indicateur."""
    if df.empty:
        return html.P("Aucune donnee disponible.", className="text-center text-muted")

    total_cas = int(df["total_cas"].sum())
    population = int(df["population_totale"].sum())
    prevalence_moy = (total_cas / population * 100) if population else 0
    nb_entites = len(df)
    
    # Déterminer le nom de la colonne géographique
    geo_column = "region" if niveau_geo == "region" else "dept"
    label_pluriel = "Régions couvertes" if niveau_geo == "region" else "Départements couverts"
    label_max = "Max (région" if niveau_geo == "region" else "Max (département"
    
    # Trouver l'entité avec la valeur max selon l'indicateur
    top_entite = df.loc[df[indicateur].idxmax()]
    
    # Récupérer le code de l'entité avec la valeur max
    code_max = str(top_entite[geo_column])
    if niveau_geo == "region":
        code_max = code_max.zfill(2)  # Padding pour les régions
    
    # Valeur à afficher selon l'indicateur
    if indicateur == "prevalence":
        valeur_max = _format_rate(top_entite["prevalence"])
        label_valeur = "Prévalence max"
    else:
        valeur_max = _format_int(top_entite["total_cas"])
        label_valeur = "Cas max"

    return html.Div(
        className="stats-container",
        children=[
            # Cas total
            html.Div(
                className="stat-card",
                children=[
                    html.H4(_format_int(total_cas), style={"color": "#c0392b", "margin": "0"}),
                    html.P("Cas total", className="stat-label"),
                ],
            ),
            # Prévalence moyenne
            html.Div(
                className="stat-card",
                children=[
                    html.H4(_format_rate(prevalence_moy), style={"color": "#2980b9", "margin": "0"}),
                    html.P("Prevalence moyenne", className="stat-label"),
                ],
            ),
            # Nombre d'entités
            html.Div(
                className="stat-card",
                children=[
                    html.H4(str(nb_entites), style={"color": "#27ae60", "margin": "0"}),
                    html.P(label_pluriel, className="stat-label"),
                ],
            ),
            # Valeur max
            html.Div(
                className="stat-card",
                children=[
                    html.H4(valeur_max, style={"color": "#f39c12", "margin": "0"}),
                    html.P(f"{label_max} {code_max})", className="stat-label"),
                ],
            ),
        ],
    )


def layout():
    """Layout de la page carte choroplèthe."""
    pathologies = get_liste_pathologies()

    return html.Div(
        className="page-container",
        children=[
            # En-tête
            html.Div(className="mb-3", children=[
                html.H1("Carte Choroplèthe - Prévalence des Pathologies", className="page-title text-center"),
                html.P(
                    "Explorez la répartition géographique des pathologies en France. "
                    "Ajustez les filtres pour personnaliser votre analyse.",
                    className="text-center text-muted"
                ),
            ]),
            
            # Contrôles / Filtres dans une carte
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="flex-controls",
                        children=[
                            html.Div([
                                html.Label("Niveau géographique", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-niveau-geo-dropdown",
                                    options=[
                                        {"label": "🌍 Régions (18 régions)", "value": "region"},
                                        {"label": "📍 Départements (101 départements)", "value": "departement"}
                                    ],
                                    value="region",
                                    clearable=False,
                                ),
                            ]),
                            
                            html.Div([
                                html.Label("Année", className="form-label"),
                                dcc.Slider(
                                    id="carte-annee-slider",
                                    min=2019,
                                    max=2023,
                                    value=2023,
                                    marks={str(year): str(year) for year in range(2019, 2024)},
                                    step=None,
                                    tooltip={"placement": "bottom"},
                                ),
                            ]),
                            
                            html.Div([
                                html.Label("Pathologie", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-pathologie-dropdown",
                                    options=[{"label": "Toutes les pathologies", "value": "ALL"}]
                                    + [{"label": p, "value": p} for p in pathologies],
                                    value="ALL",
                                    clearable=False,
                                ),
                            ]),
                            
                            html.Div([
                                html.Label("Indicateur", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-indicateur-dropdown",
                                    options=[
                                        {"label": "� Prévalence (%)", "value": "prevalence"},
                                        {"label": "🏥 Nombre de cas", "value": "total_cas"}
                                    ],
                                    value="prevalence",
                                    clearable=False,
                                ),
                            ]),
                        ],
                    ),
                ],
            ),
            
            # Carte
            html.Div(
                className="card",
                children=[
                    html.Iframe(
                        id="carte-choropleth",
                        className="map-container",
                    )
                ],
            ),
            
            # Statistiques
            html.Div(
                className="card",
                children=[
                    html.H3("Statistiques rapides", className="subsection-title"),
                    html.Div(id="carte-stats"),
                ],
            ),
        ],
    )


@callback(
    Output("carte-choropleth", "srcDoc"),
    Output("carte-stats", "children"),
    Input("carte-niveau-geo-dropdown", "value"),
    Input("carte-annee-slider", "value"),
    Input("carte-pathologie-dropdown", "value"),
    Input("carte-indicateur-dropdown", "value"),
)
def update_carte(niveau_geo: str, annee: int, pathologie_value: str, indicateur: str):
    """Callback pour mettre à jour la carte et les statistiques."""
    print(f"🔄 CALLBACK APPELÉ : niveau={niveau_geo}, annee={annee}, pathologie={pathologie_value}, indicateur={indicateur}")
    
    pathologie = None if pathologie_value in (None, "ALL") else pathologie_value
    map_html, df = create_choropleth_html(annee, pathologie, niveau_geo, indicateur)
    stats_content = _build_stats_content(df, niveau_geo, indicateur)
    
    print(f"✅ CALLBACK TERMINÉ : {len(df)} zones, HTML={len(map_html)} caractères")
    
    return map_html, stats_content
    print(f"✅ CALLBACK TERMINÉ : {len(df)} zones, HTML={len(map_html)} caractères")
    
    return map_html, stats_content
