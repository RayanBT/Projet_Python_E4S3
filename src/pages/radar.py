"""Page dédiée à l'analyse des données via un graphique radar."""

from typing import Any

from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go
import pandas as pd

from src.components.icons import icon_pin
from src.utils.db_queries import (
    get_evolution_pathologies,
    get_liste_pathologies,
    get_liste_regions,
    get_pathologies_par_region,
    get_pathologies_with_niv2,
    get_repartition_patho_niv2,
    get_repartition_patho_niv3,
)

ALLOWED_PATHOLOGIES = [
    "Traitements risques vasculaire",
    "Traitements psychotropes",
    "Maladies psychatriques",
    "Maladies neurologiques",
    "Insuffisance rénale",
    "Maladies inflammatoires/VIH",
    "Maladies cardiovasculaires",
    "Cancers"
]

NO_NIV3_PATHOLOGIES = [
    "Traitements risques vasculaire",
    "Traitements psychotropes",
    "Maladies psychatriques",
    "Maladies neurologiques",
    "Insuffisance rénale"
]


def create_radar_figure(
    dimension: str = "pathologies",
    debut_annee: int = 2015,
    fin_annee: int = 2023,
    selection: str | list[str] | None = None,
    region: str | None = None,
    pathologie_filter: str | None = None,
    indicateur: str = "total_cas"
) -> go.Figure:
    """Crée le graphique radar pour comparer les données selon la dimension choisie."""

    if dimension == "pathologies":
        if isinstance(selection, str) and selection:
            df2 = get_repartition_patho_niv2(debut_annee, fin_annee, selection)
            df2 = df2.sort_values(indicateur, ascending=False)
            categories = df2["patho_niv2"].fillna("Inconnue").tolist()
            values = df2[indicateur].tolist()
            title = f"Répartition des sous-pathologies de '{selection}' ({debut_annee}-{fin_annee})"
        else:
            df = get_evolution_pathologies(debut_annee, fin_annee, None, region)
            df = df.groupby("patho_niv1")[indicateur].sum().reset_index()
            df = df.sort_values(indicateur, ascending=False)
            categories = df["patho_niv1"].tolist()
            values = df[indicateur].tolist()
            title = f"Répartition des pathologies ({debut_annee}-{fin_annee})"

    elif dimension == "regions":
        # Agrégation sur la période
        dfs = []
        for annee in range(debut_annee, fin_annee + 1):
            df_year = get_pathologies_par_region(annee, pathologie_filter)
            dfs.append(df_year)
        df = pd.concat(dfs, ignore_index=True)
        
        if indicateur == "prevalence":
            # Pour la prévalence, on doit recalculer sur l'agrégation
            df = df.groupby("region").agg({
                "total_cas": "sum",
                "population_totale": "sum"
            }).reset_index()
            df["prevalence"] = (df["total_cas"] / df["population_totale"] * 100).round(2)
            df = df[df["region"].str.len() == 2]
        else:
            df = df.groupby("region")[indicateur].sum().reset_index()
            df = df[df["region"].str.len() == 2]
            
        if selection:
            df = df[df["region"].isin(selection)]

        region_names = {
            "11": "Île-de-France",
            "24": "Centre-Val de Loire",
            "27": "Bourgogne-Franche-Comté",
            "28": "Normandie",
            "32": "Hauts-de-France",
            "44": "Grand Est",
            "52": "Pays de la Loire",
            "53": "Bretagne",
            "75": "Nouvelle-Aquitaine",
            "76": "Occitanie",
            "84": "Auvergne-Rhône-Alpes",
            "93": "Provence-Alpes-Côte d'Azur",
            "94": "Corse",
        }
        df["region_name"] = df["region"].map(region_names)
        df = df.sort_values(indicateur, ascending=False)
        categories = df["region_name"].tolist()
        values = df[indicateur].tolist()
        
        if pathologie_filter:
            title = f"Répartition de '{pathologie_filter}' par région ({debut_annee}-{fin_annee})"
        else:
            title = f"Répartition par région ({debut_annee}-{fin_annee})"

    else:
        categories, values, title = [], [], "Aucune donnée"

    if not categories or not values:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible pour cette sélection",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 18},
        )
        return fig

    # Ajouter suffixe aux valeurs et titre selon l'indicateur
    if indicateur == "prevalence":
        hover_text = [f"{cat}<br>{val:.2f}%" for cat, val in zip(categories, values)]
        title += " (Prévalence en %)"
    else:
        hover_text = [f"{cat}<br>{val:,.0f} cas" for cat, val in zip(categories, values)]
        title += " (Nombre de cas)"

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name=f"{debut_annee}-{fin_annee}",
            marker={"color": 'rgba(31,119,180,0.8)'},
            text=hover_text,
            hoverinfo="text",
        )
    )

    fig.update_layout(
        polar={
            "radialaxis": {"visible": True, "gridcolor": "rgba(0, 0, 0, 0.1)"},
            "angularaxis": {
                "gridcolor": "rgba(0, 0, 0, 0.1)",
                "direction": "clockwise"
            },
        },
        showlegend=False,
        title={"text": title, "x": 0.5},
        height=700,
        margin={"t": 80, "b": 60, "l": 80, "r": 80},
    )
    return fig


def create_radar_figure_niv3(
    debut_annee: int = 2015,
    fin_annee: int = 2023,
    selection: str | None = None,
    indicateur: str = "total_cas"
) -> go.Figure:
    """Crée un second graphique radar montrant la répartition des patho_niv3."""
    if not selection or not isinstance(selection, str):
        return go.Figure()

    df3 = get_repartition_patho_niv3(debut_annee, fin_annee, selection)
    if df3.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune sous-sous-pathologie (patho_niv3) disponible pour cette sélection",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14},
        )
        return fig

    df3 = df3.sort_values(indicateur, ascending=False)
    categories = df3["patho_niv3"].fillna("Inconnue").tolist()
    values = df3[indicateur].tolist()
    
    # Ajouter suffixe aux valeurs et titre selon l'indicateur
    if indicateur == "prevalence":
        hover_text = [f"{cat}<br>{val:.2f}%" for cat, val in zip(categories, values)]
        title_suffix = " (Prévalence en %)"
    else:
        hover_text = [f"{cat}<br>{val:,.0f} cas" for cat, val in zip(categories, values)]
        title_suffix = " (Nombre de cas)"

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="patho_niv3",
            text=hover_text,
            hoverinfo="text",
            marker={"color": 'rgba(220,20,60,0.8)'}
        )
    )
    fig.update_layout(
        polar={
            "radialaxis": {"visible": True, "gridcolor": "rgba(0, 0, 0, 0.1)"},
            "angularaxis": {
                "gridcolor": "rgba(0, 0, 0, 0.1)",
                "direction": "clockwise"
            },
        },
        showlegend=True,
        title={"text": f"Répartition des patho_niv3 de '{selection}' ({debut_annee}-{fin_annee}){title_suffix}", "x": 0.5},
        height=700,
        margin={"t": 80, "b": 60, "l": 80, "r": 80},
    )
    return fig


def layout() -> html.Div:
    """Construit le layout de la page du graphique radar."""
    return html.Div(
        className="page-container",
        children=[
            html.Div(
                className="mb-3",
                children=[
                    html.H1(
                        "Analyse Radar Multi-Dimensionnelle",
                        className="page-title text-center",
                    ),
                    html.P(
                        (
                            "Visualisez et comparez différentes dimensions "
                            "de données sous forme de graphique radar."
                        ),
                        className="text-center text-muted",
                    ),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="flex-controls",
                        children=[
                            html.Div(
                                className="filter-section",
                                children=[
                                    html.Label("Dimension à analyser"),
                                    dcc.Dropdown(
                                        id="radar-dimension-dropdown",
                                        options=[  # type: ignore[arg-type]
                                            {"label": "Pathologies", "value": "pathologies"},
                                            {"label": "Régions", "value": "regions"},
                                        ],
                                        value="pathologies",
                                        clearable=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-section period-filter",
                                children=[
                                    html.Label("Période d'analyse", className="form-label"),
                                    html.Div(className="filter-content", children=[
                                        dcc.RangeSlider(
                                            id="radar-periode-slider",
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
                                            className="period-slider",
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                                        html.Div(
                                            id="radar-periode-display",
                                            className="period-display"
                                        )
                                    ])
                                ],
                            ),
                            html.Div(
                                className="filter-section",
                                children=[
                                    html.Label("Indicateur à visualiser"),
                                    dcc.Dropdown(
                                        id="radar-indicateur-dropdown",
                                        options=[
                                            {"label": "Nombre de cas", "value": "total_cas"},
                                            {"label": "Prévalence (%)", "value": "prevalence"},
                                        ],
                                        value="total_cas",
                                        clearable=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-section",
                                id="radar-pathologie-selector-container",
                                children=[
                                    html.Label("Choisir pathologie (optionnel)", id="radar-pathologie-selector-label"),
                                    dcc.Dropdown(
                                        id="radar-patho-niv1-dropdown",
                                        options=[
                                            {"label": p, "value": p}
                                            for p in get_pathologies_with_niv2()
                                            if p in ALLOWED_PATHOLOGIES
                                        ],
                                        value=None,
                                        placeholder="Sélectionnez une pathologie",
                                        clearable=True,
                                    ),
                                ],
                            ),
                            dcc.Dropdown(
                                id="radar-elements-dropdown",
                                multi=True,
                                style={"display": "none"},
                            ),
                            html.Div(id="radar-warning"),
                        ],
                    )
                ],
            ),
            html.Div(
                className="card mt-2",
                children=[
                    html.Div(
                        className="radar-row",
                        children=[
                            dcc.Graph(
                                id="radar-graph",
                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                                },
                                style={"width": "100%", "display": "block"},
                            ),
                            dcc.Graph(
                                id="radar-graph-niv3",
                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                                },
                                style={"display": "none"},
                            ),
                        ],
                    )
                ],
            ),
            html.Div(className="card mt-2", children=[
                html.H3(
                    [icon_pin("icon-inline"), "Comment interpréter ce graphique ?"],
                    className="subsection-title"
                ),
                html.Ul(className="info-list", children=[
                    html.Li("Chaque axe représente un élément analysé"),
                    html.Li("La distance du centre correspond à la valeur associée"),
                    html.Li("Plus la surface est grande, plus les valeurs sont élevées"),
                ]),
            ]),
            html.Div(className="text-center mt-3", children=[
                dcc.Link(
                    html.Button("← Retour à l'accueil", className="btn btn-secondary"),
                    href='/',
                ),
            ])
        ]
    )


@callback(
    [
        Output("radar-elements-dropdown", "options"),
        Output("radar-elements-dropdown", "value"),
        Output("radar-pathologie-selector-label", "children"),
        Output("radar-patho-niv1-dropdown", "options"),
        Output("radar-patho-niv1-dropdown", "placeholder"),
    ],
    Input("radar-dimension-dropdown", "value"),
)
def update_elements_options(
    dimension: str
) -> tuple[list[dict[str, str]], list[str] | None, str, list[dict[str, str]], str]:
    """Met à jour le contenu du dropdown selon la dimension."""
    if dimension == "pathologies":
        pathologies = [p for p in get_liste_pathologies() if p in ALLOWED_PATHOLOGIES]
        options = [{"label": p, "value": p} for p in pathologies]
        label = "Voir sous-pathologies (optionnel)"
        patho_options = [
            {"label": p, "value": p}
            for p in get_pathologies_with_niv2()
            if p in ALLOWED_PATHOLOGIES
        ]
        placeholder = "Sélectionnez une sous-pathologie"
        return options, pathologies, label, patho_options, placeholder
    
    # dimension == "regions"
    regions = get_liste_regions()
    regions = [r for r in regions if len(r) == 2]
    options = [{"label": r, "value": r} for r in regions]
    options = sorted(options, key=lambda x: x["label"])
    label = "Choisir pathologie (optionnel)"
    patho_options = [{"label": p, "value": p} for p in get_liste_pathologies()]
    placeholder = "Sélectionnez une pathologie"
    return options, None, label, patho_options, placeholder


@callback(
    [
        Output("radar-graph", "figure"),
        Output("radar-warning", "children"),
        Output("radar-periode-display", "children"),
        Output("radar-periode-slider", "style"),
        Output("radar-graph-niv3", "figure"),
        Output("radar-graph-niv3", "style"),
    ],
    [
        Input("radar-dimension-dropdown", "value"),
        Input("radar-periode-slider", "value"),
        Input("radar-elements-dropdown", "value"),
        Input("radar-patho-niv1-dropdown", "value"),
        Input("radar-indicateur-dropdown", "value"),
    ],
)
def update_radar(
    dimension: str,
    periode: list[int],
    selection: list[str],
    patho_niv1_selected: str | None,
    indicateur: str
) -> tuple[go.Figure, str, str, dict[str, Any], go.Figure, dict[str, str]]:
    """Met à jour le graphique radar."""
    debut_annee, fin_annee = periode
    warning = ""
    periode_text = f"De {debut_annee} à {fin_annee}"
    slider_style: dict[str, Any] = {}

    # Pour les pathologies, patho_niv1_selected affiche les sous-pathologies
    # Pour les régions, patho_niv1_selected filtre par pathologie
    if dimension == "pathologies":
        sel = patho_niv1_selected if patho_niv1_selected else selection
        figure = create_radar_figure(dimension, debut_annee, fin_annee, sel, indicateur=indicateur)
        
        if isinstance(sel, str) and sel and sel not in NO_NIV3_PATHOLOGIES:
            fig_niv3 = create_radar_figure_niv3(debut_annee, fin_annee, sel, indicateur=indicateur)
            style_niv3: dict[str, str] = {"width": "100%", "display": "block", "marginTop": "20px"}
        else:
            fig_niv3 = go.Figure()
            style_niv3 = {"display": "none"}
    else:  # dimension == "regions"
        figure = create_radar_figure(dimension, debut_annee, fin_annee, selection, pathologie_filter=patho_niv1_selected, indicateur=indicateur)
        fig_niv3 = go.Figure()
        style_niv3 = {"display": "none"}

    return figure, warning, periode_text, slider_style, fig_niv3, style_niv3
