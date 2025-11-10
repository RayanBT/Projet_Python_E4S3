"""Page dédiée à l'évolution temporelle des pathologies."""

import math
from typing import Any

from dash import Input, Output, callback, clientside_callback, dcc, html
import plotly.express as px
import plotly.graph_objects as go

from src.components.icons import icon_chart_bar, icon_pin
from src.utils.db_queries import get_evolution_pathologies, get_liste_pathologies


def create_evolution_figure(
    debut_annee: int = 2015,
    fin_annee: int = 2023,
    pathologies: list[str] | str | None = None,
    region: str | None = None
) -> go.Figure:
    """Crée le graphique d'évolution temporelle des pathologies.

    Args:
        debut_annee (int): Année de début
        fin_annee (int): Année de fin
        pathologies (list, optional): Liste des pathologies à afficher
        region (str, optional): Région spécifique à filtrer

    Returns:
        plotly.graph_objects.Figure: Figure du graphique d'évolution
    """
    if isinstance(pathologies, str):
        pathologies = [pathologies]

    df = get_evolution_pathologies(debut_annee, fin_annee, None, region)

    if pathologies:
        df = df[df["patho_niv1"].isin(pathologies)]

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible pour cette sélection",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 20}
        )
        fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            height=600
        )
        return fig

    fig = px.line(
        df,
        x="annee",
        y="total_cas",
        color="patho_niv1",
        title=f"Évolution des pathologies de {debut_annee} à {fin_annee}",
        labels={
            "annee": "Année",
            "total_cas": "Nombre de cas",
            "patho_niv1": "Pathologie"
        },
        markers=True,
        hover_data={"annee": True, "total_cas": ":,.0f", "patho_niv1": True}
    )

    fig.update_layout(
        height=600,
        hovermode='x unified',
        legend_title="Pathologies",
        xaxis={
            "tickmode": 'linear',
            "tick0": debut_annee,
            "dtick": 1
        },
        yaxis={
            "title": "Nombre de cas",
            "tickformat": ","
        },
        title_x=0.5,
        title_font_size=20,
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        margin={"r": 20, "t": 80, "l": 80, "b": 60}
    )

    fig.update_traces(
        line={"width": 3},
        marker={"size": 8}
    )

    # Ajuster l'échelle Y pour des graduations "propres"
    try:
        y_vals = df['total_cas'].dropna()
        if not y_vals.empty:
            y_min = float(y_vals.min())
            y_max = float(y_vals.max())
            span = y_max - y_min
            if span <= 0:
                pad = max(1.0, abs(y_max) * 0.05)
                new_min = max(0.0, y_min - pad)
                new_max = y_max + pad
                fig.update_yaxes(range=[new_min, new_max])
            else:
                target_intervals = 4.0
                raw_step = span / target_intervals

                magnitude = int(math.floor(math.log10(max(1.0, y_max))))
                unit = int(10 ** max(0, magnitude - 1))
                unit = max(1, unit)

                factors = [0.25, 0.5, 1, 2, 5, 10]
                candidates = [unit * f for f in factors]

                viable = [c for c in candidates if c >= raw_step]
                step = None
                if viable:
                    step = min(viable)
                else:
                    step = max(candidates)

                new_min = math.floor(y_min / step) * step
                new_max = math.ceil(y_max / step) * step
                if new_min == new_max:
                    new_max = new_min + step

                fig.update_yaxes(range=[new_min, new_max], tick0=new_min, dtick=step)
    except Exception:
        pass

    return fig


def layout() -> html.Div:
    """Construit le layout de la page évolution temporelle."""
    pathologies = get_liste_pathologies()

    return html.Div(className="page-container", children=[
        html.Div(className="mb-3", children=[
            html.H1(
                "Évolution Temporelle des Pathologies",
                className="page-title text-center"
            ),
            html.P(
                (
                    "Analysez l'évolution du nombre de cas de pathologies au fil du temps. "
                    "Comparez les différentes pathologies et observez les tendances."
                ),
                className="text-center text-muted"
            ),
        ]),

        html.Div(className="card", children=[
            html.Div(className="flex-controls", children=[
                html.Div(className="filter-section period-filter", children=[
                    html.Label("Période d'analyse", className="form-label"),
                    html.Div(className="filter-content", children=[
                        dcc.RangeSlider(
                            id='periode-slider',
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
                            id='periode-display',
                            className="period-display"
                        )
                    ])
                ]),

                html.Div(className="filter-section pathologies-filter", children=[
                    html.Label("Pathologies", className="form-label"),
                    html.Div(className="filter-content", children=[
                        dcc.Dropdown(
                            id='evolution-pathologie-dropdown',
                            options=[{'label': p, 'value': p} for p in pathologies],
                            value=[],
                            multi=True,
                            placeholder=(
                                "Sélectionnez jusqu'à 5 pathologies (toutes si vide)"
                            ),
                            clearable=True,
                            className="pathologies-dropdown"
                        ),
                        html.Div(
                            id='pathologie-counter',
                            className="pathologie-counter",
                            children="0/5 sélectionnées"
                        ),
                        html.Div(
                            id='pathologie-warning',
                            className="filter-warning"
                        )
                    ])
                ])
            ])
        ]),

        html.Div(className="card mt-2", children=[
            dcc.Graph(
                id='evolution-graph',
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                }
            )
        ]),

        html.Div(className="card mt-2", children=[
            html.H3(
                [icon_chart_bar("icon-inline"), "Statistiques clés"],
                className="subsection-title"
            ),
            html.Div(id='evolution-stats', children=[
                html.P(
                    "Sélectionnez des données pour voir les statistiques.",
                    className="text-center text-muted p-2"
                )
            ])
        ]),

        html.Div(className="card mt-2", children=[
            html.H3(
                [icon_pin("icon-inline"), "Comment interpréter ce graphique ?"],
                className="subsection-title"
            ),
            html.Ul(className="info-list", children=[
                html.Li("Chaque ligne représente une pathologie différente"),
                html.Li("Les points indiquent les valeurs exactes pour chaque année"),
                html.Li("Survolez les points pour voir les détails précis"),
                html.Li("Utilisez la légende pour afficher/masquer des pathologies"),
                html.Li("Cliquez et glissez pour zoomer sur une période spécifique"),
            ]),

            html.Div(className="alert alert-info mt-2", children=[
                html.Strong("💡 Astuce : "),
                (
                    "Double-cliquez sur le graphique pour réinitialiser "
                    "le zoom et voir toutes les données."
                )
            ])
        ]),

        html.Div(className="text-center mt-3", children=[
            dcc.Link(
                html.Button("← Retour à l'accueil", className="btn btn-secondary"),
                href='/',
            ),
            dcc.Link(
                html.Button(
                    "Voir la carte choroplèthe →",
                    className="btn btn-primary",
                    style={'marginLeft': '10px'}
                ),
                href='/carte',
            ),
        ])

    ])


clientside_callback(
    """
    function(selectedValues, allOptions) {
        if (!selectedValues || selectedValues.length < 5) {
            return [
                allOptions.map(opt => ({...opt, disabled: false})),
                selectedValues ? selectedValues.length + '/5 sélectionnées' : '0/5 sélectionnées',
                ''
            ];
        }

        if (selectedValues.length === 5) {
            const updatedOptions = allOptions.map(opt => ({
                ...opt,
                disabled: !selectedValues.includes(opt.value)
            }));
            return [
                updatedOptions,
                '5/5 sélectionnées (MAX)',
                ''
            ];
        }

        if (selectedValues.length > 5) {
            const firstFive = selectedValues.slice(0, 5);
            const updatedOptions = allOptions.map(opt => ({
                ...opt,
                disabled: !firstFive.includes(opt.value)
            }));
            return [
                updatedOptions,
                '5/5 sélectionnées (MAX)',
                '⚠️ Maximum 5 pathologies ! Les 5 premières ont été conservées.'
            ];
        }
    }
    """,
    [Output('evolution-pathologie-dropdown', 'options', allow_duplicate=True),
     Output('pathologie-counter', 'children', allow_duplicate=True),
     Output('pathologie-warning', 'children', allow_duplicate=True)],
    [Input('evolution-pathologie-dropdown', 'value'),
     Input('evolution-pathologie-dropdown', 'options')],
    prevent_initial_call=True
)


@callback(
    [Output('evolution-graph', 'figure'),
     Output('periode-display', 'children')],
    [Input('periode-slider', 'value'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_evolution(
    periode: list[int],
    pathologies: list[str]
) -> tuple[go.Figure, str]:
    """Met à jour le graphique d'évolution.

    Args:
        periode (list): Liste contenant l'année de début et de fin [debut, fin]
        pathologies (list): Liste des pathologies sélectionnées

    Returns:
        tuple: (Figure, Texte période)
    """
    debut_annee, fin_annee = periode

    periode_text = f"De {debut_annee} à {fin_annee}"

    if pathologies and len(pathologies) > 5:
        pathologies = pathologies[:5]

    if not pathologies:
        figure = create_evolution_figure(debut_annee, fin_annee, None)
        return figure, periode_text

    figure = create_evolution_figure(debut_annee, fin_annee, pathologies)

    return figure, periode_text


@callback(
    Output('evolution-stats', 'children'),
    [Input('evolution-graph', 'figure'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_stats(
    figure: dict[str, Any],
    selected_pathologies: list[str]
) -> html.Div | html.P:
    """Met à jour les statistiques affichées."""
    if not figure or 'data' not in figure or not figure['data']:
        return html.P("Aucune donnée disponible", className="text-center text-muted")

    yearly_totals: dict[int, float] = {}
    total_values = []
    stats_components = []

    for trace in figure['data']:
        try:
            patho_name = trace.get('name', 'Inconnue')

            if ('y' not in trace or not isinstance(trace['y'], dict)
                    or '_inputArray' not in trace['y']):
                continue

            input_array = trace['y']['_inputArray']
            values = []

            i = 0
            while True:
                if str(i) not in input_array:
                    break

                try:
                    value = float(input_array[str(i)])
                    values.append(value)

                    if not selected_pathologies:
                        yearly_totals[i] = yearly_totals.get(i, 0) + value
                        total_values.append(value)
                except (ValueError, TypeError):
                    pass
                i += 1

            if selected_pathologies and len(values) >= 2:
                total = sum(values)
                moyenne = total / len(values)
                evolution = (
                    ((values[-1] - values[0]) / values[0] * 100)
                    if values[0] != 0
                    else 0
                )

                stats_components.append(
                    html.Div(
                        className="stat-card",
                        children=[
                            html.H4(patho_name, className="stat-title"),
                            html.Div(
                                className="stat-details",
                                children=[
                                    html.Div([
                                        html.Strong("Total : "),
                                        html.Span(f"{total:,.0f} cas")
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("Moyenne annuelle : "),
                                        html.Span(f"{moyenne:,.0f} cas")
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("Évolution : "),
                                        html.Span(
                                            f"{evolution:+.1f}%",
                                            style={
                                                'color': '#27ae60' if evolution >= 0 else '#e74c3c',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ], className="mb-2")
                                ]
                            )
                        ]
                    )
                )
        except Exception as e:
            print(f"Erreur lors du traitement de la pathologie {patho_name}: {str(e)}")
            continue

    if not selected_pathologies and yearly_totals:
        total_global = sum(total_values)
        moyenne_globale = total_global / (len(yearly_totals) * len(figure['data']))
        max_year = max(yearly_totals.keys())
        evolution_globale = (
            (yearly_totals[max_year] - yearly_totals[0]) / yearly_totals[0] * 100
        )

        stats_components = [html.Div(
            className="stat-card",
            children=[
                html.H4("Statistiques Globales", className="stat-title"),
                html.Div(
                    className="stat-details",
                    children=[
                        html.Div([
                            html.Strong("Total toutes pathologies : "),
                            html.Span(f"{total_global:,.0f} cas")
                        ], className="mb-2"),
                        html.Div([
                            html.Strong("Moyenne annuelle globale : "),
                            html.Span(f"{moyenne_globale:,.0f} cas")
                        ], className="mb-2"),
                        html.Div([
                            html.Strong("Évolution globale : "),
                            html.Span(
                                f"{evolution_globale:+.1f}%",
                                style={
                                    'color': '#27ae60' if evolution_globale >= 0 else '#e74c3c',
                                    'fontWeight': 'bold'
                                }
                            )
                        ], className="mb-2"),
                        html.Div([
                            html.Strong("Nombre de pathologies : "),
                            html.Span(f"{len(figure['data'])}")
                        ], className="mb-2")
                    ]
                )
            ]
        )]

    return html.Div(
        className="stats-grid",
        children=stats_components if stats_components else html.P(
            "Aucune statistique disponible",
            className="text-center text-muted"
        )
    )
