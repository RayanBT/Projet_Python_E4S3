"""
Page de visualisation de la répartition de la gravité des pathologies
avec un diagramme en camembert (pie chart)
"""

from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
from src.utils.db_queries import (
    get_repartition_gravite,
    get_annees_disponibles,
    get_liste_regions,
    get_liste_pathologies
)


def layout() -> html.Div:
    """Retourne le layout de la page camembert"""
    # Récupération des données pour les filtres
    annees = get_annees_disponibles()
    regions_codes = get_liste_regions()
    pathologies = ['Toutes'] + get_liste_pathologies()
    
    # Mapping des codes régions vers noms complets
    region_names = {
        "01": "Guadeloupe (01)",
        "02": "Martinique (02)",
        "03": "Guyane (03)",
        "04": "La Réunion (04)",
        "05": "Saint-Pierre-et-Miquelon (05)",
        "06": "Mayotte (06)",
        "11": "Île-de-France (11)",
        "24": "Centre-Val de Loire (24)",
        "27": "Bourgogne-Franche-Comté (27)",
        "28": "Normandie (28)",
        "32": "Hauts-de-France (32)",
        "44": "Grand Est (44)",
        "52": "Pays de la Loire (52)",
        "53": "Bretagne (53)",
        "75": "Nouvelle-Aquitaine (75)",
        "76": "Occitanie (76)",
        "84": "Auvergne-Rhône-Alpes (84)",
        "93": "Provence-Alpes-Côte d'Azur (93)",
        "94": "Corse (94)",
    }
    
    # Options pour le dropdown avec noms complets
    regions_options = [{'label': 'Toutes', 'value': 'Toutes'}]
    regions_options += [{'label': region_names.get(code, code), 'value': code} for code in regions_codes]
    
    # Layout de la page
    return html.Div([
    # En-tête
    html.Div(className="mb-3", children=[
        html.H1(
            "Répartition de la Gravité des Pathologies",
            className="page-title text-center"
        ),
        html.P(
            (
                "Analysez la répartition de la gravité pour différentes pathologies. "
                "Comparez les différentes pathologies et observez les tendances."
            ),
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
                        id='camembert-periode-slider',
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
                        id='camembert-periode-display',
                        className="period-display"
                    )
                ])
            ]),
            
            # Sélection de la région
            html.Div(className="filter-section", children=[
                html.Label("Région", className="form-label"),
                html.Div(className="filter-content", children=[
                    dcc.Dropdown(
                        id='camembert-region-dropdown',
                        options=regions_options,
                        value='Toutes',
                        clearable=False,
                        className="filter-dropdown"
                    ),
                ])
            ]),
            
            # Sélection de la pathologie
            html.Div(className="filter-section", children=[
                html.Label("Pathologie", className="form-label"),
                html.Div(className="filter-content", children=[
                    dcc.Dropdown(
                        id='camembert-pathologie-dropdown',
                        options=[{'label': patho, 'value': patho} for patho in pathologies],
                        value='Toutes',
                        clearable=False,
                        className="filter-dropdown"
                    ),
                ])
            ]),
        ])
    ]),
    
    # Graphique principal
    html.Div(className="card mt-2", children=[
        dcc.Graph(
            id='camembert-graph',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
            }
        )
    ]),
    
    # Statistiques complémentaires
    html.Div(className="card mt-2", children=[
        html.Div(id='camembert-stats')
    ]),
    
    ], className="page-container")


@callback(
    [Output('camembert-graph', 'figure'),
     Output('camembert-stats', 'children'),
     Output('camembert-periode-display', 'children')],
    [Input('camembert-periode-slider', 'value'),
     Input('camembert-region-dropdown', 'value'),
     Input('camembert-pathologie-dropdown', 'value')]
)
def update_camembert(periode, region, pathologie):
    """
    Met à jour le diagramme en camembert et les statistiques
    """
    debut_annee, fin_annee = periode
    periode_text = f"De {debut_annee} à {fin_annee}"
    
    # Récupération des données
    df = get_repartition_gravite(debut_annee, fin_annee, region, pathologie)
    
    if df.empty:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible pour les critères sélectionnés",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig, html.Div("Aucune donnée disponible"), periode_text
    
    # Préparation des données pour le graphique
    labels = []
    values = []
    colors_map = {
        '1': '#d32f2f',      # Rouge foncé - Priorité 1 (très grave)
        '2': '#f57c00',      # Orange - Priorité 2 (grave)
        '3': '#fbc02d',      # Jaune - Priorité 3 (modéré)
        '1,2,3': '#7b1fa2',  # Violet - Multiple
        '2,3': '#1976d2',    # Bleu - Multiple
    }
    
    label_map = {
        '1': 'Très grave (1)',
        '2': 'Moyennement grave (2)',
        '3': 'Pas très grave (3)',
        '1,2,3': 'Gravités multiples (1,2,3)',
        '2,3': 'Gravités multiples modérées (2,3)',
    }
    
    colors = []
    total_cas = 0
    
    for _, row in df.iterrows():
        niveau = row['Niveau_prioritaire']
        cas = row['total_cas']
        if niveau:
            labels.append(label_map.get(niveau, f'Niveau {niveau}'))
            values.append(cas)
            colors.append(colors_map.get(niveau, '#9e9e9e'))
            total_cas += cas
    
    # Création du diagramme en camembert
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>' +
                      'Nombre de cas: %{value:,.0f}<br>' +
                      'Pourcentage: %{percent}<br>' +
                      '<extra></extra>'
    )])
    
    # Mise en forme du graphique
    title_text = f"Répartition par Niveau de Gravité ({debut_annee}-{fin_annee})"
    if region != 'Toutes':
        title_text += f" - {region}"
    if pathologie != 'Toutes':
        title_text += f" - {pathologie}"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#2c3e50')
        ),
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=12)
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=200, t=80, b=20)
    )
    
    # Statistiques complémentaires
    stats_children = [
        html.H3("📊 Statistiques détaillées", style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.Span("Total de cas analysés", className="stat-label"),
                    html.Span(f"{total_cas:,.0f}", className="stat-value"),
                ], className="stat-card"),
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("Niveau de gravité"),
                        html.Th("Nombre de cas"),
                        html.Th("Pourcentage"),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(labels[i]),
                            html.Td(f"{values[i]:,.0f}"),
                            html.Td(f"{(values[i]/total_cas*100):.2f}%"),
                        ], style={'backgroundColor': colors[i] + '20'})
                        for i in range(len(labels))
                    ])
                ], className="stats-table")
            ])
        ])
    ]
    
    return fig, stats_children, periode_text