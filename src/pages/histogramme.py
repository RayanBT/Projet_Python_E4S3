"""
Page Histogramme - Distributions statistiques des données de santé.
"""

import os
import sys
from typing import Any

from dash import Input, Output, callback, dcc, html
import pandas as pd
import plotly.graph_objects as go

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.utils.db_queries import (
    get_distribution_age,
    get_distribution_prevalence,
    get_distribution_nombre_cas,
    get_distribution_population,
    get_liste_pathologies,
    get_liste_regions,
)


def layout() -> html.Div:
    """Layout de la page histogrammes."""
    pathologies = get_liste_pathologies()
    regions = get_liste_regions()

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("Histogrammes", className="page-title"),
                        ],
                        className="page-header",
                    ),
                    html.P(
                        (
                            "Explorez les distributions statistiques des pathologies "
                            "selon différentes dimensions : âge, sexe, géographie, etc."
                        ),
                        className="page-description",
                    ),
                    html.Div(
                        [
                            html.Label("Type de distribution", className="filter-label"),
                            dcc.Dropdown(
                                id="histogram-type",
                                options=[
                                    {
                                        "label": "Distribution par Âge",
                                        "value": "age",
                                    },
                                    {
                                        "label": "Distribution de la Prévalence (%)",
                                        "value": "prevalence",
                                    },
                                    {
                                        "label": "Distribution du Nombre de Cas",
                                        "value": "nombre_cas",
                                    },
                                    {
                                        "label": "Distribution de la Population",
                                        "value": "population",
                                    },
                                ],
                                value="age",
                                clearable=False,
                                className="filter-dropdown",
                            ),
                        ],
                        className="filter-group",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Année", className="filter-label"),
                                    dcc.Dropdown(
                                        id="histogram-annee",
                                        options=[
                                            {"label": str(y), "value": y}
                                            for y in range(2015, 2024)
                                        ],
                                        value=2023,
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                                className="filter-group",
                            ),
                            html.Div(
                                [
                                    html.Label("Pathologie", className="filter-label"),
                                    dcc.Dropdown(
                                        id="histogram-pathologie",
                                        options=[
                                            {"label": "Toutes", "value": "all"}
                                        ]
                                        + [
                                            {"label": p, "value": p}
                                            for p in pathologies
                                        ],
                                        value="all",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                                className="filter-group",
                                id="filter-pathologie-container",
                            ),
                            html.Div(
                                [
                                    html.Label("Région", className="filter-label"),
                                    dcc.Dropdown(
                                        id="histogram-region",
                                        options=[{"label": "Toutes", "value": "all"}]
                                        + [
                                            {"label": f"Région {r}", "value": r}
                                            for r in regions
                                        ],
                                        value="all",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                                className="filter-group",
                                id="filter-region-container",
                            ),
                            html.Div(
                                [
                                    html.Label("Sexe", className="filter-label"),
                                    dcc.Dropdown(
                                        id="histogram-sexe",
                                        options=[
                                            {"label": "Tous", "value": "all"},
                                            {"label": "Hommes", "value": 1},
                                            {"label": "Femmes", "value": 2},
                                        ],
                                        value="all",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                                className="filter-group",
                                id="filter-sexe-container",
                            ),
                        ],
                        className="filters-row",
                    ),
                    html.Div(
                        [dcc.Graph(id="histogram-graph")],
                        className="chart-container",
                    ),
                    html.Div(id="histogram-stats", className="stats-container"),
                ],
                className="page-container",
            )
        ]
    )


@callback(
    [
        Output("filter-pathologie-container", "style"),
        Output("filter-region-container", "style"),
        Output("filter-sexe-container", "style"),
    ],
    Input("histogram-type", "value"),
)
def update_filter_visibility(
    histogram_type: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Met à jour la visibilité des filtres selon le type d'histogramme."""
    visible: dict[str, str] = {"display": "block"}

    return visible, visible, visible


@callback(
    [Output("histogram-graph", "figure"), Output("histogram-stats", "children")],
    [
        Input("histogram-type", "value"),
        Input("histogram-annee", "value"),
        Input("histogram-pathologie", "value"),
        Input("histogram-region", "value"),
        Input("histogram-sexe", "value"),
    ],
)
def update_histogram(
    histogram_type: str,
    annee: int,
    pathologie: str,
    region: str,
    sexe: str | int,
) -> tuple[go.Figure, html.Div | list[html.Div]]:
    """Met à jour l'histogramme selon les paramètres sélectionnés."""
    pathologie_param = None if pathologie == "all" else pathologie
    region_param = None if region == "all" else region
    sexe_param: int | None = (
        None
        if sexe == "all"
        else (
            int(sexe)
            if isinstance(sexe, (int, str)) and str(sexe).isdigit()
            else None
        )
    )


    if histogram_type == "age":
        df = get_distribution_age(
            annee, pathologie_param, region_param, sexe_param
        )

        def extract_age_start(age_range: str) -> int:
            """Extract l'âge de début d'une tranche.

            ex: '00-04' -> 0, '95et+' -> 95
            """
            if isinstance(age_range, str):
                if age_range.startswith("95"):
                    return 95
                return int(age_range.split("-")[0])
            return 0

        df["age_numeric"] = df["cla_age_5"].apply(extract_age_start)

        def get_age_group(age: int) -> int:
            """Regroupe les âges par décennie (0, 10, 20, ...)."""
            if age >= 90:
                return 90
            return (age // 10) * 10

        df["age_group"] = df["age_numeric"].apply(get_age_group)

        grouped_df = df.groupby("age_group", as_index=False)["nombre_cas"].sum()
        df = grouped_df.sort_values("age_group")

        x_col = "age_group"
        y_col = "nombre_cas"
        title = f"Distribution par Âge ({annee})"
        xaxis_title = "Âge"
        yaxis_title = "Nombre de Cas"

    elif histogram_type == "prevalence":
        df = get_distribution_prevalence(
            annee, pathologie_param, region_param, sexe_param
        )

        df["prevalence"] = pd.to_numeric(df["prevalence"], errors="coerce")
        df = df.dropna(subset=["prevalence"])

        def get_prev_class(prev: float) -> int:
            """Regroupe par classes de 5% (0, 5, 10, ...)."""
            return int(float(prev) // 5) * 5

        df["prev_class"] = df["prevalence"].apply(get_prev_class)
        df = df.groupby("prev_class", as_index=False).size()
        df.columns = ["prev_class", "frequence"]
        df = df.sort_values("prev_class")

        x_col = "prev_class"
        y_col = "frequence"
        title = f"Distribution de la Prévalence ({annee})"
        xaxis_title = "Prévalence (%)"
        yaxis_title = "Fréquence (Nombre d'observations)"

    elif histogram_type == "nombre_cas":
        df = get_distribution_nombre_cas(
            annee, pathologie_param, region_param, sexe_param
        )

        def get_cas_class_label(cas: float) -> str:
            """Retourne le label de la classe."""
            if cas < 500:
                return "0-500"
            if cas < 1000:
                return "500-1k"
            if cas < 2000:
                return "1k-2k"
            if cas < 3000:
                return "2k-3k"
            if cas < 4000:
                return "3k-4k"
            if cas < 5000:
                return "4k-5k"
            if cas < 10000:
                return "5k-10k"
            if cas < 20000:
                return "10k-20k"
            if cas < 30000:
                return "20k-30k"
            if cas < 40000:
                return "30k-40k"
            if cas < 50000:
                return "40k-50k"
            return "50k+"

        df["cas_class_label"] = df["nombre_cas"].apply(get_cas_class_label)
        df = df.groupby("cas_class_label", as_index=False).size()
        df.columns = ["cas_class_label", "frequence"]

        class_order = [
            "0-500",
            "500-1k",
            "1k-2k",
            "2k-3k",
            "3k-4k",
            "4k-5k",
            "5k-10k",
            "10k-20k",
            "20k-30k",
            "30k-40k",
            "40k-50k",
            "50k+",
        ]
        df["cas_class_label"] = pd.Categorical(
            df["cas_class_label"], categories=class_order, ordered=True
        )
        df = df.sort_values("cas_class_label")
        df = df[df["frequence"] > 0]

        x_col = "cas_class_label"
        y_col = "frequence"
        title = f"Distribution du Nombre de Cas ({annee})"
        xaxis_title = "Nombre de Cas"
        yaxis_title = "Fréquence (Nombre d'observations)"

    elif histogram_type == "population":
        df = get_distribution_population(
            annee, pathologie_param, region_param, sexe_param
        )

        def get_pop_class_label(pop: float) -> str:
            """Retourne le label de la classe."""
            if pop < 10000:
                return "0-10k"
            if pop < 20000:
                return "10k-20k"
            if pop < 30000:
                return "20k-30k"
            if pop < 40000:
                return "30k-40k"
            if pop < 50000:
                return "40k-50k"
            if pop < 100000:
                return "50k-100k"
            if pop < 200000:
                return "100k-200k"
            if pop < 300000:
                return "200k-300k"
            if pop < 400000:
                return "300k-400k"
            if pop < 500000:
                return "400k-500k"
            return "500k+"

        df["pop_class_label"] = df["population"].apply(get_pop_class_label)
        df = df.groupby("pop_class_label", as_index=False).size()
        df.columns = ["pop_class_label", "frequence"]

        class_order = [
            "0-10k",
            "10k-20k",
            "20k-30k",
            "30k-40k",
            "40k-50k",
            "50k-100k",
            "100k-200k",
            "200k-300k",
            "300k-400k",
            "400k-500k",
            "500k+",
        ]
        df["pop_class_label"] = pd.Categorical(
            df["pop_class_label"], categories=class_order, ordered=True
        )
        df = df.sort_values("pop_class_label")
        df = df[df["frequence"] > 0]

        x_col = "pop_class_label"
        y_col = "frequence"
        title = f"Distribution de la Population ({annee})"
        xaxis_title = "Population"
        yaxis_title = "Fréquence (Nombre d'observations)"

    else:
        df = pd.DataFrame()
        x_col = ""
        y_col = ""
        title = "Sélectionnez un type de distribution"
        xaxis_title = ""
        yaxis_title = ""


    if not df.empty:
        tick_config: dict[str, Any] = {}

        if histogram_type == "age":
            customdata = [x + 10 if x < 90 else "99+" for x in df[x_col]]
            hovertemplate = (
                f"<b>Âge %{{x}} à %{{customdata}} ans</b><br>"
                f"{yaxis_title}: %{{y:,.0f}}<extra></extra>"
            )
            bar_width = 9.8
            x_range = [-5, 105]
            tick_config = {"tickmode": "linear", "tick0": 0, "dtick": 10}
            tickangle = 0
            bargap_value = 0.0

        elif histogram_type == "prevalence":
            customdata = [x + 5 for x in df[x_col]]
            hovertemplate = (
                f"<b>Prévalence %{{x}}% à %{{customdata}}%</b><br>"
                f"{yaxis_title}: %{{y:,.0f}}<extra></extra>"
            )
            bar_width = 4.9
            max_prev: Any = df[x_col].max()
            x_range = [-2, max_prev + 7]
            tick_config = {"tickmode": "linear", "tick0": 0, "dtick": 5}
            tickangle = 0
            bargap_value = 0.0

        elif histogram_type == "nombre_cas":
            hovertemplate = (
                f"<b>%{{x}}</b><br>{yaxis_title}: %{{y:,.0f}}<extra></extra>"
            )
            bar_width = None
            x_range = None
            tickangle = -45
            bargap_value = 0.02

        elif histogram_type == "population":
            hovertemplate = (
                f"<b>%{{x}}</b><br>{yaxis_title}: %{{y:,.0f}}<extra></extra>"
            )
            bar_width = None
            x_range = None
            tickangle = -45
            bargap_value = 0.02
        else:
            hovertemplate = (
                f"<b>%{{x}}</b><br>{yaxis_title}: %{{y:,.0f}}<extra></extra>"
            )
            bar_width = None
            x_range = None
            tickangle = 0
            bargap_value = 0.02

        bar_data = {
            "x": df[x_col],
            "y": df[y_col],
            "marker": {"color": "#EC4899", "line": {"color": "#BE185D", "width": 0.5}},
            "hovertemplate": hovertemplate,
        }
        if histogram_type in ["age", "prevalence"]:
            bar_data["customdata"] = customdata
        if bar_width is not None:
            bar_data["width"] = bar_width

        fig = go.Figure(data=[go.Bar(**bar_data)])

        xaxis_config = {
            "tickfont": {"size": 10 if tickangle != 0 else 12},
            "tickangle": tickangle,
            **tick_config,
        }

        if x_range is not None:
            xaxis_config["range"] = x_range

        fig.update_layout(
            title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 20}},
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            template="plotly_white",
            hovermode="x",
            height=500,
            margin={"l": 50, "r": 50, "t": 80, "b": 120},
            xaxis=xaxis_config,
            bargap=bargap_value,
        )


        total = df[y_col].sum()
        moyenne = df[y_col].mean()
        max_val = df[y_col].max()
        min_val = df[y_col].min()

        max_idx = df[df[y_col] == max_val].index[0]
        max_label: Any = df.loc[max_idx, x_col]

        if histogram_type == "age":
            age_start_val = int(max_label)
            if age_start_val < 90:
                age_end: int | str = age_start_val + 10
            else:
                age_end = "99+"
            max_label_formatted = f"{age_start_val}-{age_end} ans"
        elif histogram_type == "prevalence":
            prev_start_val = int(max_label)
            prev_end = prev_start_val + 5
            max_label_formatted = f"{prev_start_val}-{prev_end}%"
        elif histogram_type in ["nombre_cas", "population"]:
            max_label_formatted = str(max_label)
        else:
            max_label_formatted = str(max_label)

        stats_content = [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Total observations", className="stat-label"),
                            html.Span(f"{total:,.0f}", className="stat-value-large"),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Moyenne par classe", className="stat-label"
                            ),
                            html.Span(
                                f"{moyenne:,.0f}", className="stat-value-large"
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Classe la plus fréquente",
                                className="stat-label",
                            ),
                            html.Span(f"{max_val:,.0f}", className="stat-value-large"),
                            html.Span(
                                f"{max_label_formatted}", className="stat-sublabel"
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Classe la moins fréquente",
                                className="stat-label",
                            ),
                            html.Span(f"{min_val:,.0f}", className="stat-value-large"),
                        ],
                        className="stat-card",
                    ),
                ],
                className="stats-grid",
            )
        ]

    else:
        fig = go.Figure()
        fig.update_layout(
            title="Aucune donnée disponible", template="plotly_white", height=500
        )
        stats_content = []

    return fig, stats_content
