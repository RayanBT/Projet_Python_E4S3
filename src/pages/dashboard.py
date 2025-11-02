"""Dashboard principal avec carte choropleth et graphiques interactifs.

NOTE: Ce fichier n'est plus utilisé dans la nouvelle architecture.
Les fonctionnalités ont été séparées en pages individuelles :
- carte.py : pour la carte choroplèthe
- evolution.py : pour les graphiques d'évolution
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple

import folium
from branca.colormap import LinearColormap
import plotly.express as px
from dash import Input, Output, callback, dcc, html

from src.utils.db_queries import (
    get_evolution_pathologies,
    get_liste_pathologies,
    get_pathologies_par_departement,
    get_pathologies_par_region,
)

GEOJSON_PATH = Path("data/geolocalisation/datagouv-communes.geojson")
FRANCE_CENTER: Tuple[float, float] = (46.603354, 1.888334)

SEGMENTATION_OPTIONS = [
    {"label": "R\u00e9gions", "value": "region"},
    {"label": "D\u00e9partements", "value": "departement"},
]

METRIC_OPTIONS = [
    {"label": "Pr\u00e9valence (%)", "value": "prevalence"},
    {"label": "Nombre de cas", "value": "total_cas"},
]


def _format_int(value: float | int) -> str:
    return f"{int(round(value)):,}".replace(",", " ")


def _format_rate(value: float) -> str:
    return f"{float(value):.2f} %"


@lru_cache(maxsize=1)
def _load_geo_resources() -> tuple[dict, Dict[str, str], Dict[str, str]]:
    with GEOJSON_PATH.open("r", encoding="utf-8") as geo_file:
        geo_data = json.load(geo_file)

    region_labels: Dict[str, str] = {}
    depart_labels: Dict[str, str] = {}

    for feature in geo_data.get("features", []):
        props = feature.get("properties", {})
        region_code = props.get("code_insee_region")
        if region_code is not None:
            region_code_str = f"{int(region_code):02d}"
            region_labels.setdefault(region_code_str, props.get("region", ""))

        depart_code = props.get("code_departement")
        if depart_code:
            depart_labels.setdefault(str(depart_code), props.get("departement", ""))

    return geo_data, region_labels, depart_labels


def _prepare_feature_collection(
    segmentation: str,
    stats_map: Dict[str, dict],
) -> dict:
    geo_data, region_labels, depart_labels = _load_geo_resources()
    features = []

    for feature in geo_data.get("features", []):
        props = feature.get("properties", {})
        if segmentation == "region":
            raw_code = props.get("code_insee_region")
            code = f"{int(raw_code):02d}" if raw_code is not None else None
            label = region_labels.get(code or "", props.get("region", ""))
        else:
            code = props.get("code_departement")
            code = str(code) if code is not None else None
            label = depart_labels.get(code or "", props.get("departement", ""))

        if not code:
            continue

        stats = stats_map.get(code)
        if not stats:
            continue

        features.append(
            {
                "type": feature.get("type"),
                "geometry": feature.get("geometry"),
                "properties": {
                    "code": code,
                    "label": label or code,
                    "metric_value": stats["metric_value"],
                    "total_cas_display": stats["total_cas_display"],
                    "population_display": stats["population_display"],
                    "prevalence_display": stats["prevalence_display"],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def _build_stats_map(df, segmentation: str, metric: str) -> Dict[str, dict]:
    metric_key = "prevalence" if metric == "prevalence" else "total_cas"
    stats: Dict[str, dict] = {}

    for row in df.itertuples():
        if segmentation == "region":
            code = f"{int(getattr(row, 'region')):02d}"
        else:
            code = str(getattr(row, "dept")).zfill(2)

        metric_value = float(getattr(row, metric_key))
        stats[code] = {
            "metric_value": metric_value,
            "total_cas_display": _format_int(getattr(row, "total_cas")),
            "population_display": _format_int(getattr(row, "population_totale")),
            "prevalence_display": _format_rate(getattr(row, "prevalence")),
        }

    return stats


def _compute_color_scale(values: Iterable[float]) -> Tuple[float, float]:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return 0.0, 1.0

    vmin = min(vals)
    vmax = max(vals)
    if vmin == vmax:
        if vmax == 0:
            vmax = 1.0
        else:
            vmin = vmax * 0.8
            vmax = vmax * 1.2
    return vmin, vmax


def create_choropleth_html(
    annee: int,
    segmentation: str,
    metric: str,
    pathologie: str | None,
) -> str:
    if segmentation == "region":
        df = get_pathologies_par_region(annee, pathologie)
    else:
        df = get_pathologies_par_departement(annee, pathologie)

    if df.empty:
        return "<h3 style='font-family: Arial; color:#444;'>Aucune donn\u00e9e disponible pour cette s\u00e9lection.</h3>"

    stats_map = _build_stats_map(df, segmentation, metric)
    geojson = _prepare_feature_collection(segmentation, stats_map)

    metric_label = "Pr\u00e9valence (%)" if metric == "prevalence" else "Nombre de cas"
    palette = (
        ["#fff5eb", "#fd8d3c", "#d94801", "#7f2704"]
        if metric == "prevalence"
        else ["#f7fbff", "#6baed6", "#2171b5", "#08306b"]
    )

    vmin, vmax = _compute_color_scale(stats["metric_value"] for stats in stats_map.values())
    colormap = LinearColormap(palette, vmin=vmin, vmax=vmax, caption=metric_label)

    map_obj = folium.Map(
        location=FRANCE_CENTER,
        zoom_start=5.6 if segmentation == "region" else 6.2,
        tiles="CartoDB positron",
        control_scale=True,
    )

    def _style_function(feature: dict) -> dict:
        value = feature["properties"].get("metric_value")
        if value is None:
            return {
                "fillColor": "#d9d9d9",
                "color": "#9a9a9a",
                "weight": 0.2,
                "fillOpacity": 0.4,
            }
        return {
            "fillColor": colormap(value),
            "color": "#555555",
            "weight": 0.4 if segmentation == "departement" else 0.25,
            "fillOpacity": 0.75,
        }

    folium.GeoJson(
        geojson,
        style_function=_style_function,
        highlight_function=lambda feature: {
            "weight": 2,
            "color": "#000000",
            "fillOpacity": 0.9,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=[
                "label",
                "total_cas_display",
                "population_display",
                "prevalence_display",
            ],
            aliases=[
                "Territoire :",
                "Nombre de cas :",
                "Population :",
                "Pr\u00e9valence :",
            ],
            sticky=False,
            labels=True,
            localize=True,
            style=(
                "background-color: white; color: #333333; font-family: Arial;"
                " font-size: 13px; padding: 8px 12px;"
            ),
        ),
    ).add_to(map_obj)

    colormap.add_to(map_obj)
    folium.LayerControl(collapsed=True).add_to(map_obj)

    return map_obj.get_root().render()


def create_evolution_figure(
    debut_annee: int = 2019,
    fin_annee: int = 2023,
    pathologie: str | None = None,
):
    df = get_evolution_pathologies(debut_annee, fin_annee)

    if pathologie:
        df = df[df["patho_niv1"] == pathologie]

    fig = px.line(
        df,
        x="annee",
        y="total_cas",
        color="patho_niv1",
        title="\u00c9volution des pathologies au fil du temps",
        labels={
            "annee": "Ann\u00e9e",
            "total_cas": "Nombre de cas",
            "patho_niv1": "Pathologie",
        },
    )

    fig.update_layout(
        legend_title="Pathologies",
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def layout():
    pathologies = get_liste_pathologies()

    return html.Div(
        [
            html.H1(
                "Dashboard des pathologies en France (DEPRECATED)",
                style={"textAlign": "center", "marginBottom": "30px"},
            ),
            html.Div([
                html.H3("⚠️ Cette page n'est plus utilisée"),
                html.P("Les fonctionnalités ont été séparées en pages individuelles :"),
                html.Ul([
                    html.Li(html.A("Carte Choroplèthe", href="/carte")),
                    html.Li(html.A("Évolution Temporelle", href="/evolution")),
                    html.Li(html.A("Accueil", href="/")),
                ]),
            ], style={
                "textAlign": "center",
                "padding": "40px",
                "backgroundColor": "#fff3cd",
                "border": "1px solid #ffc107",
                "borderRadius": "10px",
                "margin": "20px auto",
                "maxWidth": "600px"
            }),
        ],
        style={"padding": "20px"},
    )


# CALLBACKS COMMENTÉS POUR ÉVITER LES CONFLITS
# Ces callbacks sont maintenant dans carte.py et evolution.py

# @callback(
#     Output("choropleth-map", "srcDoc"),
#     Input("annee-slider", "value"),
#     Input("pathologie-dropdown", "value"),
#     Input("segmentation-radio", "value"),
#     Input("metric-radio", "value"),
# )
# def update_map(annee: int, pathologie: str | None, segmentation: str, metric: str) -> str:
#     return create_choropleth_html(annee, segmentation, metric, pathologie)


# @callback(
#     Output("evolution-graph", "figure"),
#     Input("pathologie-dropdown", "value"),
# )
# def update_evolution(pathologie: str | None):
#     return create_evolution_figure(pathologie=pathologie)


GEOJSON_PATH = Path("data/geolocalisation/datagouv-communes.geojson")
FRANCE_CENTER: Tuple[float, float] = (46.603354, 1.888334)

SEGMENTATION_OPTIONS = [
    {"label": "R\u00e9gions", "value": "region"},
    {"label": "D\u00e9partements", "value": "departement"},
]

METRIC_OPTIONS = [
    {"label": "Pr\u00e9valence (%)", "value": "prevalence"},
    {"label": "Nombre de cas", "value": "total_cas"},
]


def _format_int(value: float | int) -> str:
    return f"{int(round(value)):,}".replace(",", " ")


def _format_rate(value: float) -> str:
    return f"{float(value):.2f} %"


@lru_cache(maxsize=1)
def _load_geo_resources() -> tuple[dict, Dict[str, str], Dict[str, str]]:
    with GEOJSON_PATH.open("r", encoding="utf-8") as geo_file:
        geo_data = json.load(geo_file)

    region_labels: Dict[str, str] = {}
    depart_labels: Dict[str, str] = {}

    for feature in geo_data.get("features", []):
        props = feature.get("properties", {})
        region_code = props.get("code_insee_region")
        if region_code is not None:
            region_code_str = f"{int(region_code):02d}"
            region_labels.setdefault(region_code_str, props.get("region", ""))

        depart_code = props.get("code_departement")
        if depart_code:
            depart_labels.setdefault(str(depart_code), props.get("departement", ""))

    return geo_data, region_labels, depart_labels


def _prepare_feature_collection(
    segmentation: str,
    stats_map: Dict[str, dict],
) -> dict:
    geo_data, region_labels, depart_labels = _load_geo_resources()
    features = []

    for feature in geo_data.get("features", []):
        props = feature.get("properties", {})
        if segmentation == "region":
            raw_code = props.get("code_insee_region")
            code = f"{int(raw_code):02d}" if raw_code is not None else None
            label = region_labels.get(code or "", props.get("region", ""))
        else:
            code = props.get("code_departement")
            code = str(code) if code is not None else None
            label = depart_labels.get(code or "", props.get("departement", ""))

        if not code:
            continue

        stats = stats_map.get(code)
        if not stats:
            continue

        features.append(
            {
                "type": feature.get("type"),
                "geometry": feature.get("geometry"),
                "properties": {
                    "code": code,
                    "label": label or code,
                    "metric_value": stats["metric_value"],
                    "total_cas_display": stats["total_cas_display"],
                    "population_display": stats["population_display"],
                    "prevalence_display": stats["prevalence_display"],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def _build_stats_map(df, segmentation: str, metric: str) -> Dict[str, dict]:
    metric_key = "prevalence" if metric == "prevalence" else "total_cas"
    stats: Dict[str, dict] = {}

    for row in df.itertuples():
        if segmentation == "region":
            code = f"{int(getattr(row, 'region')):02d}"
        else:
            code = str(getattr(row, "dept")).zfill(2)

        metric_value = float(getattr(row, metric_key))
        stats[code] = {
            "metric_value": metric_value,
            "total_cas_display": _format_int(getattr(row, "total_cas")),
            "population_display": _format_int(getattr(row, "population_totale")),
            "prevalence_display": _format_rate(getattr(row, "prevalence")),
        }

    return stats


def _compute_color_scale(values: Iterable[float]) -> Tuple[float, float]:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return 0.0, 1.0

    vmin = min(vals)
    vmax = max(vals)
    if vmin == vmax:
        if vmax == 0:
            vmax = 1.0
        else:
            vmin = vmax * 0.8
            vmax = vmax * 1.2
    return vmin, vmax


def create_choropleth_html(
    annee: int,
    segmentation: str,
    metric: str,
    pathologie: str | None,
) -> str:
    if segmentation == "region":
        df = get_pathologies_par_region(annee, pathologie)
    else:
        df = get_pathologies_par_departement(annee, pathologie)

    if df.empty:
        return "<h3 style='font-family: Arial; color:#444;'>Aucune donn\u00e9e disponible pour cette s\u00e9lection.</h3>"

    stats_map = _build_stats_map(df, segmentation, metric)
    geojson = _prepare_feature_collection(segmentation, stats_map)

    metric_label = "Pr\u00e9valence (%)" if metric == "prevalence" else "Nombre de cas"
    palette = (
        ["#fff5eb", "#fd8d3c", "#d94801", "#7f2704"]
        if metric == "prevalence"
        else ["#f7fbff", "#6baed6", "#2171b5", "#08306b"]
    )

    vmin, vmax = _compute_color_scale(stats["metric_value"] for stats in stats_map.values())
    colormap = LinearColormap(palette, vmin=vmin, vmax=vmax, caption=metric_label)

    map_obj = folium.Map(
        location=FRANCE_CENTER,
        zoom_start=5.6 if segmentation == "region" else 6.2,
        tiles="CartoDB positron",
        control_scale=True,
    )

    def _style_function(feature: dict) -> dict:
        value = feature["properties"].get("metric_value")
        if value is None:
            return {
                "fillColor": "#d9d9d9",
                "color": "#9a9a9a",
                "weight": 0.2,
                "fillOpacity": 0.4,
            }
        return {
            "fillColor": colormap(value),
            "color": "#555555",
            "weight": 0.4 if segmentation == "departement" else 0.25,
            "fillOpacity": 0.75,
        }

    folium.GeoJson(
        geojson,
        style_function=_style_function,
        highlight_function=lambda feature: {
            "weight": 2,
            "color": "#000000",
            "fillOpacity": 0.9,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=[
                "label",
                "total_cas_display",
                "population_display",
                "prevalence_display",
            ],
            aliases=[
                "Territoire :",
                "Nombre de cas :",
                "Population :",
                "Pr\u00e9valence :",
            ],
            sticky=False,
            labels=True,
            localize=True,
            style=(
                "background-color: white; color: #333333; font-family: Arial;"
                " font-size: 13px; padding: 8px 12px;"
            ),
        ),
    ).add_to(map_obj)

    colormap.add_to(map_obj)
    folium.LayerControl(collapsed=True).add_to(map_obj)

    return map_obj.get_root().render()


def create_evolution_figure(
    debut_annee: int = 2019,
    fin_annee: int = 2023,
    pathologie: str | None = None,
):
    df = get_evolution_pathologies(debut_annee, fin_annee)

    if pathologie:
        df = df[df["patho_niv1"] == pathologie]

    fig = px.line(
        df,
        x="annee",
        y="total_cas",
        color="patho_niv1",
        title="\u00c9volution des pathologies au fil du temps",
        labels={
            "annee": "Ann\u00e9e",
            "total_cas": "Nombre de cas",
            "patho_niv1": "Pathologie",
        },
    )

    fig.update_layout(
        legend_title="Pathologies",
        hovermode="x unified",
        template="plotly_white",
    )

    return fig




def layout():
    pathologies = get_liste_pathologies()

    return html.Div(
        [
            html.H1(
                "Dashboard des pathologies en France (DEPRECATED)",
                style={"textAlign": "center", "marginBottom": "30px"},
            ),
            html.Div([
                html.H3("⚠️ Cette page n'est plus utilisée"),
                html.P("Les fonctionnalités ont été séparées en pages individuelles :"),
                html.Ul([
                    html.Li(html.A("Carte Choroplèthe", href="/carte")),
                    html.Li(html.A("Évolution Temporelle", href="/evolution")),
                    html.Li(html.A("Accueil", href="/")),
                ]),
            ], style={
                "textAlign": "center",
                "padding": "40px",
                "backgroundColor": "#fff3cd",
                "border": "1px solid #ffc107",
                "borderRadius": "10px",
                "margin": "20px auto",
                "maxWidth": "600px"
            }),
        ],
        style={"padding": "20px"},
    )


# CALLBACKS COMMENTÉS POUR ÉVITER LES CONFLITS
# Ces callbacks sont maintenant dans carte.py et evolution.py

# @callback(
#     Output("choropleth-map", "srcDoc"),
#     Input("annee-slider", "value"),
#     Input("pathologie-dropdown", "value"),
#     Input("segmentation-radio", "value"),
#     Input("metric-radio", "value"),
# )
# def update_map(annee: int, pathologie: str | None, segmentation: str, metric: str) -> str:
#     return create_choropleth_html(annee, segmentation, metric, pathologie)


# @callback(
#     Output("evolution-graph", "figure"),
#     Input("pathologie-dropdown", "value"),
# )
# def update_evolution(pathologie: str | None):
#     return create_evolution_figure(pathologie=pathologie)
