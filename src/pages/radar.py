"""Page dédiée à l'analyse des données via un graphique radar."""

from typing import Any

from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go

from src.components.icons import icon_pin
from src.utils.db_queries import (
    get_evolution_pathologies,
    get_liste_pathologies,
    get_liste_regions,
    get_pathologies_par_region,
)


def create_radar_figure(
    dimension: str = "pathologies",
    annee: int = 2023,
    selection: list[str] | None = None,
    region: str | None = None
) -> go.Figure:
    """Crée le graphique radar pour comparer les données selon la dimension choisie."""

    if dimension == "pathologies":
        df = get_evolution_pathologies(annee, annee, None, region)
        df = df.sort_values("total_cas", ascending=False)
        categories = df["patho_niv1"].tolist()
        values = df["total_cas"].tolist()
        title = f"Répartition des pathologies en {annee}"

    elif dimension == "regions":
        df = get_pathologies_par_region(annee)
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
        df = df.sort_values("total_cas", ascending=False)
        categories = df["region_name"].tolist()
        values = df["total_cas"].tolist()
        title = f"Répartition par région en {annee}"

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

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name=str(annee)
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
                                className="filter-section",
                                children=[
                                    html.Label("Année"),
                                    dcc.Slider(
                                        id="radar-annee-slider",
                                        min=2015,
                                        max=2023,
                                        value=2023,
                                        marks={
                                            2015: '2015',
                                            2017: '2017',
                                            2019: '2019',
                                            2021: '2021',
                                            2023: '2023'
                                        },
                                        step=1,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True
                                        },
                                    ),
                                    html.Div(id="radar-annee-display"),
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
                    dcc.Graph(
                        id="radar-graph",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                        },
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
        ])


# === Callbacks ===
@callback(
    [
        Output("radar-elements-dropdown", "options"),
        Output("radar-elements-dropdown", "value"),
    ],
    Input("radar-dimension-dropdown", "value"),
)
def update_elements_options(
    dimension: str
) -> tuple[list[dict[str, str]], list[str] | None]:
    """Met à jour le contenu du dropdown selon la dimension."""
    if dimension == "pathologies":
        pathologies = get_liste_pathologies()
        options = [{"label": p, "value": p} for p in pathologies]
        return options, pathologies

    # régions
    regions = get_liste_regions()
    regions = [r for r in regions if len(r) == 2]
    options = [{"label": r, "value": r} for r in regions]
    options = sorted(options, key=lambda x: x["label"])
    return options, None


@callback(
    [
        Output("radar-graph", "figure"),
        Output("radar-warning", "children"),
        Output("radar-annee-display", "children"),
        Output("radar-annee-slider", "style"),
    ],
    [
        Input("radar-dimension-dropdown", "value"),
        Input("radar-annee-slider", "value"),
        Input("radar-elements-dropdown", "value"),
    ],
)
def update_radar(
    dimension: str,
    annee: int,
    selection: list[str]
) -> tuple[go.Figure, str, str, dict[str, Any]]:
    """Met à jour le graphique radar."""
    warning = ""
    annee_text = f"Année sélectionnée : {annee}"
    slider_style: dict[str, Any] = {}

    figure = create_radar_figure(dimension, annee, selection)
    return figure, warning, annee_text, slider_style
