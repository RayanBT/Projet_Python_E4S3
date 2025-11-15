"""Page dédiée à la carte des pathologies (choroplèthe)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import folium
import pandas as pd
from dash import Input, Output, callback, callback_context, dcc, html
from dash.exceptions import PreventUpdate

from src.utils.db_queries import (
    get_liste_pathologies,
    get_pathologies_par_departement,
    get_pathologies_par_region,
)
from src.utils.geo_reference import get_dept_to_region_mapping

import config

GEOJSON_REGIONS_PATH = config.GEOJSON_REGIONS_PATH
GEOJSON_DEPARTEMENTS_PATH = config.GEOJSON_DEPARTEMENTS_PATH
FRANCE_CENTER: tuple[float, float] = config.FRANCE_CENTER
FRANCE_ZOOM: int = config.FRANCE_ZOOM


def _format_int(value: int | float) -> str:
    """Formate un entier avec des espaces comme séparateurs de milliers."""
    return f"{int(round(value)):,}".replace(",", " ")


def _format_rate(value: float) -> str:
    """Formate un taux en pourcentage avec 2 décimales."""
    return f"{float(value):.2f} %"


def _normalize_period_value(
    value: int | list[int] | tuple[int, int] | None,
) -> tuple[int, int]:
    """Normalise la valeur du slider (année ou plage)."""
    if value is None:
        return 2015, 2015
    if isinstance(value, (list, tuple)):
        if not value:
            return 2015, 2015
        start = int(value[0])
        end = int(value[1]) if len(value) > 1 else start
    else:
        start = end = int(value)
    if start > end:
        start, end = end, start
    return start, end


@lru_cache(maxsize=2)
def _load_geojson_by_level(level: str) -> dict[str, Any] | None:
    """
    Charge le GeoJSON selon le niveau géographique demandé.

    Args:
        level: "region" ou "departement"

    Returns:
        dict: GeoJSON ou None en cas d'erreur
    """
    try:
        if level == "region":
            # Charger le fichier régions avec outre-mer (1,66 Mo, 18 régions)
            if GEOJSON_REGIONS_PATH.exists():
                print(f"✅ Chargement des RÉGIONS (fichier simplifié mais avec outre-mer)")
                with GEOJSON_REGIONS_PATH.open("r", encoding="utf-8") as f:
                    return json.load(f)  # type: ignore[no-any-return]
            else:
                print(f"❌ Fichier régions introuvable : {GEOJSON_REGIONS_PATH}")
                return None

        elif level == "departement":
            # Charger le fichier départements simplifié (556 Ko, 96 départements)
            if GEOJSON_DEPARTEMENTS_PATH.exists():
                print(f"✅ Chargement des DÉPARTEMENTS (fichier simplifié mais avec outre-mer)")
                with GEOJSON_DEPARTEMENTS_PATH.open("r", encoding="utf-8") as f:
                    return json.load(f)  # type: ignore[no-any-return]
            else:
                print(f"❌ Fichier départements introuvable : {GEOJSON_DEPARTEMENTS_PATH}")
                return None

        return None

    except Exception as error:
        print(f"❌ Erreur chargement GeoJSON niveau {level}: {error}")
        import traceback

        traceback.print_exc()
        return None


def create_choropleth_html(
    debut_annee: int,
    fin_annee: int,
    pathologie: str | None,
    niveau_geo: str = "region",
    indicateur: str = "prevalence",
    zone_scope: str = "france",
    outremer_selected: str | None = None,
) -> tuple[str, pd.DataFrame]:
    """Crée une carte choroplèthe Folium et retourne le HTML + DataFrame.

    Args:
        debut_annee: Année de début de la période sélectionnée
        fin_annee: Année de fin de la période sélectionnée
        pathologie: Pathologie à filtrer (None = toutes)
        niveau_geo: "region" ou "departement"
        indicateur: "prevalence" ou "total_cas"
        zone_scope: 'france' | 'outre-mer' | 'outre-mer-select'
        outremer_selected: Nom de la région d'outre-mer si spécifique
    """

    start_year = min(debut_annee, fin_annee)
    end_year = max(debut_annee, fin_annee)
    periode_label = (
        f"{start_year}" if start_year == end_year else f"{start_year}-{end_year}"
    )

    try:
        try:
            if niveau_geo == "region":
                df = get_pathologies_par_region(start_year, pathologie, fin_annee=end_year)
                geo_column = "region"
                geo_key = "code"
                label_field = "nom"
            else:
                df = get_pathologies_par_departement(start_year, pathologie, fin_annee=end_year)
                geo_column = "dept"
                geo_key = "code"
                label_field = "nom"
        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; background-color: #fadbd8; "
                "border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur de base de données</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Impossible de récupérer les données depuis la base de données.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "<p style='font-size: 14px; margin-top: 20px;'>"
                "Vérifiez que le fichier <code>data/effectifs.sqlite3</code> "
                "existe et est accessible.</p>"
                "</div>"
            )
            return error_html, pd.DataFrame()

        if df.empty:
            return (
                (
                    "<div style='font-family: Arial; color: #e67e22; "
                    "text-align: center; padding: 40px; "
                    "background-color: #fef5e7; border: 2px solid #f39c12; "
                    "border-radius: 10px; margin: 20px;'>"
                    "<h2 style='color: #d68910;'>⚠️ Aucune donnée disponible</h2>"
                    "<p style='font-size: 16px;'>"
                    f"Il n'y a pas de données pour la période {periode_label} et "
                    "la pathologie sélectionnées.</p>"
                    "<p style='font-size: 14px; margin-top: 10px;'>"
                    "Essayez de changer les filtres ci-dessus.</p>"
                    "</div>"
                ),
                df,
            )

        try:
            df = df.copy()
            df[geo_column] = df[geo_column].astype(str)
        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; background-color: #fadbd8; "
                "border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur de traitement des données</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Les données récupérées ne sont pas au format attendu.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "</div>"
            )
            return error_html, pd.DataFrame()

        try:
            geo_data = _load_geojson_by_level(niveau_geo)

            if geo_data is None:
                error_html = (
                    "<div style='font-family: Arial; color: #e74c3c; "
                    "text-align: center; padding: 40px; "
                    "background-color: #fadbd8; border: 2px solid #e74c3c; "
                    "border-radius: 10px; margin: 20px;'>"
                    "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                    "❌ Erreur de chargement GeoJSON</h2>"
                    "<p style='font-size: 16px; margin-bottom: 10px;'>"
                    "Impossible de charger ou d'agréger le fichier "
                    "GeoJSON des communes.</p>"
                    "<p style='font-size: 14px; margin-top: 20px;'>"
                    "<strong>Vérifications à effectuer :</strong></p>"
                    "<ul style='text-align: left; display: inline-block; "
                    "font-size: 14px; color: #7f8c8d;'>"
                    "<li>Le fichier <code>data/geolocalisation/"
                    "datagouv-communes.geojson</code> existe</li>"
                    "<li>Le fichier GeoJSON est valide (format JSON correct)</li>"
                    "<li>Le fichier contient les propriétés "
                    "<code>code_insee_region</code> et <code>region</code></li>"
                    "</ul>"
                    "<p style='font-size: 14px; margin-top: 20px; "
                    "color: #e67e22;'>"
                    "Consultez la console pour plus de détails.</p>"
                    "</div>"
                )
                return error_html, df

        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; background-color: #fadbd8; "
                "border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur critique GeoJSON</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Une erreur inattendue s'est produite lors du chargement "
                "du GeoJSON.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "</div>"
            )
            return error_html, df

        OVERSEAS_NAMES = {
            "Guadeloupe",
            "Martinique",
            "Guyane",
            "La Réunion",
            "Mayotte",
        }
        OVERSEAS_CENTER_ZOOM: dict[str, tuple[float, float, int]] = {
            "Guadeloupe": (16.2650, -61.5510, 8),
            "Martinique": (14.6415, -61.0242, 8),
            "Guyane": (3.9339, -53.1258, 7),
            "La Réunion": (-21.1151, 55.5364, 8),
            "Mayotte": (-12.8275, 45.1662, 8),
        }

        try:
            if zone_scope == "outre-mer":
                if niveau_geo == "departement":
                    condition = df[geo_column].str.startswith("97") | df[
                        geo_column
                    ].isin(["971", "972", "973", "974", "976"])
                    df = df[condition].copy()
                else:
                    region_geo = geo_data
                    overseas_codes = [
                        str(f["properties"]["code"])
                        for f in region_geo["features"]
                        if f["properties"].get("nom") in OVERSEAS_NAMES
                    ]
                    df = df[df[geo_column].isin(overseas_codes)].copy()

            elif zone_scope == "metropole":
                if niveau_geo == "departement":
                    condition = ~(
                        df[geo_column].str.startswith("97")
                        | df[geo_column].isin(["971", "972", "973", "974", "976"])
                    )
                    df = df[condition].copy()
                else:
                    region_geo = geo_data
                    overseas_codes = [
                        str(f["properties"]["code"])
                        for f in region_geo["features"]
                        if f["properties"].get("nom") in OVERSEAS_NAMES
                    ]
                    df = df[~df[geo_column].isin(overseas_codes)].copy()

            elif zone_scope == "outre-mer-select" and outremer_selected:
                selected = outremer_selected
                if niveau_geo == "departement":
                    dept_to_region = get_dept_to_region_mapping()
                    dept_codes = [k for k, v in dept_to_region.items() if v == selected]
                    df = df[df[geo_column].isin(dept_codes)].copy()
                else:
                    region_geo = geo_data
                    sel_codes = [
                        str(f["properties"]["code"])
                        for f in region_geo["features"]
                        if f["properties"].get("nom") == selected
                    ]
                    df = df[df[geo_column].isin(sel_codes)].copy()
        except Exception as error:
            print(f"⚠️ Erreur lors du filtrage par zone: {error}")

        # Création de la carte Folium
        try:
            # Déterminer centre et zoom selon la sélection
            map_center = FRANCE_CENTER
            map_zoom = FRANCE_ZOOM
            if zone_scope == "outre-mer":
                # Centrer sur une vue agrégée des outre-mer : utiliser le centre de la France pour voir métropole + outre-mer
                lat, lon, z = OVERSEAS_CENTER_ZOOM["Guyane"]
                map_center = (lat, lon)
                map_zoom = 4
            elif (
                zone_scope == "outre-mer-select"
                and outremer_selected in OVERSEAS_CENTER_ZOOM
            ):
                lat, lon, z = OVERSEAS_CENTER_ZOOM[outremer_selected]
                map_center = (lat, lon)
                map_zoom = z

            fmap = folium.Map(
                location=map_center,
                zoom_start=map_zoom,
                tiles="CartoDB positron",
                control_scale=True,
                zoom_control=True,
                scrollWheelZoom=True,
                dragging=True,
                max_bounds=False,
            )
        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; background-color: #fadbd8; "
                "border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur de création de la carte</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Impossible de créer l'objet carte Folium.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "<p style='font-size: 14px; margin-top: 20px;'>"
                "Vérifiez que le module <code>folium</code> est "
                "correctement installé.</p>"
                "</div>"
            )
            return error_html, df

        try:
            if indicateur == "prevalence":
                legend_name = "Prévalence (%)"
            else:
                legend_name = "Nombre de cas"

            valeur_min = df[indicateur].min()
            valeur_max = df[indicateur].max()

            threshold_scale = [
                valeur_min,
                df[indicateur].quantile(0.2),
                df[indicateur].quantile(0.4),
                df[indicateur].quantile(0.6),
                df[indicateur].quantile(0.8),
                valeur_max,
            ]

            print(f"📊 Échelle de couleurs pour {indicateur} (QUANTILES):")
            print(f"   Min: {valeur_min:.2f}, Max: {valeur_max:.2f}")
            print(f"   Paliers: {[f'{x:.2f}' for x in threshold_scale]}")
            print("   Méthode: Quantiles (20% des données par classe)")
            choropleth = folium.Choropleth(
                geo_data=geo_data,
                data=df,
                columns=(geo_column, indicateur),
                key_on=f"feature.properties.{geo_key}",
                fill_color="YlOrRd",
                fill_opacity=0.7,
                line_opacity=0.5,
                line_weight=1.5,
                nan_fill_color="#d9d9d9",
                legend_name="",
                threshold_scale=threshold_scale,
                highlight=True,
                smooth_factor=1.0,
            )
            choropleth.add_to(fmap)

            colors = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]

            if indicateur == "prevalence":
                labels = [
                    f"{threshold_scale[0]:.2f}% - {threshold_scale[1]:.2f}%",
                    f"{threshold_scale[1]:.2f}% - {threshold_scale[2]:.2f}%",
                    f"{threshold_scale[2]:.2f}% - {threshold_scale[3]:.2f}%",
                    f"{threshold_scale[3]:.2f}% - {threshold_scale[4]:.2f}%",
                    f"{threshold_scale[4]:.2f}% - {threshold_scale[5]:.2f}%",
                ]
            else:

                def format_nombre(n: float) -> str:
                    if n >= 1_000_000:
                        return f"{n/1_000_000:.1f}M"
                    if n >= 1_000:
                        return f"{n/1_000:.0f}K"
                    return f"{int(n)}"

                labels = [
                    f"{format_nombre(threshold_scale[0])} - "
                    f"{format_nombre(threshold_scale[1])}",
                    f"{format_nombre(threshold_scale[1])} - "
                    f"{format_nombre(threshold_scale[2])}",
                    f"{format_nombre(threshold_scale[2])} - "
                    f"{format_nombre(threshold_scale[3])}",
                    f"{format_nombre(threshold_scale[3])} - "
                    f"{format_nombre(threshold_scale[4])}",
                    f"{format_nombre(threshold_scale[4])} - "
                    f"{format_nombre(threshold_scale[5])}",
                ]

            legend_html = f"""
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
            """

            for color, label in zip(colors, labels):
                legend_html += f"""
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
                """

            legend_html += "</div>"

            root = cast(Any, fmap.get_root())
            root.html.add_child(folium.Element(legend_html))

            remove_folium_legend = """
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var legends = document.getElementsByClassName('legend');
                    while(legends.length > 0) {
                        legends[0].parentNode.removeChild(legends[0]);
                    }

                    var controls = document.querySelectorAll(
                        '.leaflet-control.leaflet-control-colorbar'
                    );
                    controls.forEach(function(control) {
                        control.style.display = 'none';
                    });
                });
            </script>
            """
            root = cast(Any, fmap.get_root())
            root.html.add_child(folium.Element(remove_folium_legend))
        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; "
                "background-color: #fadbd8; border: 2px solid #e74c3c; "
                "border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur de création choroplèthe</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Impossible de créer la carte choroplèthe.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "<p style='font-size: 14px; margin-top: 20px;'>"
                "<strong>Causes possibles :</strong></p>"
                "<ul style='text-align: left; display: inline-block; "
                "font-size: 14px; color: #7f8c8d;'>"
                "<li>Incompatibilité entre les codes région "
                "de la BDD et du GeoJSON</li>"
                "<li>Colonne 'region' ou 'prevalence' manquante "
                "dans les données</li>"
                "<li>Propriété 'code_insee_region' manquante "
                "dans le GeoJSON</li>"
                "</ul>"
                "</div>"
            )
            return error_html, df

        try:
            folium.features.GeoJsonTooltip(
                fields=[label_field, geo_key],
                aliases=["Nom :", "Code :"],
                sticky=False,
                labels=True,
                localize=True,
                style=(
                    "background-color: white; color: #333333; "
                    "font-family: Arial; font-size: 14px; padding: 10px 14px; "
                    "border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"
                ),
            ).add_to(choropleth.geojson)
        except Exception as error:
            print(f"⚠️ Impossible d'ajouter les tooltips : {error}")

        try:
            if zone_scope in ("france", "metropole"):
                fmap.fit_bounds([[41.0, -5.5], [51.5, 10.0]])
        except Exception as error:
            print(f"⚠️ Impossible de définir les limites : {error}")

        try:
            html_output = fmap.get_root().render()

            import hashlib
            import time

            unique_id = hashlib.md5(
                f"{niveau_geo}-{start_year}-{end_year}-{pathologie}-{indicateur}-{time.time()}"
                .encode()
            ).hexdigest()[:8]
            html_output = html_output.replace(
                "<head>", f'<head><meta name="cache-id" content="{unique_id}">'
            )
            print(f"🔑 ID unique de carte: {unique_id}")

            return html_output, df
        except Exception as error:
            error_html = (
                "<div style='font-family: Arial; color: #e74c3c; "
                "text-align: center; padding: 40px; "
                "background-color: #fadbd8; border: 2px solid #e74c3c; "
                "border-radius: 10px; margin: 20px;'>"
                "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
                "❌ Erreur de rendu HTML</h2>"
                "<p style='font-size: 16px; margin-bottom: 10px;'>"
                "Impossible de générer le code HTML de la carte.</p>"
                f"<p style='font-size: 14px; color: #7f8c8d;'>"
                f"<strong>Détails :</strong> {str(error)}</p>"
                "</div>"
            )
            return error_html, df

    except Exception as error:
        import traceback

        traceback.print_exc()

        error_html = (
            "<div style='font-family: Arial; color: #e74c3c; "
            "text-align: center; padding: 40px; background-color: #fadbd8; "
            "border: 2px solid #e74c3c; border-radius: 10px; margin: 20px;'>"
            "<h2 style='color: #c0392b; margin-bottom: 20px;'>"
            "❌ Erreur inattendue</h2>"
            "<p style='font-size: 16px; margin-bottom: 10px;'>"
            "Une erreur inattendue s'est produite lors de la création "
            "de la carte.</p>"
            f"<p style='font-size: 14px; color: #7f8c8d;'>"
            f"<strong>Détails :</strong> {str(error)}</p>"
            "<p style='font-size: 14px; margin-top: 20px;'>"
            "Consultez la console pour la trace complète de l'erreur.</p>"
            "</div>"
        )
        return error_html, pd.DataFrame()


def _build_stats_content(
    df: pd.DataFrame, niveau_geo: str = "region", indicateur: str = "prevalence"
) -> html.P | html.Div:
    """Construit le panneau de statistiques selon le niveau et l'indicateur."""
    if df.empty:
        return html.P(
            "Aucune donnee disponible.", className="text-center text-muted"
        )

    total_cas = int(df["total_cas"].sum())
    population = int(df["population_totale"].sum())
    prevalence_moy = (total_cas / population * 100) if population else 0
    nb_entites = len(df)

    geo_column = "region" if niveau_geo == "region" else "dept"
    label_pluriel = (
        "Régions couvertes" if niveau_geo == "region" else "Départements couverts"
    )
    label_max = "Max (région" if niveau_geo == "region" else "Max (département"

    top_entite = df.loc[df[indicateur].idxmax()]

    code_max = str(top_entite[geo_column])
    if niveau_geo == "region":
        code_max = code_max.zfill(2)

    if indicateur == "prevalence":
        valeur_max = _format_rate(float(top_entite["prevalence"]))
    else:
        valeur_max = _format_int(float(top_entite["total_cas"]))

    return html.Div(
        className="stats-container",
        children=[
            html.Div(
                className="stat-card",
                children=[
                    html.H4(
                        _format_int(total_cas),
                        style={"color": "#c0392b", "margin": "0"},
                    ),
                    html.P("Cas total", className="stat-label"),
                ],
            ),
            html.Div(
                className="stat-card",
                children=[
                    html.H4(
                        _format_rate(prevalence_moy),
                        style={"color": "#2980b9", "margin": "0"},
                    ),
                    html.P("Prevalence moyenne", className="stat-label"),
                ],
            ),
            html.Div(
                className="stat-card",
                children=[
                    html.H4(str(nb_entites), style={"color": "#27ae60", "margin": "0"}),
                    html.P(label_pluriel, className="stat-label"),
                ],
            ),
            html.Div(
                className="stat-card",
                children=[
                    html.H4(valeur_max, style={"color": "#f39c12", "margin": "0"}),
                    html.P(f"{label_max} {code_max})", className="stat-label"),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    """Layout de la page carte choroplèthe."""
    pathologies = get_liste_pathologies()

    return html.Div(
        className="page-container",
        children=[
            # En-tête
            html.Div(className="mb-3", children=[
                html.H1("Carte - Prévalence des Pathologies", className="page-title text-center"),
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
                    # Première ligne : Zone (centré)
                    html.Div(className="zone-control", children=[
                        # Store to hold zone selection
                        dcc.Store(id="carte-zone-store", data={"scope": "france", "selected": None}),

                        html.Div(
                            className="zone-dropdown",
                            children=[
                                html.Div(
                                    className="zone-trigger",
                                    children=[
                                        html.Label("Zone", className="form-label"),
                                        html.Button(
                                            [
                                                html.Span("Toute la France", className="zone-main-selected"),
                                                html.Span(" ▾", className="zone-main-caret"),
                                            ],
                                            className="zone-btn",
                                            id="zone-main-btn",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="zone-menu",
                                    children=[
                                        html.Button("Toute la France", className="zone-item", id="zone-france"),
                                        html.Button("Métropole", className="zone-item", id="zone-metropole"),
                                        html.Div([  # Outre-Mer with submenu
                                            html.Button("Outre-Mer ▶", className="zone-item outremer", id="zone-outremer"),
                                            html.Div(
                                                className="submenu",
                                                children=[
                                                    html.Button("Guadeloupe", className="zone-item", id="zone-om-Guadeloupe"),
                                                    html.Button("Martinique", className="zone-item", id="zone-om-Martinique"),
                                                    html.Button("Guyane", className="zone-item", id="zone-om-Guyane"),
                                                    html.Button("La Réunion", className="zone-item", id="zone-om-La_Reunion"),
                                                    html.Button("Mayotte", className="zone-item", id="zone-om-Mayotte"),
                                                ],
                                            ),
                                        ]),
                                    ],
                                ),
                            ],
                        ),
                    ]),
                    
                    # Deuxième ligne : Autres contrôles
                    html.Div(
                        className="flex-controls",
                        children=[
                            html.Div([
                                html.Label("Niveau géographique", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-niveau-geo-dropdown",
                                    options=[  # type: ignore[arg-type]
                                        {"label": "🌍 Régions (18)", "value": "region"},
                                        {"label": "📍 Départements (101)", "value": "departement"}
                                    ],
                                    value="region",
                                    clearable=False,
                                ),
                            ]),

                            html.Div([
                                html.Label("Période", className="form-label"),
                                dcc.RangeSlider(
                                    id="carte-annee-slider",
                                    min=2015,
                                    max=2023,
                                    value=[2015, 2023],
                                    marks={
                                        2015: '2015',
                                        2017: '2017',
                                        2019: '2019',
                                        2021: '2021',
                                        2023: '2023'
                                    },
                                    step=1,
                                    allowCross=False,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                                html.Div(
                                    id="carte-periode-display",
                                    className="period-display",
                                    style={"marginTop": "8px"},
                                ),
                            ]),

                            html.Div([
                                html.Label("Pathologie", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-pathologie-dropdown",
                                    options=[{"label": "Toutes les pathologies", "value": "ALL"}]  # type: ignore[arg-type]
                                    + [{"label": p, "value": p} for p in pathologies],
                                    value="ALL",
                                    clearable=False,
                                ),
                            ]),

                            html.Div([
                                html.Label("Indicateur", className="form-label"),
                                dcc.Dropdown(
                                    id="carte-indicateur-dropdown",
                                    options=[  # type: ignore[arg-type]
                                        {
                                            "label": "📊 Prévalence (%)",
                                            "value": "prevalence",
                                        },
                                        {
                                            "label": "🏥 Nombre de cas",
                                            "value": "total_cas",
                                        },
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
            
            # Bouton de navigation
            html.Div(className="text-center mt-3", children=[
                dcc.Link(
                    html.Button("← Retour à l'accueil", className="btn btn-secondary"),
                    href='/',
                ),
            ])
        ],
    )



@callback(
    Output("carte-zone-store", "data"),
    Input("zone-france", "n_clicks"),
    Input("zone-metropole", "n_clicks"),
    Input("zone-outremer", "n_clicks"),
    Input("zone-om-Guadeloupe", "n_clicks"),
    Input("zone-om-Martinique", "n_clicks"),
    Input("zone-om-Guyane", "n_clicks"),
    Input("zone-om-La_Reunion", "n_clicks"),
    Input("zone-om-Mayotte", "n_clicks"),
)
def _zone_menu_click(
    france: int | None,
    metropole: int | None,
    outremer: int | None,
    gua: int | None,
    mar: int | None,
    guy: int | None,
    rei: int | None,
    may: int | None,
) -> dict[str, str | None]:
    """Met à jour le store `carte-zone-store` en fonction du bouton cliqué."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trig = ctx.triggered[0]["prop_id"].split(".")[0]
    if trig == "zone-france":
        return {"scope": "france", "selected": None}
    if trig == "zone-metropole":
        return {"scope": "metropole", "selected": None}
    if trig == "zone-outremer":
        return {"scope": "outre-mer", "selected": None}
    # specific outre-mer
    if trig == "zone-om-Guadeloupe":
        return {"scope": "outre-mer-select", "selected": "Guadeloupe"}
    if trig == "zone-om-Martinique":
        return {"scope": "outre-mer-select", "selected": "Martinique"}
    if trig == "zone-om-Guyane":
        return {"scope": "outre-mer-select", "selected": "Guyane"}
    if trig == "zone-om-La_Reunion":
        return {"scope": "outre-mer-select", "selected": "La Réunion"}
    if trig == "zone-om-Mayotte":
        return {"scope": "outre-mer-select", "selected": "Mayotte"}
    return {"scope": "france", "selected": None}



@callback(
    Output("zone-main-btn", "children"),
    Input("carte-zone-store", "data"),
)
def _update_zone_main_button(zone_store: dict[str, str | None]) -> list[html.Span]:
    """Met à jour le texte affiché dans le bouton principal pour refléter la sélection."""
    scope = zone_store.get("scope") if isinstance(zone_store, dict) else "france"
    selected = zone_store.get("selected") if isinstance(zone_store, dict) else None

    if scope == "france":
        label = "Toute la France"
    elif scope == "metropole":
        label = "Métropole"
    elif scope == "outre-mer":
        label = "Outre-Mer (tous)"
    elif scope == "outre-mer-select" and selected:
        label = selected
    else:
        label = "Toute la France"

    return [html.Span(label, className="zone-main-selected"), html.Span(" ▾", className="zone-main-caret")]


@callback(
    Output("carte-periode-display", "children"),
    Input("carte-annee-slider", "value"),
)
def _update_carte_periode_display(annees: list[int] | int | None) -> str:
    """Affiche la plage sélectionnée sous le slider."""
    start, end = _normalize_period_value(annees)
    if start == end:
        return f"Année sélectionnée : {start}"
    return f"Période : {start} à {end}"


@callback(
    Output("carte-choropleth", "srcDoc"),
    Output("carte-stats", "children"),
    Input("carte-niveau-geo-dropdown", "value"),
    Input("carte-annee-slider", "value"),
    Input("carte-pathologie-dropdown", "value"),
    Input("carte-indicateur-dropdown", "value"),
    Input("carte-zone-store", "data"),
)
def update_carte(
    niveau_geo: str,
    annees: list[int] | int,
    pathologie_value: str,
    indicateur: str,
    zone_store: dict[str, str | None],
) -> tuple[str, html.P | html.Div]:
    """Callback pour mettre à jour la carte et les statistiques."""
    zone_scope_raw = zone_store.get("scope") if isinstance(zone_store, dict) else "france"
    zone_scope = str(zone_scope_raw) if zone_scope_raw else "france"
    outremer_selected = zone_store.get("selected") if isinstance(zone_store, dict) else None
    start_year, end_year = _normalize_period_value(annees)
    print(
        "🔄 CALLBACK APPELÉ : "
        f"niveau={niveau_geo}, periode={start_year}-{end_year}, "
        f"pathologie={pathologie_value}, indicateur={indicateur}, "
        f"zone_scope={zone_scope}, outremer_selected={outremer_selected}"
    )

    pathologie = None if pathologie_value in (None, "ALL") else pathologie_value
    map_html, df = create_choropleth_html(
        start_year,
        end_year,
        pathologie,
        niveau_geo,
        indicateur,
        zone_scope=zone_scope,
        outremer_selected=outremer_selected,
    )
    stats_content = _build_stats_content(df, niveau_geo, indicateur)

    print(f"✅ CALLBACK TERMINÉ : {len(df)} zones, HTML={len(map_html)} caractères")

    return map_html, stats_content
