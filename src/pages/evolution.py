"""Page dédiée à l'évolution temporelle des pathologies."""

from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from src.utils.db_queries import get_evolution_pathologies, get_liste_pathologies
from src.components.icons import icon_chart_bar, icon_pin

def create_evolution_figure(debut_annee=2019, fin_annee=2023, pathologie=None, region=None):
    """Crée le graphique d'évolution temporelle des pathologies.
    
    Args:
        debut_annee (int): Année de début
        fin_annee (int): Année de fin
        pathologie (str, optional): Pathologie spécifique à filtrer
        region (str, optional): Région spécifique à filtrer
        
    Returns:
        plotly.graph_objects.Figure: Figure du graphique d'évolution
    """
    df = get_evolution_pathologies(debut_annee, fin_annee, pathologie, region)
    
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
                html.Div([
                    html.Label("Période d'analyse", className="form-label"),
                    html.Div(className="d-flex", style={'gap': '12px'}, children=[
                        html.Div(style={'flex': '1'}, children=[
                            html.Label("De :", className="form-sublabel"),
                            dcc.Dropdown(
                                id='evolution-debut-annee',
                                options=[{'label': str(year), 'value': year} for year in range(2019, 2024)],
                                value=2019,
                                clearable=False,
                            )
                        ]),
                        html.Div(style={'flex': '1'}, children=[
                            html.Label("À :", className="form-sublabel"),
                            dcc.Dropdown(
                                id='evolution-fin-annee',
                                options=[{'label': str(year), 'value': year} for year in range(2019, 2024)],
                                value=2023,
                                clearable=False,
                            )
                        ])
                    ])
                ]),
                
                # Sélection de la pathologie
                html.Div([
                    html.Label("Pathologie", className="form-label"),
                    dcc.Dropdown(
                        id='evolution-pathologie-dropdown',
                        options=[{'label': 'Toutes les pathologies', 'value': 'ALL'}] + 
                                [{'label': p, 'value': p} for p in pathologies],
                        value='ALL',
                        clearable=False,
                    )
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
    Output('evolution-graph', 'figure'),
    [Input('evolution-debut-annee', 'value'),
     Input('evolution-fin-annee', 'value'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_evolution(debut_annee, fin_annee, pathologie):
    """Met à jour le graphique d'évolution.
    
    Args:
        debut_annee (int): Année de début
        fin_annee (int): Année de fin
        pathologie (str): Pathologie sélectionnée
        
    Returns:
        plotly.graph_objects.Figure: Figure mise à jour
    """
    # Vérifier que la période est valide
    if debut_annee > fin_annee:
        debut_annee, fin_annee = fin_annee, debut_annee
    
    patho_filter = None if pathologie == 'ALL' else pathologie
    return create_evolution_figure(debut_annee, fin_annee, patho_filter)

@callback(
    Output('evolution-stats', 'children'),
    [Input('evolution-graph', 'figure')]
)
def update_stats(figure):
    """Met à jour les statistiques affichées."""
    if not figure or 'data' not in figure or not figure['data']:
        return html.P("Aucune donnée disponible", className="text-center text-muted")

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
                # On s'arrête quand on ne trouve plus d'index numérique
                if str(i) not in input_array:
                    break
                    
                try:
                    # Convertir uniquement les valeurs numériques
                    value = float(input_array[str(i)])
                    values.append(value)
                except (ValueError, TypeError):
                    pass
                i += 1
            
            # Calculer les statistiques si nous avons au moins 2 points
            if len(values) >= 2:
                total = sum(values)
                moyenne = total / len(values)
                evolution = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                
                # Créer la carte de statistiques
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
    
    return html.Div(
        className="stats-grid",
        children=stats_components if stats_components else html.P(
            "Aucune statistique disponible",
            className="text-center text-muted"
        )
    )