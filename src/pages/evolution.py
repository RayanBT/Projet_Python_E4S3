"""Page dédiée à l'évolution temporelle des pathologies."""

from dash import html, dcc, Input, Output, callback, clientside_callback
import plotly.express as px
import plotly.graph_objects as go
from src.utils.db_queries import get_evolution_pathologies, get_liste_pathologies
from src.components.icons import icon_chart_bar, icon_pin
import math

def create_evolution_figure(debut_annee=2015, fin_annee=2023, pathologies=None, region=None):
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
    # Ajuster l'échelle Y pour des graduations "propres" :
    # on cherche un pas arrondi (unité de type 10^n, ou 1/2, 1/4 de cette unité,
    # ou petits multiples) et on aligne min/max aux multiples de ce pas.
    try:
        y_vals = df['total_cas'].dropna()
        if not y_vals.empty:
            y_min = float(y_vals.min())
            y_max = float(y_vals.max())
            span = y_max - y_min
            if span <= 0:
                # données constantes : ajouter un petit padding
                pad = max(1.0, abs(y_max) * 0.05)
                new_min = max(0.0, y_min - pad)
                new_max = y_max + pad
                fig.update_yaxes(range=[new_min, new_max])
            else:
                # cible d'environ 4 intervalles (5 ticks)
                target_intervals = 4.0
                raw_step = span / target_intervals

                # Estimer une "unité" basée sur l'ordre de grandeur du maximum
                # On choisit 10^(digits-1) pour que 13000 -> unité = 1000
                magnitude = int(math.floor(math.log10(max(1.0, y_max))))
                unit = int(10 ** max(0, magnitude - 1))
                unit = max(1, unit)

                # candidats souhaités : 1/4, 1/2, 1, 2, 5, 10 fois l'unité
                factors = [0.25, 0.5, 1, 2, 5, 10]
                candidates = [unit * f for f in factors]

                # Choisir le candidat le plus proche du pas brut
                # mais préférer pas >= raw_step when possible to avoid too fine ticks
                viable = [c for c in candidates if c >= raw_step]
                step = None
                if viable:
                    # prendre le plus petit viable (le plus proche par excès)
                    step = min(viable)
                else:
                    # aucun viable (raw_step > max candidate), prendre le plus grand candidat
                    step = max(candidates)

                # Ajuster min/max aux multiples de step
                new_min = math.floor(y_min / step) * step
                new_max = math.ceil(y_max / step) * step
                if new_min == new_max:
                    new_max = new_min + step

                # Appliquer la nouvelle plage et le pas
                fig.update_yaxes(range=[new_min, new_max], tick0=new_min, dtick=step)
    except Exception:
        # En cas d'erreur, laisser Plotly gérer l'autorange
        pass
    
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
                
                # Sélection des pathologies (jusqu'à 5)
                html.Div(className="filter-section pathologies-filter", children=[
                    html.Label("Pathologies", className="form-label"),
                    html.Div(className="filter-content", children=[
                        dcc.Dropdown(
                            id='evolution-pathologie-dropdown',
                            options=[{'label': p, 'value': p} for p in pathologies],
                            value=[],  # Aucune sélection par défaut = toutes les pathologies
                            multi=True,  # Active la sélection multiple
                            placeholder="Sélectionnez jusqu'à 5 pathologies (toutes si vide)",
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

# ============================================================
# CALLBACK CLIENTSIDE (JavaScript) - Limitation instantanée
# ============================================================
clientside_callback(
    """
    function(selectedValues, allOptions) {
        // Si pas de sélection ou moins de 5, toutes les options disponibles
        if (!selectedValues || selectedValues.length < 5) {
            return [
                allOptions.map(opt => ({...opt, disabled: false})),
                selectedValues ? selectedValues.length + '/5 sélectionnées' : '0/5 sélectionnées',
                ''
            ];
        }
        
        // Si exactement 5, désactiver les autres
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
        
        // Si plus de 5 (copier-coller), garder les 5 premières
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

# ============================================================
# CALLBACK SERVEUR - Mise à jour du graphique
# ============================================================
@callback(
    [Output('evolution-graph', 'figure'),
     Output('periode-display', 'children')],
    [Input('periode-slider', 'value'),
     Input('evolution-pathologie-dropdown', 'value')]
)
def update_evolution(periode, pathologies):
    """Met à jour le graphique d'évolution.
    
    Args:
        periode (list): Liste contenant l'année de début et de fin [debut, fin]
        pathologies (list): Liste des pathologies sélectionnées
        
    Returns:
        tuple: (Figure, Texte période)
    """
    debut_annee, fin_annee = periode
    
    # Préparer le texte d'affichage de la période
    periode_text = f"De {debut_annee} à {fin_annee}"
    
    # Limiter à 5 pathologies si dépassement (sécurité serveur)
    if pathologies and len(pathologies) > 5:
        pathologies = pathologies[:5]
    
    # Si la liste est vide ou None, afficher toutes les pathologies
    if not pathologies:
        figure = create_evolution_figure(debut_annee, fin_annee, None)
        return figure, periode_text
    
    # Créer la figure avec les pathologies sélectionnées
    figure = create_evolution_figure(debut_annee, fin_annee, pathologies)
    
    return figure, periode_text

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