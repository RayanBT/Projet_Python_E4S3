"""Page dédiée à l'évolution temporelle des pathologies."""

from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from src.utils.db_queries import get_evolution_pathologies, get_liste_pathologies
from src.components.icons import icon_chart_bar, icon_pin

def create_evolution_figure(debut_annee=2019, fin_annee=2023, pathologies=None, region=None):
    """Crée le graphique d'évolution temporelle des pathologies.
    
    Args:
        debut_annee (int): Année de début
        fin_annee (int): Année de fin
        pathologies (list, optional): Liste des pathologies à afficher
        region (str, optional): Région spécifique à filtrer
        
    Returns:
        plotly.graph_objects.Figure: Figure du graphique d'évolution
    """
    # Si pathologies est une chaîne unique, la convertir en liste
    if isinstance(pathologies, str):
        pathologies = [pathologies]
    
    # Obtenir toutes les données
    df = get_evolution_pathologies(debut_annee, fin_annee, None, region)
    
    # Filtrer pour les pathologies sélectionnées si nécessaire
    if pathologies:
        df = df[df["patho_niv1"].isin(pathologies)]
    
    if df.empty:
        # Créer une figure vide avec un message
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible pour cette sélection",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            height=600
        )
        return fig
    
    # Créer le graphique en ligne
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
        xaxis=dict(
            tickmode='linear',
            tick0=debut_annee,
            dtick=1
        ),
        yaxis=dict(
            title="Nombre de cas",
            tickformat=","
        ),
        title_x=0.5,
        title_font_size=20,
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        margin={"r": 20, "t": 80, "l": 80, "b": 60}
    )
    
    # Améliorer la lisibilité des lignes
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )
    
    return fig

def layout():
    """Construit le layout de la page évolution temporelle."""
    pathologies = get_liste_pathologies()
    
    return html.Div(className="page-container", children=[
        # En-tête
        html.Div(className="mb-3", children=[
            html.H1("Évolution Temporelle des Pathologies", className="page-title text-center"),
            html.P(
                "Analysez l'évolution du nombre de cas de pathologies au fil du temps. "
                "Comparez les différentes pathologies et observez les tendances.",
                className="text-center text-muted"
            ),
        ]),
        
        # Panneau de filtres
        html.Div(className="card", children=[
            html.Div(className="flex-controls", children=[
                # Sélection de la période
                html.Div(className="filter-section period-filter", children=[
                    html.Label("Période d'analyse", className="form-label"),
                    html.Div(className="filter-content", children=[
                        dcc.RangeSlider(
                            id='evolution-periode-slider',
                            min=2019,
                            max=2023,
                            value=[2019, 2023],
                            marks={str(year): str(year) for year in range(2019, 2024)},
                            step=None,
                            className="period-slider"
                        ),
                        html.Div(
                            id='periode-display',
                            className="period-display"
                        )
                    ])
                ]),
                
                # Sélection des pathologies (jusqu'à 5)
                html.Div(className="filter-section pathologies-filter", children=[
                    html.Label("Pathologies", className="form-label"),
                    html.Div(className="filter-content", children=[
                        dcc.Dropdown(
                            id='evolution-pathologie-dropdown',
                            options=[{'label': p, 'value': p} for p in pathologies],
                            value=[],  # Aucune sélection par défaut = toutes les pathologies
                            multi=True,  # Active la sélection multiple
                            placeholder="Sélectionnez des pathologies (max. 5)",
                            clearable=True,
                            className="pathologies-dropdown"
                        ),
                        html.Div(
                            id='pathologie-warning',
                            className="filter-warning"
                        )
                    ])
                ])
            ])
        ]),
        
        # Graphique d'évolution
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
        
        # Statistiques clés
        html.Div(className="card mt-2", children=[
            html.H3([icon_chart_bar("icon-inline"), "Statistiques clés"], className="subsection-title"),
            html.Div(id='evolution-stats', children=[
                html.P("Sélectionnez des données pour voir les statistiques.", 
                      className="text-center text-muted p-2")
            ])
        ]),
        
        # Informations complémentaires
        html.Div(className="card mt-2", children=[
            html.H3([icon_pin("icon-inline"), "Comment interpréter ce graphique ?"], className="subsection-title"),
            html.Ul(className="info-list", children=[
                html.Li("Chaque ligne représente une pathologie différente"),
                html.Li("Les points indiquent les valeurs exactes pour chaque année"),
                html.Li("Survolez les points pour voir les détails précis"),
                html.Li("Utilisez la légende pour afficher/masquer des pathologies"),
                html.Li("Cliquez et glissez pour zoomer sur une période spécifique"),
            ]),
            
            html.Div(className="alert alert-info mt-2", children=[
                html.Strong("💡 Astuce : "),
                "Double-cliquez sur le graphique pour réinitialiser le zoom et voir toutes les données."
            ])
        ]),
        
        # Boutons de navigation
        html.Div(className="text-center mt-3", children=[
            dcc.Link(
                html.Button('← Retour à l\'accueil', className="btn btn-secondary"),
                href='/',
            ),
            dcc.Link(
                html.Button('Voir la carte choroplèthe →', className="btn btn-primary", style={'marginLeft': '10px'}),
                href='/carte',
            ),
        ])
        
    ])

@callback(
    [Output('evolution-graph', 'figure'),
     Output('pathologie-warning', 'children'),
     Output('evolution-pathologie-dropdown', 'value'),
     Output('periode-display', 'children')],
    [Input('evolution-periode-slider', 'value'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_evolution(periode, pathologies):
    """Met à jour le graphique d'évolution.
    
    Args:
        periode (list): Liste contenant l'année de début et de fin [debut, fin]
        pathologies (list): Liste des pathologies sélectionnées
        
    Returns:
        tuple: (Figure mise à jour, Message d'avertissement, Valeurs de sélection validées, Texte période)
    """
    debut_annee, fin_annee = periode
    
    warning = ""
    # Préparer le texte d'affichage de la période
    periode_text = f"De {debut_annee} à {fin_annee}"
    
    # Si la liste est vide, afficher toutes les pathologies
    if not pathologies:
        figure = create_evolution_figure(debut_annee, fin_annee, None)
        return figure, warning, [], periode_text
    
    # Si plus de 5 pathologies sont sélectionnées, garder les 5 premières
    if len(pathologies) > 5:
        pathologies = pathologies[:5]
        warning = "Maximum 5 pathologies peuvent être sélectionnées"
    
    # Créer une figure avec les pathologies sélectionnées
    figure = create_evolution_figure(debut_annee, fin_annee, pathologies)
    
    return figure, warning, pathologies, periode_text

@callback(
    Output('evolution-stats', 'children'),
    [Input('evolution-graph', 'figure'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_stats(figure, selected_pathologies):
    """Met à jour les statistiques affichées."""
    if not figure or 'data' not in figure or not figure['data']:
        return html.P("Aucune donnée disponible", className="text-center text-muted")

    yearly_totals = {}  # {année_index: total}
    total_values = []  # Pour stocker toutes les valeurs pour le calcul de la moyenne
    stats_components = []
    
    for trace in figure['data']:
        try:
            # Obtenir le nom de la pathologie
            patho_name = trace.get('name', 'Inconnue')
            
            # Extraire les valeurs numériques uniquement
            if 'y' not in trace or not isinstance(trace['y'], dict) or '_inputArray' not in trace['y']:
                continue
                
            input_array = trace['y']['_inputArray']
            values = []
            
            # Extraire uniquement les valeurs numériques en ignorant les métadonnées
            i = 0
            while True:
                if str(i) not in input_array:
                    break
                    
                try:
                    value = float(input_array[str(i)])
                    values.append(value)
                    
                    # Si aucune sélection spécifique, accumuler pour les stats globales
                    if not selected_pathologies:
                        yearly_totals[i] = yearly_totals.get(i, 0) + value
                        total_values.append(value)
                except (ValueError, TypeError):
                    pass
                i += 1
            
            # Si des pathologies sont sélectionnées, afficher leurs statistiques
            if selected_pathologies and len(values) >= 2:
                total = sum(values)
                moyenne = total / len(values)
                evolution = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                
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
    
    # Si aucune pathologie n'est sélectionnée, créer une carte de statistiques globales
    if not selected_pathologies and yearly_totals:
        total_global = sum(total_values)
        moyenne_globale = total_global / (len(yearly_totals) * len(figure['data']))
        evolution_globale = ((yearly_totals[max(yearly_totals.keys())] - yearly_totals[0]) / yearly_totals[0] * 100)
        
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