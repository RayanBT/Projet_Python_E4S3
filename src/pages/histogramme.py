"""
Page Histogramme - Distributions statistiques des données de santé.
"""

from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Ajouter le chemin racine au sys.path pour les imports
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
from src.components.icons import icon_chart_bar


def layout():
    """Layout de la page histogrammes."""
    # Récupération des listes pour les filtres
    pathologies = get_liste_pathologies()
    regions = get_liste_regions()

    return html.Div(
        [
            html.Div(
                [
                    # Titre de la page
                    html.Div(
                        [
                            #html.Span(icon_chart_bar(), className="icon-large"),
                            html.H1("Histogrammes", className="page-title"),
                        ],
                        className="page-header",
                    ),
                    # Description
                    html.P(
                        "Explorez les distributions statistiques des pathologies selon différentes dimensions : âge, sexe, géographie, etc.",
                        className="page-description",
                    ),
                    # Sélection du type d'histogramme
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
                    # Filtres dynamiques
                    html.Div(
                        [
                            # Année
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
                            # Pathologie
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
                            # Région
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
                            # Sexe
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
                    # Graphique
                    html.Div(
                        [dcc.Graph(id="histogram-graph")],
                        className="chart-container",
                    ),
                    # Statistiques
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
def update_filter_visibility(histogram_type):
    """Met à jour la visibilité des filtres selon le type d'histogramme."""
    visible = {"display": "block"}
    hidden = {"display": "none"}

    # Tous les histogrammes peuvent être filtrés par pathologie, région et sexe
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
def update_histogram(histogram_type, annee, pathologie, region, sexe):
    """Met à jour l'histogramme selon les paramètres sélectionnés."""
    # Conversion des valeurs "all" en None
    pathologie_param = None if pathologie == "all" else pathologie
    region_param = None if region == "all" else region
    sexe_param = None if sexe == "all" else sexe

    # Récupération des données selon le type
    if histogram_type == "age":
        df = get_distribution_age(annee, pathologie_param, region_param, sexe_param)
        
        # Conversion des tranches d'âge en valeurs numériques et regroupement par décennies
        def extract_age_start(age_range):
            """Extrait l'âge de début d'une tranche (ex: '00-04' -> 0, '95et+' -> 95)"""
            if isinstance(age_range, str):
                if age_range.startswith("95"):
                    return 95
                return int(age_range.split("-")[0])
            return 0
        
        df["age_numeric"] = df["cla_age_5"].apply(extract_age_start)
        
        # Regroupement par intervalles de 10 ans (0-10, 10-20, 20-30, ...)
        def get_age_group(age):
            """Regroupe les âges par décennie (0, 10, 20, ...)"""
            if age >= 90:
                return 90  # Groupe 90+ pour inclure 90-94 et 95+
            return (age // 10) * 10
        
        df["age_group"] = df["age_numeric"].apply(get_age_group)
        
        # Agrégation par groupe de 10 ans
        df = df.groupby("age_group", as_index=False)["nombre_cas"].sum()
        df = df.sort_values("age_group")
        
        x_col = "age_group"
        y_col = "nombre_cas"
        title = f"Distribution par Âge ({annee})"
        xaxis_title = "Âge"
        yaxis_title = "Nombre de Cas"

    elif histogram_type == "prevalence":
        # Distribution de la prévalence (%)
        df = get_distribution_prevalence(annee, pathologie_param, region_param, sexe_param)
        
        # Convertir en float si nécessaire et supprimer les valeurs nulles
        df["prevalence"] = pd.to_numeric(df["prevalence"], errors="coerce")
        df = df.dropna(subset=["prevalence"])
        
        # Regroupement par classes de 5%
        def get_prev_class(prev):
            """Regroupe par classes de 5% (0, 5, 10, ...)"""
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
        # Distribution du nombre de cas
        df = get_distribution_nombre_cas(annee, pathologie_param, region_param, sexe_param)
        
        # Regroupement par classes adaptées avec numérotation séquentielle
        def get_cas_class_label(cas):
            """Retourne le label de la classe"""
            if cas < 500:
                return "0-500"
            elif cas < 1000:
                return "500-1k"
            elif cas < 2000:
                return "1k-2k"
            elif cas < 3000:
                return "2k-3k"
            elif cas < 4000:
                return "3k-4k"
            elif cas < 5000:
                return "4k-5k"
            elif cas < 10000:
                return "5k-10k"
            elif cas < 20000:
                return "10k-20k"
            elif cas < 30000:
                return "20k-30k"
            elif cas < 40000:
                return "30k-40k"
            elif cas < 50000:
                return "40k-50k"
            else:
                return "50k+"
        
        df["cas_class_label"] = df["nombre_cas"].apply(get_cas_class_label)
        df = df.groupby("cas_class_label", as_index=False).size()
        df.columns = ["cas_class_label", "frequence"]
        
        # Définir l'ordre des classes
        class_order = ["0-500", "500-1k", "1k-2k", "2k-3k", "3k-4k", "4k-5k", 
                      "5k-10k", "10k-20k", "20k-30k", "30k-40k", "40k-50k", "50k+"]
        df["cas_class_label"] = pd.Categorical(df["cas_class_label"], categories=class_order, ordered=True)
        df = df.sort_values("cas_class_label")
        df = df[df["frequence"] > 0]  # Supprimer les classes vides
        
        x_col = "cas_class_label"
        y_col = "frequence"
        title = f"Distribution du Nombre de Cas ({annee})"
        xaxis_title = "Nombre de Cas"
        yaxis_title = "Fréquence (Nombre d'observations)"

    elif histogram_type == "population":
        # Distribution de la population
        df = get_distribution_population(annee, pathologie_param, region_param, sexe_param)
        
        # Regroupement par classes adaptées avec numérotation séquentielle
        def get_pop_class_label(pop):
            """Retourne le label de la classe"""
            if pop < 10000:
                return "0-10k"
            elif pop < 20000:
                return "10k-20k"
            elif pop < 30000:
                return "20k-30k"
            elif pop < 40000:
                return "30k-40k"
            elif pop < 50000:
                return "40k-50k"
            elif pop < 100000:
                return "50k-100k"
            elif pop < 200000:
                return "100k-200k"
            elif pop < 300000:
                return "200k-300k"
            elif pop < 400000:
                return "300k-400k"
            elif pop < 500000:
                return "400k-500k"
            else:
                return "500k+"
        
        df["pop_class_label"] = df["population"].apply(get_pop_class_label)
        df = df.groupby("pop_class_label", as_index=False).size()
        df.columns = ["pop_class_label", "frequence"]
        
        # Définir l'ordre des classes
        class_order = ["0-10k", "10k-20k", "20k-30k", "30k-40k", "40k-50k",
                      "50k-100k", "100k-200k", "200k-300k", "300k-400k", "400k-500k", "500k+"]
        df["pop_class_label"] = pd.Categorical(df["pop_class_label"], categories=class_order, ordered=True)
        df = df.sort_values("pop_class_label")
        df = df[df["frequence"] > 0]  # Supprimer les classes vides
        
        x_col = "pop_class_label"
        y_col = "frequence"
        title = f"Distribution de la Population ({annee})"
        xaxis_title = "Population"
        yaxis_title = "Fréquence (Nombre d'observations)"

    else:
        # Fallback
        df = pd.DataFrame()
        x_col = ""
        y_col = ""
        title = "Sélectionnez un type de distribution"
        xaxis_title = ""
        yaxis_title = ""

    # Création de l'histogramme
    if not df.empty:
        # Préparation des données pour le hover selon le type
        if histogram_type == "age":
            customdata = [x + 10 if x < 90 else "99+" for x in df[x_col]]
            hovertemplate = "<b>Âge %{x} à %{customdata} ans</b><br>" + yaxis_title + ": %{y:,.0f}<extra></extra>"
            bar_width = 9.8  # Largeur pour couvrir presque 10 ans
            x_range = [-5, 105]
            tick_config = dict(tickmode="linear", tick0=0, dtick=10)
            tickangle = 0
            bargap_value = 0
            
        elif histogram_type == "prevalence":
            customdata = [x + 5 for x in df[x_col]]
            hovertemplate = "<b>Prévalence %{x}% à %{customdata}%</b><br>" + yaxis_title + ": %{y:,.0f}<extra></extra>"
            bar_width = 4.9  # Largeur pour couvrir presque 5%
            max_prev = df[x_col].max()
            x_range = [-2, max_prev + 7]
            tick_config = dict(tickmode="linear", tick0=0, dtick=5)
            tickangle = 0
            bargap_value = 0
            
        elif histogram_type == "nombre_cas":
            # Labels catégoriels - largeur automatique uniforme
            hovertemplate = "<b>%{x}</b><br>" + yaxis_title + ": %{y:,.0f}<extra></extra>"
            bar_width = None  # Largeur automatique pour catégories
            x_range = None
            tick_config = {}
            tickangle = -45
            bargap_value = 0.02
            
        elif histogram_type == "population":
            # Labels catégoriels - largeur automatique uniforme
            hovertemplate = "<b>%{x}</b><br>" + yaxis_title + ": %{y:,.0f}<extra></extra>"
            bar_width = None  # Largeur automatique pour catégories
            x_range = None
            tick_config = {}
            tickangle = -45
            bargap_value = 0.02
        else:
            hovertemplate = "<b>%{x}</b><br>" + yaxis_title + ": %{y:,.0f}<extra></extra>"
            bar_width = None
            x_range = None
            tick_config = {}
            tickangle = 0
            bargap_value = 0.02

        # Création du graphique
        bar_data = {
            "x": df[x_col],
            "y": df[y_col],
            "marker": dict(
                color="#EC4899",
                line=dict(color="#BE185D", width=0.5),
            ),
            "hovertemplate": hovertemplate,
        }
        if histogram_type in ["age", "prevalence"]:
            bar_data["customdata"] = customdata
        if bar_width is not None:
            bar_data["width"] = bar_width

        fig = go.Figure(data=[go.Bar(**bar_data)])

        # Configuration du layout
        xaxis_config = dict(
            tickfont=dict(size=10 if tickangle != 0 else 12),
            tickangle=tickangle,
            **tick_config
        )
        
        if x_range is not None:
            xaxis_config["range"] = x_range

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20)),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            template="plotly_white",
            hovermode="x",
            height=500,
            margin=dict(l=50, r=50, t=80, b=120),  # Plus de marge en bas pour les labels inclinés
            xaxis=xaxis_config,
            bargap=bargap_value,  # Espace adapté selon le type
        )

        # Statistiques
        total = df[y_col].sum()
        moyenne = df[y_col].mean()
        max_val = df[y_col].max()
        min_val = df[y_col].min()

        # Récupération du label pour le maximum
        max_idx = df[df[y_col] == max_val].index[0]
        max_label = df.loc[max_idx, x_col]
        
        # Formatage du label selon le type
        if histogram_type == "age":
            age_start = max_label
            age_end = age_start + 10 if age_start < 90 else "99+"
            max_label_formatted = f"{age_start}-{age_end} ans"
        elif histogram_type == "prevalence":
            prev_start = max_label
            prev_end = prev_start + 5
            max_label_formatted = f"{prev_start}-{prev_end}%"
        elif histogram_type in ["nombre_cas", "population"]:
            # Pour nombre_cas et population, le label est déjà formaté (ex: "0-10k", "50k-100k")
            max_label_formatted = str(max_label)
        else:
            max_label_formatted = str(max_label)
        
        stats_content = [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Total observations", className="stat-label"),
                            html.Span(
                                f"{total:,.0f}", className="stat-value-large"
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span("Moyenne par classe", className="stat-label"),
                            html.Span(
                                f"{moyenne:,.0f}", className="stat-value-large"
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span("Classe la plus fréquente", className="stat-label"),
                            html.Span(
                                f"{max_val:,.0f}", className="stat-value-large"
                            ),
                            html.Span(
                                f"{max_label_formatted}", className="stat-sublabel"
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        [
                            html.Span("Classe la moins fréquente", className="stat-label"),
                            html.Span(
                                f"{min_val:,.0f}", className="stat-value-large"
                            ),
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
            title="Aucune donnée disponible",
            template="plotly_white",
            height=500,
        )
        stats_content = []

    return fig, stats_content
