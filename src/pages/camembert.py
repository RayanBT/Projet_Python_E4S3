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
    regions = ['Toutes'] + get_liste_regions()
    pathologies = ['Toutes'] + get_liste_pathologies()
    
    # Layout de la page
    return html.Div([
    html.Div([
        html.H1("Répartition de la Gravité des Pathologies", className="page-title"),
        html.P(
            "Distribution des pathologies selon leur niveau de priorité (gravité)",
            className="page-subtitle"
        ),
    ], className="page-header"),
    
    # Filtres
    html.Div([
        html.Div([
            html.Label("Année :", className="filter-label"),
            dcc.Dropdown(
                id='camembert-annee-dropdown',
                options=[{'label': str(annee), 'value': annee} for annee in annees],
                value=annees[0] if annees else 2023,
                clearable=False,
                className="filter-dropdown"
            ),
        ], className="filter-item"),
        
        html.Div([
            html.Label("Région :", className="filter-label"),
            dcc.Dropdown(
                id='camembert-region-dropdown',
                options=[{'label': region, 'value': region} for region in regions],
                value='Toutes',
                clearable=False,
                className="filter-dropdown"
            ),
        ], className="filter-item"),
        
        html.Div([
            html.Label("Pathologie :", className="filter-label"),
            dcc.Dropdown(
                id='camembert-pathologie-dropdown',
                options=[{'label': patho, 'value': patho} for patho in pathologies],
                value='Toutes',
                clearable=False,
                className="filter-dropdown"
            ),
        ], className="filter-item"),
    ], className="filters-container"),
    
    # Graphique principal
    html.Div([
        dcc.Graph(id='camembert-graph', className="graph-container")
    ], className="content-container"),
    
    # Statistiques complémentaires
    html.Div(id='camembert-stats', className="stats-container"),
    
    ], className="page-container")


@callback(
    [Output('camembert-graph', 'figure'),
     Output('camembert-stats', 'children')],
    [Input('camembert-annee-dropdown', 'value'),
     Input('camembert-region-dropdown', 'value'),
     Input('camembert-pathologie-dropdown', 'value')]
)
def update_camembert(annee, region, pathologie):
    """
    Met à jour le diagramme en camembert et les statistiques
    """
    # Récupération des données
    df = get_repartition_gravite(annee, region, pathologie)
    
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
        return fig, html.Div("Aucune donnée disponible")
    
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
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>' +
                      'Nombre de cas: %{value:,.0f}<br>' +
                      'Pourcentage: %{percent}<br>' +
                      '<extra></extra>',
        pull=[0.05 if i == 0 else 0 for i in range(len(labels))],  # Détacher la première tranche
    )])
    
    # Mise en forme du graphique
    title_text = f"Répartition par Niveau de Gravité - {annee}"
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
    
    return fig, stats_children